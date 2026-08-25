:- module(auto_dig_model_router,
          [ main/1,
            select_model/2
          ]).

:- use_module(library(error)).
:- use_module(library(http/json)).
:- use_module(library(option)).

:- initialization(main, main).

/*
 * Model-routing knowledge base.
 *
 * The router chooses a model from task facts.  The default worker is Luna Max;
 * larger tiers are escalation targets, not prestige defaults.
 */

model_spec(luna,
           _{provider:"openrouter",
             model:"openai/gpt-5.6-luna",
             family:"gpt-5.6",
             tier:"luna"}).
model_spec(terra,
           _{provider:"openrouter",
             model:"openai/gpt-5.6-terra",
             family:"gpt-5.6",
             tier:"terra"}).
model_spec(sol,
           _{provider:"openrouter",
             model:"openai/gpt-5.6-sol",
             family:"gpt-5.6",
             tier:"sol"}).

bulk_task(classification).
bulk_task(extraction).
bulk_task(normalization).
bulk_task(deduplication).
bulk_task(entity_resolution_candidate_generation).
bulk_task(queue_triage).

high_judgment_task(architecture).
high_judgment_task(threat_model).
high_judgment_task(security_adjudication).
high_judgment_task(final_adjudication).
high_judgment_task(publication_gate).

main(Argv) :-
    catch(main_run(Argv),
          Exception,
          ( print_message(error, Exception),
            fail
          )).

main_run(Argv) :-
    parse_args(Argv, Options),
    option(profile(ProfilePath), Options),
    option(output(OutputPath), Options),
    read_json_file(ProfilePath, Profile),
    select_model(Profile, Route),
    write_json_file(OutputPath, Route).

select_model(Profile0, Route) :-
    must_be(dict, Profile0),
    normalize_profile(Profile0, Profile),
    route_class(Profile, Tier, Effort, Reason),
    model_spec(Tier, Model),
    fallback_chain(Tier, Effort, Fallback),
    Route = _{
        schema:"auto-dig-model-route.v1",
        provider:Model.provider,
        model:Model.model,
        family:Model.family,
        tier:Model.tier,
        reasoning:_{effort:Effort},
        reason:Reason,
        task:Profile.task,
        phase:Profile.phase,
        risk:Profile.risk,
        failed_verifications:Profile.failed_verifications,
        fallback:Fallback
    }.

/* Hard gates first. */
route_class(Profile, sol, max,
            ["critical or irreversible work requires flagship adjudication"]) :-
    critical_profile(Profile),
    !.
route_class(Profile, sol, max,
            ["repeated verification failures exhausted lower-tier escalation"]) :-
    Profile.failed_verifications >= 2,
    !.
route_class(Profile, terra, max,
            ["one verification failure escalates from Luna before Sol"]) :-
    Profile.failed_verifications =:= 1,
    !.
route_class(Profile, luna, high,
            ["bulk deterministic work stays on Luna at reduced effort"]) :-
    bulk_task(Profile.task),
    Profile.risk \== high,
    !.
route_class(_, luna, max,
            ["Luna Max is the default bounded worker route"]).

critical_profile(Profile) :-
    Profile.risk == critical,
    !.
critical_profile(Profile) :-
    Profile.irreversible == true,
    !.
critical_profile(Profile) :-
    high_judgment_task(Profile.task).

fallback_chain(luna, high,
               [ _{provider:"openrouter",
                    model:"openai/gpt-5.6-luna",
                    reasoning:_{effort:"max"}},
                 _{provider:"openrouter",
                    model:"openai/gpt-5.6-terra",
                    reasoning:_{effort:"max"}},
                 _{provider:"openrouter",
                    model:"openai/gpt-5.6-sol",
                    reasoning:_{effort:"max"}}
               ]) :- !.
fallback_chain(luna, max,
               [ _{provider:"openrouter",
                    model:"openai/gpt-5.6-terra",
                    reasoning:_{effort:"max"}},
                 _{provider:"openrouter",
                    model:"openai/gpt-5.6-sol",
                    reasoning:_{effort:"max"}}
               ]) :- !.
fallback_chain(terra, _,
               [ _{provider:"openrouter",
                    model:"openai/gpt-5.6-sol",
                    reasoning:_{effort:"max"}}
               ]) :- !.
fallback_chain(sol, _, []).

normalize_profile(Profile0, Profile) :-
    profile_atom(Profile0, task, research, Task),
    profile_atom(Profile0, phase, execute, Phase),
    profile_atom(Profile0, risk, normal, Risk),
    profile_boolean(Profile0, irreversible, false, Irreversible),
    profile_nonnegative_integer(Profile0,
                                failed_verifications,
                                0,
                                FailedVerifications),
    Profile = _{
        task:Task,
        phase:Phase,
        risk:Risk,
        irreversible:Irreversible,
        failed_verifications:FailedVerifications
    }.

profile_atom(Dict, Key, Default, Value) :-
    (   get_dict(Key, Dict, Raw),
        Raw \== null
    ->  atom_value(Raw, Value)
    ;   Value = Default
    ).

profile_boolean(Dict, Key, Default, Value) :-
    (   get_dict(Key, Dict, Raw),
        Raw \== null
    ->  boolean_value(Raw, Value)
    ;   Value = Default
    ).

profile_nonnegative_integer(Dict, Key, Default, Value) :-
    (   get_dict(Key, Dict, Raw),
        Raw \== null
    ->  must_be(nonneg, Raw),
        Value = Raw
    ;   Value = Default
    ).

atom_value(Value, Value) :-
    atom(Value),
    !.
atom_value(Value, Atom) :-
    string(Value),
    !,
    string_lower(Value, Lower),
    atom_string(Atom, Lower).
atom_value(Value, _) :-
    throw(error(type_error(atom_or_string, Value),
                context(auto_dig_model_router,
                        'task profile values must be atoms or strings'))).

boolean_value(true, true) :- !.
boolean_value(false, false) :- !.
boolean_value("true", true) :- !.
boolean_value("false", false) :- !.
boolean_value(Value, _) :-
    throw(error(type_error(boolean, Value),
                context(auto_dig_model_router,
                        'boolean task profile value is invalid'))).

parse_args(Argv, Options) :-
    parse_args_(Argv, [], Options0),
    reverse(Options0, Options),
    require_option(profile, Options),
    require_option(output, Options).

parse_args_([], Options, Options).
parse_args_(['--profile', Path|Rest], Acc, Options) :-
    !,
    parse_args_(Rest, [profile(Path)|Acc], Options).
parse_args_(['--output', Path|Rest], Acc, Options) :-
    !,
    parse_args_(Rest, [output(Path)|Acc], Options).
parse_args_([Unknown|_], _, _) :-
    throw(error(unknown_argument(Unknown),
                context(auto_dig_model_router:main/1,
                        'expected --profile or --output'))).

require_option(Name, Options) :-
    Term =.. [Name, _],
    (   memberchk(Term, Options)
    ->  true
    ;   throw(error(missing_argument(Name),
                    context(auto_dig_model_router:main/1,
                            'required router argument is missing')))
    ).

read_json_file(Path, Value) :-
    setup_call_cleanup(
        open(Path, read, Stream, [encoding(utf8)]),
        json_read_dict(Stream, Value),
        close(Stream)).

write_json_file(Path, Value) :-
    setup_call_cleanup(
        open(Path, write, Stream, [encoding(utf8)]),
        ( json_write_dict(Stream, Value, [width(0)]), nl(Stream) ),
        close(Stream)).

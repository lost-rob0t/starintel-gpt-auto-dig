:- module(auto_dig_prolog_actor,
          [ main/1,
            select_queue/3
          ]).

:- use_module(library(http/json)).
:- use_module(library(lists)).
:- use_module(library(option)).
:- use_module(library(rlm_agent)).

:- initialization(main, main).

main(Argv) :-
    catch(main_run(Argv),
          Exception,
          ( print_message(error, Exception),
            fail
          )).

main_run(Argv) :-
    parse_args(Argv, Options),
    option(queue(QueuePath), Options),
    option(state(StatePath), Options),
    option(output(OutputPath), Options),
    option(trace(TracePath), Options, ''),
    read_json_file(QueuePath, Queue),
    read_json_file(StatePath, State),
    setup_call_cleanup(
        agent_runtime_create(
            [ max_agents(4),
              mailbox_size(8),
              worker_count(1),
              worker_backlog(1)
            ],
            Runtime),
        run_actor(Runtime, Queue, State, Decision, Trace),
        agent_runtime_destroy(Runtime)),
    write_json_file(OutputPath, Decision),
    maybe_write_trace(TracePath, Trace).

run_actor(Runtime, Queue, State, Decision, Trace) :-
    agent_spawn(Runtime,
                none,
                agent_spec{
                    name:auto_dig_queue_selector,
                    mode:worker,
                    metadata:agent_metadata{kind:"auto-dig", version:1}
                },
                [],
                SpawnOutcome),
    require_ok(spawn, SpawnOutcome),
    SpawnOutcome = ok(Actor),
    agent_supervised_call(Runtime,
                          Actor,
                          auto_dig_prolog_actor:worker_handler,
                          work(select, Queue, State),
                          [timeout(5.0)],
                          CallOutcome),
    require_decision(CallOutcome, Decision),
    agent_trace(Runtime, Trace).

worker_handler(work(select, Queue, State), Decision) :-
    select_queue(Queue, State, Decision).

select_queue(Queue, State, Decision) :-
    must_be(list, Queue),
    must_be(dict, State),
    maplist(enrich_issue, Queue, Enriched0),
    predsort(compare_candidates, Enriched0, Enriched),
    length(Enriched, QueueSize),
    state_last_issue(State, LastIssue),
    (   choose_candidate(Enriched, LastIssue, Selected)
    ->  selected_decision(Selected, State, QueueSize, Decision)
    ;   Decision = _{
            action:"idle",
            reason:"no eligible investigation target without violating repeat policy",
            queue_size:QueueSize,
            next_state:State
        }
    ).

enrich_issue(Issue, Candidate) :-
    must_be(dict, Issue),
    get_dict(number, Issue, Number),
    get_dict(title, Issue, Title),
    get_dict(url, Issue, Url),
    (   get_dict(body, Issue, Body0)
    ->  Body = Body0
    ;   Body = ""
    ),
    issue_priority(Body, Priority, Rank),
    Candidate = candidate{
        number:Number,
        title:Title,
        url:Url,
        body:Body,
        priority:Priority,
        rank:Rank,
        source:Issue
    }.

compare_candidates(Order, A, B) :-
    compare(RankOrder, B.rank, A.rank),
    (   RankOrder == (=)
    ->  compare(Order, A.number, B.number)
    ;   Order = RankOrder
    ).

choose_candidate([], _, _) :-
    fail.
choose_candidate([Candidate|Rest], LastIssue, Selected) :-
    (   same_issue(Candidate.number, LastIssue)
    ->  choose_after_repeat(Candidate, Rest, LastIssue, Selected)
    ;   Selected = Candidate
    ),
    !.

choose_after_repeat(Candidate, Rest, LastIssue, Selected) :-
    (   Candidate.rank < 3
    ->  choose_candidate(Rest, LastIssue, Selected)
    ;   same_rank_alternative(Rest, Candidate.rank, LastIssue, Alternative)
    ->  Selected = Alternative
    ;   Selected = Candidate
    ).

same_rank_alternative([Candidate|_], Rank, LastIssue, Candidate) :-
    Candidate.rank =:= Rank,
    \+ same_issue(Candidate.number, LastIssue),
    !.
same_rank_alternative([Candidate|Rest], Rank, LastIssue, Alternative) :-
    Candidate.rank =:= Rank,
    !,
    same_rank_alternative(Rest, Rank, LastIssue, Alternative).
same_rank_alternative(_, _, _, _) :-
    fail.

selected_decision(Candidate, State, QueueSize, Decision) :-
    put_dict(last_issue, State, Candidate.number, NextState0),
    put_dict(last_priority, NextState0, Candidate.priority, NextState),
    repeat_allowed(Candidate.rank, RepeatAllowed),
    Decision = _{
        action:"run",
        issue_number:Candidate.number,
        issue_title:Candidate.title,
        issue_url:Candidate.url,
        priority:Candidate.priority,
        queue_size:QueueSize,
        repeat_allowed:RepeatAllowed,
        selected_issue:Candidate.source,
        next_state:NextState
    }.

repeat_allowed(Rank, true) :-
    Rank >= 3,
    !.
repeat_allowed(_, false).

state_last_issue(State, LastIssue) :-
    (   get_dict(last_issue, State, Value),
        integer(Value)
    ->  LastIssue = Value
    ;   LastIssue = none
    ).

same_issue(Number, LastIssue) :-
    integer(LastIssue),
    Number =:= LastIssue.

issue_priority(Body, Priority, Rank) :-
    string(Body),
    split_string(Body, "\n", "\r", Lines),
    priority_after_header(Lines, Priority0),
    !,
    priority_rank(Priority0, Rank),
    Priority = Priority0.
issue_priority(_, normal, 2).

priority_after_header([Line|Rest], Priority) :-
    normalize_line(Line, Header),
    Header == "## priority",
    !,
    first_priority_line(Rest, Priority).
priority_after_header([_|Rest], Priority) :-
    priority_after_header(Rest, Priority).

first_priority_line([Line|Rest], Priority) :-
    normalize_line(Line, Normalized),
    (   Normalized == ""
    ->  first_priority_line(Rest, Priority)
    ;   priority_token(Normalized, Priority)
    ).

priority_token(Line, Priority) :-
    split_string(Line, " *`:_()[]", " *`:_()[]\t", Parts),
    member(Token, Parts),
    string_lower(Token, Lower),
    atom_string(Priority, Lower),
    priority_rank(Priority, _),
    !.

priority_rank(urgent, 4).
priority_rank(high, 3).
priority_rank(normal, 2).
priority_rank(low, 1).

normalize_line(Line, Normalized) :-
    normalize_space(string(Spaced), Line),
    string_lower(Spaced, Normalized).

require_decision(ok(Decision0), Decision) :-
    is_dict(Decision0),
    !,
    Decision = Decision0.
require_decision(Outcome, _) :-
    throw(error(auto_dig_actor_stage_failed(supervised_call, Outcome),
                context(auto_dig_prolog_actor,
                        'supervised actor did not return a decision dict'))).

require_ok(_, ok(_)) :- !.
require_ok(Stage, Outcome) :-
    throw(error(auto_dig_actor_stage_failed(Stage, Outcome),
                context(auto_dig_prolog_actor,
                        'supervised actor runtime returned a structured failure'))).

parse_args(Argv, Options) :-
    parse_args_(Argv, [], Options0),
    reverse(Options0, Options),
    require_option(queue, Options),
    require_option(state, Options),
    require_option(output, Options).

parse_args_([], Options, Options).
parse_args_(['--queue', Path|Rest], Acc, Options) :-
    !,
    parse_args_(Rest, [queue(Path)|Acc], Options).
parse_args_(['--state', Path|Rest], Acc, Options) :-
    !,
    parse_args_(Rest, [state(Path)|Acc], Options).
parse_args_(['--output', Path|Rest], Acc, Options) :-
    !,
    parse_args_(Rest, [output(Path)|Acc], Options).
parse_args_(['--trace', Path|Rest], Acc, Options) :-
    !,
    parse_args_(Rest, [trace(Path)|Acc], Options).
parse_args_([Unknown|_], _, _) :-
    throw(error(unknown_argument(Unknown),
                context(auto_dig_prolog_actor:main/1,
                        'expected --queue, --state, --output, or --trace'))).

require_option(Name, Options) :-
    Term =.. [Name, _],
    (   memberchk(Term, Options)
    ->  true
    ;   throw(error(missing_argument(Name),
                    context(auto_dig_prolog_actor:main/1,
                            'required actor argument is missing')))
    ).

read_json_file(Path, Value) :-
    setup_call_cleanup(
        open(Path, read, Stream, [encoding(utf8)]),
        json_read_dict(Stream, Raw),
        close(Stream)),
    ground_json_value(Raw, Value).

/* json_read_dict/2 uses anonymous dict tags. Those tags are variables, which
 * makes an otherwise concrete JSON tree fail ground/1. Prolog-RLM supervised
 * work deliberately requires a ground term before it crosses the worker-thread
 * boundary, so normalize every JSON dict to a stable `json` tag first. */
ground_json_value(Value0, Value) :-
    is_dict(Value0),
    !,
    dict_pairs(Value0, _, Pairs0),
    maplist(ground_json_pair, Pairs0, Pairs),
    dict_pairs(Value, json, Pairs).
ground_json_value(Values0, Values) :-
    is_list(Values0),
    !,
    maplist(ground_json_value, Values0, Values).
ground_json_value(Value, Value) :-
    atomic(Value),
    !.
ground_json_value(Value, _) :-
    throw(error(type_error(json_value, Value),
                context(auto_dig_prolog_actor,
                        'unsupported non-ground JSON value'))).

ground_json_pair(Key-Value0, Key-Value) :-
    ground_json_value(Value0, Value).

write_json_file(Path, Value) :-
    setup_call_cleanup(
        open(Path, write, Stream, [encoding(utf8)]),
        ( json_write_dict(Stream, Value, [width(0)]), nl(Stream) ),
        close(Stream)).

maybe_write_trace('', _) :- !.
maybe_write_trace(Path, Trace) :-
    setup_call_cleanup(
        open(Path, write, Stream, [encoding(utf8)]),
        forall(member(Event, Trace),
               write_term(Stream,
                          Event,
                          [ quoted(true),
                            fullstop(true),
                            nl(true)
                          ])),
        close(Stream)).

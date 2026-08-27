:- module(auto_dig_rlm_runner,
          [ main/1,
            auto_dig_runtime_options/3,
            auto_dig_runtime_options/6,
            auto_dig_query/1
          ]).

:- use_module(library(readutil)).
:- use_module(library(rlm_chain)).
:- use_module(library(rlm_completion)).
:- use_module(library(rlm_trace)).
:- use_module('./auto_dig_mcp_tools').
:- use_module('./auto_dig_mcp_runner').

:- initialization(main, main).

main(Argv) :-
    catch(main_run(Argv, ExitCode),
          Exception,
          ( print_message(error, Exception),
            ExitCode = 2
          )),
    halt(ExitCode).

main_run(Argv, ExitCode) :-
    parse_args(Argv, Args),
    read_file_to_string(Args.context_file, Context, []),
    auto_dig_query(Query),
    run_research_completion(Args, Query, Context, Outcome),
    write_trace_json(Args.output, auto_dig_rlm_result, Outcome),
    write_trace_file(Args.trace, Outcome),
    outcome_exit_code(Outcome, ExitCode).

run_research_completion(Args, Query, Context, Outcome) :-
    auto_dig_mcp_servers(Servers),
    AuthorityContext = auto_dig_rlm_research,
    setup_call_cleanup(
        auto_dig_mcp_session_open(Servers, AuthorityContext, Session),
        run_research_completion_with_session(Args,
                                             Query,
                                             Context,
                                             AuthorityContext,
                                             Session,
                                             Outcome),
        auto_dig_mcp_session_close(Session)).

run_research_completion_with_session(Args,
                                     Query,
                                     Context,
                                     AuthorityContext,
                                     Session,
                                     Outcome) :-
    auto_dig_mcp_session_registry(Session, Registry),
    auto_dig_mcp_session_capabilities(Session, McpCapabilities),
    auto_dig_runtime_options(Args.model,
                             Args.reasoning_effort,
                             Registry,
                             AuthorityContext,
                             McpCapabilities,
                             Options),
    rlm_completion(Query, text(Context), Options, Outcome).

auto_dig_runtime_options(Model, ReasoningEffort, Options) :-
    auto_dig_runtime_options(Model,
                             ReasoningEffort,
                             none,
                             none,
                             [],
                             Options).

auto_dig_runtime_options(Model,
                         ReasoningEffort,
                         Registry,
                         AuthorityContext,
                         McpCapabilities,
                         Options) :-
    openrouter_provider(Model, Provider),
    BaseCapabilities = [ rlm,
                         context(slice),
                         context(search),
                         context(peek),
                         model(openrouter)
                       ],
    append(BaseCapabilities, McpCapabilities, Capabilities0),
    sort(Capabilities0, Capabilities),
    Budget = _{ max_recursion_depth:2,
                max_concurrent_subcalls:2,
                max_model_calls:6,
                max_tool_calls:8,
                max_context_ops:12,
                max_total_tokens:8192,
                max_cost_usd:0.10,
                max_output_bytes:65536,
                time_limit:90.0
              },
    RuntimeOptions = [ provider(Provider),
                       provider_name(openrouter),
                       capabilities(Capabilities),
                       child_capabilities(Capabilities),
                       reasoning_effort(ReasoningEffort),
                       skill_mode(on),
                       skill_catalog(default),
                       prompt_compile_mode(compiled),
                       planner_attempts(3),
                       planner_max_tokens(2048),
                       context_options([max_bytes(32768), time_limit(2.0)]),
                       budget(Budget)
                     ],
    runtime_binding_options(Registry,
                            AuthorityContext,
                            RuntimeOptions,
                            Options).

runtime_binding_options(none, _, Options, Options) :- !.
runtime_binding_options(Registry,
                        AuthorityContext,
                        Options0,
                        [ tool_registry(Registry),
                          authority_context(AuthorityContext)
                        | Options0 ]).

auto_dig_query("You are the Auto-Dig Prolog actor with bounded read-only web research tools. Perform the research now; do not merely propose a future tool-enabled stage. Use Brave web/news/video search to discover relevant sources and Fetch tools to inspect primary or otherwise high-value source content. Use RLM context search, peek, slice, and recursive reasoning when useful. Separate established facts, hypotheses, constraints, unresolved claims, primary-source evidence, and falsification criteria. Preserve source URLs or identifiers in the result so claims are auditable. Do not claim research or verification that was not actually performed. Return an evidence-backed research slice plus clearly separated remaining follow-up work.").

outcome_exit_code(ok(_), 0) :- !.
outcome_exit_code(error(_), 1) :- !.
outcome_exit_code(_, 1).

write_trace_file('', _) :- !.
write_trace_file(Path, Outcome) :-
    trace_write(Path, json, auto_dig_rlm, Outcome, WriteOutcome),
    require_trace_write(WriteOutcome).

require_trace_write(ok(_)) :- !.
require_trace_write(error(Error)) :-
    throw(error(auto_dig_trace_write_failed(Error), _)).

write_trace_json(Path, Name, Payload) :-
    trace_envelope(Name, Payload, Envelope),
    trace_json(Envelope, Json),
    setup_call_cleanup(
        open(Path, write, Stream, [encoding(utf8)]),
        format(Stream, '~s~n', [Json]),
        close(Stream)).

parse_args(Argv, Args) :-
    parse_args_(Argv,
                _{ context_file:none,
                   model:none,
                   reasoning_effort:none,
                   output:none,
                   trace:''
                 },
                Args),
    require_arg(context_file, Args.context_file),
    require_arg(model, Args.model),
    require_arg(reasoning_effort, Args.reasoning_effort),
    require_arg(output, Args.output).

parse_args_([], Args, Args).
parse_args_(['--context-file', Value|Rest], Args0, Args) :-
    !,
    put_dict(context_file, Args0, Value, Args1),
    parse_args_(Rest, Args1, Args).
parse_args_(['--model', Value|Rest], Args0, Args) :-
    !,
    put_dict(model, Args0, Value, Args1),
    parse_args_(Rest, Args1, Args).
parse_args_(['--reasoning-effort', Value|Rest], Args0, Args) :-
    !,
    put_dict(reasoning_effort, Args0, Value, Args1),
    parse_args_(Rest, Args1, Args).
parse_args_(['--output', Value|Rest], Args0, Args) :-
    !,
    put_dict(output, Args0, Value, Args1),
    parse_args_(Rest, Args1, Args).
parse_args_(['--trace', Value|Rest], Args0, Args) :-
    !,
    put_dict(trace, Args0, Value, Args1),
    parse_args_(Rest, Args1, Args).
parse_args_([Unknown|_], _, _) :-
    throw(error(unknown_argument(Unknown),
                context(auto_dig_rlm_runner:main/1,
                        'expected --context-file, --model, --reasoning-effort, --output, or --trace'))).

require_arg(Name, none) :-
    !,
    throw(error(missing_argument(Name),
                context(auto_dig_rlm_runner:main/1,
                        'required runner argument is missing'))).
require_arg(_, _).

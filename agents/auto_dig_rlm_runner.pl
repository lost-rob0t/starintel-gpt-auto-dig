:- module(auto_dig_rlm_runner,
          [ main/1,
            auto_dig_runtime_options/3,
            auto_dig_runtime_options/6,
            auto_dig_context_budget/3,
            auto_dig_query/1,
            outcome_log_summary/2
          ]).

:- use_module(library(readutil)).
:- use_module(library(rlm_chain)).
:- use_module(library(rlm_direct)).
:- use_module(library(rlm_trace)).
:- use_module('./auto_dig_mcp_tools').
:- use_module('./auto_dig_mcp_runner').
:- use_module('./auto_dig_safe_log').

:- initialization(main, main).

main(Argv) :-
    catch(main_run(Argv, ExitCode),
          Exception,
          ( log_exception(fatal, Exception),
            ExitCode = 2
          )),
    halt(ExitCode).

main_run(Argv, ExitCode) :-
    parse_args(Argv, Args),
    safe_log(auto_dig_rlm,
             'phase=start mode=direct model=~w reasoning_effort=~w',
             [Args.model, Args.reasoning_effort]),
    read_file_to_string(Args.context_file, Context, []),
    string_length(Context, ContextChars),
    safe_log(auto_dig_rlm,
             'phase=context_loaded chars=~d file=~w',
             [ContextChars, Args.context_file]),
    auto_dig_query(Query),
    run_research_completion(Args, Query, Context, Outcome),
    log_outcome(Outcome),
    write_trace_json(Args.output, auto_dig_rlm_result, Outcome),
    safe_log(auto_dig_rlm, 'phase=result_written file=~w', [Args.output]),
    write_trace_file(Args.trace, Outcome),
    ( Args.trace == ''
    -> true
    ;  safe_log(auto_dig_rlm, 'phase=trace_written file=~w', [Args.trace])
    ),
    outcome_exit_code(Outcome, ExitCode),
    safe_log(auto_dig_rlm, 'phase=finish exit_code=~d', [ExitCode]).

run_research_completion(Args, Query, Context, Outcome) :-
    auto_dig_mcp_servers(Servers),
    safe_log(auto_dig_rlm, 'phase=mcp_session_open servers=~q', [Servers]),
    AuthorityContext = auto_dig_rlm_research,
    setup_call_cleanup(
        auto_dig_mcp_session_open(Servers, AuthorityContext, Session),
        run_research_completion_with_session(Args,
                                             Query,
                                             Context,
                                             AuthorityContext,
                                             Session,
                                             Outcome),
        ( safe_log(auto_dig_rlm, 'phase=mcp_session_close', []),
          auto_dig_mcp_session_close(Session)
        )).

run_research_completion_with_session(Args,
                                     Query,
                                     Context,
                                     AuthorityContext,
                                     Session,
                                     Outcome) :-
    auto_dig_mcp_session_registry(Session, Registry),
    auto_dig_mcp_session_capabilities(Session, McpCapabilities),
    length(McpCapabilities, McpCapabilityCount),
    safe_log(auto_dig_rlm,
             'phase=mcp_ready capability_count=~d capabilities=~q',
             [McpCapabilityCount, McpCapabilities]),
    auto_dig_runtime_options(Args.model,
                             Args.reasoning_effort,
                             Registry,
                             AuthorityContext,
                             McpCapabilities,
                             Options),
    memberchk(budget(Budget), Options),
    auto_dig_context_budget(Args.model, ContextWindow, ContextBudget),
    safe_log(auto_dig_rlm,
             'phase=direct_start context_window=~d token_budget=~d model_calls=~d tool_calls=~d context_ops=~d iterations=~d time_limit=~w',
             [ ContextWindow,
               ContextBudget,
               Budget.max_model_calls,
               Budget.max_tool_calls,
               Budget.max_context_ops,
               Budget.max_iterations,
               Budget.time_limit
             ]),
    rlm_direct(Query, text(Context), Options, Outcome),
    safe_log(auto_dig_rlm, 'phase=direct_return', []).

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
    auto_dig_context_budget(Model, _ContextWindow, TokenBudget),
    BaseCapabilities = [ rlm,
                         context(slice),
                         context(search),
                         context(peek),
                         model(openrouter)
                       ],
    append(BaseCapabilities, McpCapabilities, Capabilities0),
    sort(Capabilities0, Capabilities),
    Budget = _{ max_iterations:24,
                max_recursion_depth:2,
                max_concurrent_subcalls:2,
                max_model_calls:12,
                max_tool_calls:24,
                max_context_ops:32,
                max_total_tokens:TokenBudget,
                max_cost_usd:2.00,
                max_output_bytes:262144,
                time_limit:300.0
              },
    RuntimeOptions = [ provider(Provider),
                       provider_name(openrouter),
                       capabilities(Capabilities),
                       child_capabilities(Capabilities),
                       reasoning_effort(ReasoningEffort),
                       skill_mode(on),
                       skill_catalog(default),
                       prompt_compile_mode(all_tools),
                       planner_max_tokens(8192),
                       context_options([max_bytes(262144), time_limit(5.0)]),
                       budget(Budget)
                     ],
    runtime_binding_options(Registry,
                            AuthorityContext,
                            RuntimeOptions,
                            Options).

/*
 * Temporary consumer-owned model limits.
 *
 * Prolog-RLM issue #296 tracks moving this into a provider-neutral model
 * metadata API. OpenRouter currently advertises a 1,050,000-token context
 * window for all three routed GPT-5.6 tiers. Auto-Dig intentionally gives the
 * direct worker 30% of that limit: 315,000 tokens.
 */
auto_dig_model_context_window('openai/gpt-5.6-luna', 1050000).
auto_dig_model_context_window('openai/gpt-5.6-terra', 1050000).
auto_dig_model_context_window('openai/gpt-5.6-sol', 1050000).

auto_dig_context_budget(Model, ContextWindow, TokenBudget) :-
    (   auto_dig_model_context_window(Model, ContextWindow)
    ->  TokenBudget is (ContextWindow * 30) // 100
    ;   throw(error(domain_error(auto_dig_model_context_window, Model),
                    context(auto_dig_rlm_runner:auto_dig_context_budget/3,
                            'selected model needs an explicit context-window limit until Prolog-RLM #296 lands')))
    ).

runtime_binding_options(none, _, Options, Options) :- !.
runtime_binding_options(Registry,
                        AuthorityContext,
                        Options0,
                        [ tool_registry(Registry),
                          authority_context(AuthorityContext)
                        | Options0 ]).

auto_dig_query("You are the Auto-Dig Prolog actor running in native direct mode with bounded read-only web research tools. Perform the research now; do not emit a typed plan and do not merely propose a future tool-enabled stage. Use the available Brave search tools broadly to discover relevant sources, then use Fetch tools to inspect primary or otherwise high-value source content. Use RLM context search, peek, and slice when useful. Keep calling tools while useful evidence remains within budget. Separate established facts, hypotheses, constraints, unresolved claims, primary-source evidence, and falsification criteria. Preserve source URLs or identifiers in the result so claims are auditable. Do not claim research or verification that was not actually performed. Return an evidence-backed research slice plus clearly separated remaining follow-up work, including any additional tool or datasource capability that would materially improve the next pass.").

outcome_exit_code(ok(_), 0) :- !.
outcome_exit_code(error(_), 1) :- !.
outcome_exit_code(_, 1).

log_outcome(Outcome) :-
    outcome_log_summary(Outcome, Summary),
    safe_text(Summary, SafeSummary),
    ( Outcome = error(_)
    -> format(user_error,
              '::error title=Auto-Dig Prolog-RLM failure::~s~n',
              [SafeSummary]),
       flush_output(user_error)
    ;  true
    ),
    safe_log(auto_dig_rlm, 'phase=outcome ~s', [SafeSummary]).

outcome_log_summary(ok(Result), Summary) :-
    !,
    usage_from_result(Result, Usage),
    usage_summary('status=ok', Usage, Summary).
outcome_log_summary(error(Error), Summary) :-
    !,
    error_field(Error, phase, unknown, Phase),
    error_field(Error, kind, unknown, Kind),
    error_field(Error, message, "unspecified error", Message),
    error_field(Error, used, unknown, Used),
    error_field(Error, limit, unknown, Limit),
    usage_from_error(Error, Usage),
    format(string(Prefix),
           'status=error phase=~w kind=~w message=~w used=~w limit=~w',
           [Phase, Kind, Message, Used, Limit]),
    usage_summary(Prefix, Usage, Summary).
outcome_log_summary(Other, Summary) :-
    format(string(Summary), 'status=unknown outcome=~q', [Other]).

usage_from_result(Result, Usage) :-
    ( is_dict(Result), get_dict(usage, Result, Found), is_dict(Found)
    -> Usage = Found
    ;  Usage = _{}
    ).

usage_from_error(Error, Usage) :-
    ( is_dict(Error), get_dict(usage, Error, Found), is_dict(Found)
    -> Usage = Found
    ;  Usage = _{}
    ).

usage_summary(Prefix, Usage, Summary) :-
    usage_field(Usage, model_calls, unknown, ModelCalls),
    usage_field(Usage, prompt_tokens, unknown, PromptTokens),
    usage_field(Usage, completion_tokens, unknown, CompletionTokens),
    usage_field(Usage, total_tokens, unknown, TotalTokens),
    usage_field(Usage, cost_usd, unknown, CostUsd),
    format(string(Summary),
           '~w model_calls=~w prompt_tokens=~w completion_tokens=~w total_tokens=~w cost_usd=~w',
           [ Prefix,
             ModelCalls,
             PromptTokens,
             CompletionTokens,
             TotalTokens,
             CostUsd
           ]).

error_field(Error, Key, Default, Value) :-
    ( is_dict(Error), get_dict(Key, Error, Found)
    -> Value = Found
    ;  Value = Default
    ).

usage_field(Usage, Key, Default, Value) :-
    ( is_dict(Usage), get_dict(Key, Usage, Found)
    -> Value = Found
    ;  Value = Default
    ).

log_exception(Phase, Exception) :-
    message_to_string(Exception, Message),
    safe_log(auto_dig_rlm,
             'phase=~w state=exception message=~s',
             [Phase, Message]),
    safe_text(Message, SafeMessage),
    format(user_error,
           '::error title=Auto-Dig Prolog-RLM exception::phase=~w message=~s~n',
           [Phase, SafeMessage]),
    flush_output(user_error).

write_trace_file('', _) :- !.
write_trace_file(Path, Outcome) :-
    write_trace_json(Path, auto_dig_rlm, Outcome).

write_trace_json(Path, Name, Payload) :-
    trace_envelope(Name, Payload, Envelope),
    trace_json(Envelope, RawJson),
    safe_text(RawJson, Json),
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

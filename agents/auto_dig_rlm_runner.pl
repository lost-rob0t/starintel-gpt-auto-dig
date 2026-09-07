:- module(auto_dig_rlm_runner,
          [ main/1,
            auto_dig_runtime_options/3,
            auto_dig_runtime_options/6,
            auto_dig_context_budget/3,
            auto_dig_provider/2,
            auto_dig_query/1,
            auto_dig_repair_query/2,
            auto_dig_retry_options/2,
            raw_argument_retryable/1,
            outcome_log_summary/2,
            final_report_content/2,
            valid_research_report/1,
            emit_human_report/1
          ]).

:- use_module(library(readutil)).
:- use_module(library(lists), [select/3]).
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
    outcome_exit_code(Outcome, RuntimeExitCode),
    validate_and_materialize_result(Args.output,
                                    Outcome,
                                    RuntimeExitCode,
                                    ExitCode),
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
    memberchk(native_tool_cutoff_model_calls(ToolCutoff), Options),
    memberchk(synthesis_reservation(SynthesisReserve), Options),
    auto_dig_context_budget(Args.model, ContextWindow, ContextBudget),
    safe_log(auto_dig_rlm,
             'phase=direct_start context_window=~d token_budget=~d model_calls=~d native_tool_cutoff=~d synthesis_reserve=~w tool_calls=~d context_ops=~d iterations=~d time_limit=~w',
             [ ContextWindow,
               ContextBudget,
               Budget.max_model_calls,
               ToolCutoff,
               SynthesisReserve,
               Budget.max_tool_calls,
               Budget.max_context_ops,
               Budget.max_iterations,
               Budget.time_limit
             ]),
    run_bounded_direct(Query, Context, Options, Outcome),
    safe_log(auto_dig_rlm, 'phase=direct_return', []).

run_bounded_direct(Query, Context, Options, Outcome) :-
    rlm_direct(Query, text(Context), Options, FirstOutcome),
    (   raw_argument_retryable(FirstOutcome)
    ->  outcome_log_summary(FirstOutcome, FirstSummary0),
        safe_text(FirstSummary0, FirstSummary),
        safe_log(auto_dig_rlm,
                 'phase=repair_retry trigger=raw_malformed_arguments first_outcome=~s',
                 [FirstSummary]),
        auto_dig_repair_query(Query, RepairQuery),
        auto_dig_retry_options(Options, RetryOptions),
        rlm_direct(RepairQuery, text(Context), RetryOptions, RetryOutcome),
        safe_log(auto_dig_rlm,
                 'phase=repair_retry state=complete',
                 []),
        Outcome = RetryOutcome
    ;   Outcome = FirstOutcome
    ).

raw_argument_retryable(error(Error)) :-
    is_dict(Error),
    get_dict(phase, Error, native_call),
    get_dict(kind, Error, malformed_arguments),
    get_dict(cause, Error, Cause),
    is_dict(Cause),
    get_dict(phase, Cause, normalize),
    get_dict(kind, Cause, malformed_arguments).

auto_dig_retry_options(Options0, Options) :-
    select(budget(Budget0), Options0, Rest),
    RetryBudgetPatch = _{ max_iterations:12,
                          max_model_calls:6,
                          max_tool_calls:12,
                          max_context_ops:16,
                          max_total_tokens:78750,
                          max_cost_usd:0.50,
                          time_limit:180.0
                        },
    put_dict(RetryBudgetPatch, Budget0, RetryBudget),
    Options = [budget(RetryBudget)|Rest].

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
    auto_dig_provider(Model, Provider),
    Provider = provider(ProviderName, _),
    auto_dig_context_budget(Model, _ContextWindow, TokenBudget),
    BaseCapabilities = [ rlm,
                         context(slice),
                         context(search),
                         context(peek),
                         model(ProviderName)
                       ],
    append(BaseCapabilities, McpCapabilities, Capabilities0),
    sort(Capabilities0, Capabilities),
    % Keep both ceilings: a response-count cutoff bounds acquisition even on
    % fast providers, while the wall-clock reserve forces synthesis early on
    % slow providers. The hard 300s runtime deadline remains the final guard.
    Budget = _{ max_iterations:24,
                max_recursion_depth:2,
                max_concurrent_subcalls:2,
                max_model_calls:16,
                max_tool_calls:24,
                max_context_ops:32,
                max_total_tokens:TokenBudget,
                max_cost_usd:1.50,
                max_output_bytes:262144,
                time_limit:300.0
              },
    RuntimeOptions = [ provider(Provider),
                       provider_name(ProviderName),
                       capabilities(Capabilities),
                       child_capabilities(Capabilities),
                       reasoning_effort(ReasoningEffort),
                       skill_mode(on),
                       skill_catalog(default),
                       prompt_compile_mode(all_tools),
                       planner_max_tokens(8192),
                       native_tool_cutoff_model_calls(12),
                       synthesis_reservation(90.0),
                       context_options([max_bytes(262144), time_limit(5.0)]),
                       budget(Budget)
                     ],
    runtime_binding_options(Registry,
                            AuthorityContext,
                            RuntimeOptions,
                            Options).

/*
 * Provider selection: OpenRouter by default, or any OpenAI-compatible
 * endpoint (for example the in-house llm.starintel.actor gateway) when
 * AUTO_DIG_LLM_ENDPOINT is set. The credential is always env(Name); the
 * transport resolves it at call time and never logs secrets.
 */
auto_dig_provider(Model, Provider) :-
    getenv('AUTO_DIG_LLM_ENDPOINT', Endpoint),
    atom_string(Endpoint, EndpointString),
    EndpointString \== "",
    !,
    auto_dig_llm_timeout(Timeout),
    Provider = provider(openai_compatible,
                        [ endpoint(EndpointString),
                          credential(env('AUTO_DIG_LLM_API_KEY')),
                          model(Model),
                          timeout(Timeout)
                        ]).

auto_dig_provider(Model, Provider) :-
    openrouter_provider(Model, Provider).

auto_dig_llm_timeout(Timeout) :-
    getenv('AUTO_DIG_LLM_TIMEOUT', Raw),
    atom_string(Raw, RawString),
    catch(number_string(Timeout0, RawString), _, fail),
    Timeout0 > 0,
    !,
    Timeout is round(Timeout0).
auto_dig_llm_timeout(180).

/*
 * Temporary consumer-owned model limits.
 *
 * Prolog-RLM issue #296 tracks moving this into a provider-neutral model
 * model metadata API. Auto-Dig intentionally gives the direct worker 30% of
 * the selected model context window. OPENROUTER_TEST_MODEL routes to the
 * default openrouter model. AUTO_DIG_MODEL_CONTEXT_WINDOW overrides the
 * window for gateway models that are absent from the table below.
 */
auto_dig_model_context_window('z-ai/glm-5.3-flash', 1310720).
auto_dig_model_context_window('openai/gpt-5.6-luna', 1050000).
auto_dig_model_context_window('openai/gpt-5.6-terra', 1050000).
auto_dig_model_context_window('openai/gpt-5.6-sol', 1050000).

auto_dig_context_budget(_Model, ContextWindow, TokenBudget) :-
    getenv('AUTO_DIG_MODEL_CONTEXT_WINDOW', Raw),
    atom_string(Raw, RawString),
    catch(number_string(ContextWindow0, RawString), _, fail),
    ContextWindow0 > 0,
    !,
    ContextWindow = ContextWindow0,
    TokenBudget is (ContextWindow * 30) // 100.
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

auto_dig_query("You are the Auto-Dig Prolog actor running in native direct mode with bounded read-only web research tools. The supplied input context is a single research request: read it first, answer its stated goal and completion criteria, respect its scope, seed sources, and constraints, and state exactly which parts of the request remain unanswered when this bounded slice cannot cover them. Method, in order: (1) plan coverage from the request's own terms, naming its people, organizations, jurisdictions, records, and date ranges; (2) search the local StarIntel corpus first with the starintel_search and starintel_get_document tools for existing records, packets, and canonical IDs covering the request's subject, and reuse existing StarIntel IDs instead of minting duplicates; (3) Search broadly with the available Brave tools using multiple distinct queries and varied terminology, covering every required surface the request names; (4) use Fetch tools to inspect primary or otherwise high-value source content, preferring primary records (filings, official documents, legislation, court records, original statements) over outlets that merely restate another source; (5) corroborate load-bearing claims across at least two unrelated origins where feasible and label single-source claims as single-source; (6) use RLM context search, peek, and slice when useful, then synthesize. Perform the research now; do not emit a typed plan and do not merely propose a future tool-enabled stage. Budget discipline: reserve the final four model responses for synthesis; stop evidence acquisition no later than the twelfth model response. The runtime may remove all native tool schemas earlier when its wall-clock synthesis reserve activates; if tools are no longer available, treat evidence acquisition as closed and synthesize immediately from evidence already gathered. Once either boundary is reached, do not call Brave, Fetch, context tools, or write tool-call syntax as text, or call the StarIntel corpus tools; synthesize the strongest evidence already gathered into the final answer. If useful evidence remains after the boundary, list it as follow-up work instead of spending synthesis headroom. Tool-call hygiene: native tool-call arguments must be strict JSON objects with every object key appearing exactly once; never emit duplicate JSON keys. Prefer no more than four parallel native tool calls in one assistant turn so each call remains easy to validate and repair. Evidence discipline: separate established facts, hypotheses, constraints, unresolved claims, primary-source evidence, and falsification criteria. Preserve source URLs or identifiers in the result so claims are auditable. Cite only URLs that a search or fetch tool actually returned; never invent, complete, or pattern-guess a URL. Do not claim research or verification that was not actually performed. Report contract: your final assistant response MUST be a substantive Markdown report that starts exactly with '# Auto-Dig Research Output' and contains the headings '## Findings', '## Evidence', and '## Unresolved / Follow-up', with at least one http:// or https:// source URL. In '## Findings', mark each finding as established (multi-source), provisional (single-source), or hypothesis (inferred), and give falsification criteria for the load-bearing ones. In '## Evidence', map each cited claim to its exact source URL and state what that source directly supports; findings that merely restate an existing corpus record must cite that record's `_id`. In '## Unresolved / Follow-up', list unanswered request parts, single-source claims needing corroboration, and any additional tool or datasource capability that would materially improve the next pass. The final response must contain prose findings, not pending tool invocations, serialized tool calls, or a statement that the run merely completed. Even when evidence is limited, produce the report with explicit unresolved items. Return an evidence-backed research slice plus clearly separated remaining follow-up work.").

auto_dig_repair_query(Query, RepairQuery) :-
    string_concat(Query,
                  "\n\nREPAIR NOTE: the previous bounded direct attempt was rejected because at least one provider-native tool call contained malformed raw JSON arguments. Start the research again from the supplied input context. Every tool argument payload MUST be exactly one strict JSON object and every key in that object MUST appear exactly once. Do not repeat keys such as search_lang or spellcheck. Prefer no more than four parallel native tool calls per assistant turn. This is the one harness-level repair attempt; use it to complete a useful evidence-backed research slice within the smaller retry budget.",
                  RepairQuery).

final_report_content(ok(Result), Content) :-
    is_dict(Result),
    get_dict(response, Result, Response),
    is_dict(Response),
    get_dict(assistant, Response, Assistant),
    is_dict(Assistant),
    get_dict(content, Assistant, RawContent),
    text_content_string(RawContent, Text),
    canonical_report_content(Text, Content).

text_content_string(Content, Content) :-
    string(Content),
    !.
text_content_string(Content, String) :-
    atom(Content),
    atom_string(Content, String).

canonical_report_content(Text, Content) :-
    report_heading_start(Text, Start),
    !,
    sub_string(Text, Start, _, 0, Content).
canonical_report_content(Content, Content).

report_heading_start(Text, 0) :-
    sub_string(Text, 0, _, _, "# Auto-Dig Research Output"),
    !.
report_heading_start(Text, Start) :-
    sub_string(Text, Start, _, _, "# Auto-Dig Research Output"),
    Start > 0,
    Before is Start-1,
    sub_string(Text, Before, 1, _, "\n").

valid_research_report(Content) :-
    string(Content),
    normalize_space(string(Trimmed), Content),
    string_length(Trimmed, Length),
    Length >= 256,
    sub_string(Trimmed, 0, _, _, "# Auto-Dig Research Output"),
    sub_string(Trimmed, _, _, _, "## Findings"),
    sub_string(Trimmed, _, _, _, "## Evidence"),
    sub_string(Trimmed, _, _, _, "## Unresolved / Follow-up"),
    ( sub_string(Trimmed, _, _, _, "https://")
    ; sub_string(Trimmed, _, _, _, "http://")
    ),
    \+ tool_transcript_content(Trimmed).

tool_transcript_content(Content) :-
    member(Marker,
           [ "to=functions.",
             "to=multi_tool_use.",
             "functions.context_slice",
             "\"tool_uses\"",
             "\"recipient_name\""
           ]),
    sub_string(Content, _, _, _, Marker),
    !.

validate_and_materialize_result(_, _, RuntimeExitCode, RuntimeExitCode) :-
    RuntimeExitCode =\= 0,
    !.
validate_and_materialize_result(OutputPath, Outcome, 0, ExitCode) :-
    (   final_report_content(Outcome, Content),
        valid_research_report(Content)
    ->  report_path(OutputPath, ReportPath),
        write_report(ReportPath, Content),
        safe_log(auto_dig_rlm,
                 'phase=output_validation state=ok report=~w',
                 [ReportPath]),
        emit_human_report(Content),
        ExitCode = 0
    ;   safe_log(auto_dig_rlm,
                 'phase=output_validation state=error kind=non_substantive_final_output',
                 []),
        format(user_error,
               '::error title=Auto-Dig invalid final output::runtime returned ok but no substantive research report satisfied the output contract~n',
               []),
        flush_output(user_error),
        ExitCode = 1
    ).

emit_human_report(Content) :-
    format('~n~s~n', [Content]),
    flush_output.

report_path(OutputPath, ReportPath) :-
    file_directory_name(OutputPath, Directory),
    directory_file_path(Directory, 'report.md', ReportPath).

write_report(Path, Content) :-
    setup_call_cleanup(
        open(Path, write, Stream, [encoding(utf8)]),
        format(Stream, '~s~n', [Content]),
        close(Stream)).

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

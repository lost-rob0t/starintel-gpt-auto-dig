:- begin_tests(auto_dig_deadline_synthesis_hotfix).

:- use_module(library(http/json)).
:- use_module(library(process)).
:- use_module(library(readutil)).

ensure_deadline_hotfix_fixture :-
    (   getenv('GITHUB_WORKSPACE', Workspace)
    ->  true
    ;   working_directory(Workspace, Workspace)
    ),
    directory_file_path(Workspace, '.prolog-rlm', RuntimeRoot),
    directory_file_path(RuntimeRoot, 'prolog/rlm_direct.pl', DirectPath),
    read_file_to_string(DirectPath, DirectSource, []),
    (   sub_string(DirectSource, _, _, _, "native_tool_provider_headroom_seconds")
    ->  true
    ;   apply_script('scripts/apply_prolog_rlm_hotfix.py', RuntimeRoot),
        apply_script('scripts/apply_prolog_rlm_deadline_hotfix.py', RuntimeRoot)
    ).

apply_script(Script, RuntimeRoot) :-
    process_create(path(python3), [Script, RuntimeRoot], [process(Pid)]),
    process_wait(Pid, Status),
    (   Status == exit(0)
    ->  true
    ;   throw(error(hotfix_fixture_failed(Script, Status), _))
    ).

:- initialization(ensure_deadline_hotfix_fixture, now).
:- use_module(library(rlm_direct), [rlm_direct/4]).

:- dynamic model_call/1.

reset_model :-
    retractall(model_call(_)),
    assertz(model_call(0)).

next_model_call(Call) :-
    retract(model_call(Previous)),
    Call is Previous + 1,
    assertz(model_call(Call)).

tool_call(Id, Call) :-
    atom_json_dict(ArgumentsAtom,
                   json{context:"input", start:0, length:1},
                   [width(0)]),
    atom_string(ArgumentsAtom, Arguments),
    Call = json{id:Id,
                type:"function",
                function:json{name:"context_slice", arguments:Arguments}}.

response(Call, Text, ToolCalls,
         model_response{provider:fake,
                        requested_model:fake,
                        selected_model:fake,
                        response_id:ResponseId,
                        assistant:message{role:assistant,
                                          content:Text,
                                          tool_calls:ToolCalls,
                                          reasoning:"",
                                          reasoning_details:[]},
                        text:Text,
                        tool_calls:ToolCalls,
                        reasoning:"",
                        reasoning_details:[],
                        finish_reason:FinishReason,
                        usage:usage{present:true,
                                    prompt_tokens:2,
                                    completion_tokens:1,
                                    total_tokens:3,
                                    cost:0.0},
                        metadata:provider_metadata{provider:fake,
                                                   http_status:200,
                                                   response_received:true}}) :-
    format(string(ResponseId), "deadline_response_~d", [Call]),
    ( ToolCalls == [] -> FinishReason = stop ; FinishReason = tool_calls ).

deadline_model(Request, ok(Response)) :-
    next_model_call(Call),
    deadline_model_response(Call, Request, Text, ToolCalls),
    response(Call, Text, ToolCalls, Response).

deadline_model_response(1, Request, "", [ToolCall]) :-
    get_dict(tools, Request.options, Tools),
    Tools \== [],
    % Simulate one slow acquisition response. With only the synthesis reserve
    % considered, the next provider request would still start tool-enabled and
    % could consume the hard deadline, exactly as live run 33522569444 did.
    sleep(0.78),
    tool_call("slice_1", ToolCall).
deadline_model_response(2, Request, "SYNTHESIZED_BEFORE_HARD_DEADLINE", []) :-
    \+ get_dict(tools, Request.options, _),
    \+ get_dict(tool_choice, Request.options, _),
    !.
deadline_model_response(2, _, "", [ToolCall]) :-
    tool_call("slice_2", ToolCall).

options([provider(provider(openai_compatible, [])),
         provider_name(openai_compatible),
         model_handler(plunit_auto_dig_deadline_synthesis_hotfix:deadline_model),
         capabilities([context(slice)]),
         prompt_compile_mode(all_tools),
         native_tool_cutoff_model_calls(99),
         native_tool_synthesis_reserve_seconds(0.15),
         budget(_{max_iterations:4,
                  max_model_calls:3,
                  max_tool_calls:3,
                  max_context_ops:3,
                  max_total_tokens:1000,
                  max_output_bytes:8192,
                  time_limit:1.0})]).

test(provider_headroom_hides_tools_before_slow_request_can_consume_deadline) :-
    reset_model,
    options(Options),
    rlm_direct("Acquire once, then synthesize",
               text("opaque"),
               Options,
               Outcome),
    Outcome = ok(Result),
    assertion(Result.value == "SYNTHESIZED_BEFORE_HARD_DEADLINE"),
    assertion(Result.turns =:= 2),
    assertion(Result.context_calls =:= 1),
    assertion(model_call(2)).

:- end_tests(auto_dig_deadline_synthesis_hotfix).

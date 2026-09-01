:- begin_tests(auto_dig_native_cutoff_hotfix).

:- use_module(library(http/json)).
:- use_module(library(rlm_direct), [rlm_direct/4]).

:- dynamic cutoff_model_call/1.

reset_cutoff_model :-
    retractall(cutoff_model_call(_)),
    assertz(cutoff_model_call(0)).

next_cutoff_model_call(Call) :-
    retract(cutoff_model_call(Previous)),
    Call is Previous+1,
    assertz(cutoff_model_call(Call)).

cutoff_native_call(Id, Call) :-
    atom_json_dict(ArgumentsAtom,
                   json{context:"input", start:0, length:1},
                   [width(0)]),
    atom_string(ArgumentsAtom, Arguments),
    Call = json{
        id:Id,
        type:"function",
        function:json{name:"context_slice", arguments:Arguments}
    }.

cutoff_response(Call, Text, ToolCalls,
                model_response{
                    provider:fake,
                    requested_model:fake,
                    selected_model:fake,
                    response_id:ResponseId,
                    assistant:message{
                        role:assistant,
                        content:Text,
                        tool_calls:ToolCalls,
                        reasoning:"",
                        reasoning_details:[]
                    },
                    text:Text,
                    tool_calls:ToolCalls,
                    reasoning:"",
                    reasoning_details:[],
                    finish_reason:FinishReason,
                    usage:usage{
                        present:true,
                        prompt_tokens:2,
                        completion_tokens:1,
                        total_tokens:3,
                        cost:0.0
                    },
                    metadata:provider_metadata{
                        provider:fake,
                        http_status:200,
                        response_received:true
                    }
                }) :-
    format(string(ResponseId), "cutoff_response_~d", [Call]),
    (   ToolCalls == []
    ->  FinishReason = stop
    ;   FinishReason = tool_calls
    ).

cutoff_model(Request, ok(Response)) :-
    next_cutoff_model_call(Call),
    cutoff_model_response(Call, Request, Text, ToolCalls),
    cutoff_response(Call, Text, ToolCalls, Response).

cutoff_model_response(1, Request, "", [ToolCall]) :-
    get_dict(tools, Request.options, Tools),
    Tools \== [],
    cutoff_native_call("slice_1", ToolCall).
cutoff_model_response(2, Request, "SYNTHESIZED", []) :-
    \+ get_dict(tools, Request.options, _),
    \+ get_dict(tool_choice, Request.options, _),
    !.
cutoff_model_response(2, _, "", [ToolCall]) :-
    cutoff_native_call("slice_2", ToolCall).

cutoff_options(
    [ provider(provider(openai_compatible, [])),
      provider_name(openai_compatible),
      model_handler(plunit_auto_dig_native_cutoff_hotfix:cutoff_model),
      capabilities([context(slice)]),
      prompt_compile_mode(all_tools),
      native_tool_cutoff_model_calls(1),
      budget(_{
          max_iterations:4,
          max_model_calls:2,
          max_tool_calls:2,
          max_context_ops:2,
          max_total_tokens:1000,
          max_output_bytes:8192
      })
    ]).

test(provider_tools_are_removed_after_configured_model_call_cutoff) :-
    reset_cutoff_model,
    cutoff_options(Options),
    rlm_direct("Inspect once, then synthesize",
               text("opaque"),
               Options,
               Outcome),
    Outcome = ok(Result),
    assertion(Result.value == "SYNTHESIZED"),
    assertion(Result.turns =:= 2),
    assertion(Result.context_calls =:= 1),
    assertion(cutoff_model_call(2)).

:- end_tests(auto_dig_native_cutoff_hotfix).

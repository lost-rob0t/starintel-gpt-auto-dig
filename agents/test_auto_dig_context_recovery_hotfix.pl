:- begin_tests(auto_dig_context_recovery_hotfix).

:- use_module(library(http/json)).
:- use_module(library(rlm_direct), [rlm_direct/4]).

:- dynamic context_model_call/1.

reset_context_model :-
    retractall(context_model_call(_)),
    assertz(context_model_call(0)).

next_context_model_call(Call) :-
    retract(context_model_call(Previous)),
    Call is Previous+1,
    assertz(context_model_call(Call)).

native_call(Id, Name, Args, Call) :-
    atom_json_dict(ArgumentsAtom, Args, [width(0)]),
    atom_string(ArgumentsAtom, Arguments),
    atom_string(Name, WireName),
    Call = json{
        id:Id,
        type:"function",
        function:json{name:WireName, arguments:Arguments}
    }.

model_response(Call, Text, ToolCalls,
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
    format(string(ResponseId), "context_response_~d", [Call]),
    (   ToolCalls == []
    ->  FinishReason = stop
    ;   FinishReason = tool_calls
    ).

context_repair_model(Request, ok(Response)) :-
    next_context_model_call(Call),
    context_model_response(Call, Request, Text, ToolCalls),
    model_response(Call, Text, ToolCalls, Response).

context_model_response(1, _, "", [ToolCall]) :-
    native_call("ctx_1",
                context_slice,
                json{context:"missing-alias", start:0, length:4},
                ToolCall).
context_model_response(2, Request, "RECOVERED", []) :-
    context_failure_message(Request, Content),
    assertion(sub_string(Content, _, _, _, "unknown_context_alias")),
    assertion(sub_string(Content, _, _, _, "missing-alias")),
    assertion(sub_string(Content, _, _, _, "input")).

context_failure_message(Request, Content) :-
    member(Message, Request.messages),
    Message.role == tool,
    Message.tool_call_id == "ctx_1",
    Message.name == context_slice,
    Content = Message.content,
    !.

context_options(
    [ provider(provider(openai_compatible, [])),
      provider_name(openai_compatible),
      model_handler(plunit_auto_dig_context_recovery_hotfix:context_repair_model),
      capabilities([context(slice)]),
      prompt_compile_mode(all_tools),
      budget(_{
          max_iterations:4,
          max_model_calls:3,
          max_tool_calls:1,
          max_context_ops:2,
          max_total_tokens:1000,
          max_output_bytes:8192
      })
    ]).

test(unknown_context_alias_is_model_repairable_without_alias_substitution) :-
    reset_context_model,
    context_options(Options),
    rlm_direct("Read context and repair an invalid alias",
               text("opaque context content"),
               Options,
               Outcome),
    Outcome = ok(Result),
    assertion(Result.value == "RECOVERED"),
    assertion(Result.turns =:= 2),
    assertion(Result.context_calls =:= 1),
    assertion(context_model_call(2)),
    once(( member(Event, Result.trajectory),
           Event.type == native_context,
           Event.call_id == "ctx_1",
           Event.status == error
         )),
    assertion(Event.kind == unknown_context_alias),
    assertion(Event.result.value.requested_context == "missing-alias"),
    assertion(memberchk("input", Event.result.value.available_contexts)).

:- end_tests(auto_dig_context_recovery_hotfix).

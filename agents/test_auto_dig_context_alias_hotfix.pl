:- begin_tests(auto_dig_context_alias_hotfix).

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

context_native_call(Id, ContextAlias, Start, Length, Call) :-
    atom_json_dict(ArgumentsAtom,
                   json{context:ContextAlias,start:Start,length:Length},
                   [width(0)]),
    atom_string(ArgumentsAtom, Arguments),
    Call = json{
        id:Id,
        type:"function",
        function:json{name:"context_slice", arguments:Arguments}
    }.

context_response(Call, Text, ToolCalls,
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
    format(string(ResponseId), "context_alias_response_~d", [Call]),
    ( ToolCalls == [] -> FinishReason = stop ; FinishReason = tool_calls ).

context_model(Request, ok(Response)) :-
    next_context_model_call(Call),
    context_model_response(Call, Request, Text, ToolCalls),
    context_response(Call, Text, ToolCalls, Response).

% Reproduce the live GLM failure shape: a provider emits a call ID as the
% context alias instead of the retained result alias. Context reads are
% side-effect-free, so this should become a bounded repair observation rather
% than terminate the direct session.
context_model_response(1, _, "", [ToolCall]) :-
    context_native_call("context_bad",
                        "call_70e2a06482f44f86b174220f",
                        0,
                        16,
                        ToolCall).
context_model_response(2, Request, "", [ToolCall]) :-
    context_tool_message(Request, "context_bad", ErrorContent),
    assertion(sub_string(ErrorContent, _, _, _, "unknown_context_alias")),
    assertion(sub_string(ErrorContent, _, _, _, "input")),
    context_native_call("context_good", "input", 0, 16, ToolCall).
context_model_response(3, Request, "RECOVERED CONTEXT ALIAS", []) :-
    context_tool_message(Request, "context_good", SliceContent),
    assertion(\+ sub_string(SliceContent, _, _, _, "unknown_context_alias")),
    assertion(sub_string(SliceContent, _, _, _, "0123456789abcdef")).

context_tool_message(Request, CallId, Content) :-
    member(Message, Request.messages),
    Message.role == tool,
    Message.tool_call_id == CallId,
    Content = Message.content,
    !.

context_options([
    provider(provider(openai_compatible, [])),
    provider_name(openai_compatible),
    model_handler(plunit_auto_dig_context_alias_hotfix:context_model),
    capabilities([context(slice)]),
    prompt_compile_mode(all_tools),
    budget(_{
        max_iterations:6,
        max_recursion_depth:1,
        max_concurrent_subcalls:1,
        max_model_calls:4,
        max_tool_calls:0,
        max_context_ops:3,
        max_total_tokens:1000,
        max_cost_usd:1.0,
        max_output_bytes:8192,
        time_limit:10.0
    })
]).

test(unknown_context_alias_is_model_repairable_for_read_only_context) :-
    reset_context_model,
    context_options(Options),
    rlm_direct("Read the input context, repairing a bad alias if needed.",
               text("0123456789abcdef-opaque-context"),
               Options,
               Outcome),
    Outcome = ok(Result),
    assertion(Result.value == "RECOVERED CONTEXT ALIAS"),
    assertion(Result.turns =:= 3),
    assertion(Result.context_calls =:= 2),
    assertion(context_model_call(3)),
    once(( member(Event, Result.trajectory),
           Event.type == native_context,
           Event.call_id == "context_bad"
         )),
    assertion(Event.status == error),
    assertion(Event.kind == unknown_context_alias).

:- end_tests(auto_dig_context_alias_hotfix).

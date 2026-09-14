:- prolog_load_context(directory, Dir),
   directory_file_path(Dir, 'test_auto_dig_provider_retry_hotfix_base.pl', Base),
   ensure_loaded(Base).

:- begin_tests(auto_dig_context_selector_recovery).

:- use_module(library(http/json)).
:- use_module(library(rlm_direct), [rlm_direct/4]).

:- dynamic selector_model_call/1.

reset_selector_model :-
    retractall(selector_model_call(_)),
    assertz(selector_model_call(0)).

next_selector_model_call(Call) :-
    retract(selector_model_call(Previous)),
    Call is Previous+1,
    assertz(selector_model_call(Call)).

selector_native_call(Id, Name, Args, Call) :-
    atom_json_dict(ArgumentsAtom, Args, [width(0)]),
    atom_string(ArgumentsAtom, Arguments),
    atom_string(Name, WireName),
    Call = json{
        id:Id,
        type:"function",
        function:json{name:WireName, arguments:Arguments}
    }.

selector_response(Call, Text, ToolCalls,
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
    format(string(ResponseId), "selector_response_~d", [Call]),
    (   ToolCalls == []
    ->  FinishReason = stop
    ;   FinishReason = tool_calls
    ).

selector_model(Request, ok(Response)) :-
    next_selector_model_call(Call),
    selector_model_response(Call, Request, Text, ToolCalls),
    selector_response(Call, Text, ToolCalls, Response).

selector_model_response(1, _, "", [ToolCall]) :-
    selector_native_call(
        "ctx_selector_1",
        context_peek,
        json{context:"input", selector:json{type:"item", index:5}},
        ToolCall).
selector_model_response(2, Request, "RECOVERED", []) :-
    selector_tool_message(Request, Content),
    assertion(sub_string(Content, _, _, _, "unsupported_selector")),
    assertion(sub_string(Content, _, _, _, "text")),
    assertion(sub_string(Content, _, _, _, "item(5)")).

selector_tool_message(Request, Content) :-
    member(Message, Request.messages),
    Message.role == tool,
    Message.tool_call_id == "ctx_selector_1",
    Content = Message.content,
    !.

selector_options(
    [ provider(provider(openai_compatible, [])),
      provider_name(openai_compatible),
      model_handler(plunit_auto_dig_context_selector_recovery:selector_model),
      capabilities([context(peek)]),
      budget(_{
          max_iterations:4,
          max_model_calls:3,
          max_tool_calls:0,
          max_context_ops:2,
          max_total_tokens:1000,
          max_output_bytes:8192
      })
    ]).

test(text_item_selector_is_model_repairable) :-
    reset_selector_model,
    selector_options(Options),
    rlm_direct("Inspect text context and recover from a selector mismatch",
               text("line zero\nline one\nline two\nline three\nline four\nline five"),
               Options,
               Outcome),
    Outcome = ok(Result),
    assertion(Result.value == "RECOVERED"),
    assertion(Result.turns =:= 2),
    assertion(Result.context_calls =:= 1),
    assertion(selector_model_call(2)),
    once(( member(Event, Result.trajectory),
           Event.type == native_context,
           Event.call_id == "ctx_selector_1"
         )),
    assertion(Event.status == error),
    assertion(Event.kind == unsupported_selector).

:- end_tests(auto_dig_context_selector_recovery).

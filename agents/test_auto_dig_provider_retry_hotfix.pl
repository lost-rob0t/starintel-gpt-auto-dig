:- begin_tests(auto_dig_provider_retry_hotfix).

:- use_module(library(http/json)).
:- use_module(library(rlm_completion), [call_model/4]).
:- use_module(library(rlm_direct), [rlm_direct/4]).
:- use_module(library(rlm_native_tool),
              [ native_tool_call_normalize/2,
                native_tool_schema_normalize/2,
                native_tool_schema_wire/3,
                native_tool_result_message/3
              ]).
:- use_module(library(rlm_openai_compatible), []).
:- use_module(library(rlm_tool),
              [ tool_registry_create/1,
                tool_registry_destroy/1,
                tool_register/4
              ]).

:- dynamic attempt_count/1.
:- dynamic read_failure_model_call/1.

reset_attempts :-
    retractall(attempt_count(_)),
    assertz(attempt_count(0)).

next_attempt(Attempt) :-
    retract(attempt_count(Previous)),
    Attempt is Previous+1,
    assertz(attempt_count(Attempt)).

flaky_429(_, Outcome) :-
    next_attempt(Attempt),
    (   Attempt =:= 1
    ->  Outcome = error(provider_error{
                            provider:openrouter,
                            kind:provider_error,
                            code:429,
                            http_status:200,
                            response_received:true,
                            message:"temporarily rate-limited"
                        })
    ;   Outcome = ok(recovered)
    ).

fatal_401(_, error(provider_error{
                       provider:openrouter,
                       kind:provider_error,
                       code:401,
                       http_status:401,
                       response_received:true,
                       message:"unauthorized"
                   })) :-
    next_attempt(_).

retry_test_options(Handler,
                   [ model_handler(Handler),
                     provider_retry_attempts(2),
                     provider_retry_base_delay(0.0),
                     provider_retry_max_delay(0.0)
                   ]).

empty_request(model_request{messages:[], options:_{}}).

runtime_schema(Name,
               native_tool_schema{
                   name:Name,
                   description:"test provider tool name projection",
                   capability:tool(Name),
                   effect:read,
                   arguments:json_schema{
                       type:object,
                       properties:json_schema{},
                       required:[],
                       additional_properties:false
                   }
               }).

wire_schema(Name, Native, Wire) :-
    runtime_schema(Name, Runtime),
    native_tool_schema_normalize(Runtime, ok(Native)),
    native_tool_schema_wire(openai_compatible, Native, ok(Wire)).

provider_safe_name(Name) :-
    string_codes(Name, Codes),
    Codes \== [],
    maplist(provider_safe_code, Codes).

provider_safe_code(Code) :-
    (   Code >= 0'A, Code =< 0'Z
    ;   Code >= 0'a, Code =< 0'z
    ;   Code >= 0'0, Code =< 0'9
    ;   memberchk(Code, [0'_,0'-])
    ).

reset_read_failure_model :-
    retractall(read_failure_model_call(_)),
    assertz(read_failure_model_call(0)).

next_read_failure_model_call(Call) :-
    retract(read_failure_model_call(Previous)),
    Call is Previous+1,
    assertz(read_failure_model_call(Call)).

read_failure_native_call(Id, Name, Args, Call) :-
    atom_json_dict(ArgumentsAtom, Args, [width(0)]),
    atom_string(ArgumentsAtom, Arguments),
    atom_string(Name, WireName),
    Call = json{
        id:Id,
        type:"function",
        function:json{name:WireName, arguments:Arguments}
    }.

read_failure_response(Call, Text, ToolCalls,
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
    format(string(ResponseId), "read_failure_response_~d", [Call]),
    (   ToolCalls == []
    ->  FinishReason = stop
    ;   FinishReason = tool_calls
    ).

read_failure_model(Request, ok(Response)) :-
    next_read_failure_model_call(Call),
    read_failure_model_response(Call, Request, Text, ToolCalls),
    read_failure_response(Call, Text, ToolCalls, Response).

read_failure_model_response(1, _, "", [ToolCall]) :-
    read_failure_native_call(
        "fetch_1",
        read_failure_tool,
        json{url:"https://example.invalid/article", proxy:""},
        ToolCall).
read_failure_model_response(2, Request, "RECOVERED", []) :-
    read_failure_tool_message(Request, Content),
    assertion(sub_string(Content, _, _, _, "handler_exception")),
    assertion(sub_string(Content, _, _, _, "Invalid URL")).

read_failure_tool_message(Request, Content) :-
    member(Message, Request.messages),
    Message.role == tool,
    Message.tool_call_id == "fetch_1",
    Message.name == read_failure_tool,
    Content = Message.content,
    !.

read_failure_schema(
    tool_schema{
        name:read_failure_tool,
        description:"Simulate an MCP read tool rejecting an invalid optional URL",
        capability:tool(read_failure_tool),
        effect:read,
        arguments:_{
            type:object,
            properties:_{
                url:_{type:string},
                proxy:_{type:string}
            },
            required:[url],
            additional_properties:false
        },
        result:_{type:string},
        limits:_{time_limit:1.0, max_output_bytes:4096}
    }).

read_failure_handler(_, _) :-
    throw(error(
        rlm_mcp_imported_tool(
            error(mcp_error{
                phase:adapter_2025_11_25,
                kind:protocol_error,
                message:"MCP protocol operation failed",
                detail:remote_error(mcp_remote_error{
                    code: -32603,
                    data:none,
                    message:"proxy: Invalid URL"
                })
            })),
        context(read_failure_handler, "simulated remote validation error"))).

read_failure_options(Registry,
                     [ provider(provider(openai_compatible, [])),
                       provider_name(openai_compatible),
                       model_handler(
                           plunit_auto_dig_provider_retry_hotfix:read_failure_model),
                       capabilities([tool(read_failure_tool)]),
                       prompt_compile_mode(all_tools),
                       tool_registry(Registry),
                       budget(_{
                           max_iterations:4,
                           max_model_calls:3,
                           max_tool_calls:2,
                           max_context_ops:1,
                           max_total_tokens:1000,
                           max_output_bytes:8192
                       })
                     ]).

test(transient_429_retries_same_provider_request) :-
    reset_attempts,
    retry_test_options(
        plunit_auto_dig_provider_retry_hotfix:flaky_429,
        Options),
    empty_request(Request),
    call_model(Options,
               provider(openrouter, []),
               Request,
               ok(recovered)),
    attempt_count(2).

test(non_transient_401_fails_without_retry) :-
    reset_attempts,
    retry_test_options(
        plunit_auto_dig_provider_retry_hotfix:fatal_401,
        Options),
    empty_request(Request),
    call_model(Options,
               provider(openrouter, []),
               Request,
               error(Error)),
    assertion(Error.code =:= 401),
    attempt_count(1).

test(dotted_mcp_name_roundtrips_through_provider_wire) :-
    Name = 'mcp.brave.brave_web_search',
    wire_schema(Name, _, Wire),
    WireName = Wire.function.name,
    assertion(provider_safe_name(WireName)),
    assertion(\+ sub_string(WireName, _, _, _, ".")),
    WireCall = json{
        id:"call-1",
        type:"function",
        function:json{name:WireName, arguments:"{}"}
    },
    native_tool_call_normalize(WireCall, ok(Call)),
    assertion(Call.name == Name).

test(reserved_prefix_safe_name_is_collision_free) :-
    Name = 'rlm0_safe_name',
    wire_schema(Name, _, Wire),
    WireName = Wire.function.name,
    assertion(provider_safe_name(WireName)),
    assertion(WireName \== "rlm0_safe_name"),
    WireCall = json{
        id:"call-2",
        type:"function",
        function:json{name:WireName, arguments:"{}"}
    },
    native_tool_call_normalize(WireCall, ok(Call)),
    assertion(Call.name == Name).

test(tool_result_message_reencodes_internal_name_for_next_turn) :-
    Name = 'mcp.fetch.fetch_markdown',
    wire_schema(Name, _, Wire),
    WireName = Wire.function.name,
    WireCall = json{
        id:"call-3",
        type:"function",
        function:json{name:WireName, arguments:"{}"}
    },
    native_tool_call_normalize(WireCall, ok(Call)),
    Result = native_tool_result{
        call_id:"call-3",
        name:Name,
        value:json{ok:true}
    },
    native_tool_result_message(Call, Result, ok(Message)),
    Request = model_request{
        messages:[Message],
        options:generation_options{}
    },
    rlm_openai_compatible:request_payload(Request,
                                          'vendor/model',
                                          ok(Payload)),
    Payload.messages = [PayloadMessage],
    assertion(PayloadMessage.name == WireName),
    assertion(provider_safe_name(PayloadMessage.name)).

test(read_only_handler_exception_is_model_repairable) :-
    reset_read_failure_model,
    tool_registry_create(Registry),
    setup_call_cleanup(
        ( read_failure_schema(Schema),
          tool_register(
              Registry,
              Schema,
              plunit_auto_dig_provider_retry_hotfix:read_failure_handler,
              Registration),
          assertion(Registration = ok(_))
        ),
        ( read_failure_options(Registry, Options),
          rlm_direct("Use the read tool and recover from remote validation",
                     text("opaque"),
                     Options,
                     Outcome),
          Outcome = ok(Result),
          assertion(Result.value == "RECOVERED"),
          assertion(Result.turns =:= 2),
          assertion(Result.tool_calls =:= 1),
          assertion(read_failure_model_call(2)),
          once(( member(Event, Result.trajectory),
                 Event.type == native_tool,
                 Event.call_id == "fetch_1"
               )),
          assertion(Event.status == error),
          assertion(Event.kind == handler_exception)
        ),
        tool_registry_destroy(Registry)).

:- end_tests(auto_dig_provider_retry_hotfix).

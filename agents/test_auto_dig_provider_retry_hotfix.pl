:- begin_tests(auto_dig_provider_retry_hotfix).

:- use_module(library(rlm_completion), [call_model/4]).
:- use_module(library(rlm_native_tool),
              [ native_tool_call_normalize/2,
                native_tool_schema_normalize/2,
                native_tool_schema_wire/3,
                native_tool_result_message/3
              ]).
:- use_module(library(rlm_openai_compatible), []).

:- dynamic attempt_count/1.

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

:- end_tests(auto_dig_provider_retry_hotfix).

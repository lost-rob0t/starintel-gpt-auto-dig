#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


SINGLETON_PATCHES = (
    (
        Path("prolog/rlm_prompt_compiler.pl"),
        "compiler_exception(Phase, Exception, _) :-\n    time_limit_exception(Exception),",
        "compiler_exception(_Phase, Exception, _) :-\n    time_limit_exception(Exception),",
        "rlm_prompt_compiler.pl timeout singleton",
    ),
    (
        Path("prolog/rlm_skill.pl"),
        "skill_exception(Phase, Exception, _) :-\n    time_limit_exception(Exception),",
        "skill_exception(_Phase, Exception, _) :-\n    time_limit_exception(Exception),",
        "rlm_skill.pl timeout singleton",
    ),
)

COMPLETION_OLD = """call_planner(Options, Provider, Request, Outcome) :-
    option_value(planner_handler, Options, none, Handler),
    (   Handler == none
    ->  rlm_chain:model_complete_execute(Provider, Request, Outcome)
    ;   require_callable(Handler, planner_handler),
        catch(call(Handler, Request, RawOutcome),
              Exception,
              handler_exception(planner, Exception, RawOutcome)),
        normalize_handler_outcome(RawOutcome, Outcome)
    ).

call_model(Options, Provider, Request, Outcome) :-
    option_value(model_handler, Options, none, Handler),
    (   Handler == none
    ->  rlm_chain:model_complete_execute(Provider, Request, Outcome)
    ;   require_callable(Handler, model_handler),
        catch(call(Handler, Request, RawOutcome),
              Exception,
              handler_exception(model, Exception, RawOutcome)),
        normalize_handler_outcome(RawOutcome, Outcome)
    ).
"""

COMPLETION_NEW = """call_planner(Options, Provider, Request, Outcome) :-
    provider_call_with_retry(planner, Options, Provider, Request, Outcome).

call_model(Options, Provider, Request, Outcome) :-
    provider_call_with_retry(model, Options, Provider, Request, Outcome).

provider_call_with_retry(Kind, Options, Provider, Request, Outcome) :-
    provider_retry_policy(Options, MaxAttempts, BaseDelay, MaxDelay),
    provider_call_attempt(Kind,
                          Options,
                          Provider,
                          Request,
                          1,
                          MaxAttempts,
                          BaseDelay,
                          MaxDelay,
                          Outcome).

provider_call_attempt(Kind,
                      Options,
                      Provider,
                      Request,
                      Attempt,
                      MaxAttempts,
                      BaseDelay,
                      MaxDelay,
                      Outcome) :-
    provider_call_once(Kind, Options, Provider, Request, CallOutcome),
    (   CallOutcome = error(Error),
        retryable_provider_error(Error),
        Attempt < MaxAttempts
    ->  provider_retry_delay(Attempt, BaseDelay, MaxDelay, Delay),
        sleep(Delay),
        NextAttempt is Attempt+1,
        provider_call_attempt(Kind,
                              Options,
                              Provider,
                              Request,
                              NextAttempt,
                              MaxAttempts,
                              BaseDelay,
                              MaxDelay,
                              Outcome)
    ;   Outcome = CallOutcome
    ).

provider_call_once(Kind, Options, Provider, Request, Outcome) :-
    provider_handler(Kind, Options, Handler, HandlerField),
    (   Handler == none
    ->  rlm_chain:model_complete_execute(Provider, Request, Outcome)
    ;   require_callable(Handler, HandlerField),
        catch(call(Handler, Request, RawOutcome),
              Exception,
              handler_exception(Kind, Exception, RawOutcome)),
        normalize_handler_outcome(RawOutcome, Outcome)
    ).

provider_handler(planner, Options, Handler, planner_handler) :-
    option_value(planner_handler, Options, none, Handler).
provider_handler(model, Options, Handler, model_handler) :-
    option_value(model_handler, Options, none, Handler).

provider_retry_policy(Options, MaxAttempts, BaseDelay, MaxDelay) :-
    option_value(provider_retry_attempts, Options, 5, MaxAttempts),
    require_positive_integer(MaxAttempts, provider_retry_attempts),
    option_value(provider_retry_base_delay, Options, 1.0, BaseDelay),
    require_nonnegative_number(BaseDelay, provider_retry_base_delay),
    option_value(provider_retry_max_delay, Options, 8.0, MaxDelay),
    require_nonnegative_number(MaxDelay, provider_retry_max_delay).

provider_retry_delay(Attempt, BaseDelay, MaxDelay, Delay) :-
    Exponent is max(0, Attempt-1),
    Raw is BaseDelay*(2 ** Exponent),
    Delay is min(Raw, MaxDelay).

retryable_provider_error(Error) :-
    is_dict(Error),
    (   provider_transient_status(Error, code)
    ;   provider_transient_status(Error, http_status)
    ).

provider_transient_status(Error, Key) :-
    get_dict(Key, Error, Status),
    integer(Status),
    memberchk(Status, [408,425,429,500,502,503,504]).
"""

NATIVE_EXPORT_OLD = """:- module(rlm_native_tool,
          [ native_tool_call_normalize/2,
            native_tool_calls_normalize/2,
            native_tool_calls_classify/2,
            native_tool_schema_normalize/2,
            native_tool_schema_wire/3,
            native_tool_result_message/3
          ]).
"""

NATIVE_EXPORT_NEW = """:- module(rlm_native_tool,
          [ native_tool_call_normalize/2,
            native_tool_calls_normalize/2,
            native_tool_calls_classify/2,
            native_tool_schema_normalize/2,
            native_tool_schema_wire/3,
            native_tool_name_wire/2,
            native_tool_name_unwire/2,
            native_tool_result_message/3
          ]).
"""

NATIVE_CALL_OLD = """    require_key(Function, name, Name0, function),
    normalize_tool_name(Name0, Name),
    require_key(Function, arguments, Arguments0, function).
"""

NATIVE_CALL_NEW = """    require_key(Function, name, Name0, function),
    native_tool_name_unwire(Name0, Name),
    require_key(Function, arguments, Arguments0, function).
"""

NATIVE_WIRE_OLD = """native_schema_wire(openai_compatible, Schema, Wire) :-
    require_native_schema(Schema),
    atom_string(Schema.name, Name),
    Wire = json{type:\"function\",
                function:json{name:Name,
                              description:Schema.description,
                              parameters:Schema.parameters}},
    !.
"""

NATIVE_WIRE_NEW = """native_schema_wire(openai_compatible, Schema, Wire) :-
    require_native_schema(Schema),
    native_tool_name_wire(Schema.name, Name),
    Wire = json{type:\"function\",
                function:json{name:Name,
                              description:Schema.description,
                              parameters:Schema.parameters}},
    !.
"""

NATIVE_CODEC_OLD = """normalize_tool_name(Name0, Name) :-
    normalize_protocol_token(Name0, tool_name, Text),
    atom_string(Name, Text).

normalize_protocol_token(Value, Field, Text) :-
"""

NATIVE_CODEC_NEW = """normalize_tool_name(Name0, Name) :-
    normalize_protocol_token(Name0, tool_name, Text),
    atom_string(Name, Text).

% OpenAI-compatible function names accept only ASCII alphanumerics, `_`, and
% `-`. Runtime/MCP capability names intentionally retain `.` and `:`. Keep the
% runtime identity canonical and project only the provider wire name through a
% reserved, reversible codec. Safe names remain unchanged unless they occupy
% the reserved prefix, preventing collisions with encoded names.
native_tool_name_wire(Name0, WireName) :-
    normalize_tool_name(Name0, Name),
    atom_string(Name, Text),
    (   provider_safe_tool_name(Text),
        \\+ sub_string(Text, 0, 5, _, \"rlm0_\")
    ->  WireName = Text
    ;   provider_tool_encode(Text, Encoded),
        string_concat(\"rlm0_\", Encoded, WireName)
    ).

native_tool_name_unwire(Name0, Name) :-
    normalize_protocol_token(Name0, tool_name, Text),
    (   sub_string(Text, 0, 5, _, \"rlm0_\")
    ->  sub_string(Text, 5, _, 0, Encoded),
        (   provider_tool_decode(Encoded, Decoded)
        ->  normalize_tool_name(Decoded, Name)
        ;   native_error(normalize, malformed_tool_name_alias,
                         _{value:Text},
                         \"provider tool name alias is malformed\")
        )
    ;   atom_string(Name, Text)
    ).

provider_safe_tool_name(Text) :-
    string_codes(Text, Codes),
    Codes \\== [],
    maplist(provider_safe_tool_name_code, Codes).

provider_safe_tool_name_code(Code) :-
    (   Code >= 0'A, Code =< 0'Z
    ;   Code >= 0'a, Code =< 0'z
    ;   Code >= 0'0, Code =< 0'9
    ;   memberchk(Code, [0'_,0'-])
    ).

provider_tool_encode(Text, Encoded) :-
    string_codes(Text, Codes),
    (   provider_tool_encode_codes(Codes, EncodedCodes)
    ->  string_codes(Encoded, EncodedCodes)
    ;   native_error(render, unsupported_provider_tool_name,
                     _{value:Text},
                     \"provider tool name contains unsupported characters\")
    ).

provider_tool_encode_codes([], []).
provider_tool_encode_codes([Code|Codes], Encoded) :-
    provider_tool_encode_code(Code, Head),
    provider_tool_encode_codes(Codes, Tail),
    append(Head, Tail, Encoded).

provider_tool_encode_code(0'_, [0'_,0'u]) :- !.
provider_tool_encode_code(0'., [0'_,0'd]) :- !.
provider_tool_encode_code(0':, [0'_,0'c]) :- !.
provider_tool_encode_code(Code, [Code]) :-
    provider_safe_tool_name_code(Code),
    Code =\\= 0'_.

provider_tool_decode(Text, Decoded) :-
    string_codes(Text, Codes),
    provider_tool_decode_codes(Codes, DecodedCodes),
    string_codes(Decoded, DecodedCodes).

provider_tool_decode_codes([], []).
provider_tool_decode_codes([0'_,0'u|Codes], [0'_|Decoded]) :-
    !,
    provider_tool_decode_codes(Codes, Decoded).
provider_tool_decode_codes([0'_,0'd|Codes], [0'.|Decoded]) :-
    !,
    provider_tool_decode_codes(Codes, Decoded).
provider_tool_decode_codes([0'_,0'c|Codes], [0':|Decoded]) :-
    !,
    provider_tool_decode_codes(Codes, Decoded).
provider_tool_decode_codes([0'_|_], _) :-
    !,
    fail.
provider_tool_decode_codes([Code|Codes], [Code|Decoded]) :-
    provider_safe_tool_name_code(Code),
    Code =\\= 0'_,
    provider_tool_decode_codes(Codes, Decoded).

normalize_protocol_token(Value, Field, Text) :-
"""

OPENAI_IMPORT_OLD = ":- use_module(library(pairs)).\n"
OPENAI_IMPORT_NEW = """:- use_module(library(pairs)).
:- use_module(rlm_native_tool, [native_tool_name_wire/2]).
"""

OPENAI_MESSAGE_OLD = """message_payload(Message, Payload) :-
    get_dict(role, Message, Role),
    get_dict(content, Message, Content),
    Base = message_payload{role:Role, content:Content},
    copy_optional_message_fields([name,
                                  tool_call_id,
                                  tool_calls,
                                  reasoning,
                                  reasoning_details],
                                 Message, Base, Payload).
"""

OPENAI_MESSAGE_NEW = """message_payload(Message, Payload) :-
    get_dict(role, Message, Role),
    get_dict(content, Message, Content),
    Base = message_payload{role:Role, content:Content},
    copy_optional_message_fields([tool_call_id,
                                  tool_calls,
                                  reasoning,
                                  reasoning_details],
                                 Message, Base, Payload0),
    copy_optional_provider_message_name(Message, Payload0, Payload).

copy_optional_provider_message_name(Message, Payload0, Payload) :-
    (   get_dict(name, Message, Name0)
    ->  native_tool_name_wire(Name0, Name),
        put_dict(name, Payload0, Name, Payload)
    ;   Payload = Payload0
    ).
"""

DIRECT_AFTER_TOOL_OLD = """after_tool(ToolResult, Resolved, _, _, State, error(Error)) :-
    ToolResult.outcome = error(Cause),
    !,
    tool_failure_state(ToolResult, Resolved, error, State, State1),
    error_kind(Cause, tool_execution_failed, Kind),
    state_error(State1, tool, Kind, _{cause:Cause},
                \"native registered-tool execution failed\", Error).
"""

DIRECT_AFTER_TOOL_NEW = """% Read-only handler/runtime failures are safe to surface as a bounded tool
% observation. The provider can repair malformed remote arguments or choose a
% fallback without terminating the whole direct session. Effectful failures
% remain fatal because retry/fallback could duplicate or obscure effects.
recoverable_read_tool_error(Cause) :-
    is_dict(Cause),
    get_dict(phase, Cause, invoke),
    get_dict(kind, Cause, Kind),
    memberchk(Kind, [handler_failed,handler_exception,timeout]).

read_tool_failure_observation(ToolResult, Resolved, Event, Result) :-
    Call = Resolved.call,
    Binding = Resolved.binding,
    ToolResult.outcome = error(Cause),
    get_dict(kind, Cause, Kind),
    Trace = ToolResult.trace,
    read_tool_failure_value(Cause, Value),
    Result = native_tool_result{call_id:Call.id,
                                name:Call.name,
                                operation:Binding.kind,
                                value:Value,
                                truncated:false,
                                trace:Trace},
    Event = direct_event{type:native_tool,
                         call_id:Call.id,
                         name:Call.name,
                         status:error,
                         kind:Kind,
                         result:Result,
                         trace:Trace}.

read_tool_failure_value(Cause, Value) :-
    get_dict(kind, Cause, Kind),
    get_dict(message, Cause, Message),
    Base = _{error:Kind, message:Message},
    (   read_tool_failure_detail(Cause, Detail)
    ->  put_dict(detail, Base, Detail, Value)
    ;   Value = Base
    ).

read_tool_failure_detail(Cause, Detail) :-
    (   get_dict(cause, Cause, Detail)
    ;   get_dict(detail, Cause, Detail)
    ;   get_dict(exception, Cause, Detail)
    ),
    !.

after_tool(ToolResult, Resolved, Calls, Runtime, State0, Outcome) :-
    ToolResult.outcome = error(Cause),
    Resolved.binding.effect == read,
    recoverable_read_tool_error(Cause),
    !,
    read_tool_failure_observation(ToolResult, Resolved, Event, Result),
    append_observation(Resolved.call,
                       Result,
                       Event,
                       Runtime,
                       State0,
                       StateOutcome),
    continue_observation(StateOutcome, Calls, Runtime, Outcome).
after_tool(ToolResult, Resolved, _, _, State, error(Error)) :-
    ToolResult.outcome = error(Cause),
    !,
    tool_failure_state(ToolResult, Resolved, error, State, State1),
    error_kind(Cause, tool_execution_failed, Kind),
    state_error(State1, tool, Kind, _{cause:Cause},
                \"native registered-tool execution failed\", Error).
"""

DIRECT_CONTEXT_EXECUTE_OLD = """execute_one(Resolved, Runtime, State, context(ContextOutcome)) :-
    Resolved.binding.kind = context(Operation),
    !,
    context_arguments(Resolved.binding.kind, Resolved.call.arguments, Args),
    context_handle(Args.context, State.contexts, Handle),
    context_runtime_options(Runtime.options, ContextOptions),
    call_context(Operation, Handle, Args, ContextOptions, ContextOutcome).
"""

DIRECT_CONTEXT_EXECUTE_NEW = """execute_one(Resolved, Runtime, State, context(ContextOutcome)) :-
    Resolved.binding.kind = context(Operation),
    !,
    context_arguments(Resolved.binding.kind, Resolved.call.arguments, Args),
    catch(context_handle(Args.context, State.contexts, Handle),
          direct_fault(Cause),
          ContextOutcome = error(Cause)),
    (   var(ContextOutcome)
    ->  context_runtime_options(Runtime.options, ContextOptions),
        call_context(Operation, Handle, Args, ContextOptions, ContextOutcome)
    ;   true
    ).
"""

DIRECT_AFTER_CONTEXT_OLD = """after_execution(context(error(Cause)), _, _, _, State, error(Error)) :-
    !,
    state_error(State, context, context_operation_failed, _{cause:Cause},
                \"native context operation failed\", Error).
"""

DIRECT_AFTER_CONTEXT_NEW = """% An unknown opaque context alias is a read-only reference mistake, not an
% authority or effect failure. Surface it as one correlated, bounded model
% observation so the provider can retry with an alias the runtime actually
% advertised. Never guess or silently rewrite the requested alias.
recoverable_context_error(Cause) :-
    is_dict(Cause),
    get_dict(phase, Cause, context),
    get_dict(kind, Cause, unknown_context_alias),
    get_dict(context, Cause, _).

context_failure_observation(Cause, Resolved, Contexts, Event, Result) :-
    Call = Resolved.call,
    get_dict(context, Cause, RequestedContext),
    get_dict(message, Cause, Message),
    findall(Alias,
            ( member(Context, Contexts), Alias = Context.id ),
            AvailableContexts),
    Value = _{error:unknown_context_alias,
              message:Message,
              requested_context:RequestedContext,
              available_contexts:AvailableContexts},
    Trace = context_failure_trace{phase:context,
                                  kind:unknown_context_alias,
                                  requested_context:RequestedContext},
    Result = native_tool_result{call_id:Call.id,
                                name:Call.name,
                                operation:Resolved.binding.kind,
                                value:Value,
                                truncated:false,
                                trace:Trace},
    Event = direct_event{type:native_context,
                         call_id:Call.id,
                         name:Call.name,
                         status:error,
                         kind:unknown_context_alias,
                         result:Result,
                         trace:Trace}.

after_execution(context(error(Cause)), Resolved, Calls, Runtime, State0,
                Outcome) :-
    recoverable_context_error(Cause),
    !,
    context_failure_observation(Cause,
                                Resolved,
                                State0.contexts,
                                Event,
                                Result),
    append_observation(Resolved.call,
                       Result,
                       Event,
                       Runtime,
                       State0,
                       StateOutcome),
    continue_observation(StateOutcome, Calls, Runtime, Outcome).
after_execution(context(error(Cause)), _, _, _, State, error(Error)) :-
    !,
    state_error(State, context, context_operation_failed, _{cause:Cause},
                \"native context operation failed\", Error).
"""

DIRECT_PROVIDER_TURN_OLD = """provider_turn(Runtime, State0, Outcome) :-
    remaining_tokens(Runtime.budget.max_total_tokens,
                     State0.usage.total_tokens,
                     Remaining),
    planner_token_limit(Runtime.options, Requested),
    Limit is max(1, min(Requested, Remaining)),
    model_request_options(Runtime.options, Limit, BaseOptions),
    native_request_options(Runtime.options, Limit, BaseOptions, StepOptions),
    request_options(Runtime.schemas, StepOptions, RequestOptions),
    Request = model_request{messages:State0.messages,options:RequestOptions},
    call_model(Runtime.options, Runtime.provider, Request, ModelOutcome),
    after_provider(ModelOutcome, Runtime, State0, Outcome).
"""

DIRECT_PROVIDER_TURN_NEW = """provider_turn(Runtime, State0, Outcome) :-
    remaining_tokens(Runtime.budget.max_total_tokens,
                     State0.usage.total_tokens,
                     Remaining),
    planner_token_limit(Runtime.options, Requested),
    Limit is max(1, min(Requested, Remaining)),
    model_request_options(Runtime.options, Limit, BaseOptions),
    native_request_options(Runtime.options, Limit, BaseOptions, StepOptions),
    direct_request_options(Runtime, State0, StepOptions, RequestOptions),
    Request = model_request{messages:State0.messages,options:RequestOptions},
    call_model(Runtime.options, Runtime.provider, Request, ModelOutcome),
    after_provider(ModelOutcome, Runtime, State0, Outcome).

direct_request_options(Runtime, State, StepOptions, RequestOptions) :-
    native_tool_cutoff(Runtime.options, Cutoff),
    (   Cutoff == disabled
    ->  request_options(Runtime.schemas, StepOptions, RequestOptions)
    ;   State.model_calls >= Cutoff
    ->  RequestOptions = StepOptions
    ;   request_options(Runtime.schemas, StepOptions, RequestOptions)
    ).

native_tool_cutoff(Options, Cutoff) :-
    option(native_tool_cutoff_model_calls, Options, none, Requested),
    (   Requested == none
    ->  Cutoff = disabled
    ;   integer(Requested),
        Requested >= 0
    ->  Cutoff = Requested
    ;   throw(direct_fault(direct_error{
                             phase:provider,
                             kind:invalid_native_tool_cutoff,
                             option:native_tool_cutoff_model_calls,
                             value:Requested,
                             message:\"native tool cutoff must be a nonnegative integer\"}))
    ).
"""


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_tree(root: Path) -> None:
    plans: dict[Path, str] = {}

    for relative, old, new, label in SINGLETON_PATCHES:
        path = root / relative
        text = path.read_text(encoding="utf-8")
        plans[path] = replace_exact(text, old, new, label)

    completion = root / "prolog/rlm_completion.pl"
    completion_text = completion.read_text(encoding="utf-8")
    plans[completion] = replace_exact(
        completion_text,
        COMPLETION_OLD,
        COMPLETION_NEW,
        "rlm_completion.pl transient provider retry",
    )

    native_tool = root / "prolog/rlm_native_tool.pl"
    native_text = native_tool.read_text(encoding="utf-8")
    native_text = replace_exact(
        native_text,
        NATIVE_EXPORT_OLD,
        NATIVE_EXPORT_NEW,
        "rlm_native_tool.pl wire-name exports",
    )
    native_text = replace_exact(
        native_text,
        NATIVE_CALL_OLD,
        NATIVE_CALL_NEW,
        "rlm_native_tool.pl provider call-name decode",
    )
    native_text = replace_exact(
        native_text,
        NATIVE_WIRE_OLD,
        NATIVE_WIRE_NEW,
        "rlm_native_tool.pl provider schema-name encode",
    )
    native_text = replace_exact(
        native_text,
        NATIVE_CODEC_OLD,
        NATIVE_CODEC_NEW,
        "rlm_native_tool.pl reversible provider name codec",
    )
    plans[native_tool] = native_text

    openai = root / "prolog/rlm_openai_compatible.pl"
    openai_text = openai.read_text(encoding="utf-8")
    openai_text = replace_exact(
        openai_text,
        OPENAI_IMPORT_OLD,
        OPENAI_IMPORT_NEW,
        "rlm_openai_compatible.pl provider wire-name import",
    )
    openai_text = replace_exact(
        openai_text,
        OPENAI_MESSAGE_OLD,
        OPENAI_MESSAGE_NEW,
        "rlm_openai_compatible.pl tool-result name encode",
    )
    plans[openai] = openai_text

    direct = root / "prolog/rlm_direct.pl"
    direct_text = direct.read_text(encoding="utf-8")
    direct_text = replace_exact(
        direct_text,
        DIRECT_AFTER_TOOL_OLD,
        DIRECT_AFTER_TOOL_NEW,
        "rlm_direct.pl recoverable read-tool invocation failures",
    )
    direct_text = replace_exact(
        direct_text,
        DIRECT_CONTEXT_EXECUTE_OLD,
        DIRECT_CONTEXT_EXECUTE_NEW,
        "rlm_direct.pl recoverable context alias lookup",
    )
    direct_text = replace_exact(
        direct_text,
        DIRECT_AFTER_CONTEXT_OLD,
        DIRECT_AFTER_CONTEXT_NEW,
        "rlm_direct.pl context alias repair observation",
    )
    direct_text = replace_exact(
        direct_text,
        DIRECT_PROVIDER_TURN_OLD,
        DIRECT_PROVIDER_TURN_NEW,
        "rlm_direct.pl native tool cutoff before synthesis",
    )
    plans[direct] = direct_text

    # Validate every replacement before mutating any checked-out dependency file.
    for path, text in plans.items():
        if not text.endswith("\n"):
            raise RuntimeError(f"{path}: patched text unexpectedly lacks final newline")

    for path, text in plans.items():
        path.write_text(text, encoding="utf-8")
        print(f"patched {path.relative_to(root)}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply exact pinned Prolog-RLM hotfixes required by Auto-Dig CI"
    )
    parser.add_argument("root", type=Path, help="checked-out Prolog-RLM root")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")

    patch_tree(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
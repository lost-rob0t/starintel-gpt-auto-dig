#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


EXECUTE_CONTEXT_OLD = """execute_one(Resolved, Runtime, State, context(ContextOutcome)) :-
    Resolved.binding.kind = context(Operation),
    !,
    context_arguments(Resolved.binding.kind, Resolved.call.arguments, Args),
    context_handle(Args.context, State.contexts, Handle),
    context_runtime_options(Runtime.options, ContextOptions),
    call_context(Operation, Handle, Args, ContextOptions, ContextOutcome).
"""

EXECUTE_CONTEXT_NEW = """execute_one(Resolved, Runtime, State, context(ContextOutcome)) :-
    Resolved.binding.kind = context(Operation),
    !,
    context_arguments(Resolved.binding.kind, Resolved.call.arguments, Args),
    catch(context_handle(Args.context, State.contexts, Handle),
          direct_fault(Cause),
          ContextOutcome = error(Cause)),
    (   nonvar(ContextOutcome)
    ->  true
    ;   context_runtime_options(Runtime.options, ContextOptions),
        call_context(Operation, Handle, Args, ContextOptions, ContextOutcome)
    ).
"""

AFTER_CONTEXT_OLD = """after_execution(context(error(Cause)), _, _, _, State, error(Error)) :-
    !,
    state_error(State, context, context_operation_failed, _{cause:Cause},
                \"native context operation failed\", Error).
"""

AFTER_CONTEXT_NEW = """% Context operations are read-only. A bad alias or another bounded context
% read failure can therefore be returned to the provider as structured repair
% evidence without inventing an alias, retrying effects, or weakening
% capability checks. The model remains bounded by the normal model/context
% budgets and must explicitly choose a valid advertised alias on a later turn.
after_execution(context(error(Cause)), Resolved, Calls, Runtime, State0, Outcome) :-
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

context_failure_observation(Cause, Resolved, Contexts, Event, Result) :-
    error_kind(Cause, context_operation_failed, Kind),
    context_failure_message(Cause, Message),
    context_aliases(Contexts, Aliases),
    context_failure_value(Cause, Kind, Message, Aliases, Value),
    Call = Resolved.call,
    Trace = context_trace{status:error,kind:Kind},
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
                         kind:Kind,
                         result:Result}.

context_failure_message(Cause, Message) :-
    (   is_dict(Cause),
        get_dict(message, Cause, Found)
    ->  Message = Found
    ;   Message = \"native context operation failed\"
    ).

context_aliases(Contexts, Aliases) :-
    findall(Id,
            ( member(Context, Contexts),
              Id = Context.id
            ),
            Aliases0),
    sort(Aliases0, Aliases).

context_failure_value(Cause, Kind, Message, Aliases, Value) :-
    Base = _{error:Kind,
             message:Message,
             available_contexts:Aliases},
    (   is_dict(Cause),
        get_dict(context, Cause, Requested)
    ->  put_dict(requested_context, Base, Requested, Value)
    ;   Value = Base
    ).
"""


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one source block, found {count}")
    return text.replace(old, new, 1)


def apply(root: Path) -> None:
    direct = root / "prolog/rlm_direct.pl"
    text = direct.read_text(encoding="utf-8")
    text = replace_exact(
        text,
        EXECUTE_CONTEXT_OLD,
        EXECUTE_CONTEXT_NEW,
        "rlm_direct.pl context alias execution",
    )
    text = replace_exact(
        text,
        AFTER_CONTEXT_OLD,
        AFTER_CONTEXT_NEW,
        "rlm_direct.pl context failure observation",
    )
    direct.write_text(text, encoding="utf-8")
    print(f"patched {direct}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    apply(args.root)


if __name__ == "__main__":
    main()

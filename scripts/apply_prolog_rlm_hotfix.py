#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import apply_prolog_rlm_hotfix_base as base


RECOVERABLE_CONTEXT_OLD = """recoverable_context_error(Cause) :-
    is_dict(Cause),
    get_dict(phase, Cause, context),
    get_dict(kind, Cause, unknown_context_alias),
    get_dict(context, Cause, _).
"""

RECOVERABLE_CONTEXT_NEW = RECOVERABLE_CONTEXT_OLD + """
recoverable_context_error(Cause) :-
    is_dict(Cause),
    get_dict(kind, Cause, unsupported_selector),
    get_dict(context_kind, Cause, _),
    get_dict(selector, Cause, _).
"""

CONTEXT_OBSERVATION_ANCHOR = """context_failure_observation(Cause, Resolved, Contexts, Event, Result) :-
    Call = Resolved.call,
    get_dict(context, Cause, RequestedContext),
"""

UNSUPPORTED_SELECTOR_OBSERVATION = """context_failure_observation(Cause, Resolved, _Contexts, Event, Result) :-
    get_dict(kind, Cause, unsupported_selector),
    !,
    Call = Resolved.call,
    get_dict(message, Cause, Message),
    get_dict(context_kind, Cause, ContextKind),
    get_dict(selector, Cause, Selector),
    term_string(Selector, SelectorText, [quoted(true)]),
    Value = _{error:unsupported_selector,
              message:Message,
              context_kind:ContextKind,
              selector:SelectorText},
    Trace = context_failure_trace{phase:context,
                                  kind:unsupported_selector,
                                  context_kind:ContextKind,
                                  selector:SelectorText},
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
                         kind:unsupported_selector,
                         result:Result,
                         trace:Trace}.

"""


def patch_selector_recovery(root: Path) -> None:
    direct = root / "prolog/rlm_direct.pl"
    text = direct.read_text(encoding="utf-8")
    text = base.replace_exact(
        text,
        RECOVERABLE_CONTEXT_OLD,
        RECOVERABLE_CONTEXT_NEW,
        "rlm_direct.pl recover unsupported context selectors",
    )
    text = base.replace_exact(
        text,
        CONTEXT_OBSERVATION_ANCHOR,
        UNSUPPORTED_SELECTOR_OBSERVATION + CONTEXT_OBSERVATION_ANCHOR,
        "rlm_direct.pl unsupported selector repair observation",
    )
    if not text.endswith("\n"):
        raise RuntimeError(f"{direct}: patched text unexpectedly lacks final newline")
    direct.write_text(text, encoding="utf-8")
    print(f"patched {direct.relative_to(root)} unsupported-selector recovery")


def patch_tree(root: Path) -> None:
    base.patch_tree(root)
    patch_selector_recovery(root)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply pinned Prolog-RLM hotfixes required by Auto-Dig CI"
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

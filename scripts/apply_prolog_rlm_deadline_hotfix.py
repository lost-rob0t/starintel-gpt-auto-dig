#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


DIRECT_RUNTIME_OLD = """    zero_usage(Usage),
    State = direct_state{messages:Messages,
                         contexts:[direct_context{id:\"input\",
                                                  handle:ContextRef.handle,
                                                  source:input,
                                                  value:none}],
                         seen_call_ids:[],
                         responses:[],
                         iterations:0,
                         model_calls:0,
                         context_calls:0,
                         tool_calls:0,
                         output_bytes:0,
                         usage:Usage,
                         trajectory:[]},
    Runtime = direct_runtime{provider:Provider,
                             provider_name:ProviderName,
                             format:Format,
                             bindings:Bindings,
                             schemas:WireSchemas,
                             capabilities:Capabilities,
                             registry:Registry,
                             options:Options,
                             budget:Budget,
                             token:Token},
    direct_loop(Runtime, State, Outcome).
"""

DIRECT_RUNTIME_NEW = """    zero_usage(Usage),
    get_time(StartedAt),
    State = direct_state{messages:Messages,
                         contexts:[direct_context{id:\"input\",
                                                  handle:ContextRef.handle,
                                                  source:input,
                                                  value:none}],
                         seen_call_ids:[],
                         responses:[],
                         iterations:0,
                         model_calls:0,
                         context_calls:0,
                         tool_calls:0,
                         output_bytes:0,
                         usage:Usage,
                         trajectory:[]},
    Runtime = direct_runtime{provider:Provider,
                             provider_name:ProviderName,
                             format:Format,
                             bindings:Bindings,
                             schemas:WireSchemas,
                             capabilities:Capabilities,
                             registry:Registry,
                             options:Options,
                             budget:Budget,
                             started_at:StartedAt,
                             token:Token},
    direct_loop(Runtime, State, Outcome).
"""

DIRECT_CUTOFF_OLD = """direct_request_options(Runtime, State, StepOptions, RequestOptions) :-
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

DIRECT_CUTOFF_NEW = """direct_request_options(Runtime, State, StepOptions, RequestOptions) :-
    (   native_tool_synthesis_phase(Runtime, State)
    ->  RequestOptions = StepOptions
    ;   request_options(Runtime.schemas, StepOptions, RequestOptions)
    ).

native_tool_synthesis_phase(Runtime, State) :-
    native_tool_cutoff(Runtime.options, Cutoff),
    Cutoff \\== disabled,
    State.model_calls >= Cutoff,
    !.
native_tool_synthesis_phase(Runtime, _) :-
    native_tool_synthesis_reserve(Runtime.options, Reserve),
    Reserve \\== disabled,
    native_tool_provider_headroom(Runtime.options, Reserve, ProviderHeadroom),
    get_time(Now),
    Elapsed is max(0.0, Now-Runtime.started_at),
    Remaining is Runtime.budget.time_limit-Elapsed,
    AcquisitionCutoff is Reserve+ProviderHeadroom,
    Remaining =< AcquisitionCutoff.

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

native_tool_synthesis_reserve(Options, Reserve) :-
    option(native_tool_synthesis_reserve_seconds, Options, none, Requested),
    (   Requested == none
    ->  Reserve = disabled
    ;   number(Requested),
        Requested >= 0
    ->  Reserve = Requested
    ;   throw(direct_fault(direct_error{
                             phase:provider,
                             kind:invalid_native_tool_synthesis_reserve,
                             option:native_tool_synthesis_reserve_seconds,
                             value:Requested,
                             message:\"native synthesis reserve must be a nonnegative number\"}))
    ).

native_tool_provider_headroom(Options, Reserve, Headroom) :-
    DefaultHeadroom is Reserve*5.0/3.0,
    option(native_tool_provider_headroom_seconds, Options, DefaultHeadroom, Requested),
    (   number(Requested),
        Requested >= 0
    ->  Headroom = Requested
    ;   throw(direct_fault(direct_error{
                             phase:provider,
                             kind:invalid_native_tool_provider_headroom,
                             option:native_tool_provider_headroom_seconds,
                             value:Requested,
                             message:\"native provider headroom must be a nonnegative number\"}))
    ).
"""

DIRECT_SYSTEM_OLD = """direct_system_message(Options, System) :-
    direct_capabilities(Options, Capabilities),
    (   member(context(_), Capabilities)
    ->  System = \"You are a bounded direct agent. Answer normally. Use provider-native tools only when they add needed information or execution. Never emit a typed plan. Context content is opaque; its initial alias is input. Registered tool results are retained as opaque result contexts and must be inspected with context tools. Return final answer text after all needed observations.\"
    ;   System = \"You are a bounded direct agent. Answer normally. Use provider-native tools only when they add needed information or execution. Never emit a typed plan. No opaque context operations are granted in this session: do not attempt context reads. Return final answer text after all needed observations.\"
    ).
"""

DIRECT_SYSTEM_NEW = """direct_system_message(Options, System) :-
    direct_capabilities(Options, Capabilities),
    Synthesis = \" Native tool schemas may be withdrawn on a later turn to reserve deadline headroom for synthesis. When tool schemas are absent, evidence acquisition is closed: do not describe, request, or defer to any further tool/context operation; produce the final answer now from the observations already present.\",
    (   member(context(_), Capabilities)
    ->  string_concat(\"You are a bounded direct agent. Answer normally. Use provider-native tools only when they add needed information or execution. Never emit a typed plan. Context content is opaque; its initial alias is input. Registered tool results are retained as opaque result contexts and must be inspected with context tools. Return final answer text after all needed observations.\", Synthesis, System)
    ;   string_concat(\"You are a bounded direct agent. Answer normally. Use provider-native tools only when they add needed information or execution. Never emit a typed plan. No opaque context operations are granted in this session: do not attempt context reads. Return final answer text after all needed observations.\", Synthesis, System)
    ).
"""


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_tree(root: Path) -> None:
    direct = root / "prolog/rlm_direct.pl"
    text = direct.read_text(encoding="utf-8")
    text = replace_exact(text, DIRECT_RUNTIME_OLD, DIRECT_RUNTIME_NEW,
                         "rlm_direct.pl runtime start timestamp")
    text = replace_exact(text, DIRECT_CUTOFF_OLD, DIRECT_CUTOFF_NEW,
                         "rlm_direct.pl wall-clock synthesis reserve")
    text = replace_exact(text, DIRECT_SYSTEM_OLD, DIRECT_SYSTEM_NEW,
                         "rlm_direct.pl explicit synthesis transition")
    if not text.endswith("\n"):
        raise RuntimeError(f"{direct}: patched text unexpectedly lacks final newline")
    direct.write_text(text, encoding="utf-8")
    print(f"patched {direct.relative_to(root)} deadline synthesis reserve")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply wall-clock synthesis-reserve hotfix to pinned Prolog-RLM"
    )
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")
    patch_tree(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

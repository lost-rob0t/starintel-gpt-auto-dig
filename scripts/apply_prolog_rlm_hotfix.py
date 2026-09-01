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

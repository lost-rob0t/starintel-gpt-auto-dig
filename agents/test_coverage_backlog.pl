:- begin_tests(coverage_backlog).

:- use_module('./coverage_backlog').

base_state(_{schema:"auto-dig-prolog-state.v1",
             last_issue:null,
             last_priority:null,
             last_branch:null,
             last_run_id:null,
             last_success_at:null}).

ledger(State, Ledger) :-
    ensure_ledger(State, "anarchist-violence", "us-geographic-npa", "NANPA",
                  "B", 3, 1, State1, Key),
    Ledger = State1.coverage.get(Key).

test(shard_uses_only_authoritative_items) :-
    shard_items([202,203,204,205,208,999], 3, 1, Items),
    assertion(Items == [202,205,208]).

test(completed_items_do_not_repeat) :-
    base_state(State), ledger(State, L0),
    claim_batch(L0, [202,205,208,211], 2, L1-B1),
    assertion(B1 == [202,205]),
    complete_batch(L1, B1, L2),
    claim_batch(L2, [202,205,208,211], 3, _L3-B2),
    assertion(B2 == [208]).

test(failed_items_become_retryable) :-
    base_state(State), ledger(State, L0),
    claim_batch(L0, [202,205], 1, L1-B1),
    fail_batch(L1, B1, L2),
    assertion(L2.failed_retryable == [202]),
    claim_batch(L2, [202,205], 1, L3-B2),
    assertion(B2 == [202]),
    assertion(L3.failed_retryable == []).

test(new_authoritative_item_appears_later) :-
    base_state(State), ledger(State, L0),
    claim_batch(L0, [202], 1, L1-B1),
    complete_batch(L1, B1, L2),
    claim_batch(L2, [202,205], 2, _L3-B2),
    assertion(B2 == [205]).

test(identity_drift_fails,
     [throws(error(permission_error(change, coverage_ledger_identity, authority), _))]) :-
    base_state(State),
    ensure_ledger(State, "anarchist-violence", "us-geographic-npa", "NANPA",
                  "B", 3, 1, State1, _),
    ensure_ledger(State1, "anarchist-violence", "us-geographic-npa", "FCC",
                  "B", 3, 1, _, _).

:- end_tests(coverage_backlog).

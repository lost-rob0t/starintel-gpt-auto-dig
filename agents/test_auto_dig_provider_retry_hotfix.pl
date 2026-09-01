:- begin_tests(auto_dig_provider_retry_hotfix).

:- use_module(library(rlm_completion), [call_model/4]).

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

:- end_tests(auto_dig_provider_retry_hotfix).

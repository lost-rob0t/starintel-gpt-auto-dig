:- begin_tests(auto_dig_model_router).

:- use_module('./auto_dig_model_router').

test(default_research_uses_luna_max) :-
    select_model(_{task:"research"}, Route),
    assertion(Route.model == "openai/gpt-5.6-luna"),
    assertion(Route.reasoning.effort == max),
    assertion(Route.tier == "luna").

test(bulk_extraction_uses_luna_high) :-
    select_model(_{task:"extraction"}, Route),
    assertion(Route.model == "openai/gpt-5.6-luna"),
    assertion(Route.reasoning.effort == high).

test(high_priority_is_not_implicitly_flagship) :-
    select_model(_{task:"research", risk:"high"}, Route),
    assertion(Route.model == "openai/gpt-5.6-luna"),
    assertion(Route.reasoning.effort == max).

test(one_failed_verification_escalates_to_terra) :-
    select_model(_{task:"research", failed_verifications:1}, Route),
    assertion(Route.model == "openai/gpt-5.6-terra"),
    assertion(Route.reasoning.effort == max).

test(two_failed_verifications_escalate_to_sol) :-
    select_model(_{task:"research", failed_verifications:2}, Route),
    assertion(Route.model == "openai/gpt-5.6-sol"),
    assertion(Route.reasoning.effort == max).

test(threat_model_uses_sol_max) :-
    select_model(_{task:"threat_model"}, Route),
    assertion(Route.model == "openai/gpt-5.6-sol"),
    assertion(Route.reasoning.effort == max).

test(irreversible_work_uses_sol_max) :-
    select_model(_{task:"research", irreversible:true}, Route),
    assertion(Route.model == "openai/gpt-5.6-sol").

test(luna_max_has_terra_then_sol_fallback) :-
    select_model(_{task:"verification"}, Route),
    Route.fallback = [Terra, Sol],
    assertion(Terra.model == "openai/gpt-5.6-terra"),
    assertion(Sol.model == "openai/gpt-5.6-sol").

:- end_tests(auto_dig_model_router).

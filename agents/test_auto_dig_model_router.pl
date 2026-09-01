:- begin_tests(auto_dig_model_router).

:- use_module('./auto_dig_model_router').

test(default_research_uses_glm_53_flash) :-
    select_model(_{task:"research"}, Route),
    assertion(Route.model == "z-ai/glm-5.3-flash"),
    assertion(Route.reasoning.effort == none),
    assertion(Route.tier == "glm-flash"),
    assertion(Route.fallback == []).

test(bulk_extraction_stays_on_glm_53_flash) :-
    select_model(_{task:"extraction"}, Route),
    assertion(Route.model == "z-ai/glm-5.3-flash"),
    assertion(Route.reasoning.effort == none).

test(high_priority_stays_on_glm_53_flash) :-
    select_model(_{task:"research", risk:"high"}, Route),
    assertion(Route.model == "z-ai/glm-5.3-flash"),
    assertion(Route.reasoning.effort == none).

test(verification_failures_do_not_escape_dogfood_pin) :-
    select_model(_{task:"research", failed_verifications:2}, Route),
    assertion(Route.model == "z-ai/glm-5.3-flash"),
    assertion(Route.fallback == []).

test(high_judgment_task_does_not_escape_dogfood_pin) :-
    select_model(_{task:"threat_model"}, Route),
    assertion(Route.model == "z-ai/glm-5.3-flash").

test(irreversible_work_does_not_escape_dogfood_pin) :-
    select_model(_{task:"research", irreversible:true}, Route),
    assertion(Route.model == "z-ai/glm-5.3-flash").

:- end_tests(auto_dig_model_router).

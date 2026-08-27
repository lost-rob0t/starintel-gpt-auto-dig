:- begin_tests(auto_dig_rlm_runner).

:- use_module('./auto_dig_rlm_runner').
:- use_module(library(rlm_skill)).

test(native_planner_features_are_explicitly_enabled) :-
    auto_dig_runtime_options('openai/gpt-5.6-luna', max, Options),
    assertion(memberchk(skill_mode(on), Options)),
    assertion(memberchk(skill_catalog(default), Options)),
    assertion(memberchk(prompt_compile_mode(compiled), Options)),
    assertion(memberchk(planner_attempts(3), Options)),
    assertion(\+ memberchk(planner_handler(_), Options)).

test(research_context_and_recursion_are_available) :-
    auto_dig_runtime_options('openai/gpt-5.6-luna', max, Options),
    memberchk(capabilities(Capabilities), Options),
    memberchk(child_capabilities(ChildCapabilities), Options),
    assertion(memberchk(rlm, Capabilities)),
    assertion(memberchk(context(slice), Capabilities)),
    assertion(memberchk(context(search), Capabilities)),
    assertion(memberchk(context(peek), Capabilities)),
    assertion(memberchk(model(openrouter), Capabilities)),
    assertion(ChildCapabilities == Capabilities),
    memberchk(budget(Budget), Options),
    assertion(Budget.max_recursion_depth =:= 2),
    assertion(Budget.max_model_calls =:= 6),
    assertion(Budget.max_context_ops =:= 12).

test(default_operating_skill_catalog_is_present) :-
    skill_default_catalog(ok(Catalog)),
    skill_catalog_skills(Catalog, Skills),
    maplist(skill_name, Skills, Names),
    assertion(memberchk('rlm-operate', Names)),
    assertion(memberchk('rlm-recurse', Names)),
    assertion(memberchk('rlm-facts', Names)),
    assertion(memberchk('rlm-constraints', Names)).

skill_name(Skill, Name) :-
    Name = Skill.name.

:- end_tests(auto_dig_rlm_runner).

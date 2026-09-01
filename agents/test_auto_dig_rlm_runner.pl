:- begin_tests(auto_dig_rlm_runner).

:- use_module('./auto_dig_rlm_runner').
:- use_module('./auto_dig_mcp_tools').
:- use_module(library(rlm_skill)).

% Guarded live verification marker for the synthesis-reservation dogfood slice.

test(native_direct_mode_features_are_explicitly_enabled) :-
    auto_dig_runtime_options('openai/gpt-5.6-luna', max, Options),
    assertion(memberchk(skill_mode(on), Options)),
    assertion(memberchk(skill_catalog(default), Options)),
    assertion(memberchk(prompt_compile_mode(all_tools), Options)),
    assertion(memberchk(planner_max_tokens(8192), Options)),
    assertion(\+ memberchk(planner_attempts(_), Options)),
    assertion(\+ memberchk(planner_handler(_), Options)).

test(context_budget_is_thirty_percent_of_model_limit) :-
    auto_dig_context_budget('openai/gpt-5.6-luna', Window, Budget),
    assertion(Window =:= 1050000),
    assertion(Budget =:= 315000),
    auto_dig_context_budget('openai/gpt-5.6-terra', TerraWindow, TerraBudget),
    assertion(TerraWindow =:= 1050000),
    assertion(TerraBudget =:= 315000),
    auto_dig_context_budget('openai/gpt-5.6-sol', SolWindow, SolBudget),
    assertion(SolWindow =:= 1050000),
    assertion(Budget =:= 315000),
    assertion(SolBudget =:= 315000).

test(unknown_model_requires_explicit_context_limit,
     [throws(error(domain_error(auto_dig_model_context_window,
                                'example/unknown-model'), _))]) :-
    auto_dig_context_budget('example/unknown-model', _, _).

test(research_context_and_direct_tool_budget_are_available) :-
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
    assertion(Budget.max_iterations =:= 24),
    assertion(Budget.max_recursion_depth =:= 2),
    assertion(Budget.max_model_calls =:= 16),
    assertion(Budget.max_tool_calls =:= 24),
    assertion(Budget.max_context_ops =:= 32),
    assertion(Budget.max_total_tokens =:= 315000),
    assertion(Budget.max_cost_usd =:= 1.50),
    assertion(Budget.max_output_bytes =:= 262144),
    assertion(Budget.time_limit =:= 300.0).

test(raw_normalization_failure_is_the_only_harness_retry_trigger) :-
    Retryable = error(_{ phase:native_call,
                         kind:malformed_arguments,
                         cause:_{ phase:normalize,
                                  kind:malformed_arguments,
                                  message:"native tool arguments must be one ground JSON object"
                                }
                       }),
    assertion(raw_argument_retryable(Retryable)),
    SchemaFailure = error(_{ phase:native_call,
                              kind:malformed_arguments,
                              cause:_{ phase:schema,
                                       kind:malformed_arguments
                                     }
                            }),
    assertion(\+ raw_argument_retryable(SchemaFailure)),
    ProviderFailure = error(_{ phase:provider,
                                kind:provider_failed,
                                cause:_{ phase:normalize,
                                         kind:malformed_arguments
                                       }
                              }),
    assertion(\+ raw_argument_retryable(ProviderFailure)).

test(repair_retry_is_smaller_and_keeps_total_cost_cap_bounded) :-
    auto_dig_runtime_options('openai/gpt-5.6-luna', max, Options),
    auto_dig_retry_options(Options, RetryOptions),
    memberchk(budget(MainBudget), Options),
    memberchk(budget(RetryBudget), RetryOptions),
    assertion(MainBudget.max_cost_usd =:= 1.50),
    assertion(RetryBudget.max_cost_usd =:= 0.50),
    TotalCostCap is MainBudget.max_cost_usd + RetryBudget.max_cost_usd,
    assertion(TotalCostCap =:= 2.00),
    assertion(RetryBudget.max_iterations =:= 12),
    assertion(RetryBudget.max_model_calls =:= 6),
    assertion(RetryBudget.max_tool_calls =:= 12),
    assertion(RetryBudget.max_context_ops =:= 16),
    assertion(RetryBudget.max_total_tokens =:= 78750),
    assertion(RetryBudget.time_limit =:= 180.0).

test(mcp_registry_and_complete_read_tool_inventory_are_projected) :-
    auto_dig_mcp_read_capabilities(McpCapabilities),
    length(McpCapabilities, CapabilityCount),
    assertion(CapabilityCount =:= 14),
    auto_dig_runtime_options('openai/gpt-5.6-luna',
                             max,
                             fake_registry,
                             auto_dig_rlm_research,
                             McpCapabilities,
                             Options),
    assertion(memberchk(tool_registry(fake_registry), Options)),
    assertion(memberchk(authority_context(auto_dig_rlm_research), Options)),
    memberchk(capabilities(Capabilities), Options),
    memberchk(child_capabilities(ChildCapabilities), Options),
    forall(member(Capability, McpCapabilities),
           assertion(memberchk(Capability, Capabilities))),
    assertion(ChildCapabilities == Capabilities),
    assertion(memberchk(tool('mcp.brave.brave_web_search'), Capabilities)),
    assertion(memberchk(tool('mcp.brave.brave_local_search'), Capabilities)),
    assertion(memberchk(tool('mcp.brave.brave_video_search'), Capabilities)),
    assertion(memberchk(tool('mcp.brave.brave_image_search'), Capabilities)),
    assertion(memberchk(tool('mcp.brave.brave_news_search'), Capabilities)),
    assertion(memberchk(tool('mcp.brave.brave_summarizer'), Capabilities)),
    assertion(memberchk(tool('mcp.brave.brave_llm_context'), Capabilities)),
    assertion(memberchk(tool('mcp.brave.brave_place_search'), Capabilities)),
    assertion(memberchk(tool('mcp.fetch.fetch_html'), Capabilities)),
    assertion(memberchk(tool('mcp.fetch.fetch_markdown'), Capabilities)),
    assertion(memberchk(tool('mcp.fetch.fetch_readable'), Capabilities)),
    assertion(memberchk(tool('mcp.fetch.fetch_txt'), Capabilities)),
    assertion(memberchk(tool('mcp.fetch.fetch_json'), Capabilities)),
    assertion(memberchk(tool('mcp.fetch.fetch_youtube_transcript'), Capabilities)).

test(research_prompt_requires_direct_live_tool_use_and_strict_native_json) :-
    auto_dig_query(Query),
    assertion(sub_string(Query, _, _, _, "native direct mode")),
    assertion(sub_string(Query, _, _, _, "do not emit a typed plan")),
    assertion(sub_string(Query, _, _, _, "Brave")),
    assertion(sub_string(Query, _, _, _, "Fetch")),
    assertion(sub_string(Query, _, _, _, "strict JSON objects")),
    assertion(sub_string(Query, _, _, _, "every object key appearing exactly once")),
    assertion(sub_string(Query, _, _, _, "no more than four parallel native tool calls")),
    assertion(sub_string(Query, _, _, _, "additional tool or datasource capability")),
    assertion(\+ sub_string(Query, _, _, _, "suitable for the tool-enabled Auto-Dig stage")).

test(research_prompt_reserves_final_four_responses_for_synthesis) :-
    auto_dig_query(Query),
    assertion(sub_string(Query, _, _, _, "twelfth model response")),
    assertion(sub_string(Query, _, _, _, "final four model responses for synthesis")),
    assertion(sub_string(Query, _, _, _, "do not call Brave, Fetch, or context tools again")),
    assertion(sub_string(Query, _, _, _, "list it as follow-up work")),
    assertion(\+ sub_string(Query, _, _, _, "Keep calling tools while useful evidence remains within budget")).

test(repair_prompt_names_duplicate_key_failure_and_is_single_attempt) :-
    auto_dig_query(Query),
    auto_dig_repair_query(Query, RepairQuery),
    assertion(sub_string(RepairQuery, _, _, _, "previous bounded direct attempt")),
    assertion(sub_string(RepairQuery, _, _, _, "MUST appear exactly once")),
    assertion(sub_string(RepairQuery, _, _, _, "search_lang or spellcheck")),
    assertion(sub_string(RepairQuery, _, _, _, "one harness-level repair attempt")),
    assertion(sub_string(RepairQuery, _, _, _, "smaller retry budget")).

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

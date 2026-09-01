:- begin_tests(auto_dig_rlm_runner).

:- use_module('./auto_dig_rlm_runner').
:- use_module('./auto_dig_mcp_tools').
:- use_module(library(rlm_skill)).

% Guarded live verification marker for the real-output dogfood slice.

test(native_direct_mode_features_are_explicitly_enabled) :-
    auto_dig_runtime_options('z-ai/glm-5.3-flash', max, Options),
    assertion(memberchk(skill_mode(on), Options)),
    assertion(memberchk(skill_catalog(default), Options)),
    assertion(memberchk(prompt_compile_mode(all_tools), Options)),
    assertion(memberchk(planner_max_tokens(8192), Options)),
    assertion(memberchk(native_tool_cutoff_model_calls(12), Options)),
    assertion(memberchk(native_tool_synthesis_reserve_seconds(90.0), Options)),
    assertion(\+ memberchk(planner_attempts(_), Options)),
    assertion(\+ memberchk(planner_handler(_), Options)).

test(context_budget_is_thirty_percent_of_model_limit) :-
    auto_dig_context_budget('z-ai/glm-5.3-flash', FlashWindow, FlashBudget),
    assertion(FlashWindow =:= 1310720),
    assertion(FlashBudget =:= 393216),
    auto_dig_context_budget('openai/gpt-5.6-luna', Window, Budget),
    assertion(Window =:= 1050000),
    assertion(Budget =:= 315000),
    auto_dig_context_budget('openai/gpt-5.6-terra', TerraWindow, TerraBudget),
    assertion(TerraWindow =:= 1050000),
    assertion(TerraBudget =:= 315000),
    auto_dig_context_budget('openai/gpt-5.6-sol', SolWindow, SolBudget),
    assertion(SolWindow =:= 1050000),
    assertion(SolBudget =:= 315000).

test(unknown_model_requires_explicit_context_limit,
     [throws(error(domain_error(auto_dig_model_context_window,
                                'example/unknown-model'), _))]) :-
    auto_dig_context_budget('example/unknown-model', _, _).

test(research_context_and_direct_tool_budget_are_available) :-
    auto_dig_runtime_options('z-ai/glm-5.3-flash', max, Options),
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
    assertion(Budget.max_total_tokens =:= 393216),
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
    auto_dig_runtime_options('z-ai/glm-5.3-flash', max, Options),
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
    assertion(RetryBudget.time_limit =:= 180.0),
    assertion(memberchk(native_tool_synthesis_reserve_seconds(90.0), RetryOptions)).

test(mcp_registry_and_complete_read_tool_inventory_are_projected) :-
    auto_dig_mcp_read_capabilities(McpCapabilities),
    length(McpCapabilities, CapabilityCount),
    assertion(CapabilityCount =:= 14),
    auto_dig_runtime_options('z-ai/glm-5.3-flash',
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
    assertion(sub_string(Query, _, _, _, "wall-clock synthesis reserve")),
    assertion(sub_string(Query, _, _, _, "if tools are no longer available")),
    assertion(sub_string(Query, _, _, _, "do not call Brave, Fetch, context tools, or write tool-call syntax as text")),
    assertion(sub_string(Query, _, _, _, "list it as follow-up work")),
    assertion(\+ sub_string(Query, _, _, _, "Keep calling tools while useful evidence remains within budget")).

test(research_prompt_requires_human_visible_report_contract) :-
    auto_dig_query(Query),
    assertion(sub_string(Query, _, _, _, "# Auto-Dig Research Output")),
    assertion(sub_string(Query, _, _, _, "## Findings")),
    assertion(sub_string(Query, _, _, _, "## Evidence")),
    assertion(sub_string(Query, _, _, _, "## Unresolved / Follow-up")),
    assertion(sub_string(Query, _, _, _, "not pending tool invocations")),
    assertion(sub_string(Query, _, _, _, "http:// or https:// source URL")).

test(valid_report_contract_accepts_substantive_markdown) :-
    Report = "# Auto-Dig Research Output\n\n## Findings\nThe bounded live actor found a concrete, auditable fact and explains why it matters. A second sentence records the scope and avoids claiming more than the evidence supports.\n\n## Evidence\nPrimary source: https://example.org/primary-record . The source directly supports the stated finding and remains identifiable for later verification.\n\n## Unresolved / Follow-up\nA remaining claim still needs an additional independent source before publication.",
    assertion(valid_research_report(Report)).

test(metadata_only_completion_is_not_a_report) :-
    assertion(\+ valid_research_report("run complete")).

test(tool_transcript_false_success_regression_is_rejected) :-
    Transcript = "# Auto-Dig Research Output\n\n## Findings\n to=multi_tool_use.parallel code {\"tool_uses\":[{\"recipient_name\":\"functions.context_slice\"}]} to=functions.context_slice code. This is deliberately padded to exceed the minimum report length while reproducing the exact class of false-success output seen in live run 33502262680.\n\n## Evidence\nhttps://example.org/placeholder\n\n## Unresolved / Follow-up\nThe model never synthesized a real report.",
    assertion(\+ valid_research_report(Transcript)).

test(final_report_content_extracts_assistant_content) :-
    Outcome = ok(_{response:_{assistant:_{content:"hello"}}}),
    final_report_content(Outcome, Content),
    assertion(Content == "hello").

test(validated_report_is_emitted_verbatim_for_humans) :-
    Report = "# Auto-Dig Research Output\n\n## Findings\nThis is the actual human-facing actor answer.\n\n## Evidence\nhttps://example.org/source\n\n## Unresolved / Follow-up\nNothing else is hidden in a JSON wrapper.",
    with_output_to(string(Output), emit_human_report(Report)),
    assertion(sub_string(Output, _, _, _, Report)),
    assertion(\+ sub_string(Output, _, _, _, "rlm-result.json")),
    assertion(\+ sub_string(Output, _, _, _, "\"schema\"")),
    assertion(\+ sub_string(Output, _, _, _, "run complete")).

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

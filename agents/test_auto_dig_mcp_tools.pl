:- begin_tests(auto_dig_mcp_tools).

:- use_module('./auto_dig_mcp_tools').
:- use_module(library(rlm_mcp_server)).

test(server_set_is_fixed) :-
    auto_dig_mcp_servers(Servers),
    assertion(Servers == [brave, fetch, starintel]).

test(brave_definition_is_inert_fixed_and_secret_by_reference) :-
    mcp_server_definition(brave, ok(Spec)),
    assertion(Spec.transport == stdio(profile(auto_dig_brave_npx))),
    assertion(Spec.install == none),
    assertion(Spec.environment ==
              [env('BRAVE_API_KEY', env_ref('BRAVE_API_KEY'))]),
    assertion(Spec.working_directory == inherit),
    assertion(Spec.version == '2.1.0'),
    assertion(Spec.capabilities == [tools]),
    term_string(Spec, Text, [quoted(true), numbervars(true)]),
    assertion(\+ sub_string(Text, _, _, _, "{env:")),
    assertion(\+ sub_string(Text, _, _, _, "sk-")) .

test(fetch_definition_is_inert_fixed_and_configured_by_reference) :-
    mcp_server_definition(fetch, ok(Spec)),
    assertion(Spec.transport == stdio(profile(auto_dig_fetch_npx))),
    assertion(Spec.install == none),
    assertion(Spec.environment ==
              [env('DEFAULT_LIMIT',
                   config_ref(auto_dig_fetch_default_limit))]),
    assertion(Spec.working_directory == inherit),
    assertion(Spec.version == '1.1.2'),
    assertion(Spec.capabilities == [tools]).

test(starintel_definition_is_inert_fixed_and_configured_by_reference) :-
    setup_call_cleanup(
        unsetenv('STARINTEL_TOKEN'),
        ( mcp_server_definition(starintel, ok(Spec)),
          assertion(Spec.transport == stdio(profile(auto_dig_starintel_python))),
          assertion(Spec.install == none),
          assertion(Spec.environment ==
                    [env('STARINTEL_SERVER_URL',
                         config_ref(auto_dig_starintel_server_url))]),
          assertion(Spec.working_directory == inherit),
          assertion(Spec.version == '0.9.0'),
          assertion(Spec.capabilities == [tools]),
          term_string(Spec, Text, [quoted(true), numbervars(true)]),
          assertion(\+ sub_string(Text, _, _, _, "{env:")),
          assertion(\+ sub_string(Text, _, _, _, "sk-"))
        ),
        true).

test(starintel_token_binds_by_env_ref_only_when_the_host_supplies_it) :-
    setup_call_cleanup(
        setenv('STARINTEL_TOKEN', 'test-starintel-token'),
        ( mcp_server_definition(starintel, ok(Spec)),
          assertion(Spec.environment ==
                    [env('STARINTEL_SERVER_URL',
                         config_ref(auto_dig_starintel_server_url)),
                     env('STARINTEL_TOKEN', env_ref('STARINTEL_TOKEN'))])
        ),
        unsetenv('STARINTEL_TOKEN')).

test(starintel_server_url_config_defaults_to_trusted_loopback) :-
    setup_call_cleanup(
        unsetenv('STARINTEL_SERVER_URL'),
        ( rlm_mcp_policy:mcp_config_value(auto_dig_starintel_server_url, Value),
          assertion(Value == "http://127.0.0.1:5000")
        ),
        true).

test(starintel_server_url_config_prefers_the_host_environment) :-
    setup_call_cleanup(
        setenv('STARINTEL_SERVER_URL', 'https://server.starintel.actor'),
        ( rlm_mcp_policy:mcp_config_value(auto_dig_starintel_server_url, Value),
          assertion(Value == "https://server.starintel.actor")
        ),
        unsetenv('STARINTEL_SERVER_URL')).

test(starintel_profile_pins_the_in_repo_server_script) :-
    once(rlm_mcp_policy:mcp_stdio_profile(auto_dig_starintel_python, Spec)),
    assertion(Spec.executable == path(python3)),
    get_dict(argv_prefix, Spec, [Script]),
    assertion(Spec.package_format == plain),
    assertion(Spec.timeout =:= 60.0),
    assertion(Spec.max_output_bytes == 262144),
    assertion(exists_file(Script)).

test(remote_imports_are_explicitly_read_only) :-
    auto_dig_mcp_import_options(brave, BraveOptions),
    auto_dig_mcp_import_options(fetch, FetchOptions),
    auto_dig_mcp_import_options(starintel, StarIntelOptions),
    assertion(memberchk(effect(read), BraveOptions)),
    assertion(memberchk(effect(read), FetchOptions)),
    assertion(memberchk(effect(read), StarIntelOptions)),
    assertion(\+ memberchk(effect(write), BraveOptions)),
    assertion(\+ memberchk(effect(write), FetchOptions)),
    assertion(\+ memberchk(effect(write), StarIntelOptions)).

test(starintel_allow_list_admits_exactly_the_corpus_read_surface) :-
    findall(Remote, auto_dig_mcp_read_tool(starintel, Remote), Remotes),
    assertion(Remotes == [starintel_search,
                          starintel_get_document,
                          starintel_health]),
    assertion(\+ auto_dig_mcp_read_tool(starintel, starintel_write_document)),
    assertion(\+ auto_dig_mcp_read_tool(starintel, starintel_draft_document)),
    assertion(\+ auto_dig_mcp_read_tool(starintel, github_issue_reply)).

test(invocation_capabilities_are_exact_namespaced_allow_list) :-
    auto_dig_mcp_read_capabilities(Capabilities),
    assertion(Capabilities ==
              [ tool('mcp.brave.brave_image_search'),
                tool('mcp.brave.brave_llm_context'),
                tool('mcp.brave.brave_local_search'),
                tool('mcp.brave.brave_news_search'),
                tool('mcp.brave.brave_place_search'),
                tool('mcp.brave.brave_summarizer'),
                tool('mcp.brave.brave_video_search'),
                tool('mcp.brave.brave_web_search'),
                tool('mcp.fetch.fetch_html'),
                tool('mcp.fetch.fetch_json'),
                tool('mcp.fetch.fetch_markdown'),
                tool('mcp.fetch.fetch_readable'),
                tool('mcp.fetch.fetch_txt'),
                tool('mcp.fetch.fetch_youtube_transcript'),
                tool('mcp.starintel.starintel_get_document'),
                tool('mcp.starintel.starintel_health'),
                tool('mcp.starintel.starintel_search')
              ]).

test(full_brave_read_inventory_is_granted_by_default) :-
    auto_dig_mcp_read_capabilities(Capabilities),
    assertion(memberchk(tool('mcp.brave.brave_image_search'), Capabilities)),
    assertion(memberchk(tool('mcp.brave.brave_local_search'), Capabilities)),
    assertion(memberchk(tool('mcp.brave.brave_llm_context'), Capabilities)),
    assertion(memberchk(tool('mcp.brave.brave_place_search'), Capabilities)),
    assertion(memberchk(tool('mcp.brave.brave_summarizer'), Capabilities)).

:- end_tests(auto_dig_mcp_tools).

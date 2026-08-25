:- begin_tests(auto_dig_mcp_tools).

:- use_module('./auto_dig_mcp_tools').
:- use_module(library(rlm_mcp_server)).

test(server_set_is_fixed) :-
    auto_dig_mcp_servers(Servers),
    assertion(Servers == [brave, fetch]).

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

test(remote_imports_are_explicitly_read_only) :-
    auto_dig_mcp_import_options(brave, BraveOptions),
    auto_dig_mcp_import_options(fetch, FetchOptions),
    assertion(memberchk(effect(read), BraveOptions)),
    assertion(memberchk(effect(read), FetchOptions)),
    assertion(\+ memberchk(effect(write), BraveOptions)),
    assertion(\+ memberchk(effect(write), FetchOptions)).

test(invocation_capabilities_are_exact_namespaced_allow_list) :-
    auto_dig_mcp_read_capabilities(Capabilities),
    assertion(Capabilities ==
              [ tool('mcp.brave.brave_news_search'),
                tool('mcp.brave.brave_video_search'),
                tool('mcp.brave.brave_web_search'),
                tool('mcp.fetch.fetch_json'),
                tool('mcp.fetch.fetch_markdown'),
                tool('mcp.fetch.fetch_readable'),
                tool('mcp.fetch.fetch_txt'),
                tool('mcp.fetch.fetch_youtube_transcript')
              ]).

test(image_and_local_search_are_not_granted_by_default) :-
    auto_dig_mcp_read_capabilities(Capabilities),
    assertion(\+ memberchk(tool('mcp.brave.brave_image_search'), Capabilities)),
    assertion(\+ memberchk(tool('mcp.brave.brave_local_search'), Capabilities)).

:- end_tests(auto_dig_mcp_tools).

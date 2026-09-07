:- module(auto_dig_mcp_tools,
          [ auto_dig_mcp_servers/1,
            auto_dig_mcp_import_options/2,
            auto_dig_mcp_read_capabilities/1,
            auto_dig_mcp_read_capabilities/2,
            auto_dig_mcp_read_tool/2
          ]).

/** <module> Trusted Auto-Dig MCP research configuration

This module is host-owned policy. Loading it is inert: it only contributes
fixed MCP server declarations and fixed process profiles to Prolog-RLM.
Lifecycle, connection, import, capability grant, and invocation remain explicit
operations owned by the supervising actor.

The model never supplies an executable, package, version, environment value, or
side-effect classification. Brave's secret is referenced through env_ref/1 and
is resolved only at the explicit lifecycle boundary. Non-secret process tuning
is likewise represented by a trusted config_ref/1 rather than a raw declaration
value.

The StarIntel corpus server is the in-repo pinned stdio server
`agents/starintel_corpus_mcp_server.py`. It exposes the read-only corpus
surface (starintel_search, starintel_get_document, starintel_health) over the
StarIntel server API, with the on-disk corpus as the offline fallback. The
optional STARINTEL_TOKEN secret binds through env_ref/1 only when the host
environment supplies it; trusted-loopback deployments run without it. The
server base URL resolves through config_ref/1 from STARINTEL_SERVER_URL with
the loopback default, never from model arguments. The canonical StarIntel
write path is deliberately not exposed here.
*/

:- use_module(library(lists)).
:- use_module(library(rlm_mcp_policy), []).
:- use_module(library(rlm_mcp_server), []).

:- multifile rlm_mcp_policy:mcp_stdio_profile/2.
:- multifile rlm_mcp_policy:mcp_config_value/2.
:- multifile rlm_mcp_server:mcp_server/2.

:- multifile auto_dig_mcp_import_options/2.
:- multifile auto_dig_mcp_read_tool/2.

rlm_mcp_policy:mcp_stdio_profile(
    auto_dig_brave_npx,
    mcp_process_profile{
        executable:path(npx),
        argv_prefix:['-y',
                     '@brave/brave-search-mcp-server@2.1.0',
                     '--transport',
                     'stdio'],
        argv_suffix:[],
        package_format:npm,
        cwd_roots:[],
        timeout:60.0,
        max_output_bytes:262144
    }).

rlm_mcp_policy:mcp_stdio_profile(
    auto_dig_fetch_npx,
    mcp_process_profile{
        executable:path(npx),
        argv_prefix:['-y', 'mcp-fetch-server@1.1.2'],
        argv_suffix:[],
        package_format:npm,
        cwd_roots:[],
        timeout:60.0,
        max_output_bytes:262144
    }).

rlm_mcp_policy:mcp_config_value(auto_dig_fetch_default_limit, "50000").

rlm_mcp_policy:mcp_config_value(auto_dig_starintel_server_url, Value) :-
    (   getenv('STARINTEL_SERVER_URL', Raw),
        atom_string(Raw, RawString),
        RawString \== ''
    ->  Value = RawString
    ;   Value = "http://127.0.0.1:5000"
    ).

rlm_mcp_policy:mcp_stdio_profile(
    auto_dig_starintel_python,
    mcp_process_profile{
        executable:path(python3),
        argv_prefix:[ServerScript],
        argv_suffix:[],
        package_format:plain,
        cwd_roots:[],
        timeout:60.0,
        max_output_bytes:262144
    }) :-
    starintel_corpus_server_script(ServerScript).

starintel_corpus_server_script(Script) :-
    source_file(auto_dig_mcp_tools:auto_dig_mcp_read_tool(_, _), Source),
    file_directory_name(Source, AgentsDirectory),
    directory_file_path(AgentsDirectory, 'starintel_corpus_mcp_server.py', Script).

rlm_mcp_server:mcp_server(
    brave,
    mcp_server_spec{
        transport:stdio(profile(auto_dig_brave_npx)),
        install:none,
        environment:[env('BRAVE_API_KEY', env_ref('BRAVE_API_KEY'))],
        working_directory:inherit,
        version:'2.1.0',
        capabilities:[tools],
        options:[timeout(60.0)]
    }).

rlm_mcp_server:mcp_server(
    fetch,
    mcp_server_spec{
        transport:stdio(profile(auto_dig_fetch_npx)),
        install:none,
        environment:[env('DEFAULT_LIMIT',
                         config_ref(auto_dig_fetch_default_limit))],
        working_directory:inherit,
        version:'1.1.2',
        capabilities:[tools],
        options:[timeout(60.0)]
    }).

rlm_mcp_server:mcp_server(
    starintel,
    mcp_server_spec{
        transport:stdio(profile(auto_dig_starintel_python)),
        install:none,
        environment:Environment,
        working_directory:inherit,
        version:'0.9.0',
        capabilities:[tools],
        options:[timeout(60.0)]
    }) :-
    starintel_server_environment(Environment).

/*
 * The optional bearer token binds through env_ref/1 only when the host
 * environment actually supplies a non-empty secret; trusted-loopback
 * deployments run without any token binding. The base URL is always the
 * trusted config_ref/1 above, never a model-supplied argument.
 */
starintel_server_environment(Environment) :-
    (   getenv('STARINTEL_TOKEN', Raw),
        atom_string(Raw, RawString),
        RawString \== ''
    ->  Environment = [env('STARINTEL_SERVER_URL',
                           config_ref(auto_dig_starintel_server_url)),
                       env('STARINTEL_TOKEN', env_ref('STARINTEL_TOKEN'))]
    ;   Environment = [env('STARINTEL_SERVER_URL',
                           config_ref(auto_dig_starintel_server_url))]
    ).

auto_dig_mcp_servers([brave, fetch, starintel]).

auto_dig_mcp_import_options(brave,
                            [ effect(read),
                              time_limit(30.0),
                              max_output_bytes(262144)
                            ]).
auto_dig_mcp_import_options(fetch,
                            [ effect(read),
                              time_limit(30.0),
                              max_output_bytes(262144)
                            ]).
auto_dig_mcp_import_options(starintel,
                            [ effect(read),
                              time_limit(30.0),
                              max_output_bytes(262144)
                            ]).

/*
 * Trusted read-only research allow-list.
 *
 * The pinned Prolog-RLM renders runtime type:any as unconstrained provider
 * JSON Schema, so the complete trusted Brave + Fetch inventory is projectable.
 */
auto_dig_mcp_read_tool(brave, brave_web_search).
auto_dig_mcp_read_tool(brave, brave_local_search).
auto_dig_mcp_read_tool(brave, brave_video_search).
auto_dig_mcp_read_tool(brave, brave_image_search).
auto_dig_mcp_read_tool(brave, brave_news_search).
auto_dig_mcp_read_tool(brave, brave_summarizer).
auto_dig_mcp_read_tool(brave, brave_llm_context).
auto_dig_mcp_read_tool(brave, brave_place_search).

auto_dig_mcp_read_tool(fetch, fetch_html).
auto_dig_mcp_read_tool(fetch, fetch_markdown).
auto_dig_mcp_read_tool(fetch, fetch_readable).
auto_dig_mcp_read_tool(fetch, fetch_txt).
auto_dig_mcp_read_tool(fetch, fetch_json).
auto_dig_mcp_read_tool(fetch, fetch_youtube_transcript).

auto_dig_mcp_read_tool(starintel, starintel_search).
auto_dig_mcp_read_tool(starintel, starintel_get_document).
auto_dig_mcp_read_tool(starintel, starintel_health).

auto_dig_mcp_read_capabilities(Capabilities) :-
    auto_dig_mcp_servers(Servers),
    auto_dig_mcp_read_capabilities(Servers, Capabilities).

auto_dig_mcp_read_capabilities(Servers, Capabilities) :-
    findall(tool(LocalName),
            ( member(Server, Servers),
              auto_dig_mcp_read_tool(Server, RemoteName),
              format(atom(LocalName), 'mcp.~w.~w', [Server, RemoteName])
            ),
            Capabilities0),
    sort(Capabilities0, Capabilities).

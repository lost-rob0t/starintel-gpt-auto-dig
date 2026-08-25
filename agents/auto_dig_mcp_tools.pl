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
*/

:- use_module(library(lists)).
:- use_module(library(rlm_mcp_policy), []).
:- use_module(library(rlm_mcp_server), []).

:- multifile rlm_mcp_policy:mcp_stdio_profile/2.
:- multifile rlm_mcp_policy:mcp_config_value/2.
:- multifile rlm_mcp_server:mcp_server/2.

% These two policy predicates are multifile so trusted host/test modules can
% contribute additional declared MCP servers without weakening the fixed
% production server set returned by auto_dig_mcp_servers/1.
:- multifile auto_dig_mcp_import_options/2.
:- multifile auto_dig_mcp_read_tool/2.

/* Fixed host execution profiles. Versions intentionally match opencode.jsonc
 * so both research surfaces exercise the same external server builds. */
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

auto_dig_mcp_servers([brave, fetch]).

/* Imported MCP tools are conservatively classified as write by Prolog-RLM
 * unless trusted host code supplies an effect. These two servers are retrieval
 * surfaces, so Auto-Dig explicitly imports them as read-only effects. */
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

/* Least-privilege invocation allow-list. Import may discover more remote tools,
 * but the RLM receives capabilities only for these research operations. */
auto_dig_mcp_read_tool(brave, brave_web_search).
auto_dig_mcp_read_tool(brave, brave_news_search).
auto_dig_mcp_read_tool(brave, brave_video_search).

auto_dig_mcp_read_tool(fetch, fetch_markdown).
auto_dig_mcp_read_tool(fetch, fetch_readable).
auto_dig_mcp_read_tool(fetch, fetch_txt).
auto_dig_mcp_read_tool(fetch, fetch_json).
auto_dig_mcp_read_tool(fetch, fetch_youtube_transcript).

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

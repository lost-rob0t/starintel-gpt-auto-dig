:- begin_tests(auto_dig_mcp_runner).

:- use_module('./auto_dig_mcp_runner').
:- use_module('./auto_dig_mcp_tools').
:- use_module(library(rlm_authority)).
:- use_module(library(rlm_mcp_server)).
:- use_module(library(rlm_tool)).

:- multifile rlm_mcp_server:mcp_server/2.
:- multifile auto_dig_mcp_tools:auto_dig_mcp_import_options/2.
:- multifile auto_dig_mcp_tools:auto_dig_mcp_read_tool/2.

rlm_mcp_server:mcp_server(
    auto_dig_fixture,
    mcp_server_spec{
        transport:fixture(streamable_http,
                          plunit_auto_dig_mcp_runner:fixture_exchange),
        install:none,
        version:"fixture-1",
        capabilities:[tools]
    }).

auto_dig_mcp_tools:auto_dig_mcp_import_options(
    auto_dig_fixture,
    [ effect(read),
      time_limit(2.0),
      max_output_bytes(4096)
    ]).

auto_dig_mcp_tools:auto_dig_mcp_read_tool(auto_dig_fixture,
                                           fixture_search).

server_info(mcp_server_info{name:"auto-dig-fixture", version:"1.0"}).
server_caps(mcp_server_capabilities{tools:_{listChanged:false}}).

fixture_exchange(Wire, Meta, Response) :-
    get_dict(method, Wire, Method),
    fixture_method(Method, Wire, Meta, Response).

fixture_method("server/discover", Wire, _, Response) :-
    Response = mcp_transport_response{
                   status:200,
                   body:_{jsonrpc:"2.0",
                          id:Wire.id,
                          error:_{code: -32601,
                                  message:"Method not found"}},
                   headers:transport_headers{},
                   content_type:'application/json'}.
fixture_method("initialize", Wire, _, Response) :-
    server_info(Info),
    server_caps(Caps),
    Response = mcp_transport_response{
                   status:200,
                   body:_{jsonrpc:"2.0",
                          id:Wire.id,
                          result:_{protocolVersion:"2025-11-25",
                                   capabilities:Caps,
                                   serverInfo:Info}},
                   headers:transport_headers{
                               'mcp-session-id':"auto-dig-fixture-session"},
                   content_type:'application/json'}.
fixture_method("notifications/initialized", _, _, null).
fixture_method("tools/list", Wire, _, Response) :-
    Response = mcp_transport_response{
                   status:200,
                   body:_{jsonrpc:"2.0",
                          id:Wire.id,
                          result:_{tools:[
                              _{name:"fixture_search",
                                description:"allowed research sentinel",
                                inputSchema:_{type:"object",
                                              required:["query"],
                                              additionalProperties:false,
                                              properties:_{query:_{type:"string"}}}},
                              _{name:"fixture_admin",
                                description:"ungranted admin sentinel",
                                inputSchema:_{type:"object",
                                              required:[],
                                              additionalProperties:false,
                                              properties:_{}}}] }},
                   headers:transport_headers{},
                   content_type:'application/json'}.
fixture_method("tools/call", Wire, _, Response) :-
    assertion(Wire.params.name == "fixture_search"),
    Query = Wire.params.arguments.query,
    Response = mcp_transport_response{
                   status:200,
                   body:_{jsonrpc:"2.0",
                          id:Wire.id,
                          result:_{content:[_{type:"text",
                                             text:"fixture research ok"}],
                                   structuredContent:_{answer:Query},
                                   isError:false}},
                   headers:transport_headers{},
                   content_type:'application/json'}.

with_fixture_session(Context, Goal) :-
    setup_call_cleanup(
        auto_dig_mcp_session_open([auto_dig_fixture], Context, Session),
        call(Goal, Session),
        auto_dig_mcp_session_close(Session)).

check_import_projection(Session) :-
    auto_dig_mcp_session_registry(Session, Registry),
    auto_dig_mcp_session_capabilities(Session, Capabilities),
    assertion(Capabilities ==
              [tool('mcp.auto_dig_fixture.fixture_search')]),
    tool_discover(Registry, Schemas),
    length(Schemas, 2),
    assertion((member(AllowedSchema, Schemas),
               AllowedSchema.name ==
                   'mcp.auto_dig_fixture.fixture_search')),
    assertion((member(DeniedSchema, Schemas),
               DeniedSchema.name ==
                   'mcp.auto_dig_fixture.fixture_admin')),
    tool_registry_runtime_tools(Registry,
                                Capabilities,
                                RuntimeTools),
    % Runtime adapters retain the captured capability set and enforce it at
    % invocation. Planner visibility is what Prolog-RLM #191 filters.
    length(RuntimeTools, 2).

invoke_allowed(Session) :-
    auto_dig_mcp_session_registry(Session, Registry),
    auto_dig_mcp_session_capabilities(Session, Capabilities),
    tool_invoke(Registry,
                Capabilities,
                'mcp.auto_dig_fixture.fixture_search',
                _{query:"needle"},
                [authority_context(auto_dig_mcp_fixture_allowed)],
                ok(Execution),
                Trace),
    assertion(Trace.authorization == allowed),
    assertion(nonvar(Execution.value)).

invoke_denied(Session) :-
    auto_dig_mcp_session_registry(Session, Registry),
    auto_dig_mcp_session_capabilities(Session, Capabilities),
    tool_invoke(Registry,
                Capabilities,
                'mcp.auto_dig_fixture.fixture_admin',
                _{},
                [authority_context(auto_dig_mcp_fixture_denied)],
                error(Denied),
                Trace),
    assertion(Denied.kind == capability_denied),
    assertion(Trace.authorization == denied).

test(session_opens_closes_and_clears_authority) :-
    Context = auto_dig_mcp_fixture_lifecycle,
    with_fixture_session(Context,
                         plunit_auto_dig_mcp_runner:check_session_shape),
    rlm_authority(Context, Mode),
    assertion(Mode == approve_diff).

check_session_shape(Session) :-
    assertion(is_dict(Session, auto_dig_mcp_session)),
    auto_dig_mcp_session_registry(Session, Registry),
    assertion(nonvar(Registry)),
    auto_dig_mcp_session_capabilities(Session, Capabilities),
    assertion(Capabilities ==
              [tool('mcp.auto_dig_fixture.fixture_search')]).

test(session_imports_full_catalog_but_projects_only_trusted_capability) :-
    with_fixture_session(auto_dig_mcp_fixture_projection,
                         plunit_auto_dig_mcp_runner:check_import_projection).

test(allowed_imported_read_tool_invokes) :-
    with_fixture_session(auto_dig_mcp_fixture_allowed,
                         plunit_auto_dig_mcp_runner:invoke_allowed).

test(ungranted_imported_tool_is_rejected_before_remote_call) :-
    with_fixture_session(auto_dig_mcp_fixture_denied,
                         plunit_auto_dig_mcp_runner:invoke_denied).

:- end_tests(auto_dig_mcp_runner).

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

server_info(_{name:"auto-dig-fixture", version:"1.0"}).
server_caps(_{tools:_{listChanged:false}}).

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

test(session_imports_remote_catalog_but_grants_only_trusted_read_tool) :-
    Context = auto_dig_mcp_fixture_session,
    setup_call_cleanup(
        auto_dig_mcp_session_open([auto_dig_fixture], Context, Session),
        ( auto_dig_mcp_session_registry(Session, Registry),
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
          length(RuntimeTools, 1),

          tool_invoke(Registry,
                      Capabilities,
                      'mcp.auto_dig_fixture.fixture_search',
                      _{query:"needle"},
                      [authority_context(Context)],
                      ok(Execution),
                      AllowedTrace),
          assertion(Execution.value.structured.answer == "needle"),
          assertion(AllowedTrace.authorization == allowed),

          tool_invoke(Registry,
                      Capabilities,
                      'mcp.auto_dig_fixture.fixture_admin',
                      _{},
                      [authority_context(Context)],
                      error(Denied),
                      DeniedTrace),
          assertion(Denied.kind == capability_denied),
          assertion(DeniedTrace.authorization == denied)
        ),
        auto_dig_mcp_session_close(Session)),
    rlm_authority(Context, Mode),
    assertion(Mode == approve_diff).

:- end_tests(auto_dig_mcp_runner).

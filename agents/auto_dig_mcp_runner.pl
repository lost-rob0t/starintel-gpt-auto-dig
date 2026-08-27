:- module(auto_dig_mcp_runner,
          [ auto_dig_mcp_session_open/3,
            auto_dig_mcp_session_close/1,
            auto_dig_mcp_session_registry/2,
            auto_dig_mcp_session_capabilities/2
          ]).

/** <module> Explicit MCP lifecycle for Auto-Dig research

The trusted host owns every lifecycle transition. Server declarations remain
inert until this module is called. Opening a session creates one private tool
registry, grants a dedicated authority context `allow_session` only for the
bounded server lifecycle, starts/connects/imports each requested server, and
computes the exact read capability allow-list for those servers.

Importing a remote tool does not grant its capability. The registry may contain
additional server-advertised tools, but callers receive only the capabilities
selected by auto_dig_mcp_tools. Prolog-RLM consequently filters both executable
tools and planner-visible schemas through the same list.
*/

:- use_module('./auto_dig_mcp_tools').
:- use_module('./auto_dig_safe_log').
:- use_module(library(rlm_authority)).
:- use_module(library(rlm_mcp)).
:- use_module(library(rlm_mcp_server)).
:- use_module(library(rlm_mcp_tool)).
:- use_module(library(rlm_tool)).

:- meta_predicate lifecycle_phase(+, 0).

% Named tags keep the host handshake terms fully ground. Anonymous-tag dicts
% are convenient JSON values but are the wrong representation at an authority
% or async boundary where ground/1 is part of the contract.
client_info(mcp_client_info{name:"starintel-auto-dig", version:"1.0"}).
client_capabilities(mcp_client_capabilities{}).

auto_dig_mcp_session_open(Servers, AuthorityContext, Session) :-
    require_server_list(Servers),
    require_authority_context(AuthorityContext),
    mcp_log('session_open servers=~q', [Servers]),
    lifecycle_phase(registry_create,
                    tool_registry_create(Registry)),
    catch(open_session(Servers,
                       AuthorityContext,
                       Registry,
                       Session),
          Exception,
          ( mcp_log('session_open state=error', []),
            safe_registry_destroy(Registry),
            safe_authority_clear(AuthorityContext),
            throw(Exception)
          )),
    mcp_log('session_open state=ok', []).

open_session(Servers, AuthorityContext, Registry, Session) :-
    lifecycle_phase(authority_setup,
                    rlm_set_authority(AuthorityContext,
                                      allow_session,
                                      AuthorityOutcome)),
    require_ok(authority_setup, AuthorityOutcome, _),
    open_servers(Servers, AuthorityContext, Registry, ServerStates),
    lifecycle_phase(capability_projection,
                    auto_dig_mcp_read_capabilities(Servers,
                                                   Capabilities)),
    length(Capabilities, CapabilityCount),
    mcp_log('capability_projection count=~d', [CapabilityCount]),
    Session = auto_dig_mcp_session{
                  authority_context:AuthorityContext,
                  registry:Registry,
                  capabilities:Capabilities,
                  servers:ServerStates
              }.

open_servers([], _, _, []).
open_servers([Server|Servers], AuthorityContext, Registry,
             [State|States]) :-
    open_server(Server, AuthorityContext, Registry, State),
    catch(open_servers(Servers, AuthorityContext, Registry, States),
          Exception,
          ( safe_server_close(State),
            throw(Exception)
          )).

open_server(Server, AuthorityContext, Registry, State) :-
    lifecycle_phase(mcp_run(Server),
                    rlm_run_mcp_server(
                        Server,
                        [authority_context(AuthorityContext)],
                        RunOutcome)),
    require_ok(mcp_run(Server), RunOutcome, Handle),
    catch(connect_and_import(Server, Registry, Handle, State),
          Exception,
          ( safe_stop_handle(Handle),
            throw(Exception)
          )).

connect_and_import(Server, Registry, Handle, State) :-
    client_info(ClientInfo),
    client_capabilities(ClientCapabilities),
    lifecycle_phase(mcp_connect(Server),
                    rlm_connect_mcp_server(Handle,
                                           ClientInfo,
                                           ClientCapabilities,
                                           [],
                                           ConnectOutcome)),
    require_ok(mcp_connect(Server), ConnectOutcome, Client),
    catch(import_server_tools(Server,
                              Registry,
                              Handle,
                              Client,
                              State),
          Exception,
          ( safe_client_close(Client),
            throw(Exception)
          )).

import_server_tools(Server, Registry, Handle, Client, State) :-
    (   auto_dig_mcp_import_options(Server, ImportOptions)
    ->  true
    ;   throw(error(auto_dig_mcp_runner_error{
                        phase:import_policy,
                        server:Server,
                        kind:missing_import_policy}, _))
    ),
    lifecycle_phase(mcp_import(Server),
                    mcp_import_tools(Registry,
                                     Server,
                                     Client,
                                     ImportOptions,
                                     ImportOutcome)),
    require_ok(mcp_import(Server), ImportOutcome, Import),
    length(Import.tools, ImportedCount),
    mcp_log('mcp_import server=~w imported_tools=~d',
            [Server, ImportedCount]),
    State = auto_dig_mcp_server_state{
                server:Server,
                handle:Handle,
                import_state:Import.state,
                imported_tools:Import.tools
            }.

auto_dig_mcp_session_registry(Session, Registry) :-
    require_session(Session),
    Registry = Session.registry.

auto_dig_mcp_session_capabilities(Session, Capabilities) :-
    require_session(Session),
    Capabilities = Session.capabilities.

auto_dig_mcp_session_close(Session) :-
    require_session(Session),
    mcp_log('session_close state=start', []),
    reverse(Session.servers, ReverseStates),
    maplist(safe_server_close, ReverseStates),
    safe_registry_destroy(Session.registry),
    safe_authority_clear(Session.authority_context),
    mcp_log('session_close state=ok', []).

safe_server_close(State) :-
    (   is_dict(State, auto_dig_mcp_server_state),
        get_dict(import_state, State, ImportState)
    ->  catch(mcp_import_state_destroy(ImportState), _, true)
    ;   true
    ),
    (   is_dict(State, auto_dig_mcp_server_state),
        get_dict(handle, State, Handle)
    ->  safe_stop_handle(Handle)
    ;   true
    ).

safe_stop_handle(Handle) :-
    catch(rlm_stop_mcp_server(Handle, _), _, true).

safe_client_close(Client) :-
    catch(mcp_client_close(Client, _), _, true).

safe_registry_destroy(Registry) :-
    catch(tool_registry_destroy(Registry), _, true).

safe_authority_clear(Context) :-
    catch(rlm_authority_clear(Context), _, true).

lifecycle_phase(Phase, Goal) :-
    mcp_log('phase=~q state=start', [Phase]),
    catch((   call(Goal)
          ->  mcp_log('phase=~q state=ok', [Phase])
          ;   throw(error(auto_dig_mcp_runner_error{
                              phase:Phase,
                              kind:goal_failed}, _))
          ),
          Exception,
          ( message_to_string(Exception, Message),
            mcp_log('phase=~q state=error message=~s', [Phase, Message]),
            throw(error(auto_dig_mcp_runner_error{
                            phase:Phase,
                            exception:Exception}, _))
          )).

require_ok(_, ok(Value), Value) :- !.
require_ok(Phase, error(Error), _) :-
    throw(error(auto_dig_mcp_runner_error{
                    phase:Phase,
                    cause:Error}, _)).
require_ok(Phase, Outcome, _) :-
    throw(error(auto_dig_mcp_runner_error{
                    phase:Phase,
                    kind:unexpected_outcome,
                    outcome:Outcome}, _)).

require_server_list(Servers) :-
    is_list(Servers),
    Servers \== [],
    ground(Servers),
    forall(member(Server, Servers),
           ( atom(Server), Server \== '' )),
    !.
require_server_list(Servers) :-
    throw(error(type_error(auto_dig_mcp_server_list, Servers), _)).

require_authority_context(Context) :-
    ground(Context),
    !.
require_authority_context(_) :-
    throw(error(instantiation_error,
                context(auto_dig_mcp_runner,
                        'authority context must be ground'))).

require_session(Session) :-
    is_dict(Session, auto_dig_mcp_session),
    get_dict(authority_context, Session, _),
    get_dict(registry, Session, _),
    get_dict(capabilities, Session, Capabilities),
    is_list(Capabilities),
    get_dict(servers, Session, Servers),
    is_list(Servers),
    !.
require_session(Session) :-
    throw(error(type_error(auto_dig_mcp_session, Session), _)).

mcp_log(Format, Args) :-
    safe_log(auto_dig_mcp, Format, Args).

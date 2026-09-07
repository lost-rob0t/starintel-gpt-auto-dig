:- begin_tests(auto_dig_starintel_tools).

:- use_module('./auto_dig_starintel_tools').
:- use_module(library(rlm_authority)).
:- use_module(library(rlm_effect)).
:- use_module(library(rlm_tool)).

config(Root, Write, Reply,
       auto_dig_starintel_config{
           root:Root,
           allow_db_write:Write,
           allow_issue_reply:Reply,
           github_repository:"example/repo",
           issue:7}).

test(read_only_registration_never_grants_mutation) :-
    working_directory(RootAtom, RootAtom),
    atom_string(RootAtom, Root),
    config(Root, false, false, Config),
    tool_registry_create(Registry),
    setup_call_cleanup(
        auto_dig_starintel_tools_register(Registry, Config, RootCaps, ChildCaps),
        ( assertion(RootCaps == ChildCaps),
          assertion(memberchk(tool(starintel_search), RootCaps)),
          assertion(\+ memberchk(tool(starintel_write_document), RootCaps)),
          assertion(\+ memberchk(tool(github_issue_reply), RootCaps)),
          tool_lookup(Registry, starintel_search, ok(SearchSchema)),
          assertion(SearchSchema.effect == read),
          tool_lookup(Registry, starintel_write_document, error(_))
        ),
        tool_registry_destroy(Registry)).

test(write_and_reply_are_root_only_capabilities) :-
    working_directory(RootAtom, RootAtom),
    atom_string(RootAtom, Root),
    config(Root, true, true, Config),
    tool_registry_create(Registry),
    setup_call_cleanup(
        auto_dig_starintel_tools_register(Registry, Config, RootCaps, ChildCaps),
        ( assertion(memberchk(tool(starintel_write_document), RootCaps)),
          assertion(memberchk(tool(github_issue_reply), RootCaps)),
          assertion(\+ memberchk(tool(starintel_write_document), ChildCaps)),
          assertion(\+ memberchk(tool(github_issue_reply), ChildCaps)),
          tool_lookup(Registry, starintel_write_document, ok(WriteSchema)),
          assertion(WriteSchema.effect == write),
          tool_lookup(Registry, github_issue_reply, ok(ReplySchema)),
          assertion(ReplySchema.effect == write)
        ),
        tool_registry_destroy(Registry)).

test(types_tool_executes_through_registered_handler) :-
    working_directory(RootAtom, RootAtom),
    atom_string(RootAtom, Root),
    config(Root, false, false, Config),
    tool_registry_create(Registry),
    setup_call_cleanup(
        auto_dig_starintel_tools_register(Registry, Config, RootCaps, _),
        ( tool_invoke(Registry, RootCaps, starintel_types, _{}, [],
                      ok(Result), _),
          assertion(Result.value.schema_version == "0.9.0"),
          assertion(memberchk("org", Result.value.dtypes))
        ),
        tool_registry_destroy(Registry)).

:- end_tests(auto_dig_starintel_tools).

:- module(auto_dig_starintel_tools,
          [ auto_dig_starintel_tools_register/4,
            auto_dig_starintel_read_capabilities/1
          ]).

/** <module> Narrow StarIntel and selected-issue tools for Auto-Dig */

:- use_module(library(http/json)).
:- use_module(library(process)).
:- use_module(library(readutil)).
:- use_module(library(rlm_tool)).

auto_dig_starintel_read_capabilities(
    [ tool(starintel_types),
      tool(starintel_schema),
      tool(starintel_search),
      tool(starintel_draft_document),
      tool(starintel_validate_document)
    ]).

auto_dig_starintel_tools_register(Registry, Config,
                                  RootCapabilities,
                                  ChildCapabilities) :-
    require_config(Config),
    read_tool_specs(ReadSpecs),
    maplist(register_tool(Registry, Config), ReadSpecs),
    auto_dig_starintel_read_capabilities(ChildCapabilities),
    optional_tool_specs(Config, OptionalSpecs, OptionalCapabilities),
    maplist(register_tool(Registry, Config), OptionalSpecs),
    append(ChildCapabilities, OptionalCapabilities, RootCapabilities).

read_tool_specs(
    [ spec(types, starintel_types,
           "List exact StarIntel v0.9.0 document types.",
           _{type:object, properties:_{}, required:[], additional_properties:false},
           10.0),
      spec(schema, starintel_schema,
           "Inspect the executable schema for one exact StarIntel dtype before drafting.",
           _{type:object,
             properties:_{dtype:_{type:string}},
             required:[dtype], additional_properties:false},
           10.0),
      spec(search, starintel_search,
           "Search canonical DB and packet records before creating identities.",
           _{type:object,
             properties:_{query:_{type:string}, dtype:_{type:string},
                          dataset:_{type:string}, predicate:_{type:string},
                          id:_{type:string}, source:_{type:string},
                          min_confidence:_{type:number}, limit:_{type:integer}},
             required:[], additional_properties:false},
           20.0),
      spec(draft, starintel_draft_document,
           "Create a complete schema-valid StarIntel document without writing it.",
           _{type:object,
             properties:_{dtype:_{type:string}, dataset:_{type:string},
                          id:_{type:string}, title:_{type:string},
                          summary:_{type:string},
                          data:_{type:object, additional_properties:true},
                          metadata:_{type:object, additional_properties:true}},
             required:[dtype,dataset,id,data], additional_properties:false},
           10.0),
      spec('validate-document', starintel_validate_document,
           "Validate one complete StarIntel document against the executable schema.",
           _{type:object,
             properties:_{document:_{type:object, additional_properties:true}},
             required:[document], additional_properties:false},
           10.0)
    ]).

optional_tool_specs(Config, Specs, Capabilities) :-
    (   Config.allow_db_write == true
    ->  WriteSpecs = [write_spec],
        WriteCapabilities = [tool(starintel_write_document)]
    ;   WriteSpecs = [],
        WriteCapabilities = []
    ),
    (   Config.allow_issue_reply == true
    ->  ReplySpecs = [reply_spec],
        ReplyCapabilities = [tool(github_issue_reply)]
    ;   ReplySpecs = [],
        ReplyCapabilities = []
    ),
    append(WriteSpecs, ReplySpecs, Specs),
    append(WriteCapabilities, ReplyCapabilities, Capabilities).

register_tool(Registry, Config,
              spec(Command, Name, Description, Arguments, TimeLimit)) :-
    read_schema(Name, Description, Arguments, TimeLimit, Schema),
    tool_register(Registry, Schema,
                  auto_dig_starintel_tools:adapter_handler(Config, Command),
                  Outcome),
    require_registration(Name, Outcome).
register_tool(Registry, Config, write_spec) :-
    write_schema(Schema),
    Handler = tool_handler(
                  auto_dig_starintel_tools:write_preflight(Config),
                  auto_dig_starintel_tools:adapter_handler(Config,
                                                            'write-document')),
    tool_register(Registry, Schema, Handler, Outcome),
    require_registration(starintel_write_document, Outcome).
register_tool(Registry, Config, reply_spec) :-
    reply_schema(Schema),
    Handler = tool_handler(
                  auto_dig_starintel_tools:reply_preflight(Config),
                  auto_dig_starintel_tools:adapter_handler(Config,
                                                            'issue-reply')),
    tool_register(Registry, Schema, Handler, Outcome),
    require_registration(github_issue_reply, Outcome).

read_schema(Name, Description, Arguments, TimeLimit,
            tool_schema{name:Name, description:Description,
                        capability:tool(Name), effect:read,
                        arguments:Arguments,
                        result:_{type:object, additional_properties:true},
                        limits:_{time_limit:TimeLimit,
                                 max_output_bytes:131072}}).

write_schema(
    tool_schema{name:starintel_write_document,
                description:"Atomically add one validated canonical DB document. Existing changed IDs are rejected.",
                capability:tool(starintel_write_document), effect:write,
                arguments:_{type:object,
                            properties:_{document:_{type:object,
                                                    additional_properties:true}},
                            required:[document], additional_properties:false},
                result:_{type:object, additional_properties:true},
                limits:_{time_limit:30.0, max_output_bytes:16384}}).

reply_schema(
    tool_schema{name:github_issue_reply,
                description:"Post one idempotently marked progress reply to the host-selected investigation issue.",
                capability:tool(github_issue_reply), effect:write,
                arguments:_{type:object,
                            properties:_{body:_{type:string}},
                            required:[body], additional_properties:false},
                result:_{type:object, additional_properties:true},
                limits:_{time_limit:30.0, max_output_bytes:32768}}).

write_preflight(Config, Args, Normalized, Details) :-
    adapter_call(Config, 'prepare-write', Args, Prepared),
    Normalized = Prepared.request,
    Details = Prepared.details.

reply_preflight(Config, Args, Normalized, Details) :-
    adapter_call(Config, 'prepare-issue-reply', Args, Prepared),
    Normalized = Prepared.request,
    Details = Prepared.details.

adapter_handler(Config, Command, Args, Result) :-
    adapter_call(Config, Command, Args, Result).

adapter_call(Config, Command, Request, Result) :-
    adapter_script(Script),
    adapter_arguments(Config, Script, Command, Arguments),
    atom_json_dict(InputAtom, Request, [width(0)]),
    setup_call_cleanup(
        process_create(path(python3), Arguments,
                       [ stdin(pipe(In)), stdout(pipe(Out)), stderr(pipe(Err)),
                         process(Pid)
                       ]),
        adapter_exchange(Pid, In, Out, Err, InputAtom, Result),
        close_adapter_streams(In, Out, Err)).

adapter_arguments(Config, Script, Command,
                  [Script, Command, '--root', Config.root|Tail]) :-
    (   Config.allow_issue_reply == true
    ->  number_string(Config.issue, Issue),
        Tail = ['--github-repository', Config.github_repository,
                '--issue', Issue]
    ;   Tail = []
    ).

adapter_exchange(Pid, In, Out, Err, InputAtom, Result) :-
    format(In, '~w~n', [InputAtom]),
    close(In),
    read_string(Out, _, OutputText),
    read_string(Err, _, ErrorText),
    process_wait(Pid, Status),
    atom_string(OutputAtom, OutputText),
    (   catch(atom_json_dict(OutputAtom, Envelope, []), _, fail),
        is_dict(Envelope),
        get_dict(ok, Envelope, true),
        Status == exit(0)
    ->  Result = Envelope.result
    ;   adapter_error(OutputText, ErrorText, Message),
        throw(error(auto_dig_starintel_adapter_error{
                        command_status:Status,
                        message:Message}, _))
    ).

adapter_error(OutputText, ErrorText, Message) :-
    (   catch(( atom_string(OutputAtom, OutputText),
                atom_json_dict(OutputAtom, Envelope, []),
                get_dict(error, Envelope, Message0)
              ), _, fail)
    ->  Message = Message0
    ;   ErrorText \== ""
    ->  Message = ErrorText
    ;   Message = OutputText
    ).

close_adapter_streams(In, Out, Err) :-
    maplist(close_if_open, [In, Out, Err]).

close_if_open(Stream) :-
    catch(close(Stream), _, true).

adapter_script(Path) :-
    source_file(auto_dig_starintel_tools:auto_dig_starintel_tools_register(_,_,_,_),
                Source),
    file_directory_name(Source, AgentsDirectory),
    file_directory_name(AgentsDirectory, Root),
    directory_file_path(Root, 'scripts/auto_dig_starintel_adapter.py', Path).

require_registration(_, ok(_)) :- !.
require_registration(Name, Outcome) :-
    throw(error(auto_dig_starintel_tool_registration_failed{
                    tool:Name, outcome:Outcome}, _)).

require_config(Config) :-
    is_dict(Config, auto_dig_starintel_config),
    ground(Config),
    get_dict(root, Config, Root),
    string(Root),
    get_dict(allow_db_write, Config, AllowDbWrite),
    memberchk(AllowDbWrite, [true,false]),
    get_dict(allow_issue_reply, Config, AllowIssueReply),
    memberchk(AllowIssueReply, [true,false]),
    (   AllowIssueReply == false
    ;   get_dict(github_repository, Config, Repository),
        string(Repository),
        Repository \== "",
        get_dict(issue, Config, Issue),
        integer(Issue),
        Issue > 0
    ),
    !.
require_config(Config) :-
    throw(error(type_error(auto_dig_starintel_tool_config, Config), _)).

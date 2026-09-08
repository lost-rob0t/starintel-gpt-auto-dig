:- module(coverage_backlog,
          [ main/1,
            ensure_ledger/9,
            shard_items/4,
            unresolved_items/3,
            claim_batch/4,
            complete_batch/3,
            fail_batch/3
          ]).

:- use_module(library(http/json)).
:- use_module(library(lists)).
:- use_module(library(option)).

:- initialization(main, main).

state_schema("auto-dig-prolog-state.v1").
ledger_schema("auto-dig-coverage-ledger.v1").

main(Argv) :-
    catch(main_run(Argv), Error, (print_message(error, Error), fail)).

main_run(Argv) :-
    parse_args(Argv, Options),
    option(state(StatePath), Options),
    option(valid_items(ValidPath), Options),
    option(corpus(Corpus), Options),
    option(seed_kind(SeedKind), Options),
    option(authority(Authority), Options),
    option(shard(Shard), Options),
    option(shard_count(ShardCount), Options),
    option(shard_index(ShardIndex), Options),
    option(batch_size(BatchSize), Options, 3),
    option(action(Action), Options, next),
    read_json_file(StatePath, State0),
    read_json_file(ValidPath, ValidItems),
    must_be(dict, State0),
    must_be(list, ValidItems),
    ensure_ledger(State0, Corpus, SeedKind, Authority, Shard,
                  ShardCount, ShardIndex, State1, Key),
    get_dict(coverage, State1, Coverage1),
    get_dict(Key, Coverage1, Ledger0),
    run_action(Action, Options, Ledger0, ValidItems, BatchSize, Ledger, Items),
    put_dict(Key, Coverage1, Ledger, Coverage),
    put_dict(coverage, State1, Coverage, State),
    atomic_write_json(StatePath, State),
    json_write_dict(current_output,
                    _{ledger:Key, action:Action, items:Items},
                    [width(0)]),
    nl.

run_action(next, _, Ledger0, ValidItems, BatchSize, Ledger, Items) :-
    claim_batch(Ledger0, ValidItems, BatchSize, Ledger-Items).
run_action(complete, Options, Ledger0, _, _, Ledger, Items) :-
    option(items(Items), Options),
    Items \== [],
    complete_batch(Ledger0, Items, Ledger).
run_action(fail, Options, Ledger0, _, _, Ledger, Items) :-
    option(items(Items), Options),
    Items \== [],
    fail_batch(Ledger0, Items, Ledger).

ensure_ledger(State0, Corpus0, SeedKind0, Authority0, Shard0,
              ShardCount, ShardIndex, State, Key) :-
    state_schema(StateSchema),
    get_dict(schema, State0, StateSchema),
    positive_integer(ShardCount),
    integer(ShardIndex),
    ShardIndex >= 0,
    ShardIndex < ShardCount,
    nonempty_string(Corpus0, Corpus),
    nonempty_string(SeedKind0, SeedKind),
    nonempty_string(Authority0, Authority),
    nonempty_string(Shard0, Shard),
    atomic_list_concat([Corpus, SeedKind, Shard], '/', Key),
    (   get_dict(coverage, State0, Coverage0)
    ->  must_be(dict, Coverage0)
    ;   Coverage0 = json{}
    ),
    (   get_dict(Key, Coverage0, Existing)
    ->  validate_ledger_identity(Existing, Corpus, SeedKind, Authority,
                                 Shard, ShardCount, ShardIndex),
        canonicalize_ledger(Existing, Ledger)
    ;   ledger_schema(LedgerSchema),
        Ledger = json{
            schema:LedgerSchema,
            corpus:Corpus,
            seed_kind:SeedKind,
            authority:Authority,
            shard:Shard,
            shard_count:ShardCount,
            shard_index:ShardIndex,
            ordering:"numeric_ascending",
            completed:[],
            in_progress:[],
            failed_retryable:[]
        }
    ),
    put_dict(Key, Coverage0, Ledger, Coverage),
    put_dict(coverage, State0, Coverage, State).

validate_ledger_identity(Ledger, Corpus, SeedKind, Authority,
                         Shard, ShardCount, ShardIndex) :-
    ledger_schema(LedgerSchema),
    get_dict(schema, Ledger, LedgerSchema),
    immutable_field(Ledger, corpus, Corpus),
    immutable_field(Ledger, seed_kind, SeedKind),
    immutable_field(Ledger, authority, Authority),
    immutable_field(Ledger, shard, Shard),
    immutable_field(Ledger, shard_count, ShardCount),
    immutable_field(Ledger, shard_index, ShardIndex).

immutable_field(Dict, Key, Expected) :-
    get_dict(Key, Dict, Actual),
    (   Actual == Expected
    ->  true
    ;   throw(error(permission_error(change, coverage_ledger_identity, Key),
                    context(coverage_backlog, Actual-Expected)))
    ).

canonicalize_ledger(Ledger0, Ledger) :-
    canonical_field(Ledger0, completed, Completed),
    canonical_field(Ledger0, in_progress, InProgress),
    canonical_field(Ledger0, failed_retryable, Retryable),
    put_dict(_{completed:Completed,
               in_progress:InProgress,
               failed_retryable:Retryable}, Ledger0, Ledger).

canonical_field(Dict, Key, Items) :-
    (   get_dict(Key, Dict, Raw)
    ->  canonical_items(Raw, Items)
    ;   Items = []
    ).

shard_items(ValidItems0, ShardCount, ShardIndex, Items) :-
    positive_integer(ShardCount),
    integer(ShardIndex),
    ShardIndex >= 0,
    ShardIndex < ShardCount,
    canonical_items(ValidItems0, ValidItems),
    include(in_shard(ShardCount, ShardIndex), ValidItems, Items).

in_shard(ShardCount, ShardIndex, Item) :-
    Item mod ShardCount =:= ShardIndex.

unresolved_items(Ledger, ValidItems, Unresolved) :-
    get_dict(shard_count, Ledger, ShardCount),
    get_dict(shard_index, Ledger, ShardIndex),
    shard_items(ValidItems, ShardCount, ShardIndex, ShardItems),
    canonical_field(Ledger, completed, Completed),
    canonical_field(Ledger, in_progress, InProgress),
    exclude(member_of(Completed), ShardItems, NotCompleted),
    exclude(member_of(InProgress), NotCompleted, Unresolved).

member_of(List, Item) :- memberchk(Item, List).

claim_batch(Ledger0, ValidItems, BatchSize, Ledger-Items) :-
    positive_integer(BatchSize),
    unresolved_items(Ledger0, ValidItems, Unresolved),
    take(BatchSize, Unresolved, Items),
    canonical_field(Ledger0, in_progress, InProgress0),
    append(InProgress0, Items, InProgress1),
    canonical_items(InProgress1, InProgress),
    canonical_field(Ledger0, failed_retryable, Retry0),
    subtract(Retry0, Items, Retry),
    put_dict(_{in_progress:InProgress, failed_retryable:Retry}, Ledger0, Ledger).

complete_batch(Ledger0, Items0, Ledger) :-
    canonical_items(Items0, Items),
    canonical_field(Ledger0, in_progress, InProgress0),
    require_subset(Items, InProgress0, complete),
    canonical_field(Ledger0, completed, Completed0),
    append(Completed0, Items, Completed1),
    canonical_items(Completed1, Completed),
    subtract(InProgress0, Items, InProgress),
    canonical_field(Ledger0, failed_retryable, Retry0),
    subtract(Retry0, Items, Retry),
    put_dict(_{completed:Completed,
               in_progress:InProgress,
               failed_retryable:Retry}, Ledger0, Ledger).

fail_batch(Ledger0, Items0, Ledger) :-
    canonical_items(Items0, Items),
    canonical_field(Ledger0, in_progress, InProgress0),
    require_subset(Items, InProgress0, fail),
    subtract(InProgress0, Items, InProgress),
    canonical_field(Ledger0, failed_retryable, Retry0),
    append(Retry0, Items, Retry1),
    canonical_items(Retry1, Retry),
    put_dict(_{in_progress:InProgress, failed_retryable:Retry}, Ledger0, Ledger).

require_subset([], _, _).
require_subset([Item|Rest], Set, Action) :-
    (   memberchk(Item, Set)
    ->  require_subset(Rest, Set, Action)
    ;   throw(error(permission_error(Action, unclaimed_coverage_item, Item),
                    context(coverage_backlog, Item)))
    ).

canonical_items(Items0, Items) :-
    must_be(list, Items0),
    maplist(nonnegative_integer, Items0),
    sort(Items0, Items).

nonnegative_integer(Value) :-
    must_be(integer, Value),
    (Value >= 0 -> true ; domain_error(nonnegative_integer, Value)).

positive_integer(Value) :-
    must_be(integer, Value),
    (Value >= 1 -> true ; domain_error(positive_integer, Value)).

nonempty_string(Value0, Value) :-
    (atom(Value0) -> atom_string(Value0, Value) ; Value = Value0),
    must_be(string, Value),
    normalize_space(string(Value), Value),
    (Value \== "" -> true ; domain_error(nonempty_string, Value0)).

take(0, _, []) :- !.
take(_, [], []) :- !.
take(N, [X|Xs], [X|Ys]) :-
    N > 0,
    N1 is N - 1,
    take(N1, Xs, Ys).

read_json_file(Path, Value) :-
    setup_call_cleanup(open(Path, read, Stream, [encoding(utf8)]),
                       json_read_dict(Stream, Value),
                       close(Stream)).

atomic_write_json(Path, Value) :-
    file_directory_name(Path, Dir),
    file_base_name(Path, Base),
    tmp_file_stream(text, Tmp, Stream),
    setup_call_cleanup(
        true,
        ( json_write_dict(Stream, Value, [width(0)]), nl(Stream), close(Stream),
          atomic_list_concat([Dir, '/.', Base, '.new'], TargetTmp),
          rename_file(Tmp, TargetTmp),
          rename_file(TargetTmp, Path)
        ),
        (is_stream(Stream) -> close(Stream, [force(true)]) ; true)).

parse_args(Argv, Options) :- parse_args_(Argv, [], Options0), reverse(Options0, Options).
parse_args_([], Options, Options).
parse_args_(['--state', V|R], A, O) :- !, parse_args_(R, [state(V)|A], O).
parse_args_(['--valid-items', V|R], A, O) :- !, parse_args_(R, [valid_items(V)|A], O).
parse_args_(['--corpus', V|R], A, O) :- !, parse_args_(R, [corpus(V)|A], O).
parse_args_(['--seed-kind', V|R], A, O) :- !, parse_args_(R, [seed_kind(V)|A], O).
parse_args_(['--authority', V|R], A, O) :- !, parse_args_(R, [authority(V)|A], O).
parse_args_(['--shard', V|R], A, O) :- !, parse_args_(R, [shard(V)|A], O).
parse_args_(['--shard-count', V|R], A, O) :- !, atom_number(V, N), parse_args_(R, [shard_count(N)|A], O).
parse_args_(['--shard-index', V|R], A, O) :- !, atom_number(V, N), parse_args_(R, [shard_index(N)|A], O).
parse_args_(['--batch-size', V|R], A, O) :- !, atom_number(V, N), parse_args_(R, [batch_size(N)|A], O).
parse_args_(['--action', V|R], A, O) :- !, atom_string(Action, V), memberchk(Action, [next,complete,fail]), parse_args_(R, [action(Action)|A], O).
parse_args_(['--items', V|R], A, O) :- !, split_string(V, ",", " ", Parts), maplist(number_string, Items, Parts), parse_args_(R, [items(Items)|A], O).
parse_args_([Unknown|_], _, _) :- domain_error(coverage_backlog_argument, Unknown).

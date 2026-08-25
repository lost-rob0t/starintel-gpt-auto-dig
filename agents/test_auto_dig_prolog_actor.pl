:- begin_tests(auto_dig_prolog_actor).

:- use_module('./auto_dig_prolog_actor').

issue(Number, Priority, Dict) :-
    format(string(Body), '## Priority~n~n~w~n', [Priority]),
    format(string(Title), 'issue ~d', [Number]),
    format(string(Url), 'https://example.invalid/issues/~d', [Number]),
    Dict = _{number:Number, title:Title, url:Url, body:Body}.

state(Last, State) :-
    State = _{
        schema:"auto-dig-prolog-state.v1",
        last_issue:Last,
        last_priority:null,
        last_branch:null,
        last_run_id:null,
        last_success_at:null
    }.

test(json_dict_tags_are_grounded_recursively) :-
    Raw = _{outer:_{items:[_{value:1}, _{value:2}]}, enabled:true},
    assertion(\+ ground(Raw)),
    auto_dig_prolog_actor:ground_json_value(Raw, Ground),
    assertion(ground(Ground)),
    assertion(Ground.outer.items = [json{value:1}, json{value:2}]).

test(high_priority_may_repeat_when_uniquely_highest) :-
    issue(10, high, High),
    issue(11, normal, Normal),
    state(10, State),
    select_queue([Normal, High], State, Decision),
    assertion(Decision.action == "run"),
    assertion(Decision.issue_number =:= 10),
    assertion(Decision.priority == high),
    assertion(Decision.repeat_allowed == true).

test(high_priority_prefers_same_rank_alternative_before_repeat) :-
    issue(10, high, First),
    issue(11, high, Second),
    issue(12, normal, Normal),
    state(10, State),
    select_queue([Normal, First, Second], State, Decision),
    assertion(Decision.action == "run"),
    assertion(Decision.issue_number =:= 11),
    assertion(Decision.priority == high).

test(normal_priority_does_not_repeat_when_alternative_exists) :-
    issue(10, normal, First),
    issue(11, normal, Second),
    state(10, State),
    select_queue([First, Second], State, Decision),
    assertion(Decision.action == "run"),
    assertion(Decision.issue_number =:= 11),
    assertion(Decision.repeat_allowed == false).

test(single_normal_repeat_idles) :-
    issue(10, normal, Only),
    state(10, State),
    select_queue([Only], State, Decision),
    assertion(Decision.action == "idle").

test(priority_order_is_urgent_high_normal_low) :-
    issue(1, low, Low),
    issue(2, normal, Normal),
    issue(3, high, High),
    issue(4, urgent, Urgent),
    state(null, State),
    select_queue([Low, Normal, High, Urgent], State, Decision),
    assertion(Decision.issue_number =:= 4),
    assertion(Decision.priority == urgent).

test(markdown_priority_markup_is_accepted) :-
    Issue = _{
        number:12,
        title:"marked",
        url:"https://example.invalid/issues/12",
        body:"## Priority\n\n**high**\n"
    },
    state(null, State),
    select_queue([Issue], State, Decision),
    assertion(Decision.priority == high).

test(missing_priority_defaults_to_normal) :-
    Issue = _{
        number:13,
        title:"default",
        url:"https://example.invalid/issues/13",
        body:"no priority heading"
    },
    state(null, State),
    select_queue([Issue], State, Decision),
    assertion(Decision.priority == normal).

:- end_tests(auto_dig_prolog_actor).

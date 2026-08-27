:- module(auto_dig_safe_log,
          [ safe_log/3,
            safe_text/2
          ]).

/** <module> Emission-boundary logging for Auto-Dig

All diagnostic text passes through this module immediately before it is
written to stderr. There is intentionally no post-hoc log redaction stage.
Known credential values are removed by exact value and common credential
syntax is scrubbed before the formatted line leaves the process.
*/

safe_log(Tag, Format, Args) :-
    format(string(Raw), Format, Args),
    safe_text(Raw, Safe),
    get_time(Now),
    format_time(string(Timestamp), '%FT%TZ', Now, [utc(true)]),
    format(user_error, '[~w] ~s ~s~n', [Tag, Timestamp, Safe]),
    flush_output(user_error).

safe_text(Text0, Safe) :-
    text_string(Text0, Text),
    redact_known_secrets(Text, KnownSafe),
    redact_markers(KnownSafe,
                   [ "authorization: bearer ",
                     "authorization:",
                     "authorization=",
                     "api_key=",
                     "api-key=",
                     "apikey=",
                     "access_token=",
                     "access-token=",
                     "refresh_token=",
                     "refresh-token=",
                     "password=",
                     "passwd=",
                     "secret=",
                     "credential=",
                     "?key=",
                     "&key=",
                     "?token=",
                     "&token="
                   ],
                   MarkerSafe),
    redact_prefixes(MarkerSafe,
                    [ "github_pat_",
                      "ghp_",
                      "gho_",
                      "ghu_",
                      "ghs_",
                      "ghr_",
                      "sk-or-v1-"
                    ],
                    Safe).

text_string(Text, String) :-
    string(Text),
    !,
    String = Text.
text_string(Text, String) :-
    atom(Text),
    !,
    atom_string(Text, String).
text_string(Text, String) :-
    term_string(Text, String, [quoted(true)]).

secret_env('OPENROUTER_API_KEY').
secret_env('BRAVE_API_KEY').
secret_env('PROLOG_RLM_BUG_TOKEN').
secret_env('BUG_TOKEN').
secret_env('GH_TOKEN').
secret_env('GITHUB_TOKEN').

redact_known_secrets(Text0, Text) :-
    findall(Value,
            ( secret_env(Name),
              getenv(Name, Value),
              Value \== '',
              string_length(Value, Length),
              Length >= 4
            ),
            Values0),
    sort(Values0, Values),
    foldl(replace_secret, Values, Text0, Text).

replace_secret(Secret, Text0, Text) :-
    replace_all(Text0, Secret, "[REDACTED]", Text).

replace_all(Text0, Needle, Replacement, Text) :-
    (   sub_string(Text0, Before, Length, After, Needle)
    ->  sub_string(Text0, 0, Before, _, Prefix),
        Start is Before + Length,
        sub_string(Text0, Start, After, 0, Suffix),
        string_concat(Prefix, Replacement, Head),
        string_concat(Head, Suffix, Next),
        replace_all(Next, Needle, Replacement, Text)
    ;   Text = Text0
    ).

redact_markers(Text, [], Text).
redact_markers(Text0, [Marker|Markers], Text) :-
    redact_marker(Text0, Marker, Text1),
    redact_markers(Text1, Markers, Text).

redact_marker(Text0, Marker, Text) :-
    string_lower(Text0, Lower),
    string_lower(Marker, MarkerLower),
    (   sub_string(Lower, Before, Length, After, MarkerLower)
    ->  sub_string(Text0, 0, Before, _, Prefix),
        Start is Before + Length,
        sub_string(Text0, Start, After, 0, Tail),
        split_credential_tail(Tail, Rest),
        string_concat(Prefix, Marker, Head0),
        string_concat(Head0, "[REDACTED]", Head),
        string_concat(Head, Rest, Next),
        redact_marker(Next, Marker, Text)
    ;   Text = Text0
    ).

redact_prefixes(Text, [], Text).
redact_prefixes(Text0, [Prefix|Prefixes], Text) :-
    redact_prefix(Text0, Prefix, Text1),
    redact_prefixes(Text1, Prefixes, Text).

redact_prefix(Text0, Prefix, Text) :-
    string_lower(Text0, Lower),
    string_lower(Prefix, PrefixLower),
    (   sub_string(Lower, Before, Length, After, PrefixLower)
    ->  sub_string(Text0, 0, Before, _, Head),
        Start is Before + Length,
        sub_string(Text0, Start, After, 0, Tail),
        split_credential_tail(Tail, Rest),
        string_concat(Head, "[REDACTED]", NextHead),
        string_concat(NextHead, Rest, Next),
        redact_prefix(Next, Prefix, Text)
    ;   Text = Text0
    ).

split_credential_tail(Tail, Rest) :-
    string_codes(Tail, Codes),
    drop_secret_codes(Codes, RestCodes),
    string_codes(Rest, RestCodes).

drop_secret_codes([], []).
drop_secret_codes([Code|Codes], [Code|Codes]) :-
    credential_delimiter(Code),
    !.
drop_secret_codes([_|Codes], Rest) :-
    drop_secret_codes(Codes, Rest).

credential_delimiter(0' ).
credential_delimiter(0'\t).
credential_delimiter(0'\n).
credential_delimiter(0'\r).
credential_delimiter(0',).
credential_delimiter(0';).
credential_delimiter(0']).
credential_delimiter(0'}).
credential_delimiter(0')).
credential_delimiter(0'&).

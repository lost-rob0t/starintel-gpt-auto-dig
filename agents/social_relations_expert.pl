:- module(social_relations_expert,
          [ clear_social_kb/0,
            load_starintel_jsonl/1,
            ingest_document/1,
            relation_assessment/3,
            association_candidate/4,
            bridge_candidate/4,
            suggested_followup/3,
            explain_relation/3,
            expert_version/1
          ]).

/** <module> Evidence-bound social relationship reasoning

This expert consumes StarIntel documents and produces explainable assessments
and generic association candidates. It never writes canonical StarIntel state.
Derived candidates are intentionally weaker than explicit source-backed
relations and always require review before promotion.
*/

:- use_module(library(http/json)).
:- use_module(library(readutil)).
:- use_module(library(lists)).

:- dynamic social_document/2.
:- dynamic social_relation/8.

expert_version('social-relations-expert.v1').

clear_social_kb :-
    retractall(social_document(_, _)),
    retractall(social_relation(_, _, _, _, _, _, _, _)).

load_starintel_jsonl(Path) :-
    setup_call_cleanup(
        open(Path, read, Stream, [encoding(utf8)]),
        load_starintel_stream(Stream),
        close(Stream)).

load_starintel_stream(Stream) :-
    read_line_to_string(Stream, Line),
    (   Line == end_of_file
    ->  true
    ;   (   Line == ""
        ->  true
        ;   atom_string(Atom, Line),
            atom_json_dict(Atom, Document, [value_string_as(atom)]),
            ingest_document(Document)
        ),
        load_starintel_stream(Stream)
    ).

ingest_document(Document) :-
    must_be(dict, Document),
    dict_required_atom(Document, '_id', Id),
    retractall(social_document(Id, _)),
    assertz(social_document(Id, Document)),
    retractall(social_relation(Id, _, _, _, _, _, _, _)),
    (   document_dtype(Document, relation)
    ->  index_relation(Document)
    ;   true
    ).

document_dtype(Document, DType) :-
    get_dict(dtype, Document, Raw),
    text_atom(Raw, DType).

index_relation(Document) :-
    dict_required_atom(Document, '_id', Id),
    get_dict(data, Document, Data),
    must_be(dict, Data),
    dict_required_atom(Data, subject, Subject),
    dict_required_atom(Data, predicate, Predicate),
    dict_required_atom(Data, object, Object),
    dict_default(Data, directed, true, Directed0),
    directed_value(Directed0, Directed),
    dict_default(Data, confidence, 0.5, Confidence0),
    confidence_value(Confidence0, Confidence),
    dict_default(Document, dataset, unknown, Dataset0),
    text_atom(Dataset0, Dataset),
    assertz(social_relation(Id,
                            Subject,
                            Predicate,
                            Object,
                            Directed,
                            Confidence,
                            Dataset,
                            Document)).

dict_required_atom(Dict, Key, Value) :-
    get_dict(Key, Dict, Raw),
    text_atom(Raw, Value).

dict_default(Dict, Key, Default, Value) :-
    ( get_dict(Key, Dict, Found) -> Value = Found ; Value = Default ).

text_atom(Value, Value) :-
    atom(Value),
    !.
text_atom(Value, Atom) :-
    string(Value),
    !,
    atom_string(Atom, Value).
text_atom(Value, Atom) :-
    number(Value),
    !,
    atom_number(Atom, Value).

directed_value(@(false), false) :- !.
directed_value(false, false) :- !.
directed_value(0, false) :- !.
directed_value(_, true).

confidence_value(Value, Confidence) :-
    number(Value),
    !,
    Confidence is max(0.0, min(1.0, float(Value))).
confidence_value(_, 0.5).

/*
 * Predicates eligible for social-structure scoring. Unknown predicates do not
 * silently acquire meaning: add them here only after their ontology semantics
 * are understood.
 */
predicate_weight(works_for, 0.90).
predicate_weight(worked_for, 0.75).
predicate_weight(employed_by, 0.90).
predicate_weight(board_member_of, 0.95).
predicate_weight(officer_of, 0.95).
predicate_weight(advises, 0.78).
predicate_weight(collaborates_with, 0.82).
predicate_weight(partnered_with, 0.82).
predicate_weight(communicates_with, 0.72).
predicate_weight(appears_with, 0.48).
predicate_weight(attended_with, 0.42).
predicate_weight(member_of, 0.68).
predicate_weight(follows, 0.28).
predicate_weight(mentions, 0.20).

/*
 * These may be recorded when explicit lawful evidence exists, but this expert
 * never derives them from proximity, common neighbors, embeddings, or weak
 * contextual signals.
 */
sensitive_predicate(family_of).
sensitive_predicate(parent_of).
sensitive_predicate(child_of).
sensitive_predicate(sibling_of).
sensitive_predicate(spouse_of).
sensitive_predicate(romantic_partner_of).
sensitive_predicate(sexual_partner_of).
sensitive_predicate(political_affiliation).
sensitive_predicate(religious_affiliation).
sensitive_predicate(religion).
sensitive_predicate(health_condition).
sensitive_predicate(medical_condition).
sensitive_predicate(sexual_orientation).
sensitive_predicate(race).
sensitive_predicate(ethnicity).
sensitive_predicate(union_member_of).
sensitive_predicate(criminal_status).

identity_predicate(same_as).
identity_predicate(account_of).
identity_predicate(controls_account).

usable_social_predicate(Predicate) :-
    predicate_weight(Predicate, _),
    \+ sensitive_predicate(Predicate),
    \+ identity_predicate(Predicate).

/*
 * Shared-context inference is intentionally narrower than direct scoring.
 * Membership alone is excluded because an organization can encode sensitive
 * political, religious, or labor-union affiliation.
 */
context_predicate(works_for).
context_predicate(worked_for).
context_predicate(employed_by).
context_predicate(board_member_of).
context_predicate(officer_of).
context_predicate(advises).
context_predicate(collaborates_with).
context_predicate(partnered_with).
context_predicate(communicates_with).
context_predicate(appears_with).
context_predicate(attended_with).

pair_relation(A,
              B,
              RelationId,
              Predicate,
              Confidence,
              Directed,
              Document) :-
    social_relation(RelationId,
                    Subject,
                    Predicate,
                    Object,
                    Directed,
                    Confidence,
                    _Dataset,
                    Document),
    usable_social_predicate(Predicate),
    (   A = Subject,
        B = Object
    ;   A = Object,
        B = Subject
    ),
    dif(A, B).

source_key(Source, Key) :-
    is_dict(Source),
    (   get_dict(url, Source, Raw)
    ->  text_atom(Raw, Key)
    ;   get_dict(publisher, Source, Raw)
    ->  text_atom(Raw, Key)
    ;   get_dict(title, Source, Raw)
    ->  text_atom(Raw, Key)
    ).

document_source_keys(Document, Keys) :-
    (   get_dict(sources, Document, Sources),
        is_list(Sources)
    ->  findall(Key,
                ( member(Source, Sources),
                  source_key(Source, Key)
                ),
                Raw),
        sort(Raw, Keys)
    ;   Keys = []
    ).

source_factor(0, 0.72) :- !.
source_factor(Count, Factor) :-
    Factor is min(1.0, 0.78 + (0.08 * Count)).

pair_signal(A, B, Signal) :-
    pair_relation(A,
                  B,
                  RelationId,
                  Predicate,
                  Confidence,
                  Directed,
                  Document),
    predicate_weight(Predicate, Weight),
    document_source_keys(Document, SourceKeys),
    length(SourceKeys, SourceCount),
    source_factor(SourceCount, SourceFactor),
    Contribution is Weight * Confidence * SourceFactor,
    Signal = _{ relation_id:RelationId,
                predicate:Predicate,
                confidence:Confidence,
                directed:Directed,
                weight:Weight,
                source_count:SourceCount,
                source_keys:SourceKeys,
                contribution:Contribution
              }.

signal_total(Signals, Total) :-
    findall(Value,
            ( member(Signal, Signals),
              get_dict(contribution, Signal, Value)
            ),
            Values),
    sum_list(Values, Total).

signal_predicates(Signals, Predicates) :-
    findall(Predicate,
            ( member(Signal, Signals),
              get_dict(predicate, Signal, Predicate)
            ),
            Raw),
    sort(Raw, Predicates).

signal_relation_ids(Signals, RelationIds) :-
    findall(RelationId,
            ( member(Signal, Signals),
              get_dict(relation_id, Signal, RelationId)
            ),
            Raw),
    sort(Raw, RelationIds).

signal_source_keys(Signals, SourceKeys) :-
    findall(Key,
            ( member(Signal, Signals),
              get_dict(source_keys, Signal, Keys),
              member(Key, Keys)
            ),
            Raw),
    sort(Raw, SourceKeys).

directed_usable_relation(A, B) :-
    social_relation(_,
                    A,
                    Predicate,
                    B,
                    true,
                    _,
                    _,
                    _),
    usable_social_predicate(Predicate).

reciprocity(A, B, true) :-
    directed_usable_relation(A, B),
    directed_usable_relation(B, A),
    !.
reciprocity(_, _, false).

score_class(Score, strong_source_backed) :-
    Score >= 0.85,
    !.
score_class(Score, moderate_source_backed) :-
    Score >= 0.60,
    !.
score_class(_, weak_or_contextual).

relation_assessment(A, B, Assessment) :-
    findall(Signal, pair_signal(A, B, Signal), Signals),
    Signals \= [],
    signal_total(Signals, Total),
    Score is min(0.99, 1.0 - exp(-Total)),
    score_class(Score, Class),
    signal_predicates(Signals, Predicates),
    signal_relation_ids(Signals, RelationIds),
    signal_source_keys(Signals, SourceKeys),
    length(Predicates, Multiplexity),
    length(SourceKeys, IndependentSourceCount),
    reciprocity(A, B, Reciprocal),
    expert_version(Expert),
    Assessment = _{ expert:Expert,
                    subject:A,
                    object:B,
                    score:Score,
                    class:Class,
                    predicates:Predicates,
                    multiplexity:Multiplexity,
                    independent_source_count:IndependentSourceCount,
                    reciprocal:Reciprocal,
                    supporting_relation_ids:RelationIds,
                    signals:Signals,
                    derived:false,
                    requires_review:false
                  }.

context_edge(A, Neighbor, Predicate, RelationId) :-
    pair_relation(A,
                  Neighbor,
                  RelationId,
                  Predicate,
                  _Confidence,
                  _Directed,
                  _Document),
    context_predicate(Predicate),
    dif(A, Neighbor).

common_context_neighbor(A, B, Neighbor) :-
    context_edge(A, Neighbor, _PredicateA, RelationA),
    context_edge(B, Neighbor, _PredicateB, RelationB),
    RelationA \== RelationB,
    dif(A, B),
    dif(A, Neighbor),
    dif(B, Neighbor).

direct_pair_exists(A, B) :-
    pair_signal(A, B, _),
    !.

association_candidate(A, B, Score, Reasons) :-
    dif(A, B),
    \+ direct_pair_exists(A, B),
    findall(Neighbor,
            common_context_neighbor(A, B, Neighbor),
            NeighborRaw),
    sort(NeighborRaw, Neighbors),
    length(Neighbors, Count),
    Count >= 2,
    findall(RelationId,
            ( member(Neighbor, Neighbors),
              ( context_edge(A, Neighbor, _, RelationId)
              ; context_edge(B, Neighbor, _, RelationId)
              )
            ),
            RelationRaw),
    sort(RelationRaw, RelationIds),
    Score is min(0.72, 0.30 + (0.12 * Count)),
    expert_version(Expert),
    Reasons = _{ expert:Expert,
                 rule:shared_context_v1,
                 derived_predicate:associated_with,
                 common_neighbors:Neighbors,
                 common_neighbor_count:Count,
                 supporting_relation_ids:RelationIds,
                 derived:true,
                 requires_review:true,
                 confidence_cap:0.72
               }.

bridge_candidate(Node, Left, Right, Score) :-
    dif(Node, Left),
    dif(Node, Right),
    dif(Left, Right),
    relation_assessment(Node, Left, LeftAssessment),
    relation_assessment(Node, Right, RightAssessment),
    \+ direct_pair_exists(Left, Right),
    get_dict(score, LeftAssessment, LeftScore),
    get_dict(score, RightAssessment, RightScore),
    Score is 0.90 * min(LeftScore, RightScore).

suggested_followup(A, B, Followup) :-
    relation_assessment(A, B, Assessment),
    get_dict(class, Assessment, Class),
    Class == weak_or_contextual,
    get_dict(supporting_relation_ids, Assessment, RelationIds),
    Followup = _{ kind:investigation_target,
                  priority:normal,
                  question:verify_relationship_with_independent_public_evidence,
                  subject:A,
                  object:B,
                  seed_ids:RelationIds,
                  desired_evidence:[primary_source,
                                    independent_secondary_source],
                  avoid:[private_contact_data,
                         sensitive_trait_inference]
                }.
suggested_followup(A, B, Followup) :-
    association_candidate(A, B, _Score, Reasons),
    get_dict(supporting_relation_ids, Reasons, RelationIds),
    Followup = _{ kind:investigation_target,
                  priority:normal,
                  question:test_shared_context_association,
                  subject:A,
                  object:B,
                  seed_ids:RelationIds,
                  desired_evidence:[direct_public_interaction,
                                    independent_source],
                  avoid:[identity_guessing,
                         sensitive_relationship_inference]
                }.

explain_relation(A, B, Explanation) :-
    relation_assessment(A, B, Assessment),
    !,
    Explanation = _{kind:explicit_evidence_aggregation,
                    assessment:Assessment}.
explain_relation(A, B, Explanation) :-
    association_candidate(A, B, Score, Reasons),
    Explanation = _{kind:derived_association_candidate,
                    score:Score,
                    reasons:Reasons}.

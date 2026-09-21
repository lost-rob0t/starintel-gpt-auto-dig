:- begin_tests(social_relations_expert).

:- use_module(social_relations_expert).

relation_doc(Id, Subject, Predicate, Object, Confidence, Publisher, Document) :-
    Document = _{ '_id':Id,
                  dtype:relation,
                  dataset:test_social,
                  sources:[_{publisher:Publisher,
                             url:Id}],
                  data:_{subject:Subject,
                         predicate:Predicate,
                         object:Object,
                         directed:true,
                         confidence:Confidence}
                }.

setup_direct :-
    clear_social_kb,
    relation_doc(r1, alice, works_for, org_x, 0.95, source_a, D1),
    relation_doc(r2, alice, advises, org_x, 0.90, source_b, D2),
    ingest_document(D1),
    ingest_document(D2).

setup_shared_context :-
    clear_social_kb,
    relation_doc(r1, alice, works_for, org_x, 0.95, source_a, D1),
    relation_doc(r2, bob, works_for, org_x, 0.95, source_b, D2),
    relation_doc(r3, alice, collaborates_with, project_y, 0.90, source_c, D3),
    relation_doc(r4, bob, collaborates_with, project_y, 0.90, source_d, D4),
    maplist(ingest_document, [D1,D2,D3,D4]).

test(direct_assessment_is_explainable,
     [setup(setup_direct)]) :-
    relation_assessment(alice, org_x, Assessment),
    get_dict(score, Assessment, Score),
    get_dict(multiplexity, Assessment, 2),
    get_dict(independent_source_count, Assessment, 2),
    get_dict(supporting_relation_ids, Assessment, RelationIds),
    assertion(Score > 0.70),
    assertion(RelationIds == [r1,r2]).

test(shared_context_candidate_is_review_only,
     [setup(setup_shared_context)]) :-
    association_candidate(alice, bob, Score, Reasons),
    get_dict(derived_predicate, Reasons, associated_with),
    get_dict(common_neighbor_count, Reasons, 2),
    get_dict(requires_review, Reasons, true),
    assertion(Score =< 0.72).

test(sensitive_predicate_does_not_feed_generic_scoring) :-
    clear_social_kb,
    relation_doc(r1, alice, political_affiliation, org_p, 1.0, source_a, Doc),
    ingest_document(Doc),
    assertion(\+ relation_assessment(alice, org_p, _)),
    assertion(\+ association_candidate(alice, org_p, _, _)).

test(proximity_does_not_become_identity) :-
    setup_shared_context,
    association_candidate(alice, bob, _Score, Reasons),
    get_dict(derived_predicate, Reasons, Predicate),
    assertion(Predicate == associated_with),
    assertion(Predicate \== same_as),
    assertion(Predicate \== account_of).

:- end_tests(social_relations_expert).

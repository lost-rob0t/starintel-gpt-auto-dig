% Durable policy for social-relations research.
% Loaded by .prolog/kb/index.pl.

:- multifile invariant/2, method/2, tooling/3.

invariant(social_relations_canonical_authority,
    "The social-relations expert is a reasoning projection only. It may emit
assessments, explanations, and proposed generic association records, but it
never writes canonical StarIntel documents directly.").

invariant(social_relations_evidence_boundary,
    "Keep explicit source-backed relations distinct from derived association
candidates. Common-neighbor, graph-centrality, co-occurrence, embedding, or LLM
signals may justify an investigation target; they do not establish a hidden
real-world relationship by themselves.").

invariant(social_relations_sensitive_derivation_ban,
    "Never derive family, romantic/sexual, political, religious, health,
race/ethnicity, union, criminal-status, or account-identity relationships from
graph proximity or weak contextual evidence. Explicit lawful source material
may be represented separately with provenance, but inference does not promote
those predicates.").

invariant(social_relations_public_or_authorized_sources,
    "Research must stay within public or operator-authorized evidence. Do not
turn relation mining into collection of private addresses, private contacts,
credentials, or other unnecessary personal data.").

method(social_relations_assessment,
    "Aggregate multiple typed relation documents using ontology-specific
weights, source independence, multiplexity, and reciprocity. Return supporting
relation IDs and every scoring signal so the assessment is reproducible.").

method(social_relations_candidate_generation,
    "Generate only generic associated_with candidates from at least two
non-sensitive shared contexts. Cap derived confidence, mark requires_review,
and create a follow-up investigation target when direct evidence is missing.").

tooling(social_relations_expert,
    'agents/social_relations_expert.pl',
    "SWI-Prolog expert for evidence aggregation, shared-context candidates,
bridge detection, follow-up generation, and explanations.").

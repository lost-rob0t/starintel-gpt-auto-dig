% Durable StarIntel Auto-Dig operational knowledge.
% Load with: swipl -q -s .prolog/kb/index.pl -g halt
:- multifile root_cause/3, invariant/2, method/2, tooling/3.
:- ensure_loaded('backlog-import.pl').
:- ensure_loaded('workflow-guard.pl').
:- ensure_loaded('spec-release.pl').
:- ensure_loaded('merge-gate-version-pin.pl').
:- ensure_loaded('dig-queue-cross-ties.pl').
:- ensure_loaded('dig-queue-cross-ties-w3.pl').
:- ensure_loaded('cross-tie-pass.pl').
:- ensure_loaded('social-relations-policy.pl').

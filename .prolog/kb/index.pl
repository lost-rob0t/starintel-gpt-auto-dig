% Durable StarIntel Auto-Dig operational knowledge.
% Load with: swipl -q -s .prolog/kb/index.pl -g halt
:- multifile root_cause/3, invariant/2, method/2.
:- ensure_loaded('backlog-import.pl').
:- ensure_loaded('workflow-guard.pl').

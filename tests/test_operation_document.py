from __future__ import annotations

import copy
import unittest

from starintel_doc import Document, ValidationError, document_schema, validate_document


class OperationDocumentTests(unittest.TestCase):
    def operation(self) -> dict:
        return Document.create(
            "operation",
            "election-2026",
            doc_id="starintel:operation:election-2026-comms",
            title="Election 2026 public communications research",
            data={
                "mission": "Map the approved public communications research surface.",
                "objectives": ["discover", "collect", "correlate", "report"],
                "status": "active",
                "in_scope": ["public communications"],
                "out_of_scope": ["private contact information"],
                "target_policy": {
                    "allowed_dtypes": ["target", "investigation-target"],
                    "allowed_roles": ["primary", "supporting", "derived"],
                },
                "targets": {
                    "primary": ["starintel:target:election-2026-comms"],
                    "supporting": [
                        "starintel:investigation-target:election-2026-discord-discovery"
                    ],
                    "derived": [],
                    "excluded": [],
                },
                "phases": [
                    {
                        "phase_id": "discovery",
                        "title": "Discovery",
                        "objective": "Discover valid public collection surfaces.",
                        "state": "completed",
                        "depends_on": [],
                        "dataset_binding_ids": ["raw"],
                        "required_capability_ids": [],
                        "completion_evidence": ["starintel:research-pass:discovery-1"],
                    },
                    {
                        "phase_id": "collection",
                        "title": "Collection",
                        "objective": "Collect approved public records.",
                        "state": "active",
                        "depends_on": ["discovery"],
                        "in_scope": ["public communications"],
                        "dataset_binding_ids": ["raw", "working"],
                        "required_capability_ids": ["discord-collector"],
                    },
                    {
                        "phase_id": "analysis",
                        "title": "Analysis",
                        "objective": "Correlate collected records.",
                        "state": "planned",
                        "depends_on": ["collection"],
                        "dataset_binding_ids": ["working", "analysis"],
                        "required_capability_ids": [],
                    },
                ],
                "datasets": [
                    {
                        "binding_id": "raw",
                        "dataset": "election-2026-raw",
                        "role": "collection",
                        "access": "append",
                        "phases": ["discovery", "collection"],
                        "purpose": "Immutable public-source collection.",
                    },
                    {
                        "binding_id": "working",
                        "dataset": "election-2026-working",
                        "role": "working",
                        "access": "read-write",
                        "phases": ["collection", "analysis"],
                        "purpose": "Normalized working set.",
                    },
                    {
                        "binding_id": "analysis",
                        "dataset": "election-2026-analysis",
                        "role": "derived",
                        "access": "append",
                        "phases": ["analysis"],
                        "purpose": "Derived analysis output.",
                    },
                ],
                "capability_gaps": [
                    {
                        "capability_id": "discord-collector",
                        "category": "actor",
                        "description": "Public Discord collection actor.",
                        "required_by": ["collection"],
                        "blocking": False,
                        "status": "available",
                        "capability_ref": "starintel:actor:discord-collector",
                    }
                ],
                "assignments": [
                    {
                        "assignment_id": "collector-a",
                        "agent_id": "agent:auto-dig",
                        "phase_ids": ["collection"],
                        "role": "collector",
                        "status": "active",
                    }
                ],
                "post_actions": [
                    {
                        "action_id": "report",
                        "action_type": "generate-report",
                        "dataset_binding_ids": ["analysis"],
                        "status": "planned",
                        "config": {"format": "org"},
                    }
                ],
            },
        ).to_dict()

    def test_operation_is_canonical_dtype_with_action_schema_org_type(self) -> None:
        operation = self.operation()
        self.assertEqual(operation["dtype"], "operation")
        self.assertEqual(operation["schema_org"]["@type"], "Action")
        self.assertIn("operation", document_schema()["properties"]["dtype"]["enum"])

    def test_operation_can_reference_both_target_dtypes(self) -> None:
        operation = self.operation()
        targets = operation["data"]["targets"]
        self.assertTrue(targets["primary"][0].startswith("starintel:target:"))
        self.assertTrue(
            targets["supporting"][0].startswith("starintel:investigation-target:")
        )
        validate_document(operation)

    def test_unknown_phase_dependency_is_rejected(self) -> None:
        operation = self.operation()
        operation["data"]["phases"][1]["depends_on"] = ["does-not-exist"]
        with self.assertRaisesRegex(ValidationError, "unknown reference"):
            validate_document(operation)

    def test_phase_dependency_cycle_is_rejected(self) -> None:
        operation = self.operation()
        operation["data"]["phases"][0]["state"] = "planned"
        operation["data"]["phases"][0]["completion_evidence"] = []
        operation["data"]["phases"][0]["depends_on"] = ["analysis"]
        with self.assertRaisesRegex(ValidationError, "dependency cycle"):
            validate_document(operation)

    def test_operation_scope_overrides_phase_scope(self) -> None:
        operation = self.operation()
        operation["data"]["phases"][1]["in_scope"].append(
            "private contact information"
        )
        with self.assertRaisesRegex(ValidationError, "out_of_scope overrides"):
            validate_document(operation)

    def test_completed_phase_requires_completion_evidence(self) -> None:
        operation = self.operation()
        operation["data"]["phases"][0]["completion_evidence"] = []
        with self.assertRaisesRegex(ValidationError, "requires evidence"):
            validate_document(operation)

    def test_completed_operation_requires_terminal_phases(self) -> None:
        operation = self.operation()
        operation["data"]["status"] = "completed"
        with self.assertRaisesRegex(ValidationError, "nonterminal phases"):
            validate_document(operation)

    def test_bad_dataset_and_capability_references_are_rejected(self) -> None:
        for key, value in (
            ("dataset_binding_ids", ["missing-dataset"]),
            ("required_capability_ids", ["missing-capability"]),
        ):
            operation = copy.deepcopy(self.operation())
            operation["data"]["phases"][1][key] = value
            with self.assertRaisesRegex(ValidationError, "unknown reference"):
                validate_document(operation)


if __name__ == "__main__":
    unittest.main()

"""Canonical contract, scope, chronology and graph integrity for public announcements."""
import importlib.util
import json
import unittest
from collections import Counter
from datetime import datetime
from pathlib import Path

from starintel_canonical import validate_document

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'digs/columbus/2026-10-11-public-event-announcements/starintel-documents.jsonl'


class PublicEventsPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [json.loads(line) for line in PATH.read_text().splitlines()]

    def test_canonical_contract_and_counts(self):
        self.assertEqual(Counter(d['dtype'] for d in self.rows),
                         {'url': 3, 'scope': 1, 'mission': 1, 'finding': 6, 'target': 6, 'mission-target': 6})
        for doc in self.rows:
            validate_document(doc)
            self.assertEqual(doc['schemaVersion'], '0.10.1')
            self.assertNotIn('confidence', doc)
            self.assertNotIn('_id', doc)

    def test_reference_closure_and_unique_ids(self):
        ids = {d['id']: d['dtype'] for d in self.rows}
        self.assertEqual(len(ids), len(self.rows))
        def walk(value):
            if isinstance(value, dict):
                if set(value) == {'schema', 'id'}:
                    self.assertEqual(ids[value['id']], value['schema'])
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(self.rows)

    def test_no_execution_and_bounded_scope(self):
        for doc in self.rows:
            if doc['dtype'] == 'target':
                self.assertEqual(doc['state'], 'paused')
                self.assertFalse(doc['options']['executionEnabled'])
                self.assertFalse(doc['recurring'])
                self.assertNotIn('schedule', doc)
                self.assertNotIn('nextRunAt', doc)
            elif doc['dtype'] == 'mission':
                self.assertEqual(doc['state'], 'draft')
                self.assertFalse(doc['constraints']['executionEnabled'])
            elif doc['dtype'] == 'mission-target':
                self.assertFalse(doc['options']['executionEnabled'])
        scope = next(d for d in self.rows if d['dtype'] == 'scope')
        self.assertIn('attendee identities or RSVPs', scope['outOfScope'])
        self.assertIn('private WiGLE data', scope['outOfScope'])

    def test_announced_times_and_uncertainty(self):
        findings = [d for d in self.rows if d['dtype'] == 'finding']
        for doc in findings:
            event = doc['extensions']['org.starintel.columbus.publicEvent']
            start, end = (datetime.fromisoformat(event[k]) for k in ('start', 'end'))
            self.assertLess(start, end)
            self.assertGreater(start.timestamp(), doc['observedAt'])
            self.assertEqual(start.utcoffset().total_seconds(), -14400)
            self.assertEqual(event['status'], 'announced')
            self.assertIsNone(doc['provenance']['publishedAt'])
        no_kings = next(d for d in findings if 'no-kings' in d['id'])
        self.assertIn('Atrium', no_kings['description'])
        self.assertIn('no verified precise route', no_kings['description'])
        relocated = next(d for d in findings if 'stop-the-cruelty' in d['id'])
        self.assertIn('relocation', relocated['description'])

    def test_reproducible_canonical_builder(self):
        spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build_columbus_public_events_packet.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.build(), self.rows)


if __name__ == '__main__':
    unittest.main()

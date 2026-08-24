"""
tests/test_use_aliquot.py

Unit tests for aliquot consumption reasons and tracking.
"""

import tempfile
import unittest
from pathlib import Path

import database.connection as db_conn
from database.schema import initialize_database
from services.protein_service import ProteinService


class UseAliquotTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        self.db_path = Path(tmp.name)
        db_conn.DATABASE_FILE = self.db_path
        initialize_database()
        self.service = ProteinService()

    def tearDown(self):
        self.db_path.unlink(missing_ok=True)

    def test_consume_with_experiment_reason(self):
        record_id, _ = self.service.repository.create_expressed(
            protein_name="TAU5",
            construct="pDEST17",
            variant="WT",
            media="LB",
            batch_no="B1",
            volume_per_falcon_l=0.5,
            buffer="PBS",
            date_stored="2026-08-24",
            notebook_ref="",
            total_falcons=5,
            notes="",
        )

        reason = "Experiment: Western blot for expression verification"
        self.service.consume_expressed(record_id, 2, reason=reason)

        history = self.service.list_usage_history("protein_expressed", record_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["quantity"], 2)
        self.assertEqual(history[0]["reason"], "Experiment: Western blot for expression verification")

    def test_consume_with_qc_reason(self):
        record_id, _ = self.service.repository.create_purified(
            protein_name="TAU5",
            construct="pDEST17",
            variant="WT",
            media="15N",
            batch_no="P1",
            concentration_um=100.0,
            volume_ul=50.0,
            buffer="PBS",
            date_stored="2026-08-24",
            notebook_ref="",
            total_aliquots=10,
            notes="",
        )

        self.service.consume_purified(record_id, 1, reason="QC")

        history = self.service.list_usage_history("protein_purified", record_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["quantity"], 1)
        self.assertEqual(history[0]["reason"], "QC")


if __name__ == "__main__":
    unittest.main()

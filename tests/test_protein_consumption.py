import tempfile
import unittest
from pathlib import Path

import database.connection as db_conn
from database.schema import initialize_database
from services.protein_service import ProteinService


class ProteinConsumptionTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        self.db_path = Path(tmp.name)
        db_conn.DATABASE_FILE = self.db_path
        initialize_database()
        self.service = ProteinService()

    def tearDown(self):
        self.db_path.unlink(missing_ok=True)

    def test_consume_expressed_updates_used_and_history(self):
        record_id, _ = self.service.repository.create_expressed(
            protein_name="Test Protein",
            construct="CT",
            variant="WT",
            media="LB",
            batch_no="B-1",
            volume_per_falcon_l=1.0,
            buffer="PBS",
            date_stored="2026-08-17",
            notebook_ref="NB-1",
            total_falcons=10,
            notes="",
        )

        self.service.consume_expressed(record_id, 3, reason="usage test")

        updated = self.service.repository.get_expressed(record_id)
        self.assertEqual(updated.used_falcons, 3)
        self.assertEqual(updated.remaining_falcons, 7)

        history = self.service.list_usage_history("protein_expressed", record_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["quantity"], 3)

        with self.assertRaises(ValueError):
            self.service.consume_expressed(record_id, 8, reason="too much")

    def test_consume_purified_updates_used_and_history(self):
        record_id, _ = self.service.repository.create_purified(
            protein_name="Purified Protein",
            construct="CT",
            variant="WT",
            media="15N",
            batch_no="P-1",
            concentration_um=50.0,
            volume_ul=100.0,
            buffer="Tris",
            date_stored="2026-08-17",
            notebook_ref="NB-2",
            total_aliquots=6,
            notes="",
        )

        self.service.consume_purified(record_id, 2, reason="purified usage")

        updated = self.service.repository.get_purified(record_id)
        self.assertEqual(updated.used_aliquots, 2)
        self.assertEqual(updated.remaining_aliquots, 4)

        history = self.service.list_usage_history("protein_purified", record_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["quantity"], 2)


if __name__ == "__main__":
    unittest.main()

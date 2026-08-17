"""
services/protein_service.py

Business logic for Proteins: validation, and the location
assignment flow (pick a box with enough free space, click a
starting position, and the required number of consecutive free
positions from there are reserved for the batch).
"""

from repositories.protein_repository import ProteinRepository
from services.storage_service import StorageService
from services.attachment_service import AttachmentService


class ProteinService:

    def __init__(self):
        self.repository = ProteinRepository()
        self.storage_service = StorageService()
        self.attachment_service = AttachmentService()

    # =====================================================
    # SEARCH / LIST
    # =====================================================

    def list_expressed(self):
        return self.repository.list_expressed()

    def search_expressed(self, text):
        return self.repository.search_expressed(text)

    def list_purified(self):
        return self.repository.list_purified()

    def search_purified(self, text):
        return self.repository.search_purified(text)

    def search_all(self, text):
        """Used by the Proteins module's top-level search ('Registro')."""
        return {
            "expressed": self.repository.search_expressed(text),
            "purified": self.repository.search_purified(text),
        }

    # =====================================================
    # LOCATION ASSIGNMENT
    # =====================================================

    def find_boxes_with_space(self, box_type, count):
        """
        Candidate boxes of the given type with at least `count`
        free positions. Consecutiveness is only guaranteed once a
        starting position is picked (see find_consecutive_run) --
        this is just a first-pass filter to narrow the list.
        """

        boxes = self.storage_service.list_boxes()
        candidates = []

        for box in boxes:
            if box.box_type != box_type:
                continue

            free = self.storage_service.list_free_positions(box.id)

            if len(free) >= count:
                candidates.append(box)

        return candidates

    def find_consecutive_run(self, box_id, start_position, count):
        """
        Starting at `start_position`, walks the box's positions in
        their natural order (A1, A2, ... A8, B1, ...) and returns
        the first `count` free ones. Raises ValueError if there
        isn't enough free room from that starting point.
        """

        all_positions = self.storage_service.list_positions(box_id)
        occupied = {
            o["position"]
            for o in self.storage_service.list_occupied_positions(
                box_id
            )
        }

        labels = [p.position for p in all_positions]

        if start_position not in labels:
            raise ValueError(
                f"'{start_position}' is not a valid position on "
                f"this box."
            )

        start_index = labels.index(start_position)
        run = []

        for label in labels[start_index:]:

            if label in occupied:
                break

            run.append(label)

            if len(run) == count:
                break

        if len(run) < count:
            raise ValueError(
                f"Not enough consecutive free positions starting "
                f"at {start_position} (found {len(run)}, need "
                f"{count}). Try a different starting position."
            )

        return run

    # =====================================================
    # REGISTER
    # =====================================================

    def register_expressed(
        self,
        *,
        protein_name,
        construct,
        variant,
        media,
        batch_no,
        volume_per_falcon_l,
        buffer,
        date_stored,
        notebook_ref,
        total_falcons,
        notes,
        box_id,
        start_position,
        uploaded_files=None,
    ):

        if not protein_name.strip():
            raise ValueError("Protein name cannot be empty.")

        if total_falcons < 1:
            raise ValueError("Number of Falcons must be at least 1.")

        box = self.storage_service.get_box(box_id)

        if box.box_type != "FALCON":
            raise ValueError(
                "Expressed proteins can only be stored in "
                "FALCON 50ml boxes."
            )

        run = self.find_consecutive_run(
            box_id, start_position, total_falcons
        )

        record_id, sample_id = self.repository.create_expressed(
            protein_name=protein_name.strip(),
            construct=construct,
            variant=variant,
            media=media,
            batch_no=batch_no,
            volume_per_falcon_l=volume_per_falcon_l,
            buffer=buffer,
            date_stored=date_stored,
            notebook_ref=notebook_ref,
            total_falcons=total_falcons,
            notes=notes,
        )

        self._create_containers(
            box_id, run, "PROTEIN_EXPRESSED", record_id, sample_id
        )
        self._save_attachments(
            "protein_expressed", record_id, uploaded_files
        )

        return record_id, sample_id

    def register_purified(
        self,
        *,
        protein_name,
        construct,
        variant,
        media,
        batch_no,
        concentration_um,
        volume_ul,
        buffer,
        date_stored,
        notebook_ref,
        total_aliquots,
        notes,
        box_id,
        start_position,
        uploaded_files=None,
    ):

        if not protein_name.strip():
            raise ValueError("Protein name cannot be empty.")

        if total_aliquots < 1:
            raise ValueError("Number of aliquots must be at least 1.")

        box = self.storage_service.get_box(box_id)

        if box.box_type != "EPPENDORF":
            raise ValueError(
                "Purified proteins can only be stored in "
                "EPPENDORF boxes."
            )

        run = self.find_consecutive_run(
            box_id, start_position, total_aliquots
        )

        record_id, sample_id = self.repository.create_purified(
            protein_name=protein_name.strip(),
            construct=construct,
            variant=variant,
            media=media,
            batch_no=batch_no,
            concentration_um=concentration_um,
            volume_ul=volume_ul,
            buffer=buffer,
            date_stored=date_stored,
            notebook_ref=notebook_ref,
            total_aliquots=total_aliquots,
            notes=notes,
        )

        self._create_containers(
            box_id, run, "PROTEIN_PURIFIED", record_id, sample_id
        )
        self._save_attachments(
            "protein_purified", record_id, uploaded_files
        )

        return record_id, sample_id

    # =====================================================
    # INTERNAL HELPERS
    # =====================================================

    def _create_containers(
        self, box_id, position_labels, container_type, item_id,
        sample_id
    ):

        for i, position_label in enumerate(position_labels, start=1):

            position = self.storage_service.get_position_by_name(
                box_id, position_label
            )

            self.storage_service.create_container(
                position_id=position.id,
                container_type=container_type,
                item_id=item_id,
                label=f"{sample_id}-{i}",
                notes="",
            )

    def _save_attachments(self, owner_table, owner_id, uploaded_files):

        if not uploaded_files:
            return

        for uploaded_file in uploaded_files:
            self.attachment_service.save(
                owner_table, owner_id, uploaded_file
            )
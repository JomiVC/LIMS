"""
services/attachment_service.py

Saves uploaded files to disk (under storage/attachments/, per
config.py) and records them in the generic `attachments` table.
Reusable by any module (Proteins, DNA, Proteases, E.Coli strains).
"""

from pathlib import Path

from config import ATTACHMENTS_DIR
from repositories.attachment_repository import AttachmentRepository


class AttachmentService:

    def __init__(self):
        self.repository = AttachmentRepository()

    def save(self, owner_table: str, owner_id: int, uploaded_file) -> int:
        """
        `uploaded_file` is a Streamlit UploadedFile (from
        st.file_uploader). Saved under
        storage/attachments/<owner_table>/<owner_id>/<file_name>.
        """

        folder = Path(ATTACHMENTS_DIR) / owner_table / str(owner_id)
        folder.mkdir(parents=True, exist_ok=True)

        dest = folder / uploaded_file.name

        with open(dest, "wb") as f:
            f.write(uploaded_file.getbuffer())

        relative_path = str(
            dest.relative_to(Path(ATTACHMENTS_DIR).parent)
        )

        return self.repository.create(
            owner_table=owner_table,
            owner_id=owner_id,
            file_name=uploaded_file.name,
            file_path=relative_path,
        )

    def list_for(self, owner_table: str, owner_id: int):
        return self.repository.list_for(owner_table, owner_id)
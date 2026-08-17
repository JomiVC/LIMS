"""Reusable attachment download and preview widgets."""

from pathlib import Path

import streamlit as st

from config import ATTACHMENTS_DIR, BASE_DIR


_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
_TEXT_EXTENSIONS = {".csv", ".log", ".md", ".txt", ".tsv"}


def render_attachments(attachments, key_prefix):
    """Show downloadable attachments and previews for PDFs, images and text."""
    if not attachments:
        st.caption("No attachments for this sample.")
        return

    st.markdown("**Attachments:**")
    for attachment in attachments:
        relative_path = Path(attachment["file_path"])
        file_path = ATTACHMENTS_DIR.parent / relative_path
        if not file_path.exists():
            # Supports attachment records created by an older path format.
            file_path = BASE_DIR / relative_path
        file_name = attachment["file_name"]

        if not file_path.exists():
            st.caption(f"File not found: {file_name}")
            continue

        data = file_path.read_bytes()
        extension = file_path.suffix.lower()

        with st.expander(file_name):
            st.download_button(
                label="Download",
                data=data,
                file_name=file_name,
                key=f"{key_prefix}_download_{attachment['id']}",
            )

            if extension in _IMAGE_EXTENSIONS:
                st.image(data, caption=file_name, use_container_width=True)
            elif extension == ".pdf":
                st.pdf(data, height=650)
            elif extension in _TEXT_EXTENSIONS:
                st.code(data.decode("utf-8", errors="replace"), language=None)
            else:
                st.caption("Preview is not available for this file type. Download it to open it.")

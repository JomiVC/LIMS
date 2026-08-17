"""
pages/proteins.py

Proteins module.

Structure:
    (search bar, searches across expressed + purified)
    Registro          -- global search results
    Expressed proteins -- search scoped to expressed + register new
    Purified proteins  -- search scoped to purified + register new
    Proteases          -- pending (guidelines not defined yet)

Assumption made here (flag if wrong): "Registro" is a read-only
cross-type search view; the registration forms live inside their
own "Expressed proteins" / "Purified proteins" tabs.
"""

import streamlit as st

from services.protein_service import ProteinService
from ui.box_grid import render_box_grid


st.set_page_config(page_title="LIMS - Proteins", page_icon="🧫")

protein_service = ProteinService()

st.title("🧫 Proteins")

query = st.text_input("Search", key="proteins_search_query")

tab_registro, tab_expressed, tab_purified, tab_proteases = st.tabs(
    ["Registro", "Expressed proteins", "Purified proteins", "Proteases"]
)


# ==========================================================
# REGISTRO (global search)
# ==========================================================

with tab_registro:

    if not query:
        st.caption("Type above to search across all protein records.")

    else:
        results = protein_service.search_all(query)

        if not results["expressed"] and not results["purified"]:
            st.info("No matching records found.")

        else:
            for record in results["expressed"]:
                st.markdown(
                    f"**{record.sample_id}** — {record.protein_name} "
                    f"(Expressed, {record.total_falcons} Falcons)"
                )

            for record in results["purified"]:
                st.markdown(
                    f"**{record.sample_id}** — {record.protein_name} "
                    f"(Purified, {record.total_aliquots} Aliquots)"
                )


# ==========================================================
# SHARED: location picker (box with space -> click start position)
# ==========================================================

def _location_picker(box_type, count, key_prefix):
    """
    Renders box selection + selectable grid for picking a starting
    position. Returns (box_id, start_position) once both are
    chosen, or (None, None) otherwise.
    """

    if count < 1:
        st.caption("Enter a quantity above to choose a location.")
        return None, None

    boxes = protein_service.find_boxes_with_space(box_type, count)

    if not boxes:
        st.warning(
            f"No {box_type} box currently has {count} free "
            f"position(s). Register a new box in Storage first."
        )
        return None, None

    box_options = {b.id: b.box_name for b in boxes}

    box_id = st.selectbox(
        "Box",
        options=list(box_options.keys()),
        format_func=lambda bid: box_options[bid],
        key=f"{key_prefix}_box_select",
    )

    box = next(b for b in boxes if b.id == box_id)

    occupied = protein_service.storage_service.list_occupied_positions(
        box_id
    )

    start_position = render_box_grid(
        box, occupied, selectable=True, key_prefix=key_prefix
    )

    if start_position:
        st.session_state[f"{key_prefix}_start_position"] = start_position

    start_position = st.session_state.get(f"{key_prefix}_start_position")

    if not start_position:
        st.info("Click the starting position on the grid above.")
        return box_id, None

    try:
        run = protein_service.find_consecutive_run(
            box_id, start_position, count
        )
    except ValueError as e:
        st.error(str(e))
        return box_id, None

    st.success(f"Will occupy: {', '.join(run)}")
    return box_id, start_position


# ==========================================================
# EXPRESSED PROTEINS
# ==========================================================

with tab_expressed:

    if query:
        st.subheader("Search results")

        for record in protein_service.search_expressed(query):
            st.markdown(
                f"**{record.sample_id}** — {record.protein_name} "
                f"({record.total_falcons} Falcons)"
            )

        st.divider()

    st.subheader("Register new")

    protein_name = st.text_input("Protein Name", key="exp_protein_name")
    construct = st.text_input("Construct", key="exp_construct")
    variant = st.text_input("Variant", key="exp_variant")
    media = st.text_input("Media", key="exp_media")
    batch_no = st.text_input("Batch No.", key="exp_batch_no")
    volume_per_falcon_l = st.number_input(
        "Vol./Falcon (L)", min_value=0.0, step=0.1, key="exp_vol"
    )
    buffer = st.text_input("Buffer", key="exp_buffer")
    date_stored = st.date_input("Date Stored", key="exp_date")
    notebook_ref = st.text_input("Notebook Ref.", key="exp_notebook")
    total_falcons = st.number_input(
        "N. Falcons", min_value=1, step=1, value=1, key="exp_total"
    )
    notes = st.text_area("Notes", value="", key="exp_notes")

    uploaded_files = st.file_uploader(
        "Attachments (PDF, chromatograms, gels...)",
        accept_multiple_files=True,
        key="exp_files",
    )

    st.divider()
    st.subheader("Location")

    exp_box_id, exp_start = _location_picker(
        "FALCON", int(total_falcons), "exp_loc"
    )

    st.divider()

    if st.button("Register", key="exp_register_btn"):

        if not exp_box_id or not exp_start:
            st.error("Choose a box and starting position first.")

        else:
            try:
                record_id, sample_id = protein_service.register_expressed(
                    protein_name=protein_name,
                    construct=construct,
                    variant=variant,
                    media=media,
                    batch_no=batch_no,
                    volume_per_falcon_l=volume_per_falcon_l,
                    buffer=buffer,
                    date_stored=str(date_stored),
                    notebook_ref=notebook_ref,
                    total_falcons=int(total_falcons),
                    notes=notes,
                    box_id=exp_box_id,
                    start_position=exp_start,
                    uploaded_files=uploaded_files,
                )
            except ValueError as e:
                st.error(str(e))
            else:
                st.success(f"Registered as {sample_id}.")
                st.session_state.pop("exp_loc_start_position", None)
                st.rerun()


# ==========================================================
# PURIFIED PROTEINS
# ==========================================================

with tab_purified:

    if query:
        st.subheader("Search results")

        for record in protein_service.search_purified(query):
            st.markdown(
                f"**{record.sample_id}** — {record.protein_name} "
                f"({record.total_aliquots} Aliquots)"
            )

        st.divider()

    st.subheader("Register new")

    p_protein_name = st.text_input("Protein Name", key="pur_protein_name")
    p_construct = st.text_input("Construct", key="pur_construct")
    p_variant = st.text_input("Variant", key="pur_variant")
    p_media = st.text_input("Media", key="pur_media")
    p_batch_no = st.text_input("Batch No.", key="pur_batch_no")
    p_conc = st.number_input(
        "Conc. (µM)", min_value=0.0, step=0.1, key="pur_conc"
    )
    p_vol = st.number_input(
        "Vol. (µL)", min_value=0.0, step=1.0, key="pur_vol"
    )
    p_buffer = st.text_input("Buffer", key="pur_buffer")
    p_date = st.date_input("Date Stored", key="pur_date")
    p_notebook = st.text_input("Notebook Ref.", key="pur_notebook")
    p_total = st.number_input(
        "Total Aliquots", min_value=1, step=1, value=1, key="pur_total"
    )
    p_notes = st.text_area("Notes", value="", key="pur_notes")

    p_uploaded_files = st.file_uploader(
        "Attachments (PDF, chromatograms, gels...)",
        accept_multiple_files=True,
        key="pur_files",
    )

    st.divider()
    st.subheader("Location")

    pur_box_id, pur_start = _location_picker(
        "EPPENDORF", int(p_total), "pur_loc"
    )

    st.divider()

    if st.button("Register", key="pur_register_btn"):

        if not pur_box_id or not pur_start:
            st.error("Choose a box and starting position first.")

        else:
            try:
                record_id, sample_id = protein_service.register_purified(
                    protein_name=p_protein_name,
                    construct=p_construct,
                    variant=p_variant,
                    media=p_media,
                    batch_no=p_batch_no,
                    concentration_um=p_conc,
                    volume_ul=p_vol,
                    buffer=p_buffer,
                    date_stored=str(p_date),
                    notebook_ref=p_notebook,
                    total_aliquots=int(p_total),
                    notes=p_notes,
                    box_id=pur_box_id,
                    start_position=pur_start,
                    uploaded_files=p_uploaded_files,
                )
            except ValueError as e:
                st.error(str(e))
            else:
                st.success(f"Registered as {sample_id}.")
                st.session_state.pop("pur_loc_start_position", None)
                st.rerun()


# ==========================================================
# PROTEASES (pending -- guidelines not yet given for this tab)
# ==========================================================

with tab_proteases:

    st.info(
        "Proteases module pending -- guidelines for this tab "
        "haven't been specified yet."
    )
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
import os
import time
from pathlib import Path

import pandas as pd

from config import BASE_DIR
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
# SHARED: display attachments
# ==========================================================

def _display_attachments(owner_table, owner_id):
    """
    Display attachments for a protein record with download links.
    """
    if owner_table == "protein_expressed":
        attachments = protein_service.get_attachments_expressed(owner_id)
    else:
        attachments = protein_service.get_attachments_purified(owner_id)
    
    if attachments:
        st.markdown("**📎 Attachments:**")
        for att in attachments:
            # Convert relative path to absolute
            file_path = BASE_DIR / att["file_path"]
            if file_path.exists():
                with open(file_path, "rb") as f:
                    st.download_button(
                        label=f"📥 {att['file_name']}",
                        data=f.read(),
                        file_name=att['file_name'],
                        key=f"download_{att['id']}"
                    )
            else:
                st.caption(f"⚠️ {att['file_name']} (file not found at {file_path})")


def _protein_row_dict(record, is_expressed=True):
    """Convert a protein record into a flat row for a dataframe view."""
    total = record.total_falcons if is_expressed else record.total_aliquots
    used = record.used_falcons if is_expressed else record.used_aliquots
    remaining = record.remaining_falcons if is_expressed else record.remaining_aliquots

    row = {
        "Type": "Expressed protein" if is_expressed else "Purified protein",
        "Sample ID": record.sample_id,
        "Protein": record.protein_name,
        "Construct": record.construct or "—",
        "Variant": record.variant or "—",
        "Media": record.media or "—",
        "Batch": record.batch_no or "—",
        "Buffer": record.buffer or "—",
        "Date Stored": record.date_stored or "—",
        "Notebook Ref": record.notebook_ref or "—",
        "Total": total,
        "Used": used,
        "Remaining": remaining,
        "Notes": record.notes or "—",
    }

    if is_expressed:
        row["Vol/Falcon (L)"] = record.volume_per_falcon_l or "—"
    else:
        row["Conc. (µM)"] = record.concentration_um or "—"
        row["Vol. (µL)"] = record.volume_ul or "—"

    return row


def _display_protein_details(record, is_expressed=True):
    """
    Display all details of a protein record (expressed or purified).
    """
    total = record.total_falcons if is_expressed else record.total_aliquots
    used = record.used_falcons if is_expressed else record.used_aliquots
    remaining = record.remaining_falcons if is_expressed else record.remaining_aliquots

    cols = st.columns([2, 1])
    
    with cols[0]:
        st.markdown(f"**{record.sample_id}** — {record.protein_name}")
        
    with cols[1]:
        if is_expressed:
            st.caption(f"🔵 {remaining} remaining / {total} total")
        else:
            st.caption(f"🔵 {remaining} remaining / {total} total")
    
    # Display all details in an expandable section
    with st.expander("📋 View Details", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**🔨 Construct:** {record.construct or '—'}")
            st.write(f"**🔄 Variant:** {record.variant or '—'}")
            st.write(f"**🥛 Media:** {record.media or '—'}")
            st.write(f"**📦 Batch:** {record.batch_no or '—'}")
            st.write(f"**🧪 Buffer:** {record.buffer or '—'}")
            st.write(f"**📅 Date Stored:** {record.date_stored or '—'}")
        
        with col2:
            st.write(f"**📔 Notebook Ref:** {record.notebook_ref or '—'}")
            if is_expressed:
                st.write(f"**📊 Vol/Falcon (L):** {record.volume_per_falcon_l or '—'}")
            else:
                st.write(f"**📐 Concentration (µM):** {record.concentration_um or '—'}")
                st.write(f"**💧 Volume (µL):** {record.volume_ul or '—'}")
            st.write(f"**🔢 Total:** {total}")
            st.write(f"**🧮 Used:** {used}")
            st.write(f"**📦 Remaining:** {remaining}")
        
        if record.notes:
            st.write(f"**📝 Notes:** {record.notes}")

        st.divider()
        st.markdown("**🧪 Consumption / Use aliquot**")
        consume_prefix = f"{('exp' if is_expressed else 'pur')}_{record.id}_{record.sample_id.replace('-', '_')}"
        qty = st.number_input(
            "Qty to use",
            min_value=1,
            max_value=remaining if remaining > 0 else 1,
            step=1,
            value=1,
            key=f"{consume_prefix}_qty",
        )

        if st.button("Use aliquot", key=f"{consume_prefix}_btn"):
            try:
                if is_expressed:
                    protein_service.consume_expressed(record.id, int(qty), reason="manual use")
                else:
                    protein_service.consume_purified(record.id, int(qty), reason="manual use")
                st.success(f"✅ {qty} aliquot(s) used.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

        history = protein_service.list_usage_history(
            "protein_expressed" if is_expressed else "protein_purified",
            record.id,
        )
        if history:
            st.divider()
            st.markdown("**🕘 Usage history:**")
            for event in history[:5]:
                st.write(f"• {event['used_at'][:19]} — {event['quantity']} used ({event['reason']})")
        
        st.divider()
        _display_attachments(
            "protein_expressed" if is_expressed else "protein_purified",
            record.id
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
            filter_type = st.selectbox(
                "Filter by type",
                options=["All", "Expressed", "Purified"],
                key="protein_global_filter",
            )

            rows = []
            records = []
            if results["expressed"]:
                for record in results["expressed"]:
                    if filter_type in ("All", "Expressed"):
                        rows.append(_protein_row_dict(record, is_expressed=True))
                        records.append((True, record))

            if results["purified"]:
                for record in results["purified"]:
                    if filter_type in ("All", "Purified"):
                        rows.append(_protein_row_dict(record, is_expressed=False))
                        records.append((False, record))

            if not rows:
                st.info("No records match the selected filter.")
            else:
                df = pd.DataFrame(rows)
                selected = st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    selection_mode="single-row",
                    on_select="rerun",
                    key="protein_global_table",
                )

                if selected and selected.selection.rows:
                    record_tuple = records[selected.selection.rows[0]]
                    st.divider()
                    _display_protein_details(record_tuple[1], is_expressed=record_tuple[0])


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
        records = protein_service.search_expressed(query)
        if records:
            df = pd.DataFrame([
                _protein_row_dict(record, is_expressed=True)
                for record in records
            ])
            selected = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key="expressed_table",
            )
            if selected and selected.selection.rows:
                st.divider()
                _display_protein_details(records[selected.selection.rows[0]], is_expressed=True)
        else:
            st.info("No matching expressed proteins found.")

    st.subheader("Register new")

    protein_name = st.text_input("Protein Name", key="exp_protein_name")
    construct = st.text_input("Construct", key="exp_construct")
    variant = st.text_input("Variant", key="exp_variant")
    media = st.selectbox("Media", options=["LB", "15N", "15N13C"], key="exp_media")
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
                st.success(f"✅ Registered as {sample_id}.")
                if uploaded_files:
                    st.info(f"📎 {len(uploaded_files)} file(s) attached and saved.")
                    with st.expander("View attached files"):
                        _display_attachments("protein_expressed", record_id)
                st.session_state.pop("exp_loc_start_position", None)
                time.sleep(1.5)
                st.rerun()


# ==========================================================
# PURIFIED PROTEINS
# ==========================================================

with tab_purified:

    if query:
        st.subheader("Search results")
        records = protein_service.search_purified(query)
        if records:
            df = pd.DataFrame([
                _protein_row_dict(record, is_expressed=False)
                for record in records
            ])
            selected = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key="purified_table",
            )
            if selected and selected.selection.rows:
                st.divider()
                _display_protein_details(records[selected.selection.rows[0]], is_expressed=False)
        else:
            st.info("No matching purified proteins found.")

    st.subheader("Register new")

    p_protein_name = st.text_input("Protein Name", key="pur_protein_name")
    p_construct = st.text_input("Construct", key="pur_construct")
    p_variant = st.text_input("Variant", key="pur_variant")
    p_media = st.selectbox("Media", options=["LB", "15N", "15N13C"], key="pur_media")
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
                st.success(f"✅ Registered as {sample_id}.")
                if p_uploaded_files:
                    st.info(f"📎 {len(p_uploaded_files)} file(s) attached and saved.")
                    with st.expander("View attached files"):
                        _display_attachments("protein_purified", record_id)
                st.session_state.pop("pur_loc_start_position", None)
                time.sleep(1.5)
                st.rerun()


# ==========================================================
# PROTEASES (pending -- guidelines not yet given for this tab)
# ==========================================================

with tab_proteases:

    st.info(
        "Proteases module pending -- guidelines for this tab "
        "haven't been specified yet."
    )
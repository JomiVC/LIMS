"""
pages/storage.py

Storage module.

Structure:
    Samples
        - Search
    Boxes
        - Browse
        - Assign item (interim -- will move into each producing
          module's registration flow, e.g. Proteins/DNA/E.Coli,
          once those exist; kept here for now so the assignment
          feature stays testable)
    New equipment
        - Create Box
        - Create Rack
        - Create Freezer
"""

import streamlit as st
from collections import defaultdict
from pathlib import Path

import pandas as pd

from config import BASE_DIR
from services.storage_service import StorageService
from services.item_service import ItemService, CONTAINER_TYPE_LABELS
from services.protein_service import ProteinService
from ui.attachments import render_attachments
from ui.box_grid import render_box_grid
from ui.use_aliquot import render_use_aliquot_form
from ui.rack_grid import (
    render_rack_grid,
    get_rack_slot_combos,
    clear_active_selection,
)


st.set_page_config(page_title="LIMS - Storage", page_icon="📦")

# Streamlit reruns this script after every interaction. Clear stale
# selections only when arriving from another page; clearing them on every
# rerun would discard the box selection before its dialog can be rendered.
if st.session_state.get("_active_page_marker") != "storage":
    clear_active_selection("browse")
    st.session_state.pop("browse_selected_container", None)

st.session_state["_active_page_marker"] = "storage"

storage_service = StorageService()
item_service = ItemService()
protein_service = ProteinService()

st.title("📦 Storage")


def _protein_table_row(container_type, protein_record, location_text):
    """Return a flat row with all protein record fields for tabular search."""
    if container_type == "PROTEIN_EXPRESSED":
        row = {
            "Type": "Expressed protein",
            "Sample ID": protein_record.sample_id,
            "Protein": protein_record.protein_name,
            "Construct": protein_record.construct or "—",
            "Variant": protein_record.variant or "—",
            "Media": protein_record.media or "—",
            "Batch": protein_record.batch_no or "—",
            "Volume/Falcon (L)": protein_record.volume_per_falcon_l or "—",
            "Buffer": protein_record.buffer or "—",
            "Date Stored": protein_record.date_stored or "—",
            "Notebook Ref": protein_record.notebook_ref or "—",
            "Total": protein_record.total_falcons,
            "Used": protein_record.used_falcons,
            "Remaining": protein_record.remaining_falcons,
            "Notes": protein_record.notes or "—",
            "Location": location_text,
        }
    else:
        row = {
            "Type": "Purified protein",
            "Sample ID": protein_record.sample_id,
            "Protein": protein_record.protein_name,
            "Construct": protein_record.construct or "—",
            "Variant": protein_record.variant or "—",
            "Media": protein_record.media or "—",
            "Batch": protein_record.batch_no or "—",
            "Conc. (µM)": protein_record.concentration_um or "—",
            "Vol. (µL)": protein_record.volume_ul or "—",
            "Buffer": protein_record.buffer or "—",
            "Date Stored": protein_record.date_stored or "—",
            "Notebook Ref": protein_record.notebook_ref or "—",
            "Total": protein_record.total_aliquots,
            "Used": protein_record.used_aliquots,
            "Remaining": protein_record.remaining_aliquots,
            "Notes": protein_record.notes or "—",
            "Location": location_text,
        }
    return row


def _format_sample_tooltip(record):
    """
    Build the compact tooltip label shown on hover over an occupied
    grid position.

    Format: Sample ID | Protein Name | Construct | Variant | Media
    Any missing (None or empty) field is rendered as "-".
    """
    fields = [
        record.sample_id,
        record.protein_name,
        record.construct,
        record.variant,
        record.media,
    ]
    return " | ".join(field if field else "-" for field in fields)


def _display_storage_record_actions(record, container_type):
    """Show the same two actions for a selected storage row: attachments or aliquot use."""
    action = st.radio(
        "Action",
        options=["View attachments", "Use aliquot"],
        horizontal=True,
        key=f"storage_row_action_{container_type}_{record.id}",
    )

    owner_table = (
        "protein_expressed"
        if container_type == "PROTEIN_EXPRESSED"
        else "protein_purified"
    )

    if action == "View attachments":
        attachments = protein_service.get_attachments_expressed(record.id) if owner_table == "protein_expressed" else protein_service.get_attachments_purified(record.id)
        render_attachments(
            attachments,
            key_prefix=f"storage_row_{container_type}_{record.id}",
        )
        return
        if attachments:
            st.markdown("**📎 Attachments:**")
            for att in attachments:
                file_path = BASE_DIR / att["file_path"]
                if file_path.exists():
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"📥 {att['file_name']}",
                            data=f.read(),
                            file_name=att['file_name'],
                            key=f"storage_row_download_{att['id']}"
                        )
                else:
                    st.caption(f"⚠️ {att['file_name']} (file not found at {file_path})")
        else:
            st.caption("No attachments for this sample.")

    elif action == "Use aliquot":
        remaining = record.remaining_falcons if owner_table == "protein_expressed" else record.remaining_aliquots
        total = record.total_falcons if owner_table == "protein_expressed" else record.total_aliquots
        used = record.used_falcons if owner_table == "protein_expressed" else record.used_aliquots

        key_pfx = f"storage_row_{container_type}_{record.id}"
        qty, reason_text, is_confirmed = render_use_aliquot_form(key_pfx, remaining)

        if is_confirmed:
            try:
                if owner_table == "protein_expressed":
                    protein_service.consume_expressed(record.id, int(qty), reason=reason_text)
                else:
                    protein_service.consume_purified(record.id, int(qty), reason=reason_text)
                st.success(f"✅ {qty} aliquot(s) used.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

        st.caption(f"Total: {total} | Used: {used} | Remaining: {remaining}")


def _show_container_details(container_details):
    """
    Display detailed info about a container and its attachments.
    (Shown inline within the box dialog, not in a nested modal)
    """
    tooltip_label = container_details.get("tooltip_label")
    header_text = tooltip_label if tooltip_label else container_details['label']
    st.subheader(f"📋 {header_text}")

    if container_details['item_details']:
        row = {
            "Label": container_details['label'],
            "Type": container_details['container_type'],
            "Item": container_details['item_name'] or "—",
        }
        row.update(container_details['item_details'])
        st.dataframe(
            pd.DataFrame([row]),
            use_container_width=True,
            hide_index=True,
        )

    action = st.radio(
        "Action",
        options=["View attachments", "Use aliquot"],
        horizontal=True,
        key=f"storage_action_{container_details['container_id']}",
    )

    if action == "View attachments":
        render_attachments(
            container_details["attachments"],
            key_prefix=f"storage_container_{container_details['container_id']}",
        )
        return

    elif action == "Use aliquot" and container_details["container_type"] in {"PROTEIN_EXPRESSED", "PROTEIN_PURIFIED"}:
        item_id = container_details.get("item_id")
        owner_table = "protein_expressed" if container_details["container_type"] == "PROTEIN_EXPRESSED" else "protein_purified"
        if item_id:
            item_record = protein_service.repository.get_expressed(item_id) if owner_table == "protein_expressed" else protein_service.repository.get_purified(item_id)
            if item_record:
                remaining = item_record.remaining_falcons if owner_table == "protein_expressed" else item_record.remaining_aliquots
                total = item_record.total_falcons if owner_table == "protein_expressed" else item_record.total_aliquots
                used = item_record.used_falcons if owner_table == "protein_expressed" else item_record.used_aliquots

                key_pfx = f"storage_use_{container_details['container_id']}"
                qty, reason_text, is_confirmed = render_use_aliquot_form(key_pfx, remaining)

                if is_confirmed:
                    try:
                        if owner_table == "protein_expressed":
                            protein_service.consume_expressed(item_id, int(qty), reason=reason_text)
                        else:
                            protein_service.consume_purified(item_id, int(qty), reason=reason_text)
                        st.success(f"✅ {qty} aliquot(s) used.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

                st.caption(f"Total: {total} | Used: {used} | Remaining: {remaining}")

                history = protein_service.list_usage_history(owner_table, item_id)
                if history:
                    st.divider()
                    st.markdown("**🕘 Usage history:**")
                    for event in history[:5]:
                        st.write(f"• {event['used_at'][:19]} — {event['quantity']} used ({event['reason']})")


def show_box_dialog(box):
    """
    Opens the box's grid (plus notes and position counts) as a
    read-only modal dialog that overlays the rack grid, instead of
    rendering inline below it.

    Read-only by design: editing or deleting a box is done exclusively
    from "New equipment > Edit Equipment", not from Browse.
    """

    @st.dialog(f"Box: {box.box_name}", width="large")
    def _dialog():

        shelf_display = box.shelf or "—"
        st.write(f"**Slot:** {shelf_display} / {box.slot}")

        if box.notes:
            st.write(f"**Notes:** {box.notes}")

        free = storage_service.list_free_positions(box.id)
        occupied = storage_service.list_occupied_positions(box.id)

        st.write(
            f"**Positions:** {len(occupied)} occupied, "
            f"{len(free)} free"
        )

        st.divider()

        # Enrich occupied positions with item details
        enriched_data = []
        for occ in occupied:
            container_id = occ.get("container_id")
            if container_id:
                details = storage_service.get_container_details(container_id)
                if details:
                    if details.get("container_type") in {"PROTEIN_EXPRESSED", "PROTEIN_PURIFIED"}:
                        item_id = details.get("item_id")
                        record = None
                        if item_id:
                            record = (
                                protein_service.repository.get_expressed(item_id)
                                if details["container_type"] == "PROTEIN_EXPRESSED"
                                else protein_service.repository.get_purified(item_id)
                            )
                        details["tooltip_label"] = (
                            _format_sample_tooltip(record) if record else "-"
                        )
                    enriched_data.append(details)

        render_box_grid(box, occupied, key_prefix="browse", enriched_data=enriched_data)
        
        # Check if a container was clicked and show its details inline
        selected_container = st.session_state.get("browse_selected_container")
        
        if selected_container:
            st.divider()
            # Show the detail section inline within the dialog
            _show_container_details(selected_container)
            # Clear the selection so it doesn't reopen
            st.session_state.pop("browse_selected_container", None)

    _dialog()
    clear_active_selection("browse")


tab_samples, tab_boxes, tab_new_equipment = st.tabs(
    ["Samples", "Boxes", "New equipment"]
)


# ==========================================================
# SAMPLES
# ==========================================================

with tab_samples:

    st.subheader("Search")

    query = st.text_input(
        "Search by sample name",
        key="samples_search_query",
    )

    query_text = (query or "").strip()
    query_lower = query_text.lower()
    table_rows = []
    selected_records = []

    for container_type in CONTAINER_TYPE_LABELS:
        if container_type == "PROTEIN_EXPRESSED":
            records = (
                protein_service.repository.search_expressed(query_text)
                if query_text
                else protein_service.repository.list_expressed()
            )
            for record in records:
                location = storage_service.get_container_for_item(
                    container_type, record.id
                )
                location_text = (
                    f"{location['rack_name']} / {location['box_name']} "
                    f"/ {location['position']}"
                    if location
                    else "Not yet assigned to a location"
                )
                row = _protein_table_row(container_type, record, location_text)
                table_rows.append(row)
                selected_records.append(("PROTEIN_EXPRESSED", record, location_text))

        elif container_type == "PROTEIN_PURIFIED":
            records = (
                protein_service.repository.search_purified(query_text)
                if query_text
                else protein_service.repository.list_purified()
            )
            for record in records:
                location = storage_service.get_container_for_item(
                    container_type, record.id
                )
                location_text = (
                    f"{location['rack_name']} / {location['box_name']} "
                    f"/ {location['position']}"
                    if location
                    else "Not yet assigned to a location"
                )
                row = _protein_table_row(container_type, record, location_text)
                table_rows.append(row)
                selected_records.append(("PROTEIN_PURIFIED", record, location_text))

        else:
            for row in item_service.list_items(container_type):
                if query_text and query_lower not in row["name"].lower():
                    continue
                location = storage_service.get_container_for_item(
                    container_type, row["id"]
                )
                location_text = (
                    f"{location['rack_name']} / {location['box_name']} "
                    f"/ {location['position']}"
                    if location
                    else "Not yet assigned to a location"
                )
                table_rows.append({
                    "Type": CONTAINER_TYPE_LABELS[container_type],
                    "Sample ID": "—",
                    "Protein": row["name"],
                    "Construct": "—",
                    "Variant": "—",
                    "Media": "—",
                    "Batch": "—",
                    "Volume/Falcon (L)": "—",
                    "Conc. (µM)": "—",
                    "Vol. (µL)": "—",
                    "Buffer": "—",
                    "Date Stored": "—",
                    "Notebook Ref": "—",
                    "Total": "—",
                    "Used": "—",
                    "Remaining": "—",
                    "Notes": row.get("notes") or "—",
                    "Location": location_text,
                })
                selected_records.append((container_type, row, location_text))

    if not table_rows:
        st.info("No matching samples found.")

    else:
        df = pd.DataFrame(table_rows)
        selected = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="storage_search_table",
        )

        if selected and selected.selection.rows:
            idx = selected.selection.rows[0]
            container_type, record, location_text = selected_records[idx]
            st.divider()
            st.subheader(f"{record.sample_id if hasattr(record, 'sample_id') else record.get('Protein', 'Record')} — {record.protein_name if hasattr(record, 'protein_name') else record.get('Protein', 'Record')}")
            if hasattr(record, "protein_name"):
                _display_storage_record_actions(record, container_type)
            else:
                st.caption("No attachments or aliquot actions are available for this record type.")

    if not query_text:
        st.caption("Showing all records in the database.")


# ==========================================================
# BOXES
# ==========================================================

with tab_boxes:

    browse_tab, assign_tab = st.tabs(["Browse", "Assign item"])

    # ------------------------------------------------------
    # BROWSE
    # ------------------------------------------------------

    with browse_tab:

        freezers = storage_service.list_freezers()

        if not freezers:
            st.info("No freezers registered yet.")

        else:
            freezer_options = {f.id: f.name for f in freezers}

            if len(freezers) > 1:
                selected_freezer_id = st.selectbox(
                    "Freezer",
                    options=list(freezer_options.keys()),
                    format_func=lambda fid: freezer_options[fid],
                    key="browse_freezer_select",
                )
            else:
                selected_freezer_id = freezers[0].id

            all_racks = storage_service.list_racks()
            freezer_racks = [
                r for r in all_racks
                if r.freezer_id == selected_freezer_id
            ]

            all_boxes = storage_service.list_boxes()
            boxes_by_rack_id = defaultdict(list)
            for b in all_boxes:
                boxes_by_rack_id[b.rack_id].append(b)

            active = render_rack_grid(
                freezer_racks,
                key_prefix="browse",
                boxes_by_rack_id=boxes_by_rack_id,
            )

            if not active:
                st.info(
                    "Open a rack's dropdown above and pick a slot "
                    "to see its box."
                )

            else:
                active_rack_id, active_index = active

                active_rack = storage_service.get_rack(active_rack_id)
                combos = get_rack_slot_combos(active_rack)

                boxes_in_rack = boxes_by_rack_id.get(
                    active_rack_id, []
                )
                box_by_slot = {
                    (b.shelf, b.slot): b for b in boxes_in_rack
                }

                shelf, slot = combos[active_index]
                box = box_by_slot.get((shelf, slot))

                if box is None:
                    st.info(
                        "This slot is empty. Register a box here "
                        "from 'New equipment > Create Box'."
                    )

                else:
                    show_box_dialog(box)


    # ------------------------------------------------------
    # ASSIGN ITEM (interim)
    # ------------------------------------------------------

    with assign_tab:

        boxes = storage_service.list_boxes()

        if not boxes:
            st.warning(
                "No boxes registered yet. Register one in "
                "'New equipment' first."
            )

        else:
            box_options = {box.id: box.box_name for box in boxes}

            selected_box_id = st.selectbox(
                "Box",
                options=list(box_options.keys()),
                format_func=lambda bid: box_options[bid],
                key="assign_box_select",
            )

            selected_box = storage_service.get_box(selected_box_id)
            occupied = storage_service.list_occupied_positions(
                selected_box_id
            )

            clicked_position = render_box_grid(
                selected_box,
                occupied,
                selectable=True,
                key_prefix="assign",
            )

            if clicked_position:
                st.session_state["assign_selected_position"] = (
                    clicked_position
                )

            selected_position_label = st.session_state.get(
                "assign_selected_position"
            )

            if not selected_position_label:
                st.info(
                    "Click a free position on the grid to assign "
                    "an item."
                )

            else:
                position = storage_service.get_position_by_name(
                    selected_box_id, selected_position_label
                )

                if position is None:
                    st.error(
                        f"Position '{selected_position_label}' not "
                        f"found on this box."
                    )

                else:
                    st.divider()
                    st.subheader(
                        f"Assign item to {selected_position_label}"
                    )

                    container_type = st.selectbox(
                        "Item type",
                        options=list(CONTAINER_TYPE_LABELS.keys()),
                        format_func=lambda ct: (
                            CONTAINER_TYPE_LABELS[ct]
                        ),
                        key="assign_type_select",
                    )

                    existing_items = item_service.list_items(
                        container_type
                    )

                    if not existing_items:
                        st.info(
                            f"No {CONTAINER_TYPE_LABELS[container_type]} "
                            f"items registered yet. Register one in "
                            f"its own module first, then come back "
                            f"here to assign it a location."
                        )

                    else:
                        item_options = {
                            row["id"]: row["name"]
                            for row in existing_items
                        }

                        item_id = st.selectbox(
                            CONTAINER_TYPE_LABELS[container_type],
                            options=list(item_options.keys()),
                            format_func=lambda iid: (
                                item_options[iid]
                            ),
                            key="assign_existing_item_select",
                        )

                        with st.form(
                            "assign_container_form",
                            clear_on_submit=True,
                        ):

                            label = st.text_input("Container label")
                            container_notes = st.text_area(
                                "Container notes", value=""
                            )

                            submitted = st.form_submit_button("Save")

                            if submitted:

                                try:
                                    storage_service.create_container(
                                        position_id=position.id,
                                        container_type=container_type,
                                        item_id=item_id,
                                        label=label,
                                        notes=container_notes,
                                    )

                                except ValueError as e:
                                    st.error(str(e))

                                else:
                                    st.success(
                                        f"Assigned to "
                                        f"{selected_position_label} "
                                        f"in '{selected_box.box_name}'."
                                    )
                                    del st.session_state[
                                        "assign_selected_position"
                                    ]
                                    st.rerun()


# ==========================================================
# NEW EQUIPMENT
# ==========================================================

with tab_new_equipment:

    create_box_tab, create_rack_tab, create_freezer_tab = st.tabs(
        ["Create Box", "Create Rack", "Create Freezer"]
    )

    # ------------------------------------------------------
    # CREATE BOX
    # ------------------------------------------------------

    with create_box_tab:

        racks = storage_service.list_racks()

        if not racks:
            st.warning(
                "No racks created yet. Create a rack before "
                "registering a box."
            )

        else:
            rack_options = {rack.id: rack.rack_name for rack in racks}

            selected_rack_id = st.selectbox(
                "Rack",
                options=list(rack_options.keys()),
                format_func=lambda rid: rack_options[rid],
                key="create_box_rack_select",
            )

            config = storage_service.get_rack_configuration(
                selected_rack_id
            )

            BOX_TYPE_LABELS = {
                "EPPENDORF": "EPPENDORF",
                "FALCON_15": "FALCON 15ml",
                "FALCON": "FALCON 50ml",
            }

            with st.form("create_box_form", clear_on_submit=True):

                box_name = st.text_input("Box name")

                box_type = st.selectbox(
                    "Box type",
                    options=config["allowed_box_types"],
                    format_func=lambda bt: BOX_TYPE_LABELS[bt],
                )

                if config["has_shelf"]:
                    shelf = st.selectbox(
                        "Shelf", options=config["shelves"]
                    )
                else:
                    shelf = None
                    st.caption("This rack has no shelves.")

                slot = st.selectbox("Slot", options=config["slots"])

                owner = st.text_input("Owner")

                notes = st.text_area("Notes", value="")

                submitted = st.form_submit_button("Save")

                if submitted:

                    try:
                        box_id = storage_service.create_box(
                            box_name=box_name,
                            box_type=box_type,
                            owner=owner,
                            rack_id=selected_rack_id,
                            shelf=shelf,
                            slot=slot,
                            notes=notes,
                        )

                    except ValueError as e:
                        st.error(str(e))

                    else:
                        positions = storage_service.list_positions(
                            box_id
                        )

                        st.success(
                            f"Box '{box_name}' created (id={box_id}) "
                            f"with {len(positions)} positions."
                        )

    # ------------------------------------------------------
    # CREATE RACK
    # ------------------------------------------------------

    with create_rack_tab:

        freezers = storage_service.list_freezers()

        if not freezers:
            st.warning(
                "No freezers registered yet. Create one in "
                "'Create Freezer' first."
            )

        else:
            freezer_options = {f.id: f.name for f in freezers}

            with st.form("create_rack_form", clear_on_submit=True):

                rack_freezer_id = st.selectbox(
                    "Freezer",
                    options=list(freezer_options.keys()),
                    format_func=lambda fid: freezer_options[fid],
                    key="create_rack_freezer_select",
                )

                rack_name = st.text_input("Rack name")

                rack_type = st.selectbox(
                    "Rack type", options=["EPPENDORF", "FALCON"]
                )

                has_shelf = st.checkbox("Has shelves (Upper / Lower)")

                slot_count = st.number_input(
                    "Number of slots", min_value=1, value=5, step=1
                )

                rack_notes = st.text_area("Description", value="")

                if st.form_submit_button("Save"):

                    try:
                        storage_service.create_rack(
                            freezer_id=rack_freezer_id,
                            rack_name=rack_name,
                            rack_type=rack_type,
                            has_shelf=has_shelf,
                            slot_count=int(slot_count),
                            description=rack_notes,
                        )
                    except ValueError as e:
                        st.error(str(e))
                    else:
                        st.success(f"Rack '{rack_name}' created.")
                        st.rerun()

            st.divider()
            st.subheader("Existing racks")

            racks = storage_service.list_racks()

            if not racks:
                st.info("No racks registered yet.")

            else:
                for freezer in freezers:

                    freezer_racks = [
                        r for r in racks if r.freezer_id == freezer.id
                    ]

                    if not freezer_racks:
                        continue

                    st.markdown(f"**{freezer.name}**")

                    for rack in freezer_racks:
                        shelf_info = (
                            "with shelves"
                            if rack.has_shelf
                            else "no shelves"
                        )
                        st.caption(
                            f"{rack.rack_name} — {rack.rack_type} — "
                            f"{shelf_info} — {rack.slot_count} slots"
                        )

    # ------------------------------------------------------
    # CREATE FREEZER
    # ------------------------------------------------------

    with create_freezer_tab:

        with st.form("create_freezer_form", clear_on_submit=True):

            freezer_name = st.text_input("Name")

            freezer_temp = st.selectbox(
                "Temperature (°C)",
                options=[-20, -80],
                key="create_freezer_temp_select",
            )

            freezer_notes = st.text_area("Description", value="")

            if st.form_submit_button("Save"):

                try:
                    storage_service.create_freezer(
                        name=freezer_name,
                        temperature=freezer_temp,
                        description=freezer_notes,
                    )
                except ValueError as e:
                    st.error(str(e))
                else:
                    st.success(f"Freezer '{freezer_name}' created.")
                    st.rerun()

        st.divider()
        st.subheader("Existing freezers")

        freezers = storage_service.list_freezers()

        if not freezers:
            st.info("No freezers registered yet.")

        else:
            for freezer in freezers:
                with st.expander(
                    f"{freezer.name} ({freezer.temperature}°C)"
                ):
                    if freezer.description:
                        st.write(freezer.description)
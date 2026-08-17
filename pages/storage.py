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

from services.storage_service import StorageService
from services.item_service import ItemService, CONTAINER_TYPE_LABELS
from ui.box_grid import render_box_grid
from ui.rack_grid import (
    render_rack_grid,
    get_rack_slot_combos,
    clear_active_selection,
)


st.set_page_config(page_title="LIMS - Storage", page_icon="📦")

# Streamlit's session_state persists across page navigation, so a
# leftover "active" grid selection from a previous visit would
# reopen the box dialog immediately on arrival. Reset it only when
# we detect we've just navigated here from a different page (i.e.
# the marker left by the previously active page isn't "storage").
if st.session_state.get("_active_page_marker") != "storage":
    clear_active_selection("browse")

st.session_state["_active_page_marker"] = "storage"

storage_service = StorageService()
item_service = ItemService()

st.title("📦 Storage")


def show_box_dialog(box, all_racks):
    """
    Opens the box's grid (plus notes, position counts, edit and
    delete) as a modal dialog that overlays the rack grid, instead
    of rendering inline below it.
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

        render_box_grid(box, occupied, key_prefix="browse")

        st.divider()

        edit_tab, delete_tab = st.tabs(["✏️ Edit", "🗑️ Delete"])

        # --- EDIT ---
        with edit_tab:

            all_rack_options = {r.id: r.rack_name for r in all_racks}

            with st.form(f"edit_box_{box.id}"):

                new_rack_id = st.selectbox(
                    "Rack",
                    options=list(all_rack_options.keys()),
                    format_func=lambda rid: all_rack_options[rid],
                    index=list(all_rack_options.keys())
                        .index(box.rack_id)
                        if box.rack_id in all_rack_options
                        else 0,
                    key=f"edit_rack_{box.id}",
                )

                edit_config = storage_service.get_rack_configuration(
                    new_rack_id
                )

                if edit_config["has_shelf"]:
                    new_shelf = st.selectbox(
                        "Shelf",
                        options=edit_config["shelves"],
                        index=edit_config["shelves"]
                            .index(box.shelf)
                            if box.shelf in edit_config["shelves"]
                            else 0,
                        key=f"edit_shelf_{box.id}",
                    )
                else:
                    new_shelf = None

                new_slot = st.selectbox(
                    "Slot",
                    options=edit_config["slots"],
                    index=edit_config["slots"].index(box.slot)
                        if box.slot in edit_config["slots"]
                        else 0,
                    key=f"edit_slot_{box.id}",
                )

                new_owner = st.text_input(
                    "Owner",
                    value=box.owner or "",
                    key=f"edit_owner_{box.id}",
                )

                new_notes = st.text_area(
                    "Notes",
                    value=box.notes or "",
                    key=f"edit_notes_{box.id}",
                )

                save = st.form_submit_button("Save changes")

                if save:
                    try:
                        storage_service.update_box(
                            box_id=box.id,
                            rack_id=new_rack_id,
                            shelf=new_shelf,
                            slot=new_slot,
                            owner=new_owner,
                            notes=new_notes,
                        )
                    except ValueError as e:
                        st.error(str(e))
                    else:
                        st.success("Box updated.")
                        clear_active_selection("browse")
                        st.rerun()

        # --- DELETE ---
        with delete_tab:

            st.warning(
                "A box can only be deleted if all of its "
                "positions are free."
            )

            confirm = st.checkbox(
                f"I confirm I want to delete '{box.box_name}'",
                key=f"confirm_delete_{box.id}",
            )

            if st.button(
                "Delete box",
                key=f"delete_{box.id}",
                disabled=not confirm,
            ):
                try:
                    storage_service.delete_box(box.id)
                except ValueError as e:
                    st.error(str(e))
                else:
                    st.success(f"Box '{box.box_name}' deleted.")
                    clear_active_selection("browse")
                    st.rerun()

    _dialog()


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

    if query:

        query_lower = query.strip().lower()
        results = []

        for container_type in CONTAINER_TYPE_LABELS:

            for row in item_service.list_items(container_type):

                if query_lower in row["name"].lower():
                    results.append((container_type, row))

        if not results:
            st.info("No matching samples found.")

        else:
            for container_type, row in results:

                location = storage_service.get_container_for_item(
                    container_type, row["id"]
                )

                location_text = (
                    f"{location['rack_name']} / {location['box_name']} "
                    f"/ {location['position']}"
                    if location
                    else "Not yet assigned to a location"
                )

                st.markdown(
                    f"**{row['name']}** "
                    f"({CONTAINER_TYPE_LABELS[container_type]})"
                )
                st.caption(location_text)

                if row["notes"]:
                    st.caption(f"Notes: {row['notes']}")

                st.divider()

    else:
        st.caption(
            "Type a name to search across DNA, protein aliquots, "
            "and reagent lots."
        )
        st.caption(
            "File attachments and full location grids will be "
            "added once the producing modules (Proteins, DNA, "
            "E.Coli strains) exist."
        )


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
                    show_box_dialog(box, all_racks)


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
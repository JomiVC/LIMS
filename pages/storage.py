"""
pages/storage.py

Storage module -- everything related to the physical storage
hierarchy (freezers, racks, boxes) and assigning items to
positions.

Structure:
    Register new storage
        - Register box
        - Register rack
        - Register freezer
    Boxes
        - Browse boxes
        - Assign item
"""

import streamlit as st

from services.storage_service import StorageService
from services.item_service import ItemService, CONTAINER_TYPE_LABELS
from ui.box_grid import render_box_grid


st.set_page_config(page_title="LIMS - Storage", page_icon="📦")

storage_service = StorageService()
item_service = ItemService()

st.title("📦 Storage")

top_register, top_boxes = st.tabs(["Register new storage", "Boxes"])


# ==========================================================
# TOP TAB: REGISTER NEW STORAGE
# ==========================================================

with top_register:

    reg_box_tab, reg_rack_tab, reg_freezer_tab = st.tabs(
        ["Register box", "Register rack", "Register freezer"]
    )

    # ------------------------------------------------------
    # REGISTER BOX
    # ------------------------------------------------------

    with reg_box_tab:

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
                key="reg_box_rack_select",
            )

            # Config depends on the selected rack, so it's read
            # outside the form to update shelf/slot options live.
            config = storage_service.get_rack_configuration(
                selected_rack_id
            )

            with st.form("create_box_form", clear_on_submit=True):

                box_name = st.text_input("Box name")

                box_type = st.selectbox(
                    "Box type",
                    options=["EPPENDORF", "FALCON", "FALCON_15"],
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
    # REGISTER RACK
    # ------------------------------------------------------

    with reg_rack_tab:

        freezers = storage_service.list_freezers()

        if not freezers:
            st.warning(
                "No freezers registered yet. Create one in "
                "'Register freezer' first."
            )

        else:
            freezer_options = {f.id: f.name for f in freezers}

            with st.form("create_rack_form", clear_on_submit=True):

                rack_freezer_id = st.selectbox(
                    "Freezer",
                    options=list(freezer_options.keys()),
                    format_func=lambda fid: freezer_options[fid],
                    key="reg_rack_freezer_select",
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
    # REGISTER FREEZER
    # ------------------------------------------------------

    with reg_freezer_tab:

        with st.form("create_freezer_form", clear_on_submit=True):

            freezer_name = st.text_input("Name")

            freezer_temp = st.selectbox(
                "Temperature (°C)",
                options=[-20, -80],
                key="reg_freezer_temp_select",
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


# ==========================================================
# TOP TAB: BOXES
# ==========================================================

with top_boxes:

    browse_tab, assign_tab = st.tabs(["Browse boxes", "Assign item"])

    # ------------------------------------------------------
    # BROWSE BOXES
    # ------------------------------------------------------

    with browse_tab:

        boxes = storage_service.list_boxes()
        all_racks = storage_service.list_racks()
        rack_options_browse = {
            rack.id: rack.rack_name for rack in all_racks
        }

        if not boxes:
            st.info("No boxes registered yet.")

        else:
            for box in boxes:

                rack_name = rack_options_browse.get(
                    box.rack_id, "unknown rack"
                )

                with st.expander(
                    f"{box.box_name} ({box.box_type}) — {rack_name} "
                    f"— {box.owner or 'no owner'}"
                ):

                    st.write(
                        f"**Slot:** {box.shelf or '—'} / {box.slot}"
                    )

                    if box.notes:
                        st.write(f"**Notes:** {box.notes}")

                    free = storage_service.list_free_positions(box.id)
                    occupied = storage_service.list_occupied_positions(
                        box.id
                    )

                    st.write(
                        f"**Positions:** {len(occupied)} occupied, "
                        f"{len(free)} free"
                    )

                    st.divider()

                    render_box_grid(box, occupied, key_prefix="browse")

                    st.divider()

                    edit_tab, delete_tab = st.tabs(
                        ["✏️ Edit", "🗑️ Delete"]
                    )

                    # --- EDIT ---
                    with edit_tab:

                        with st.form(f"edit_box_{box.id}"):

                            new_rack_id = st.selectbox(
                                "Rack",
                                options=list(
                                    rack_options_browse.keys()
                                ),
                                format_func=lambda rid: (
                                    rack_options_browse[rid]
                                ),
                                index=list(
                                    rack_options_browse.keys()
                                ).index(box.rack_id)
                                    if box.rack_id in rack_options_browse
                                    else 0,
                                key=f"edit_rack_{box.id}",
                            )

                            edit_config = (
                                storage_service.get_rack_configuration(
                                    new_rack_id
                                )
                            )

                            if edit_config["has_shelf"]:
                                new_shelf = st.selectbox(
                                    "Shelf",
                                    options=edit_config["shelves"],
                                    index=edit_config["shelves"]
                                        .index(box.shelf)
                                        if box.shelf
                                        in edit_config["shelves"]
                                        else 0,
                                    key=f"edit_shelf_{box.id}",
                                )
                            else:
                                new_shelf = None

                            new_slot = st.selectbox(
                                "Slot",
                                options=edit_config["slots"],
                                index=edit_config["slots"]
                                    .index(box.slot)
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

                            save = st.form_submit_button(
                                "Save changes"
                            )

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
                                    st.rerun()

                    # --- DELETE ---
                    with delete_tab:

                        st.warning(
                            "A box can only be deleted if all of "
                            "its positions are free."
                        )

                        confirm = st.checkbox(
                            f"I confirm I want to delete "
                            f"'{box.box_name}'",
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
                                st.success(
                                    f"Box '{box.box_name}' deleted."
                                )
                                st.rerun()

    # ------------------------------------------------------
    # ASSIGN ITEM
    # ------------------------------------------------------

    with assign_tab:

        boxes = storage_service.list_boxes()

        if not boxes:
            st.warning(
                "No boxes registered yet. Register one in "
                "'Register new storage' first."
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

            # Persist the clicked position across reruns (the form
            # below causes its own reruns on submit).
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
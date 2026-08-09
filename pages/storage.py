"""
pages/1_📦_Storage.py

Storage module -- register a box and browse existing ones.

Streamlit re-runs this whole script on every interaction, so the
service is re-created each run. This is safe here because
StorageRepository no longer holds a persistent connection (each
repository call opens/closes its own).
"""

import streamlit as st

from services.storage_service import StorageService


st.set_page_config(page_title="LIMS - Storage", page_icon="📦")


def render_box_grid(box, occupied_positions):
    """
    Renders the physical grid of a box.

    EPPENDORF: 8 rows x 8 columns
    FALCON:    4 rows x 4 columns

    Free/occupied buttons currently have no on_click handler --
    they're a visual reference for now. This is a natural hook for
    the upcoming Containers UI: clicking a free (⚪) position could
    open the "assign item to this position" form directly.
    """

    if box.box_type == "EPPENDORF":
        rows = list("ABCDEFGH")
        columns = list(range(1, 9))

    elif box.box_type == "FALCON":
        rows = list("ABCD")
        columns = list(range(1, 5))

    else:
        st.warning(f"Unknown geometry for box '{box.box_name}'.")
        return

    # ------------------------------------------------------
    # OCCUPIED POSITIONS
    # ------------------------------------------------------

    occupied = {}

    for item in occupied_positions:
        position = item.get("position")

        if position:
            occupied[position] = item

    # ------------------------------------------------------
    # COLUMN HEADER
    # ------------------------------------------------------

    header = st.columns(len(columns) + 1)

    with header[0]:
        st.write("")

    for index, column in enumerate(columns, start=1):
        with header[index]:
            st.markdown(f"**{column}**")

    # ------------------------------------------------------
    # GRID
    # ------------------------------------------------------

    for row in rows:

        grid = st.columns(len(columns) + 1)

        # Row label
        with grid[0]:
            st.markdown(f"**{row}**")

        # Cells
        for index, column in enumerate(columns, start=1):

            position = f"{row}{column}"

            with grid[index]:

                if position in occupied:

                    item = occupied[position]
                    label = item.get("label") or "Occupied"

                    st.button(
                        f"🔵 {position}",
                        key=f"storage_occupied_{box.id}_{position}",
                        help=f"{position} — {label}",
                        use_container_width=True,
                        disabled=True,
                    )

                else:

                    st.button(
                        f"⚪ {position}",
                        key=f"storage_free_{box.id}_{position}",
                        help=f"{position} — Free",
                        use_container_width=True,
                    )

    # ------------------------------------------------------
    # LEGEND
    # ------------------------------------------------------

    st.caption("⚪ Free    🔵 Occupied")


service = StorageService()

st.title("📦 Storage")

tab_new, tab_browse = st.tabs(["Register box", "Browse boxes"])


# ==========================================================
# TAB: REGISTER BOX
# ==========================================================

with tab_new:

    racks = service.list_racks()

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
            key="rack_select",
        )

        # Config depends on the selected rack, so it's read outside
        # the form to update shelf/slot options live as the rack
        # changes. Streamlit forms don't rerun on internal widget
        # changes, only on submit, so this selectbox stays outside.
        config = service.get_rack_configuration(selected_rack_id)

        with st.form("create_box_form", clear_on_submit=True):

            box_name = st.text_input("Box name")

            box_type = st.selectbox(
                "Box type",
                options=["EPPENDORF", "FALCON"],
            )

            if config["has_shelf"]:
                shelf = st.selectbox("Shelf", options=config["shelves"])
            else:
                shelf = None
                st.caption("This rack has no shelves.")

            slot = st.selectbox("Slot", options=config["slots"])

            owner = st.text_input("Owner")

            notes = st.text_area("Notes", value="")

            submitted = st.form_submit_button("Save")

            if submitted:

                try:
                    box_id = service.create_box(
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
                    positions = service.list_positions(box_id)

                    st.success(
                        f"Box '{box_name}' created (id={box_id}) with "
                        f"{len(positions)} positions."
                    )


# ==========================================================
# TAB: BROWSE BOXES
# ==========================================================

with tab_browse:

    boxes = service.list_boxes()
    all_racks = service.list_racks()
    rack_options_browse = {rack.id: rack.rack_name for rack in all_racks}

    if not boxes:
        st.info("No boxes registered yet.")

    else:
        for box in boxes:

            rack_name = rack_options_browse.get(box.rack_id, "unknown rack")

            with st.expander(
                f"{box.box_name} ({box.box_type}) — {rack_name} — "
                f"{box.owner or 'no owner'}"
            ):

                st.write(f"**Slot:** {box.shelf or '—'} / {box.slot}")

                if box.notes:
                    st.write(f"**Notes:** {box.notes}")

                free = service.list_free_positions(box.id)
                occupied = service.list_occupied_positions(box.id)

                st.write(
                    f"**Positions:** {len(occupied)} occupied, "
                    f"{len(free)} free"
                )

                st.divider()

                render_box_grid(box, occupied)

                st.divider()

                edit_tab, delete_tab = st.tabs(["✏️ Edit", "🗑️ Delete"])

                # --- EDIT ---
                with edit_tab:

                    with st.form(f"edit_box_{box.id}"):

                        new_rack_id = st.selectbox(
                            "Rack",
                            options=list(rack_options_browse.keys()),
                            format_func=lambda rid: rack_options_browse[rid],
                            index=list(rack_options_browse.keys())
                                .index(box.rack_id)
                                if box.rack_id in rack_options_browse
                                else 0,
                            key=f"edit_rack_{box.id}",
                        )

                        edit_config = service.get_rack_configuration(
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
                                service.update_box(
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
                            service.delete_box(box.id)
                        except ValueError as e:
                            st.error(str(e))
                        else:
                            st.success(f"Box '{box.box_name}' deleted.")
                            st.rerun()
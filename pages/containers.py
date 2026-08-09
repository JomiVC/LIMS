"""
pages/containers.py

Containers module -- assign an EXISTING item (DNA / protein aliquot
/ reagent lot) to a free position inside a box.

This page does NOT create items. DNA, protein aliquots, and
reagent lots are registered in their own dedicated modules (with
their full set of fields) once those are built. Here we only pick
a free position and link it to an item that already exists.

Flow:
1. Pick a box.
2. Click a free (⚪) position on the grid.
3. Pick the item type, then select the existing item to place there.
4. Save.
"""

import streamlit as st

from services.storage_service import StorageService
from services.item_service import ItemService, CONTAINER_TYPE_LABELS
from ui.box_grid import render_box_grid


st.set_page_config(page_title="LIMS - Containers", page_icon="🧫")

storage_service = StorageService()
item_service = ItemService()

st.title("🧫 Containers")

boxes = storage_service.list_boxes()

if not boxes:
    st.warning("No boxes registered yet. Create one in Storage first.")
    st.stop()

box_options = {box.id: box.box_name for box in boxes}

selected_box_id = st.selectbox(
    "Box",
    options=list(box_options.keys()),
    format_func=lambda bid: box_options[bid],
    key="containers_box_select",
)

selected_box = storage_service.get_box(selected_box_id)
occupied = storage_service.list_occupied_positions(selected_box_id)

clicked_position = render_box_grid(
    selected_box,
    occupied,
    selectable=True,
    key_prefix="containers",
)

# Persist the clicked position across reruns (the form below causes
# its own reruns on submit, which would otherwise lose the click).
if clicked_position:
    st.session_state["containers_selected_position"] = clicked_position

selected_position_label = st.session_state.get(
    "containers_selected_position"
)

if not selected_position_label:
    st.info("Click a free position on the grid to assign an item.")
    st.stop()

position = storage_service.get_position_by_name(
    selected_box_id, selected_position_label
)

if position is None:
    st.error(
        f"Position '{selected_position_label}' not found on this box."
    )
    st.stop()

st.divider()
st.subheader(f"Assign item to {selected_position_label}")

container_type = st.selectbox(
    "Item type",
    options=list(CONTAINER_TYPE_LABELS.keys()),
    format_func=lambda ct: CONTAINER_TYPE_LABELS[ct],
    key="containers_type_select",
)

existing_items = item_service.list_items(container_type)

if not existing_items:
    st.info(
        f"No {CONTAINER_TYPE_LABELS[container_type]} items registered "
        f"yet. Register one in its own module first, then come back "
        f"here to assign it a location."
    )
    st.stop()

item_options = {row["id"]: row["name"] for row in existing_items}

item_id = st.selectbox(
    CONTAINER_TYPE_LABELS[container_type],
    options=list(item_options.keys()),
    format_func=lambda iid: item_options[iid],
    key="containers_existing_item_select",
)

with st.form("assign_container_form", clear_on_submit=True):

    label = st.text_input("Container label")
    container_notes = st.text_area("Container notes", value="")

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
                f"Assigned to {selected_position_label} in "
                f"'{selected_box.box_name}'."
            )
            del st.session_state["containers_selected_position"]
            st.rerun()
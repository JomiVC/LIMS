"""
pages/storage.py

Storage management page.
"""

import streamlit as st

from services.storage_service import StorageService


st.set_page_config(
    page_title="Storage",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Storage Management")

service = StorageService()

st.subheader("Register new storage box")

with st.form("create_box"):

    box_name = st.text_input("Box name")

    owner = st.text_input("Owner")

    box_type = st.selectbox(
        "Box type",
        ["EPPENDORF", "FALCON"]
    )

    racks = service.list_racks()

    rack_options = {
        f"{rack['rack_name']} ({rack['rack_type']})": rack["id"]
        for rack in racks
    }

    selected_rack = st.selectbox(
        "Rack",
        list(rack_options.keys())
    )
    selected_rack_name = selected_rack.split(" ")[0]

    falcon_rack = selected_rack_name in ["A", "B", "C", "D"]
    
    if falcon_rack:

    shelf = st.selectbox(
        "Shelf",
        ["Upper", "Lower"]
    )

    else:

    shelf = None

    slot = st.selectbox(
    "Slot",
    [1, 2, 3, 4, 5]
    )
    notes = st.text_area("Notes")

    submitted = st.form_submit_button("Create box")

if submitted:

    try:

        service.create_box(
            box_name=box_name,
            box_type=box_type,
            owner=owner,
            rack_id=rack_options[selected_rack],
            shelf=shelf,
            slot=slot,
            notes=notes,
        )

        st.success("Box created successfully.")

    except Exception as exc:

        st.error(str(exc))

st.divider()

st.subheader("Registered boxes")

boxes = service.list_boxes()

if boxes:

    table = []

    for box in boxes:

        table.append(
            {
                "Name": box["box_name"],
                "Type": box["box_type"],
                "Owner": box["owner"],
                "Rack": box["rack_name"],
                "Shelf": box["shelf"],
                "Slot": box["slot"],
            }
        )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info("No storage boxes registered.")
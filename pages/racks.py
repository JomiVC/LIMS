"""
pages/racks.py

Freezer and Rack management -- create and browse the physical
storage structure that boxes live in.
"""

import streamlit as st

from services.storage_service import StorageService


st.set_page_config(page_title="LIMS - Racks", page_icon="🗄️")

service = StorageService()

st.title("🗄️ Freezers & Racks")

tab_freezers, tab_racks = st.tabs(["Freezers", "Racks"])


# ==========================================================
# TAB: FREEZERS
# ==========================================================

with tab_freezers:

    st.subheader("Register a freezer")

    with st.form("create_freezer_form", clear_on_submit=True):

        freezer_name = st.text_input("Name")
        freezer_temp = st.number_input(
            "Temperature (°C)", value=-20.0, step=1.0
        )
        freezer_notes = st.text_area("Description", value="")

        if st.form_submit_button("Save"):

            try:
                service.create_freezer(
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

    freezers = service.list_freezers()

    if not freezers:
        st.info("No freezers registered yet.")

    else:
        for freezer in freezers:
            with st.expander(f"{freezer.name} ({freezer.temperature}°C)"):
                if freezer.description:
                    st.write(freezer.description)


# ==========================================================
# TAB: RACKS
# ==========================================================

with tab_racks:

    freezers = service.list_freezers()

    if not freezers:
        st.warning(
            "No freezers registered yet. Create one in the "
            "Freezers tab first."
        )
        st.stop()

    st.subheader("Register a rack")

    freezer_options = {f.id: f.name for f in freezers}

    with st.form("create_rack_form", clear_on_submit=True):

        rack_freezer_id = st.selectbox(
            "Freezer",
            options=list(freezer_options.keys()),
            format_func=lambda fid: freezer_options[fid],
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
                service.create_rack(
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

    racks = service.list_racks()

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
                    "with shelves" if rack.has_shelf else "no shelves"
                )
                st.caption(
                    f"{rack.rack_name} — {rack.rack_type} — "
                    f"{shelf_info} — {rack.slot_count} slots"
                )
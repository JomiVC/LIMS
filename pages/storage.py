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

service = StorageService()

st.title("📦 Storage")

tab_new, tab_browse = st.tabs(["Registrar caja", "Ver cajas"])


# ==========================================================
# TAB: REGISTRAR CAJA
# ==========================================================

with tab_new:

    racks = service.list_racks()

    if not racks:
        st.warning(
            "No hay racks creados todavía. Crea un rack antes de "
            "registrar una caja."
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

            box_name = st.text_input("Nombre de la caja")

            box_type = st.selectbox(
                "Tipo de caja",
                options=["EPPENDORF", "FALCON"],
            )

            if config["has_shelf"]:
                shelf = st.selectbox("Shelf", options=config["shelves"])
            else:
                shelf = None
                st.caption("Este rack no tiene shelves.")

            slot = st.selectbox("Slot", options=config["slots"])

            owner = st.text_input("Propietario")

            notes = st.text_area("Notas", value="")

            submitted = st.form_submit_button("Guardar")

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
                        f"Caja '{box_name}' creada (id={box_id}) con "
                        f"{len(positions)} posiciones."
                    )


# ==========================================================
# TAB: VER CAJAS
# ==========================================================

with tab_browse:

    boxes = service.list_boxes()
    all_racks = service.list_racks()
    rack_options_browse = {rack.id: rack.rack_name for rack in all_racks}

    if not boxes:
        st.info("No hay cajas registradas todavía.")

    else:
        for box in boxes:

            rack_name = rack_options_browse.get(box.rack_id, "rack desconocido")

            with st.expander(
                f"{box.box_name} ({box.box_type}) — {rack_name} — "
                f"{box.owner or 'sin dueño'}"
            ):

                st.write(f"**Slot:** {box.shelf or '—'} / {box.slot}")

                if box.notes:
                    st.write(f"**Notas:** {box.notes}")

                free = service.list_free_positions(box.id)
                occupied = service.list_occupied_positions(box.id)

                st.write(
                    f"**Posiciones:** {len(occupied)} ocupadas, "
                    f"{len(free)} libres"
                )

                st.divider()

                edit_tab, delete_tab = st.tabs(["✏️ Editar", "🗑️ Eliminar"])

                # --- EDITAR ---
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
                            "Propietario",
                            value=box.owner or "",
                            key=f"edit_owner_{box.id}",
                        )

                        new_notes = st.text_area(
                            "Notas",
                            value=box.notes or "",
                            key=f"edit_notes_{box.id}",
                        )

                        save = st.form_submit_button("Guardar cambios")

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
                                st.success("Caja actualizada.")
                                st.rerun()

                # --- ELIMINAR ---
                with delete_tab:

                    st.warning(
                        "Solo se puede eliminar una caja si todas "
                        "sus posiciones están libres."
                    )

                    confirm = st.checkbox(
                        f"Confirmo que quiero eliminar '{box.box_name}'",
                        key=f"confirm_delete_{box.id}",
                    )

                    if st.button(
                        "Eliminar caja",
                        key=f"delete_{box.id}",
                        disabled=not confirm,
                    ):
                        try:
                            service.delete_box(box.id)
                        except ValueError as e:
                            st.error(str(e))
                        else:
                            st.success(f"Caja '{box.box_name}' eliminada.")
                            st.rerun()
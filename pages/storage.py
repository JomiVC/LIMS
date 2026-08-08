"""
pages/storage.py

Storage management page.
"""

import streamlit as st

from services.storage_service import StorageService


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="LIMS - Storage",
    page_icon="📦",
    layout="wide",
)


service = StorageService()


# ==========================================================
# HELPERS
# ==========================================================

def get_box_grid(box_type):
    """
    Return the rows and columns for a box type.
    """

    if box_type == "EPPENDORF":
        return list("ABCDEFGH"), list(range(1, 9))

    if box_type == "FALCON":
        return list("ABCD"), list(range(1, 5))

    return [], []


def render_box_grid(box, occupied_positions):
    """
    Render a visual grid representing the physical box.
    """

    rows, columns = get_box_grid(box.box_type)

    if not rows or not columns:
        st.warning(
            f"No se conoce la geometría de la caja "
            f"'{box.box_name}'."
        )
        return

    occupied = {}

    for item in occupied_positions:

        position = item.get("position")

        if position:
            occupied[position] = item

    # ------------------------------------------------------
    # GRID CSS
    # ------------------------------------------------------

    st.markdown(
        """
        <style>

        .storage-grid {
            display: grid;
            gap: 5px;
            width: 100%;
            margin-top: 10px;
            margin-bottom: 10px;
        }

        .storage-cell {
            min-height: 60px;
            border-radius: 7px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 5px;
            box-sizing: border-box;
            font-size: 0.8rem;
        }

        .storage-header {
            font-weight: bold;
            min-height: 30px;
        }

        .storage-row-label {
            font-weight: bold;
        }

        .storage-free {
            border: 1px solid #cbd5e1;
            background: #f8fafc;
        }

        .storage-occupied {
            border: 1px solid #60a5fa;
            background: #dbeafe;
        }

        .storage-position {
            font-weight: bold;
        }

        .storage-content {
            font-size: 0.65rem;
            margin-top: 4px;
            word-break: break-word;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------
    # NUMBER OF COLUMNS
    # ------------------------------------------------------

    number_of_columns = len(columns) + 1

    column_template = (
        "42px "
        + " ".join(
            ["minmax(55px, 1fr)"] * len(columns)
        )
    )

    st.markdown(
        f"""
        <style>
        .storage-grid {{
            grid-template-columns: {column_template};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------
    # GRID
    # ------------------------------------------------------

    grid = []

    # Top-left empty cell
    grid.append(
        '<div class="storage-cell storage-header"></div>'
    )

    # Column headers
    for column in columns:

        grid.append(
            f"""
            <div class="storage-cell storage-header">
                {column}
            </div>
            """
        )

    # Rows
    for row in rows:

        grid.append(
            f"""
            <div class="storage-cell storage-row-label">
                {row}
            </div>
            """
        )

        for column in columns:

            position = f"{row}{column}"

            if position in occupied:

                item = occupied[position]

                label = item.get("label") or "Ocupada"
                container_type = (
                    item.get("container_type") or ""
                )

                grid.append(
                    f"""
                    <div
                        class="storage-cell storage-occupied"
                        title="{position}"
                    >
                        <span class="storage-position">
                            {position}
                        </span>

                        <span class="storage-content">
                            {label}
                        </span>

                        <span class="storage-content">
                            {container_type}
                        </span>
                    </div>
                    """
                )

            else:

                grid.append(
                    f"""
                    <div
                        class="storage-cell storage-free"
                        title="{position}"
                    >
                        <span class="storage-position">
                            {position}
                        </span>

                        <span class="storage-content">
                            Libre
                        </span>
                    </div>
                    """
                )

    grid_html = (
        '<div class="storage-grid">'
        + "".join(grid)
        + "</div>"
    )

    st.markdown(
        grid_html,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------
    # LEGEND
    # ------------------------------------------------------

    st.write(
        "Leyenda: ⬜ Libre    🟦 Ocupada"
    )


# ==========================================================
# PAGE TITLE
# ==========================================================

st.title("📦 Storage")


# ==========================================================
# TABS
# ==========================================================

tab_new, tab_browse = st.tabs(
    [
        "Registrar caja",
        "Ver cajas",
    ]
)


# ==========================================================
# REGISTER BOX
# ==========================================================

with tab_new:

    racks = service.list_racks()

    if not racks:

        st.warning(
            "No hay racks creados todavía. "
            "Crea un rack antes de registrar una caja."
        )

    else:

        rack_options = {
            rack.id: rack.rack_name
            for rack in racks
        }

        selected_rack_id = st.selectbox(
            "Rack",
            options=list(rack_options.keys()),
            format_func=lambda rack_id:
                rack_options[rack_id],
        )

        config = service.get_rack_configuration(
            selected_rack_id
        )

        with st.form(
            "create_box_form",
            clear_on_submit=True,
        ):

            box_name = st.text_input(
                "Nombre de la caja"
            )

            box_type = st.selectbox(
                "Tipo de caja",
                [
                    "EPPENDORF",
                    "FALCON",
                ],
            )

            if config["has_shelf"]:

                shelf = st.selectbox(
                    "Shelf",
                    config["shelves"],
                )

            else:

                shelf = None

                st.caption(
                    "Este rack no utiliza Shelf."
                )

            slot = st.selectbox(
                "Slot",
                config["slots"],
            )

            owner = st.text_input(
                "Propietario"
            )

            notes = st.text_area(
                "Notas"
            )

            submitted = st.form_submit_button(
                "Guardar caja"
            )

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

                except ValueError as error:

                    st.error(str(error))

                else:

                    positions = service.list_positions(
                        box_id
                    )

                    st.success(
                        f"Caja '{box_name}' creada "
                        f"con {len(positions)} posiciones."
                    )


# ==========================================================
# BROWSE BOXES
# ==========================================================

with tab_browse:

    boxes = service.list_boxes()

    racks = service.list_racks()

    rack_names = {
        rack.id: rack.rack_name
        for rack in racks
    }

    if not boxes:

        st.info(
            "No hay cajas registradas todavía."
        )

    else:

        for box in boxes:

            rack_name = rack_names.get(
                box.rack_id,
                "Rack desconocido",
            )

            location = rack_name

            if box.shelf:
                location += f" / {box.shelf}"

            location += f" / Slot {box.slot}"

            with st.expander(
                f"{box.box_name} "
                f"({box.box_type}) — "
                f"{location}"
            ):

                # --------------------------------------------------
                # INFORMATION
                # --------------------------------------------------

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.write(
                        f"**Propietario:** "
                        f"{box.owner or '—'}"
                    )

                with col2:

                    st.write(
                        f"**Rack:** "
                        f"{rack_name}"
                    )

                with col3:

                    st.write(
                        f"**Slot:** "
                        f"{box.slot}"
                    )

                if box.shelf:

                    st.write(
                        f"**Shelf:** "
                        f"{box.shelf}"
                    )

                if box.notes:

                    st.write(
                        f"**Notas:** "
                        f"{box.notes}"
                    )

                # --------------------------------------------------
                # POSITIONS
                # --------------------------------------------------

                free_positions = (
                    service.list_free_positions(
                        box.id
                    )
                )

                occupied_positions = (
                    service.list_occupied_positions(
                        box.id
                    )
                )

                total_positions = (
                    len(free_positions)
                    + len(occupied_positions)
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Total",
                        total_positions,
                    )

                with col2:

                    st.metric(
                        "Ocupadas",
                        len(occupied_positions),
                    )

                with col3:

                    st.metric(
                        "Libres",
                        len(free_positions),
                    )

                st.divider()

                # --------------------------------------------------
                # GRID
                # --------------------------------------------------

                st.subheader(
                    "Mapa de posiciones"
                )

                render_box_grid(
                    box,
                    occupied_positions,
                )

                st.divider()

                # --------------------------------------------------
                # EDIT / DELETE
                # --------------------------------------------------

                edit_tab, delete_tab = st.tabs(
                    [
                        "✏️ Editar",
                        "🗑️ Eliminar",
                    ]
                )

                # ==================================================
                # EDIT
                # ==================================================

                with edit_tab:

                    with st.form(
                        f"edit_box_{box.id}"
                    ):

                        rack_ids = list(
                            rack_names.keys()
                        )

                        if box.rack_id in rack_ids:

                            current_rack_index = (
                                rack_ids.index(
                                    box.rack_id
                                )
                            )

                        else:

                            current_rack_index = 0

                        new_rack_id = st.selectbox(
                            "Rack",
                            rack_ids,
                            index=current_rack_index,
                            format_func=lambda rack_id:
                                rack_names[rack_id],
                        )

                        edit_config = (
                            service.get_rack_configuration(
                                new_rack_id
                            )
                        )

                        if edit_config["has_shelf"]:

                            shelf_options = (
                                edit_config["shelves"]
                            )

                            if box.shelf in shelf_options:

                                shelf_index = (
                                    shelf_options.index(
                                        box.shelf
                                    )
                                )

                            else:

                                shelf_index = 0

                            new_shelf = st.selectbox(
                                "Shelf",
                                shelf_options,
                                index=shelf_index,
                            )

                        else:

                            new_shelf = None

                            st.caption(
                                "Este rack no utiliza Shelf."
                            )

                        slot_options = (
                            edit_config["slots"]
                        )

                        if box.slot in slot_options:

                            slot_index = (
                                slot_options.index(
                                    box.slot
                                )
                            )

                        else:

                            slot_index = 0

                        new_slot = st.selectbox(
                            "Slot",
                            slot_options,
                            index=slot_index,
                        )

                        new_owner = st.text_input(
                            "Propietario",
                            value=box.owner or "",
                        )

                        new_notes = st.text_area(
                            "Notas",
                            value=box.notes or "",
                        )

                        save = st.form_submit_button(
                            "Guardar cambios"
                        )

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

                            except ValueError as error:

                                st.error(
                                    str(error)
                                )

                            else:

                                st.success(
                                    "Caja actualizada correctamente."
                                )

                                st.rerun()

                # ==================================================
                # DELETE
                # ==================================================

                with delete_tab:

                    if occupied_positions:

                        st.warning(
                            "Esta caja contiene posiciones "
                            "ocupadas y no puede eliminarse."
                        )

                    else:

                        st.info(
                            "La caja está vacía y puede eliminarse."
                        )

                        confirm = st.checkbox(
                            "Confirmo que quiero eliminar "
                            f"'{box.box_name}'",
                            key=f"confirm_delete_{box.id}",
                        )

                        if st.button(
                            "Eliminar caja",
                            key=f"delete_box_{box.id}",
                            disabled=not confirm,
                        ):

                            try:

                                service.delete_box(
                                    box.id
                                )

                            except ValueError as error:

                                st.error(
                                    str(error)
                                )

                            else:

                                st.success(
                                    f"Caja '{box.box_name}' eliminada."
                                )

                                st.rerun()


"""
ui/box_grid.py

Shared box grid renderer, used by both the Storage page (read-only
view) and the Containers page (selectable, to pick a free position
to assign an item to).
"""

import streamlit as st


def render_box_grid(box, occupied_positions, selectable=False, key_prefix="", enriched_data=None):
    """
    Renders the physical grid of a box.

    EPPENDORF: 8 rows x 8 columns
    FALCON:    4 rows x 4 columns

    If `selectable` is True, clicking a free (⚪) position returns
    its label (e.g. "A1") for that rerun. Occupied (🔵) positions
    are always disabled, selectable or not -- you assign an item to
    a free slot, not to one that's already taken.
    
    If `enriched_data` is provided, occupied buttons will show item
    names in help text and store container_id in session_state when
    clicked for viewing details.

    Returns the clicked free position's label, or None if nothing
    was clicked this rerun.
    """

    if box.box_type == "EPPENDORF":
        rows = list("ABCDEFGH")
        columns = list(range(1, 9))

    elif box.box_type == "FALCON":
        rows = list("ABCD")
        columns = list(range(1, 5))

    elif box.box_type == "FALCON_15":
        rows = list("ABCDEFG")
        columns = list(range(1, 8))

    else:
        st.warning(f"Unknown geometry for box '{box.box_name}'.")
        return None

    # Build enriched data map by container_id
    enriched_map = {}
    if enriched_data:
        for data in enriched_data:
            container_id = data.get("container_id")
            if container_id:
                enriched_map[container_id] = data

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

    clicked_position = None

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
                    container_id = item.get("container_id")
                    
                    # Build help text with item name if available
                    help_text = f"{position} — {label}"
                    if enriched_data and container_id in enriched_map:
                        enriched = enriched_map[container_id]
                        item_name = enriched.get("item_name", "Unknown")
                        help_text = f"{position} — {label}\n({item_name})"

                    clicked = st.button(
                        f"🔵 {position}",
                        key=f"{key_prefix}_occupied_{box.id}_{position}",
                        help=help_text,
                        use_container_width=True,
                    )
                    
                    # If enriched data is available and button is clicked,
                    # store container info and trigger rerun to show modal
                    if clicked and enriched_data and container_id in enriched_map:
                        st.session_state[f"{key_prefix}_selected_container"] = enriched_map[container_id]
                        st.rerun()

                else:

                    clicked = st.button(
                        f"⚪ {position}",
                        key=f"{key_prefix}_free_{box.id}_{position}",
                        help=(
                            f"{position} — Click to assign an item"
                            if selectable
                            else f"{position} — Free"
                        ),
                        use_container_width=True,
                    )

                    if clicked and selectable:
                        clicked_position = position

    # ------------------------------------------------------
    # LEGEND
    # ------------------------------------------------------

    legend = "⚪ Free    🔵 Occupied"

    if selectable:
        legend += "    (click a free position to assign an item)"

    st.caption(legend)

    return clicked_position
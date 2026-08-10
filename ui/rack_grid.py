"""
ui/rack_grid.py

Renders the racks of a freezer as a spatial grid, grouped by rack
type. Fill order is left-to-right, top-to-bottom (rack "1" top-left,
last rack bottom-right).

Layout assumption: EPPENDORF racks are laid out 8 per column
(matches the lab's Freezer 1: 40 racks -> 5 columns x 8 rows).
FALCON racks are laid out 1 per column (a single row). Column count
is derived from how many racks of that type exist, so this still
works for freezers with a different rack count -- it isn't hardcoded
to exactly 40/4.

If `selected_rack_id` is given and `boxes_by_rack_id` provides that
rack's boxes, a box dropdown is rendered directly under that rack's
button, in the same grid cell -- not in a separate section below the
whole grid.
"""

import math
from collections import defaultdict

import streamlit as st


ROWS_BY_RACK_TYPE = {
    "EPPENDORF": 8,
    "FALCON": 1,
}


def render_rack_grid(
    racks,
    key_prefix="",
    selected_rack_id=None,
    boxes_by_rack_id=None,
):
    """
    `racks` is a list of Rack model instances (any order -- they're
    grouped and re-sorted by rack_name here).

    `boxes_by_rack_id`, if given, is a dict {rack_id: [Box, ...]}.
    When the rack in a given cell matches `selected_rack_id`, its
    box dropdown is rendered right under its button. The chosen
    box's id ends up in
    st.session_state[f"{key_prefix}_box_select_{rack_id}"] --
    read it there after calling this function.

    Returns the id of the rack that was clicked this rerun, or None.
    """

    if not racks:
        st.info("No racks in this freezer yet.")
        return None

    by_type = defaultdict(list)

    for rack in racks:
        by_type[rack.rack_type].append(rack)

    clicked_rack_id = None

    for rack_type, group in by_type.items():

        group = sorted(
            group,
            key=lambda r: (
                int(r.rack_name) if r.rack_name.isdigit() else 0,
                r.rack_name,
            ),
        )

        rows = ROWS_BY_RACK_TYPE.get(rack_type, 1)
        cols = math.ceil(len(group) / rows)

        st.markdown(f"**{rack_type} racks**")

        index = 0

        for _ in range(rows):

            row_columns = st.columns(cols)

            for col in range(cols):

                with row_columns[col]:

                    if index >= len(group):
                        st.write("")
                        continue

                    rack = group[index]
                    index += 1

                    if st.button(
                        rack.rack_name,
                        key=f"{key_prefix}_rack_{rack.id}",
                        use_container_width=True,
                    ):
                        clicked_rack_id = rack.id

                    if (
                        boxes_by_rack_id is not None
                        and selected_rack_id == rack.id
                    ):
                        boxes = boxes_by_rack_id.get(rack.id, [])

                        if not boxes:
                            st.caption("No boxes")

                        else:
                            box_options = {
                                b.id: b.box_name for b in boxes
                            }

                            st.selectbox(
                                "Box",
                                options=list(box_options.keys()),
                                format_func=lambda bid: (
                                    box_options[bid]
                                ),
                                key=(
                                    f"{key_prefix}_box_select_"
                                    f"{rack.id}"
                                ),
                                label_visibility="collapsed",
                            )

        st.caption("")  # small spacing between rack-type sections

    return clicked_rack_id
"""
ui/rack_grid.py

Renders the racks of a freezer as a spatial grid, grouped by rack
type. Fill order is top-to-bottom within each column, then moves to
the next column (rack "1" top of column 1, "8" bottom of column 1,
"9" top of column 2, and so on).

Layout assumption: EPPENDORF racks are laid out 8 per column
(matches the lab's Freezer 1: 40 racks -> 5 columns x 8 rows).
FALCON racks are laid out 1 per column (a single row). Column count
is derived from how many racks of that type exist, so this still
works for freezers with a different rack count -- it isn't hardcoded
to exactly 40/4.

If `selected_rack_id` is given, a box dropdown is rendered directly
under that rack's button, in the same grid cell. The dropdown always
lists every physical slot in the rack (shelf x slot combinations, in
order), whether occupied or not -- occupied slots show the box name,
empty ones show "EMPTY".
"""

import math
from collections import defaultdict

import streamlit as st


ROWS_BY_RACK_TYPE = {
    "EPPENDORF": 8,
    "FALCON": 1,
}


def get_rack_slot_combos(rack):
    """
    Returns the ordered list of (shelf, slot) pairs representing
    every physical box position in a rack. `shelf` is None for
    racks without shelves.
    """

    slots = list(range(1, rack.slot_count + 1))

    if rack.has_shelf:
        return [
            (shelf, slot)
            for shelf in ("Upper", "Lower")
            for slot in slots
        ]

    return [(None, slot) for slot in slots]


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
    slot dropdown is rendered right under its button. The selected
    slot's index (into get_rack_slot_combos(rack)) ends up in
    st.session_state[f"{key_prefix}_box_select_{rack_id}"] -- use
    get_rack_slot_combos() with that index to resolve it back to a
    (shelf, slot) pair after calling this function.

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

        for row_index in range(rows):

            row_columns = st.columns(cols)

            for col in range(cols):

                with row_columns[col]:

                    index = col * rows + row_index

                    if index >= len(group):
                        st.write("")
                        continue

                    rack = group[index]

                    if st.button(
                        rack.rack_name,
                        key=f"{key_prefix}_rack_{rack.id}",
                        use_container_width=True,
                    ):
                        clicked_rack_id = rack.id

                    if selected_rack_id == rack.id:

                        boxes = (
                            boxes_by_rack_id.get(rack.id, [])
                            if boxes_by_rack_id
                            else []
                        )
                        box_by_slot = {
                            (b.shelf, b.slot): b for b in boxes
                        }

                        combos = get_rack_slot_combos(rack)

                        def _format_slot(i, combos=combos, box_by_slot=box_by_slot):
                            shelf, slot = combos[i]
                            box = box_by_slot.get((shelf, slot))
                            name = box.box_name if box else "EMPTY"
                            prefix = (
                                f"{shelf} {slot}" if shelf
                                else f"Slot {slot}"
                            )
                            return f"{prefix}: {name}"

                        st.selectbox(
                            "Slot",
                            options=list(range(len(combos))),
                            format_func=_format_slot,
                            key=f"{key_prefix}_box_select_{rack.id}",
                            label_visibility="collapsed",
                        )

        st.caption("")  # small spacing between rack-type sections

    return clicked_rack_id
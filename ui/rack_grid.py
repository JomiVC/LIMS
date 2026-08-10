"""
ui/rack_grid.py

Renders the racks of a freezer as a spatial grid, grouped by rack
type. Fill order is top-to-bottom within each column, then moves to
the next column (rack "1" top of column 1, "8" bottom of column 1,
"9" top of column 2, and so on).

Layout assumption: EPPENDORF racks are laid out 8 per column
(matches the lab's Freezer 1: 40 racks -> 5 columns x 8 rows).
FALCON racks are laid out 1 per column (a single row). Column count
is derived from how many racks of that type exist.

Each rack cell IS a dropdown (st.selectbox), not a button. Closed,
it shows the rack's own name/number. Opening it lists every slot in
that rack (occupied slots show the box name, empty ones "EMPTY").
Picking a slot in any rack makes that rack+slot the "active
selection", returned by render_rack_grid() for the caller to act on.
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


def _active_selection_key(key_prefix):
    return f"{key_prefix}_active_selection"


def clear_active_selection(key_prefix):
    """
    Call after an action that should return the grid to its default
    state (e.g. a box was edited/deleted and its dialog closed).
    """

    st.session_state.pop(_active_selection_key(key_prefix), None)


def render_rack_grid(racks, key_prefix="", boxes_by_rack_id=None):
    """
    `racks` is a list of Rack model instances (any order -- they're
    grouped and re-sorted by rack_name here).

    `boxes_by_rack_id`, if given, is a dict {rack_id: [Box, ...]}
    used to label each slot with its box name or "EMPTY".

    Returns (rack_id, combo_index) for whichever slot was just
    picked (in any rack's dropdown), or None if nothing is active
    yet. Use get_rack_slot_combos(rack) to turn combo_index back
    into a (shelf, slot) pair.
    """

    if not racks:
        st.info("No racks in this freezer yet.")
        return None

    by_type = defaultdict(list)

    for rack in racks:
        by_type[rack.rack_type].append(rack)

    active_key = _active_selection_key(key_prefix)

    def _make_on_change(rack_id, widget_key):

        def _on_change():
            value = st.session_state.get(widget_key)
            if value is not None:
                st.session_state[active_key] = (rack_id, value)

        return _on_change

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

                    combos = get_rack_slot_combos(rack)
                    boxes = (
                        boxes_by_rack_id.get(rack.id, [])
                        if boxes_by_rack_id
                        else []
                    )
                    box_by_slot = {
                        (b.shelf, b.slot): b for b in boxes
                    }

                    def _format_option(
                        i, rack=rack, combos=combos,
                        box_by_slot=box_by_slot
                    ):
                        if i is None:
                            return rack.rack_name

                        shelf, slot = combos[i]
                        box = box_by_slot.get((shelf, slot))
                        name = box.box_name if box else "EMPTY"
                        prefix = (
                            f"{shelf} {slot}" if shelf
                            else f"Slot {slot}"
                        )
                        return f"{prefix}: {name}"

                    widget_key = f"{key_prefix}_rack_select_{rack.id}"

                    st.selectbox(
                        rack.rack_name,
                        options=[None] + list(range(len(combos))),
                        format_func=_format_option,
                        key=widget_key,
                        label_visibility="collapsed",
                        on_change=_make_on_change(
                            rack.id, widget_key
                        ),
                    )

        st.caption("")  # small spacing between rack-type sections

    return st.session_state.get(active_key)
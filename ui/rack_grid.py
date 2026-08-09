"""
ui/rack_grid.py

Renders the racks of a freezer as a spatial grid, grouped by rack
type. Clicking a rack returns its id for that rerun.

Layout assumption: EPPENDORF racks are laid out 8 per column
(matches the lab's Freezer 1: 40 racks -> 5 columns x 8 rows).
FALCON racks are laid out 1 per column (a single row). Column count
is derived from how many racks of that type exist, so this still
works for freezers with a different rack count -- it isn't hardcoded
to exactly 40/4.
"""

import math
from collections import defaultdict

import streamlit as st


ROWS_BY_RACK_TYPE = {
    "EPPENDORF": 8,
    "FALCON": 1,
}


def render_rack_grid(racks, key_prefix=""):
    """
    `racks` is a list of Rack model instances (any order -- they're
    grouped and re-sorted by rack_name here). Returns the id of the
    rack that was clicked this rerun, or None.
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

                    else:
                        rack = group[index]

                        if st.button(
                            rack.rack_name,
                            key=f"{key_prefix}_rack_{rack.id}",
                            use_container_width=True,
                        ):
                            clicked_rack_id = rack.id

                        index += 1

        st.caption("")  # small spacing between rack-type sections

    return clicked_rack_id
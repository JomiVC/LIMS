"""
ui/use_aliquot.py

Reusable Streamlit UI component for rendering the aliquot consumption form.
Pure UI layer: no business logic, no database operations.
"""

import streamlit as st
from typing import Tuple, Optional


def render_use_aliquot_form(key_prefix: str, remaining_qty: int) -> Tuple[int, Optional[str], bool]:
    """
    Renders quantity input, reason selector, optional mandatory experiment description, and confirm button.

    Returns:
        (quantity_to_use, reason_text_for_history, is_confirmed_clicked)
    """
    qty = st.number_input(
        "Qty to use",
        min_value=1,
        max_value=remaining_qty if remaining_qty > 0 else 1,
        step=1,
        value=1,
        key=f"{key_prefix}_qty",
    )

    reason_option = st.selectbox(
        "Reason for use*",
        options=["Experiment", "QC", "Re-purification"],
        key=f"{key_prefix}_reason_option",
    )

    exp_desc = ""
    can_confirm = True

    if reason_option == "Experiment":
        exp_desc = st.text_input(
            "Experiment description*",
            placeholder="e.g. Western blot for mutant expression analysis",
            key=f"{key_prefix}_exp_desc",
        )
        if not exp_desc.strip():
            st.caption("⚠️ Experiment description is required.")
            can_confirm = False

    reason_text: Optional[str] = None
    if reason_option == "Experiment":
        reason_text = f"Experiment: {exp_desc.strip()}"
    elif reason_option == "QC":
        reason_text = "QC"
    elif reason_option == "Re-purification":
        reason_text = "Re-purification"

    is_confirmed = False
    if st.button("Confirm use", key=f"{key_prefix}_btn", disabled=not can_confirm):
        is_confirmed = True

    return int(qty), reason_text, is_confirmed

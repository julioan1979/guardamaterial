from __future__ import annotations

from typing import Dict

import pandas as pd
import streamlit as st

from airtable_client import AirtableClient
from utils import helpers


def _box_items(box_id: str, items_df: pd.DataFrame) -> pd.DataFrame:
    if items_df.empty or "Caixa" not in items_df.columns:
        return pd.DataFrame()
    mask = items_df["Caixa"].apply(lambda value: isinstance(value, list) and box_id in value)
    return items_df[mask]


def render(*, dataframes: Dict[str, pd.DataFrame], client: AirtableClient, refresh_callback) -> None:
    sec_df = dataframes.get("Secções", pd.DataFrame())
    loc_df = dataframes.get("Locais", pd.DataFrame())
    sub_df = dataframes.get("Sublocais", pd.DataFrame())
    box_df = dataframes.get("Caixas e Armazéns", pd.DataFrame())
    items_df = dataframes.get("Itens", pd.DataFrame())

    if sec_df.empty:
        st.info("Ainda não existem secções cadastradas no Airtable.")
        return

    box_lookup = helpers.build_lookup(box_df)

    st.subheader("Hierarquia de Inventário")
    st.caption("Explore da secção até ao conteúdo de cada caixa.")

    for _, sec in sec_df.iterrows():
        section_name = helpers.get_display_value(sec)
        with st.expander(f"Secção: {section_name}", expanded=False):
            related_locals = helpers.filter_by_link(loc_df, "Secção", sec["id"])
            if related_locals.empty:
                st.markdown("_Sem locais associados._")
                continue

            for _, local in related_locals.iterrows():
                local_name = helpers.get_display_value(local)
                st.markdown(f"### Local: {local_name}")
                related_sublocals = helpers.filter_by_link(sub_df, "Local", local["id"])
                if related_sublocals.empty:
                    st.markdown("_Sem sublocais registados._")
                    continue

                for _, sublocal in related_sublocals.iterrows():
                    sublocal_name = helpers.get_display_value(sublocal)
                    with st.expander(f"Sublocal: {sublocal_name}", expanded=False):
                        related_boxes = helpers.filter_by_link(box_df, "Sublocal", sublocal["id"])
                        if related_boxes.empty:
                            st.markdown("_Sem caixas associadas._")
                            continue

                        for _, box in related_boxes.iterrows():
                            box_name = helpers.get_display_value(box)
                            cols = st.columns([3, 1])
                            with cols[0]:
                                st.markdown(f"**Caixa:** {box_name}")
                                if "Estado" in box and isinstance(box["Estado"], str):
                                    st.caption(f"Estado atual: {box['Estado']}")
                            with cols[1]:
                                if st.button("Ver detalhes", key=f"box-{box['id']}"):
                                    st.session_state["selected_box"] = box["id"]

    selected_box_id = st.session_state.get("selected_box")
    if selected_box_id:
        selected_box_name = box_lookup.get(selected_box_id, selected_box_id)
        st.divider()
        st.subheader(f"Conteúdo da caixa: {selected_box_name}")
        box_items = _box_items(selected_box_id, items_df)
        if box_items.empty:
            st.info("Esta caixa ainda não possui itens registados.")
        else:
            display_df = box_items.copy()
            display_df["Caixa"] = display_df["Caixa"].apply(
                lambda value: ", ".join(value) if isinstance(value, list) else value
            )
            st.dataframe(display_df, use_container_width=True)

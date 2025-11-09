from __future__ import annotations

from datetime import date
from typing import Dict

import pandas as pd
import streamlit as st

from airtable_client import AirtableClient
from utils import helpers


def render(*, dataframes: Dict[str, pd.DataFrame], client: AirtableClient, refresh_callback) -> None:
    items_df = dataframes.get("Itens", pd.DataFrame())
    boxes_df = dataframes.get("Caixas e Armazéns", pd.DataFrame())
    movements_df = dataframes.get("Movimentos", pd.DataFrame())

    st.subheader("Registar movimento de item")

    if items_df.empty or boxes_df.empty:
        st.warning("É necessário ter itens e caixas registados para movimentar inventário.")
        return

    items_lookup = helpers.build_lookup(items_df)
    box_lookup = helpers.build_lookup(boxes_df)

    with st.form("form-movimento"):
        item_id = st.selectbox(
            "Item",
            options=list(items_lookup.keys()),
            format_func=lambda option: items_lookup[option],
        )
        current_box_id = st.selectbox(
            "Caixa de origem",
            options=list(box_lookup.keys()),
            format_func=lambda option: box_lookup[option],
        )
        destination_box_id = st.selectbox(
            "Caixa de destino",
            options=list(box_lookup.keys()),
            format_func=lambda option: box_lookup[option],
        )
        movement_date = st.date_input("Data do movimento", value=date.today())
        notes = st.text_area("Observações")

        submitted = st.form_submit_button("Registar movimento", use_container_width=True)

    if submitted:
        if current_box_id == destination_box_id:
            st.error("Selecione caixas de origem e destino diferentes.")
            return

        payload = {
            "Item": [item_id],
            "De": [current_box_id],
            "Para": [destination_box_id],
            "Data": movement_date.isoformat(),
            "Observações": notes,
        }

        try:
            client.create_record("Movimentos", payload)
            update_fields = {"Caixa": [destination_box_id]}
            if "Contenção atual" in items_df.columns:
                update_fields["Contenção atual"] = [destination_box_id]
            client.update_record("Itens", item_id, update_fields)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Não foi possível registar o movimento: {exc}")
        else:
            st.success("Movimento registado e item atualizado!")
            refresh_callback()
            st.experimental_rerun()

    st.divider()
    st.subheader("Histórico de movimentos")
    if movements_df.empty:
        st.info("Ainda não existem movimentos registados.")
    else:
        st.dataframe(movements_df, use_container_width=True)

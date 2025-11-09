from __future__ import annotations

from typing import Dict

import pandas as pd
import streamlit as st

from airtable_client import AirtableClient
from utils import helpers


def _select_with_lookup(label: str, options: Dict[str, str]) -> str | None:
    if not options:
        st.warning(f"Não foram encontradas opções para {label.lower()}.")
        return None
    option_id = st.selectbox(
        label,
        options=list(options.keys()),
        format_func=lambda option: options[option],
        key=f"select-{label.lower()}",
    )
    return option_id


def render(*, dataframes: Dict[str, pd.DataFrame], client: AirtableClient, refresh_callback) -> None:
    sections_lookup = helpers.build_lookup(dataframes.get("Secções", pd.DataFrame()))
    locals_df = dataframes.get("Locais", pd.DataFrame())
    sublocals_df = dataframes.get("Sublocais", pd.DataFrame())
    boxes_df = dataframes.get("Caixas e Armazéns", pd.DataFrame())
    items_df = dataframes.get("Itens", pd.DataFrame())

    st.subheader("Adicionar novo item")
    with st.form("form-novo-item"):
        section_id = _select_with_lookup("Secção", sections_lookup)

        if section_id:
            filtered_locals = helpers.filter_by_link(locals_df, "Secção", section_id)
            local_lookup = helpers.build_lookup(filtered_locals)
        else:
            local_lookup = helpers.build_lookup(locals_df)

        local_id = _select_with_lookup("Local", local_lookup) if local_lookup else None

        if local_id:
            filtered_sublocals = helpers.filter_by_link(sublocals_df, "Local", local_id)
            sublocal_lookup = helpers.build_lookup(filtered_sublocals)
        else:
            sublocal_lookup = helpers.build_lookup(sublocals_df)

        sublocal_id = _select_with_lookup("Sublocal", sublocal_lookup) if sublocal_lookup else None

        if sublocal_id:
            filtered_boxes = helpers.filter_by_link(boxes_df, "Sublocal", sublocal_id)
            box_lookup = helpers.build_lookup(filtered_boxes)
        else:
            box_lookup = helpers.build_lookup(boxes_df)

        box_id = _select_with_lookup("Caixa", box_lookup) if box_lookup else None

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nome do item")
            category = st.text_input("Categoria")
            quantity = st.number_input("Quantidade", min_value=0, step=1, value=0)
        with col2:
            unit = st.text_input("Unidade", value="unid.")
            description = st.text_area("Descrição")

        submitted = st.form_submit_button("Guardar no Airtable", use_container_width=True)

    if submitted:
        if not name:
            st.error("Indique o nome do item.")
            return
        if not box_id:
            st.error("Selecione a caixa onde o item será guardado.")
            return

        payload = {
            "Nome": name,
            "Categoria": category,
            "Quantidade": quantity,
            "Unidade": unit,
            "Descrição": description,
            "Caixa": [box_id],
        }

        try:
            client.create_record("Itens", payload)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Não foi possível guardar o item: {exc}")
        else:
            st.success("Item registado com sucesso!")
            refresh_callback()
            st.experimental_rerun()

    st.divider()
    st.subheader("Itens registados")

    if items_df.empty:
        st.info("Ainda não existem itens no Airtable.")
        return

    filter_text = st.text_input("Filtrar por texto", placeholder="Nome, categoria, caixa...")
    filtered_df = items_df.copy()
    if filter_text:
        filter_text_lower = filter_text.lower()
        filtered_df = filtered_df[filtered_df.apply(
            lambda row: filter_text_lower in " ".join(map(str, row.dropna().tolist())).lower(),
            axis=1,
        )]

    st.dataframe(filtered_df, use_container_width=True)

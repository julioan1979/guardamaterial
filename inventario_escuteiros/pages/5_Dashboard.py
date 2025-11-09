from __future__ import annotations

from typing import Dict

import pandas as pd
import plotly.express as px
import streamlit as st

from airtable_client import AirtableClient


def _metric_value(df: pd.DataFrame) -> int:
    return 0 if df is None or df.empty else len(df)


def _count_divergent_boxes(boxes_df: pd.DataFrame) -> int:
    if boxes_df.empty or "Estado" not in boxes_df.columns:
        return 0
    return int((boxes_df["Estado"].astype(str).str.lower() == "divergência").sum())


def render(*, dataframes: Dict[str, pd.DataFrame], client: AirtableClient, refresh_callback) -> None:
    items_df = dataframes.get("Itens", pd.DataFrame())
    boxes_df = dataframes.get("Caixas e Armazéns", pd.DataFrame())
    audits_df = dataframes.get("Auditorias", pd.DataFrame())
    movements_df = dataframes.get("Movimentos", pd.DataFrame())

    st.subheader("Indicadores rápidos")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de itens", _metric_value(items_df))
    col2.metric("Total de caixas", _metric_value(boxes_df))
    col3.metric("Auditorias", _metric_value(audits_df))
    col4.metric("Divergências abertas", _count_divergent_boxes(boxes_df))

    st.divider()

    st.subheader("Itens por categoria")
    if items_df.empty or "Categoria" not in items_df.columns:
        st.info("Ainda não existem dados suficientes para este gráfico.")
    else:
        category_counts = (
            items_df.groupby("Categoria")
            .size()
            .reset_index(name="Quantidade")
            .sort_values(by="Quantidade", ascending=False)
        )
        fig_category = px.bar(category_counts, x="Categoria", y="Quantidade", text="Quantidade")
        fig_category.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_category, use_container_width=True)

    st.subheader("Auditorias por resultado")
    if audits_df.empty or "Resultado" not in audits_df.columns:
        st.info("Sem dados de auditoria para apresentar.")
    else:
        result_counts = (
            audits_df.groupby("Resultado")
            .size()
            .reset_index(name="Total")
        )
        fig_audit = px.pie(result_counts, names="Resultado", values="Total", hole=0.4)
        fig_audit.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_audit, use_container_width=True)

    st.subheader("Movimentos por mês")
    if movements_df.empty or "Data" not in movements_df.columns:
        st.info("Sem registos de movimentos ainda.")
    else:
        movement_dates = pd.to_datetime(movements_df["Data"], errors="coerce")
        valid_movements = movements_df.assign(Data=movement_dates).dropna(subset=["Data"])
        if valid_movements.empty:
            st.info("As datas dos movimentos não estão definidas corretamente.")
        else:
            valid_movements["Mês"] = valid_movements["Data"].dt.to_period("M").astype(str)
            monthly_counts = (
                valid_movements.groupby("Mês")
                .size()
                .reset_index(name="Movimentos")
            )
            fig_movements = px.line(monthly_counts, x="Mês", y="Movimentos", markers=True)
            fig_movements.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_movements, use_container_width=True)

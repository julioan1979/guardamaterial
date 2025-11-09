from __future__ import annotations

from datetime import date
from typing import Dict

import pandas as pd
import streamlit as st

from airtable_client import AirtableClient
from utils import helpers


DEFAULT_RESULTS = ["Conforme", "Divergência", "Revisão necessária"]


def render(*, dataframes: Dict[str, pd.DataFrame], client: AirtableClient, refresh_callback) -> None:
    audits_df = dataframes.get("Auditorias", pd.DataFrame())
    boxes_df = dataframes.get("Caixas e Armazéns", pd.DataFrame())

    st.subheader("Auditorias anteriores")
    if audits_df.empty:
        st.info("Ainda não foram registadas auditorias.")
    else:
        st.dataframe(audits_df, use_container_width=True)

    st.divider()

    if st.button("Nova auditoria", use_container_width=True):
        st.session_state["show_audit_form"] = True

    if st.session_state.get("show_audit_form"):
        st.subheader("Registar nova auditoria")
        box_lookup = helpers.build_lookup(boxes_df)
        with st.form("form-auditoria"):
            box_id = (
                st.selectbox(
                    "Caixa",
                    options=list(box_lookup.keys()),
                    format_func=lambda option: box_lookup[option],
                )
                if box_lookup
                else None
            )
            audit_date = st.date_input("Data", value=date.today())
            responsible = st.text_input("Responsável")
            result = st.selectbox("Resultado", DEFAULT_RESULTS)
            notes = st.text_area("Observações")
            st.caption(
                "Pode carregar uma fotografia ou fornecer um URL já disponível publicamente."
            )
            uploaded_photo = st.file_uploader("Fotografia (opcional)", type=["png", "jpg", "jpeg"])  # noqa: E501
            photo_url = st.text_input("URL da fotografia")

            submitted = st.form_submit_button("Guardar auditoria", use_container_width=True)

        if submitted:
            if not box_id:
                st.error("Selecione a caixa a auditar.")
                return

            attachments = []
            if photo_url:
                attachments.append({"url": photo_url})
            elif uploaded_photo is not None:
                data_url = helpers.encode_file_to_data_url(uploaded_photo)
                if data_url:
                    attachments.append({"url": data_url, "filename": uploaded_photo.name})

            payload = {
                "Caixa": [box_id],
                "Data": audit_date.isoformat(),
                "Responsável": responsible,
                "Resultado": result,
                "Observações": notes,
            }
            if attachments:
                payload["Foto"] = attachments

            try:
                client.create_record("Auditorias", payload)
                client.update_record("Caixas e Armazéns", box_id, {"Estado": result})
            except Exception as exc:  # noqa: BLE001
                st.error(f"Não foi possível guardar a auditoria: {exc}")
            else:
                st.success("Auditoria registada com sucesso!")
                st.session_state.pop("show_audit_form", None)
                refresh_callback()
                st.experimental_rerun()

from __future__ import annotations

from datetime import datetime
from typing import Dict

import streamlit as st


def render_sidebar(app_name: str, pages: Dict[str, str]) -> str:
    st.sidebar.title(app_name)
    st.sidebar.caption("Selecione uma área do inventário para trabalhar.")
    st.sidebar.divider()
    choice = st.sidebar.radio("Páginas", list(pages.keys()), index=0)
    st.sidebar.divider()
    st.sidebar.info(
        "Os dados são sincronizados diretamente com o Airtable. Use o botão de recarregar para obter a versão mais recente."
    )
    return choice


def render_header(section: str, last_updated: datetime | None) -> None:
    st.title(section)
    if last_updated is not None:
        st.caption(f"Última atualização de dados: {last_updated:%d/%m/%Y %H:%M}")
    else:
        st.caption("Última atualização de dados: agora mesmo")


def render_refresh_button(clear_cache_callback) -> None:
    if st.sidebar.button("🔄 Recarregar dados", use_container_width=True):
        clear_cache_callback()
        st.experimental_rerun()

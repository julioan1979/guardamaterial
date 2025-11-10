from __future__ import annotations

import importlib
from datetime import datetime
from typing import Dict

import pandas as pd
import streamlit as st

from airtable_client import AirtableClient
from utils import helpers, layout
from utils.auth import authenticate_user, get_airtable_credentials

APP_NAME = "Inventário Escuteiros"
TABLES = [
    "Secções",
    "Locais",
    "Sublocais",
    "Caixas e Armazéns",
    "Itens",
    "Movimentos",
    "Auditorias",
]
PAGE_MODULES = {
    "Visão Geral": "pages.1_Visão_Geral",
    "Gestão de Itens": "pages.2_Gestão_de_Itens",
    "Auditorias": "pages.3_Auditorias",
    "Movimentos": "pages.4_Movimentos",
    "Dashboard": "pages.5_Dashboard",
}


st.set_page_config(page_title=APP_NAME, layout="wide")


def _get_credentials() -> tuple[str, str]:
    return get_airtable_credentials()


@st.cache_resource
def get_client(api_key: str, base_id: str) -> AirtableClient:
    return AirtableClient(api_key=api_key, base_id=base_id)


@st.cache_data(ttl=300)
def load_table_data(api_key: str, base_id: str, table_name: str) -> pd.DataFrame:
    client = AirtableClient(api_key=api_key, base_id=base_id)
    records = client.list_records(table_name)
    return helpers.records_to_dataframe(records)


def load_all_data(api_key: str, base_id: str) -> Dict[str, pd.DataFrame]:
    data: Dict[str, pd.DataFrame] = {}
    for table in TABLES:
        try:
            data[table] = load_table_data(api_key, base_id, table)
        except Exception as exc:  # noqa: BLE001
            st.warning(f"Não foi possível carregar a tabela '{table}': {exc}")
            data[table] = pd.DataFrame()
    return data


def clear_data_cache() -> None:
    load_table_data.clear()


def _ensure_authenticated() -> bool:
    """Renderiza o formulário de login e valida as credenciais."""
    user = st.session_state.get("user")
    if user:
        return True

    submitted = False
    email = ""
    password = ""
    placeholder = st.empty()
    with placeholder.container():
        st.title(APP_NAME)
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Palavra-passe", type="password")
            submitted = st.form_submit_button("Entrar")
        if not submitted:
            st.info("Autentique-se para aceder ao inventário.")

    if submitted:
        try:
            user = authenticate_user(email, password)
        except RuntimeError as exc:
            st.error(str(exc))
            return False

        if user:
            st.session_state["user"] = user
            placeholder.empty()
            st.success(f"Bem-vindo, {user.get('Email', 'utilizador')}!")
            return True

        st.error("Credenciais inválidas. Confirme o email e a palavra-passe.")

    return False


def main() -> None:
    if not _ensure_authenticated():
        return

    api_key, base_id = _get_credentials()
    client = get_client(api_key, base_id)

    selected_page = layout.render_sidebar(APP_NAME, PAGE_MODULES)
    layout.render_refresh_button(clear_data_cache)

    user = st.session_state.get("user")
    if user:
        st.sidebar.caption(f"Utilizador autenticado: {user.get('Email', 'sem email')}")

    dataframes = load_all_data(api_key, base_id)
    last_updated = helpers.latest_timestamp_from_dataframes(dataframes)
    layout.render_header(APP_NAME, last_updated or datetime.now())

    st.success(
        "Os dados apresentados refletem o estado atual do Airtable. Utilize as páginas laterais para gerir o inventário."
    )

    module_name = PAGE_MODULES[selected_page]
    module = importlib.import_module(module_name)

    render = getattr(module, "render", None)
    if render is None:
        st.error(f"A página '{selected_page}' não possui a função render(dataframes, client, refresh_callback).")
        return

    render(dataframes=dataframes, client=client, refresh_callback=clear_data_cache)


if __name__ == "__main__":
    main()

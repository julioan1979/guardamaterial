"""Streamlit app for scout inventory management backed by Airtable.

Aplicação Streamlit para gestão de inventário das secções de escuteiros.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st
from pyairtable import Api, Table

st.set_page_config(
    page_title="Gestão de Stock - Escuteiros",
    page_icon="🎒",
    layout="wide",
)

SECCOES_PADRAO = [
    "Alcateia",
    "Exploradores",
    "Pioneiros",
    "Caminheiros",
    "Dirigentes",
]


def obter_seccoes_configuradas() -> List[str]:
    return st.session_state.get("seccoes_disponiveis", SECCOES_PADRAO)


@dataclass
class AirtableConfig:
    api_key: str
    base_id: str
    inventory_table: str
    transactions_table: str

    @property
    def is_valid(self) -> bool:
        return all(
            [
                bool(self.api_key.strip()),
                bool(self.base_id.strip()),
                bool(self.inventory_table.strip()),
                bool(self.transactions_table.strip()),
            ]
        )


def _valor_secreto(chaves: List[str], predefinido: str = "") -> str:
    """Tenta obter um valor de ``st.secrets`` suportando níveis hierárquicos."""

    try:
        segredo_atual = st.secrets  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - comportamento depende do runtime
        return predefinido

    for chave in chaves:
        if isinstance(segredo_atual, dict) and chave in segredo_atual:
            segredo_atual = segredo_atual[chave]
        else:
            return predefinido

    if isinstance(segredo_atual, (str, int, float)):
        return str(segredo_atual)

    return predefinido


def _ler_valor_config(chaves_secrets: List[List[str]], env_key: str, fallback: str = "") -> str:
    """Obtém o valor de secrets, depois variáveis de ambiente e, por fim, um default."""

    for chaves in chaves_secrets:
        valor = _valor_secreto(chaves, "")
        if valor:
            return valor

    valor_env = os.getenv(env_key, "")
    if valor_env:
        return valor_env

    return fallback


def obter_configuracao() -> AirtableConfig:
    """Lê as credenciais do Airtable a partir do sidebar, secrets ou variáveis de ambiente."""
    if "airtable_config" not in st.session_state:
        st.session_state.airtable_config = AirtableConfig(
            api_key=_ler_valor_config(
                [["airtable", "api_key"], ["AIRTABLE_API_KEY"]],
                "AIRTABLE_API_KEY",
            ),
            base_id=_ler_valor_config(
                [["airtable", "base_id"], ["AIRTABLE_BASE_ID"]],
                "AIRTABLE_BASE_ID",
            ),
            inventory_table=_ler_valor_config(
                [["airtable", "inventory_table"], ["AIRTABLE_INVENTORY_TABLE"]],
                "AIRTABLE_INVENTORY_TABLE",
                "Inventário",
            ),
            transactions_table=_ler_valor_config(
                [["airtable", "transactions_table"], ["AIRTABLE_TRANSACTIONS_TABLE"]],
                "AIRTABLE_TRANSACTIONS_TABLE",
                "Movimentos",
            ),
        )

    config: AirtableConfig = st.session_state.airtable_config

    with st.sidebar:
        st.header("Configuração do Airtable")
        api_key = st.text_input(
            "API Key",
            value=config.api_key,
            type="password",
            help="Crie uma API Key em https://airtable.com/account",
        )
        base_id = st.text_input(
            "Base ID",
            value=config.base_id,
            help="Identificador da base (ex.: appXXXXXXXXXXXXXX)",
        )
        inventory_table = st.text_input(
            "Tabela de Inventário",
            value=config.inventory_table,
            help="Nome da tabela onde estão os artigos",
        )
        transactions_table = st.text_input(
            "Tabela de Movimentos",
            value=config.transactions_table,
            help="Nome da tabela onde ficam registados os movimentos",
        )
        st.caption(
            "Pode guardar estas variáveis em .streamlit/secrets.toml ou como variáveis de ambiente "
            "para evitar ter de as introduzir sempre."
        )
        seccoes_extra_input = st.text_input(
            "Secções adicionais (separadas por vírgula)",
            value=st.session_state.get("seccoes_extra_input", ""),
            help="Ex.: Lobitos, Guias",
        )
        st.session_state["seccoes_extra_input"] = seccoes_extra_input
        seccoes_extra = [sec.strip() for sec in seccoes_extra_input.split(",") if sec.strip()]
        seccoes_personalizadas = list(dict.fromkeys(SECCOES_PADRAO + seccoes_extra))
        st.session_state["seccoes_disponiveis"] = seccoes_personalizadas

    st.session_state.airtable_config = AirtableConfig(
        api_key=api_key,
        base_id=base_id,
        inventory_table=inventory_table,
        transactions_table=transactions_table,
    )
    return st.session_state.airtable_config


def obter_cliente_airtable(config: AirtableConfig) -> Api:
    """Cria (ou reutiliza) um cliente da API do Airtable.

    O cliente fica em cache na sessão para evitar múltiplas inicializações ao
    longo do ciclo de vida da aplicação Streamlit.
    """

    chave_cliente = (config.api_key, config.base_id)
    cliente_guardado = st.session_state.get("_airtable_client")
    chave_guardada = st.session_state.get("_airtable_client_key")

    if cliente_guardado is None or chave_guardada != chave_cliente:
        st.session_state["_airtable_client"] = Api(config.api_key)
        st.session_state["_airtable_client_key"] = chave_cliente

    return st.session_state["_airtable_client"]


def obter_tabela(config: AirtableConfig, nome_tabela: str) -> Table:
    cliente = obter_cliente_airtable(config)
    return cliente.table(config.base_id, nome_tabela)


@st.cache_data(ttl=60, show_spinner=False)
def carregar_inventario(config: AirtableConfig) -> pd.DataFrame:
    """Obtém todos os artigos do inventário."""
    tabela = obter_tabela(config, config.inventory_table)
    registos = tabela.all()

    dados: List[Dict[str, Optional[str]]] = []
    for registo in registos:
        campos = registo.get("fields", {})
        dados.append(
            {
                "id": registo.get("id"),
                "Artigo": campos.get("Artigo") or campos.get("Nome") or "Sem nome",
                "Secção": campos.get("Secção") or campos.get("Secao") or campos.get("Section"),
                "Quantidade": campos.get("Quantidade", 0),
                "Stock Mínimo": campos.get("Stock Mínimo", 0),
                "Localização": campos.get("Localização") or campos.get("Local"),
                "Notas": campos.get("Notas", ""),
                "Atualizado": campos.get("Atualizado em") or campos.get("updated_at"),
            }
        )

    if not dados:
        return pd.DataFrame(
            columns=[
                "id",
                "Artigo",
                "Secção",
                "Quantidade",
                "Stock Mínimo",
                "Localização",
                "Notas",
                "Atualizado",
            ]
        )

    df = pd.DataFrame(dados)
    df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0).astype(int)
    df["Stock Mínimo"] = pd.to_numeric(df["Stock Mínimo"], errors="coerce").fillna(0).astype(int)
    return df


@st.cache_data(ttl=60, show_spinner=False)
def carregar_movimentos(config: AirtableConfig) -> pd.DataFrame:
    tabela = obter_tabela(config, config.transactions_table)
    registos = tabela.all(sort=[("Data", "desc")])

    dados: List[Dict[str, Optional[str]]] = []
    for registo in registos:
        campos = registo.get("fields", {})
        dados.append(
            {
                "id": registo.get("id"),
                "Data": campos.get("Data"),
                "Artigo": campos.get("Artigo"),
                "Secção": campos.get("Secção") or campos.get("Secao"),
                "Quantidade": campos.get("Quantidade", 0),
                "Responsável": campos.get("Responsável"),
                "Tipo": campos.get("Tipo"),
                "Notas": campos.get("Notas", ""),
            }
        )

    if not dados:
        return pd.DataFrame(
            columns=[
                "id",
                "Data",
                "Artigo",
                "Secção",
                "Quantidade",
                "Responsável",
                "Tipo",
                "Notas",
            ]
        )

    df = pd.DataFrame(dados)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0).astype(int)
    return df


def limpar_caches():
    carregar_inventario.clear()
    carregar_movimentos.clear()


def criar_tabela_movimentos(config: AirtableConfig, movimento: Dict[str, object]) -> None:
    tabela = obter_tabela(config, config.transactions_table)
    tabela.create(movimento)


def atualizar_quantidade(config: AirtableConfig, registo_id: str, nova_quantidade: int) -> None:
    tabela = obter_tabela(config, config.inventory_table)
    tabela.update(
        registo_id,
        {
            "Quantidade": nova_quantidade,
            "Atualizado em": datetime.utcnow().isoformat(),
        },
    )


def criar_registo_inventario(config: AirtableConfig, dados: Dict[str, object]) -> None:
    tabela = obter_tabela(config, config.inventory_table)
    tabela.create(dados | {"Atualizado em": datetime.utcnow().isoformat()})


def atualizar_artigo(config: AirtableConfig, registo_id: str, campos: Dict[str, object]) -> None:
    tabela = obter_tabela(config, config.inventory_table)
    tabela.update(registo_id, campos | {"Atualizado em": datetime.utcnow().isoformat()})


def apagar_artigo(config: AirtableConfig, registo_id: str) -> None:
    tabela = obter_tabela(config, config.inventory_table)
    tabela.delete(registo_id)


def interface_resumo(inventario: pd.DataFrame) -> None:
    st.subheader("Resumo Geral")
    if inventario.empty:
        st.info("Ainda não existem artigos registados.")
        return

    total_artigos = inventario.shape[0]
    total_stock = int(inventario["Quantidade"].sum())
    artigos_em_risco = inventario[inventario["Quantidade"] <= inventario["Stock Mínimo"]]

    col1, col2, col3 = st.columns(3)
    col1.metric("Artigos", total_artigos)
    col2.metric("Quantidade total", total_stock)
    col3.metric("Artigos em alerta", artigos_em_risco.shape[0])

    st.markdown("### Stock por secção")
    seccoes = obter_seccoes_configuradas()
    por_seccao = (
        inventario.groupby("Secção")["Quantidade"].sum().reindex(seccoes, fill_value=0).reset_index()
    )
    st.bar_chart(por_seccao, x="Secção", y="Quantidade")

    if not artigos_em_risco.empty:
        st.warning("Artigos abaixo do stock mínimo:")
        st.dataframe(artigos_em_risco[["Artigo", "Secção", "Quantidade", "Stock Mínimo"]])

    csv_data = inventario.drop(columns=["id"]).to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descarregar inventário (CSV)",
        data=csv_data,
        file_name="inventario_escuteiros.csv",
        mime="text/csv",
    )


def interface_gestao_inventario(config: AirtableConfig, inventario: pd.DataFrame) -> None:
    st.subheader("Gestão de Inventário")
    with st.expander("Adicionar novo artigo", expanded=False):
        with st.form("form_novo_artigo"):
            artigo = st.text_input("Nome do artigo", placeholder="Ex.: Mochila de patrulha")
            seccao = st.selectbox("Secção", options=obter_seccoes_configuradas())
            quantidade = st.number_input("Quantidade inicial", min_value=0, step=1)
            stock_minimo = st.number_input("Stock mínimo", min_value=0, step=1)
            localizacao = st.text_input("Localização", placeholder="Ex.: Armazém principal")
            notas = st.text_area("Notas", placeholder="Observações relevantes")
            submitted = st.form_submit_button("Adicionar")

        if submitted:
            if not artigo.strip():
                st.error("O nome do artigo é obrigatório.")
            else:
                try:
                    criar_registo_inventario(
                        config,
                        {
                            "Artigo": artigo.strip(),
                            "Secção": seccao,
                            "Quantidade": int(quantidade),
                            "Stock Mínimo": int(stock_minimo),
                            "Localização": localizacao.strip(),
                            "Notas": notas.strip(),
                        },
                    )
                    st.success("Artigo adicionado com sucesso!")
                    limpar_caches()
                except Exception as exc:  # pragma: no cover - feedback ao utilizador
                    st.error(f"Erro ao criar o artigo: {exc}")

    st.markdown("### Artigos existentes")
    if inventario.empty:
        st.info("Sem artigos para apresentar.")
        return

    st.dataframe(inventario.drop(columns=["id"]).set_index("Artigo"))

    with st.expander("Atualizar artigo", expanded=False):
        artigos = inventario["Artigo"].tolist()
        selecionado = st.selectbox("Escolha o artigo", options=artigos)
        registo = inventario[inventario["Artigo"] == selecionado].iloc[0]
        seccoes_configuradas = obter_seccoes_configuradas()
        seccao_atual = registo.get("Secção")
        indice_seccao = seccoes_configuradas.index(seccao_atual) if seccao_atual in seccoes_configuradas else 0
        with st.form("form_atualizar_artigo"):
            nova_seccao = st.selectbox(
                "Secção",
                options=seccoes_configuradas,
                index=indice_seccao,
            )
            nova_quantidade = st.number_input(
                "Quantidade",
                min_value=0,
                step=1,
                value=int(registo["Quantidade"]),
            )
            novo_stock_minimo = st.number_input(
                "Stock mínimo",
                min_value=0,
                step=1,
                value=int(registo["Stock Mínimo"]),
            )
            nova_localizacao = st.text_input(
                "Localização",
                value=registo.get("Localização") or "",
            )
            novas_notas = st.text_area("Notas", value=registo.get("Notas") or "")
            remover = st.checkbox(
                "Eliminar artigo do inventário",
                value=False,
                help="Esta ação remove o artigo definitivamente da tabela de inventário.",
            )
            atualizar = st.form_submit_button("Guardar alterações")

        if atualizar:
            try:
                if remover:
                    apagar_artigo(config, registo["id"])
                    st.success("Artigo eliminado do inventário.")
                else:
                    atualizar_artigo(
                        config,
                        registo["id"],
                        {
                            "Secção": nova_seccao,
                            "Quantidade": int(nova_quantidade),
                            "Stock Mínimo": int(novo_stock_minimo),
                            "Localização": nova_localizacao.strip(),
                            "Notas": novas_notas.strip(),
                        },
                    )
                    st.success("Artigo atualizado!")
                limpar_caches()
            except Exception as exc:  # pragma: no cover - feedback ao utilizador
                st.error(f"Não foi possível atualizar o artigo: {exc}")


def interface_movimentos(config: AirtableConfig, inventario: pd.DataFrame) -> None:
    st.subheader("Registo de Movimentos")
    if inventario.empty:
        st.info("Crie primeiro artigos no inventário.")
        return

    with st.form("form_movimento"):
        seccoes_disponiveis = sorted(
            inventario["Secção"].dropna().unique().tolist() or obter_seccoes_configuradas()
        )
        seccao = st.selectbox("Secção", options=seccoes_disponiveis)
        inventario_filtrado = inventario[inventario["Secção"] == seccao]
        artigo_nome = st.selectbox("Artigo", options=inventario_filtrado["Artigo"].tolist())
        registo_atual = inventario_filtrado[inventario_filtrado["Artigo"] == artigo_nome].iloc[0]
        tipo = st.selectbox("Tipo de movimento", options=["Entrada", "Saída"])
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        responsavel = st.text_input("Responsável", placeholder="Nome de quem regista")
        notas = st.text_area("Notas", placeholder="Observações")
        data_movimento = st.date_input("Data", value=datetime.today())
        submitted = st.form_submit_button("Registar movimento")

    if submitted:
        delta = int(quantidade) if tipo == "Entrada" else -int(quantidade)
        nova_quantidade = int(registo_atual["Quantidade"]) + delta
        if nova_quantidade < 0:
            st.error("Não é possível ficar com stock negativo.")
            return
        try:
            atualizar_quantidade(
                config,
                registo_atual["id"],
                nova_quantidade,
            )
            criar_tabela_movimentos(
                config,
                {
                    "Data": data_movimento.isoformat(),
                    "Artigo": artigo_nome,
                    "Secção": seccao,
                    "Quantidade": delta,
                    "Responsável": responsavel.strip(),
                    "Tipo": tipo,
                    "Notas": notas.strip(),
                },
            )
            st.success("Movimento registado com sucesso!")
            limpar_caches()
        except Exception as exc:  # pragma: no cover - feedback ao utilizador
            st.error(f"Erro ao registar movimento: {exc}")

    movimentos = carregar_movimentos(config)
    if movimentos.empty:
        st.info("Ainda sem movimentos registados.")
    else:
        seccoes_movimentos = sorted(
            movimentos["Secção"].dropna().unique().tolist() or obter_seccoes_configuradas()
        )
        seccao_filtro = st.selectbox(
            "Filtrar movimentos por secção",
            options=["Todas"] + seccoes_movimentos,
            key="filtro_movimentos",
        )
        movimentos_filtrados = movimentos
        if seccao_filtro != "Todas":
            movimentos_filtrados = movimentos_filtrados[movimentos_filtrados["Secção"] == seccao_filtro]
        st.dataframe(
            movimentos_filtrados.sort_values("Data", ascending=False).reset_index(drop=True),
            use_container_width=True,
        )
        if not movimentos_filtrados.empty:
            st.download_button(
                "Descarregar movimentos (CSV)",
                data=movimentos_filtrados.to_csv(index=False).encode("utf-8"),
                file_name="movimentos_inventario.csv",
                mime="text/csv",
            )


def interface_documentacao():
    with st.expander("Como preparar a base no Airtable", expanded=False):
        st.markdown(
            """
            ### Estrutura sugerida do Airtable
            - **Tabela de Inventário** (ex.: `Inventário`)
              - `Artigo` (Texto)
              - `Secção` (Lista única com as secções do agrupamento)
              - `Quantidade` (Número)
              - `Stock Mínimo` (Número)
              - `Localização` (Texto)
              - `Notas` (Texto longo)
              - `Atualizado em` (Data/Hora) — preenchido automaticamente pela aplicação.
            - **Tabela de Movimentos** (ex.: `Movimentos`)
              - `Data` (Data)
              - `Artigo` (Texto ou ligação à tabela de Inventário)
              - `Secção` (Texto)
              - `Quantidade` (Número — positivo para entradas e negativo para saídas)
              - `Responsável` (Texto)
              - `Tipo` (Texto — "Entrada" ou "Saída")
              - `Notas` (Texto longo)

            > Sugestão: adicione *views* no Airtable para destacar artigos em ruptura ou movimentos recentes.
            """
        )


def main() -> None:
    st.title("Gestão de Stock do Agrupamento")
    config = obter_configuracao()

    if not config.is_valid:
        st.warning(
            "Introduza as credenciais do Airtable no menu lateral para começar. "
            "Caso ainda não tenha uma base, consulte a documentação abaixo."
        )
        interface_documentacao()
        return

    try:
        inventario = carregar_inventario(config)
    except Exception as exc:  # pragma: no cover - feedback ao utilizador
        st.error(
            "Não foi possível comunicar com o Airtable. Verifique os dados configurados e tente novamente. "
            f"Detalhe técnico: {exc}"
        )
        interface_documentacao()
        return

    tab_inventario, tab_movimentos, tab_resumo, tab_documentacao = st.tabs(
        [
            "Inventário",
            "Movimentos",
            "Resumo",
            "Documentação",
        ]
    )

    with tab_inventario:
        interface_gestao_inventario(config, inventario)

    with tab_movimentos:
        interface_movimentos(config, inventario)

    with tab_resumo:
        interface_resumo(inventario)

    with tab_documentacao:
        interface_documentacao()


if __name__ == "__main__":
    main()

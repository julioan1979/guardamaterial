"""Streamlit app for scout inventory management backed by Airtable.

Aplicação Streamlit para gestão de inventário das secções de escuteiros.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from collections.abc import Mapping
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from pyairtable import Api, Table

from inventario_escuteiros.utils.auth import authenticate_user, get_airtable_credentials

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


def garantir_autenticacao() -> bool:
    """Solicita credenciais ao utilizador e valida-as com o Airtable."""
    utilizador = st.session_state.get("user")
    if utilizador:
        return True

    submitted = False
    email = ""
    password = ""
    placeholder = st.empty()
    with placeholder.container():
        st.subheader("Iniciar sessão")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Palavra-passe", type="password")
            submitted = st.form_submit_button("Entrar")
        if not submitted:
            st.info("Autentique-se para aceder ao inventário do agrupamento.")

    if submitted:
        try:
            utilizador = authenticate_user(email, password)
        except RuntimeError as exc:
            st.error(str(exc))
            return False

        if utilizador:
            st.session_state["user"] = utilizador
            placeholder.empty()
            st.success(f"Bem-vindo, {utilizador.get('Email', 'utilizador')}!")
            return True

        st.error("Credenciais inválidas. Confirme o email e a palavra-passe.")

    return False


@dataclass(frozen=True)
class TableMetadata:
    """Representa uma tabela do Airtable e os respetivos campos conhecidos."""

    nome: str
    campos: Tuple[str, ...] = ()

    @property
    def campos_ordenados(self) -> List[str]:
        """Devolve os campos ordenados alfabeticamente."""

        return sorted(self.campos, key=lambda valor: valor.casefold())


@dataclass(frozen=True)
class BaseMetadata:
    """Metadados simplificados referentes a uma base do Airtable."""

    tabelas: Tuple[TableMetadata, ...] = ()

    @property
    def nomes_tabelas(self) -> List[str]:
        """Lista os nomes das tabelas conhecidos."""

        return [tabela.nome for tabela in self.tabelas]

    def obter_tabela(self, nome: str) -> Optional[TableMetadata]:
        """Procura uma tabela pelos metadados carregados."""

        for tabela in self.tabelas:
            if tabela.nome == nome:
                return tabela
        return None


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


_MISSING = object()


def _obter_valor_mapeamento(mapeamento: Mapping[str, Any], chave: str) -> Any:
    """Obtém um valor de um mapeamento recorrendo a comparação case-insensitive."""

    if chave in mapeamento:
        return mapeamento[chave]

    chave_normalizada = chave.casefold()
    for chave_existente in mapeamento:
        if isinstance(chave_existente, str) and chave_existente.casefold() == chave_normalizada:
            return mapeamento[chave_existente]
    return _MISSING


def _valor_secreto(chaves: List[str], predefinido: str = "") -> str:
    """Tenta obter um valor de ``st.secrets`` suportando níveis hierárquicos."""

    try:
        segredo_atual: Any = st.secrets  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - comportamento depende do runtime
        return predefinido

    for chave in chaves:
        if isinstance(segredo_atual, Mapping):
            segredo_atual = _obter_valor_mapeamento(segredo_atual, chave)
            if segredo_atual is _MISSING:
                return predefinido
            continue

        try:
            segredo_atual = segredo_atual[chave]  # type: ignore[index]
        except Exception:  # pragma: no cover - compatibilidade com objectos personalizados
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


def _parse_metadata_tables(response: object) -> BaseMetadata:
    """Converte a resposta da API de metadados num objeto estruturado."""

    tabelas: List[TableMetadata] = []
    if isinstance(response, dict):
        tabelas_payload = response.get("tables", [])
        if isinstance(tabelas_payload, list):
            for tabela_info in tabelas_payload:
                if not isinstance(tabela_info, dict):
                    continue
                nome = tabela_info.get("name")
                if not isinstance(nome, str):
                    continue
                nome = nome.strip()
                if not nome:
                    continue
                campos_payload = tabela_info.get("fields", [])
                campos: List[str] = []
                if isinstance(campos_payload, list):
                    for campo_info in campos_payload:
                        if not isinstance(campo_info, dict):
                            continue
                        nome_campo = campo_info.get("name")
                        if not isinstance(nome_campo, str):
                            continue
                        nome_campo = nome_campo.strip()
                        if nome_campo:
                            campos.append(nome_campo)
                campos_unicos = tuple(dict.fromkeys(campos))
                tabelas.append(TableMetadata(nome=nome, campos=campos_unicos))
    return BaseMetadata(tabelas=tuple(tabelas))


def _formatar_erro_metadados(exc: Exception, base_id: str) -> RuntimeError:
    """Gera uma mensagem de erro amigável ao falhar a leitura de metadados."""

    mensagem = (
        "Não foi possível obter automaticamente a lista de tabelas do Airtable. "
        "Confirme se a chave tem o scope 'schema.bases.read' e se a base está acessível."
    )
    detalhes = str(exc).strip()
    if detalhes:
        mensagem = f"{mensagem} (base: {base_id}). Detalhe técnico: {detalhes}"
    else:
        mensagem = f"{mensagem} (base: {base_id})."
    return RuntimeError(mensagem)


def _extrair_tipo_erro(payload: Mapping[str, Any]) -> Optional[str]:
    """Obtém o identificador de erro de uma resposta do Airtable."""

    tipo = payload.get("type")
    if isinstance(tipo, str) and tipo.strip():
        return tipo.strip()

    erro_interno = payload.get("error")
    if isinstance(erro_interno, Mapping):
        tipo_interno = erro_interno.get("type")
        if isinstance(tipo_interno, str) and tipo_interno.strip():
            return tipo_interno.strip()

    return None


def _detalhes_erro_airtable(exc: Exception) -> Tuple[Optional[int], Optional[str], str]:
    """Extrai dados relevantes de uma exceção devolvida pela API do Airtable."""

    status_code: Optional[int] = None
    error_type: Optional[str] = None
    mensagem = str(exc).strip()

    resposta = getattr(exc, "response", None)
    if resposta is not None:
        status_code = getattr(resposta, "status_code", None)
        try:
            payload = resposta.json()
        except Exception:  # pragma: no cover - depende do objeto response
            payload = None
        if isinstance(payload, Mapping):
            error_type = _extrair_tipo_erro(payload) or error_type

    error_attr = getattr(exc, "error", None)
    if isinstance(error_attr, Mapping):
        error_type = _extrair_tipo_erro(error_attr) or error_type

    if error_type is None and mensagem:
        correspondencia = re.search(r"[A-Z_]*INVALID[A-Z_]*", mensagem)
        if correspondencia:
            error_type = correspondencia.group(0)

    return status_code, error_type, mensagem


def _formatar_erro_airtable(exc: Exception, config: AirtableConfig) -> str:
    """Constrói uma mensagem informativa para erros devolvidos pelo Airtable."""

    status_code, error_type, mensagem = _detalhes_erro_airtable(exc)

    partes: List[str] = [
        "Não foi possível comunicar com o Airtable. Confirme as credenciais configuradas e tente novamente."
    ]

    if error_type == "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND":
        partes.append(
            "Verifique se o token tem acesso à base configurada "
            f"('{config.base_id}') e se as tabelas '{config.inventory_table}' e "
            f"'{config.transactions_table}' existem com estes nomes. "
            "Pode ajustar os nomes na barra lateral ou através das variáveis "
            "AIRTABLE_INVENTORY_TABLE e AIRTABLE_TRANSACTIONS_TABLE."
        )
    elif status_code == 401:
        partes.append(
            "O Airtable devolveu um erro de autenticação (HTTP 401). "
            "Confirme a chave ou token configurado."
        )
    elif status_code == 404:
        partes.append(
            "O Airtable não encontrou o recurso solicitado (HTTP 404). "
            "Confirme o ID da base e os nomes das tabelas definidos na aplicação."
        )

    if mensagem:
        partes.append(f"Detalhe técnico: {mensagem}")
    elif status_code is not None:
        partes.append(f"Detalhe técnico: HTTP {status_code}")

    return " ".join(parte.strip() for parte in partes if parte.strip())


def _build_airtable_metadata_url(api: Api, base_id: str) -> str:
    """Construir o URL absoluto para consultar os metadados de uma base."""

    return api.build_url(f"meta/bases/{base_id}/tables")


def _request_airtable_metadata(api: Api, base_id: str) -> object:
    """Efetua a chamada HTTP à API de metadados do Airtable."""

    url = _build_airtable_metadata_url(api, base_id)
    return api.request("get", url)


@st.cache_data(ttl=300, show_spinner=False)
def carregar_metadados_base(api_key: str, base_id: str) -> BaseMetadata:
    """Obtém os metadados disponíveis da base configurada no Airtable."""

    api = Api(api_key)
    try:
        response = _request_airtable_metadata(api, base_id)
    except Exception as exc:  # noqa: BLE001 - dependente da API externa
        raise _formatar_erro_metadados(exc, base_id) from exc

    return _parse_metadata_tables(response)


def obter_configuracao() -> AirtableConfig:
    """Obtém a configuração do Airtable usando secrets/variáveis e ajustes no sidebar."""
    api_key, base_id = get_airtable_credentials()

    if "airtable_config" not in st.session_state:
        st.session_state.airtable_config = AirtableConfig(
            api_key=api_key,
            base_id=base_id,
            inventory_table=_ler_valor_config(
                [
                    ["airtable", "inventory_table"],
                    ["AIRTABLE_INVENTORY_TABLE"],
                    ["inventory_table"],
                ],
                "AIRTABLE_INVENTORY_TABLE",
                "Inventário",
            ),
            transactions_table=_ler_valor_config(
                [
                    ["airtable", "transactions_table"],
                    ["AIRTABLE_TRANSACTIONS_TABLE"],
                    ["transactions_table"],
                ],
                "AIRTABLE_TRANSACTIONS_TABLE",
                "Movimentos",
            ),
        )

    config: AirtableConfig = st.session_state.airtable_config

    metadata: Optional[BaseMetadata] = None
    metadata_error: Optional[str] = None

    try:
        metadata = carregar_metadados_base(api_key, base_id)
    except RuntimeError as exc:
        metadata_error = str(exc)

    if metadata is not None:
        st.session_state["_airtable_metadata"] = metadata
        st.session_state.pop("_airtable_metadata_error", None)
    elif metadata_error:
        st.session_state["_airtable_metadata_error"] = metadata_error

    with st.sidebar:
        st.header("Configuração do Airtable")
        st.caption(
            "As credenciais são carregadas automaticamente de st.secrets ou variáveis de ambiente."
        )
        inventory_table = _selecionar_tabela(
            "Tabela de Inventário",
            valor_atual=config.inventory_table,
            metadata=metadata,
            chave="inventory_table",
            ajuda="Nome da tabela onde estão os artigos",
        )
        _mostrar_campos_tabela("Inventário", metadata, inventory_table)
        transactions_table = _selecionar_tabela(
            "Tabela de Movimentos",
            valor_atual=config.transactions_table,
            metadata=metadata,
            chave="transactions_table",
            ajuda="Nome da tabela onde ficam registados os movimentos",
        )
        _mostrar_campos_tabela("Movimentos", metadata, transactions_table)
        seccoes_extra_input = st.text_input(
            "Secções adicionais (separadas por vírgula)",
            value=st.session_state.get("seccoes_extra_input", ""),
            help="Ex.: Lobitos, Guias",
        )
        st.session_state["seccoes_extra_input"] = seccoes_extra_input
        seccoes_extra = [sec.strip() for sec in seccoes_extra_input.split(",") if sec.strip()]
        seccoes_personalizadas = list(dict.fromkeys(SECCOES_PADRAO + seccoes_extra))
        st.session_state["seccoes_disponiveis"] = seccoes_personalizadas

        if metadata_error:
            st.warning(metadata_error)
        elif metadata and metadata.tabelas:
            with st.expander("Tabelas detectadas no Airtable", expanded=False):
                for tabela in metadata.tabelas:
                    st.markdown(f"**{tabela.nome}**")
                    campos = tabela.campos_ordenados
                    if campos:
                        st.caption(", ".join(campos))
                    else:
                        st.caption("Sem campos disponíveis na API de metadados.")

    st.session_state.airtable_config = AirtableConfig(
        api_key=api_key,
        base_id=base_id,
        inventory_table=inventory_table.strip() or config.inventory_table,
        transactions_table=transactions_table.strip() or config.transactions_table,
    )
    return st.session_state.airtable_config


def _selecionar_tabela(
    rotulo: str,
    *,
    valor_atual: str,
    metadata: Optional[BaseMetadata],
    chave: str,
    ajuda: str,
) -> str:
    """Mostra um campo adaptado à informação disponível na API de metadados."""

    if metadata and metadata.tabelas:
        opcoes = list(dict.fromkeys(metadata.nomes_tabelas))
        if valor_atual and valor_atual not in opcoes:
            opcoes.insert(0, valor_atual)
        opcoes.append("Outro (introduzir manualmente)")
        indice = opcoes.index(valor_atual) if valor_atual in opcoes else 0
        escolha = st.selectbox(
            rotulo,
            options=opcoes,
            index=indice,
            key=f"{chave}_select",
            help=f"{ajuda}. Selecionado a partir das tabelas visíveis na base.",
        )
        if escolha == "Outro (introduzir manualmente)":
            return st.text_input(
                f"{rotulo} (manual)",
                value=valor_atual,
                key=f"{chave}_manual",
                help=ajuda,
            )
        return escolha

    return st.text_input(
        rotulo,
        value=valor_atual,
        key=f"{chave}_input",
        help=ajuda,
    )


def _mostrar_campos_tabela(
    titulo: str,
    metadata: Optional[BaseMetadata],
    nome_tabela: str,
) -> None:
    """Apresenta os campos conhecidos para uma tabela selecionada."""

    if not metadata or not nome_tabela:
        return

    tabela_info = metadata.obter_tabela(nome_tabela)
    if not tabela_info:
        return

    campos = tabela_info.campos_ordenados
    if not campos:
        st.caption(f"Estrutura conhecida para {titulo}: sem campos listados na API.")
        return

    st.caption(f"Estrutura conhecida para {titulo}: {', '.join(campos)}.")


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
    metadata = st.session_state.get("_airtable_metadata")
    metadata_error = st.session_state.get("_airtable_metadata_error")

    if isinstance(metadata, BaseMetadata) and metadata.tabelas:
        st.markdown("### Tabelas detectadas automaticamente")
        for tabela in metadata.tabelas:
            campos_lista = tabela.campos_ordenados
            campos = ", ".join(campos_lista) if campos_lista else "(sem campos listados)"
            st.markdown(f"- **{tabela.nome}**: {campos}")
    elif isinstance(metadata_error, str) and metadata_error:
        st.warning(metadata_error)

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
            - **Tabela de Utilizadores** (ex.: `Utilizadores`)
              - `Email` (Texto — um endereço por registo)
              - `PasswordHash` (Texto — hash Bcrypt da palavra-passe, recomendado)
              - `Palavra-passe` (Texto — suporte temporário para migração; mantenha-o vazio após configurar os hashes)

            > Sugestão: adicione *views* no Airtable para destacar artigos em ruptura ou movimentos recentes.
            > 
            > Compatibilidade temporária: a aplicação aceita credenciais na coluna `Palavra-passe` para facilitar a migração. 
            > Gere hashes Bcrypt para cada registo, preencha `PasswordHash` e, depois de confirmar o acesso, apague os valores 
            > em texto simples.
            """
        )


def main() -> None:
    st.title("Gestão de Stock do Agrupamento")
    if not garantir_autenticacao():
        return

    try:
        config = obter_configuracao()
    except RuntimeError as exc:
        st.error(str(exc))
        interface_documentacao()
        return

    if not config.is_valid:
        st.error(
            "Configuração do Airtable incompleta. Defina as credenciais através de st.secrets "
            "ou variáveis de ambiente."
        )
        interface_documentacao()
        return

    try:
        inventario = carregar_inventario(config)
    except Exception as exc:  # pragma: no cover - feedback ao utilizador
        st.error(_formatar_erro_airtable(exc, config))
        interface_documentacao()
        return

    utilizador = st.session_state.get("user")
    if utilizador:
        st.sidebar.caption(f"Utilizador autenticado: {utilizador.get('Email', 'sem email')}")

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

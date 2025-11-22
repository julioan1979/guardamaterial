from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

import streamlit as st
from pyairtable import Api, Table

ENV_API_KEY = "AIRTABLE_API_KEY"
ENV_BASE_ID = "AIRTABLE_BASE_ID"


@dataclass
class AirtableClient:
    """Pequeno wrapper em torno da API do Airtable."""

    api_key: str
    base_id: str
    _cache: Dict[str, Table] = field(default_factory=dict, init=False, repr=False)

    def get_table(self, table_name: str) -> Table:
        if table_name not in self._cache:
            self._cache[table_name] = Table(self.api_key, self.base_id, table_name)
        return self._cache[table_name]

    def list_records(
        self,
        table_name: str,
        fields: Optional[Iterable[str]] = None,
        formula: Optional[str] = None,
        max_records: Optional[int] = None,
        view: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        table = self.get_table(table_name)
        return table.all(fields=fields, formula=formula, max_records=max_records, view=view)

    def create_record(self, table_name: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        table = self.get_table(table_name)
        return table.create(fields)

    def update_record(self, table_name: str, record_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        table = self.get_table(table_name)
        return table.update(record_id, fields)

    def batch_update(self, table_name: str, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        table = self.get_table(table_name)
        return table.batch_update(records)

    def delete_record(self, table_name: str, record_id: str) -> Dict[str, Any]:
        table = self.get_table(table_name)
        return table.delete(record_id)


def _obter_valor_mapeamento(mapeamento: Mapping[str, Any], chave: str) -> Any:
    """Obtém valores de um mapeamento considerando comparações case-insensitive."""

    try:
        if chave in mapeamento:
            return mapeamento[chave]
    except Exception:  # pragma: no cover - depende da origem do mapeamento
        return None

    chave_normalizada = chave.casefold()
    for chave_existente in mapeamento:
        if isinstance(chave_existente, str) and chave_existente.casefold() == chave_normalizada:
            return mapeamento[chave_existente]
    return None


def _valor_secreto(caminho: Tuple[str, ...]) -> str:
    """Tenta ler um valor de ``st.secrets`` seguindo o caminho fornecido."""

    try:
        segredo_atual: Any = st.secrets  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - dependente do runtime Streamlit
        return ""

    for chave in caminho:
        if isinstance(segredo_atual, Mapping):
            segredo_atual = _obter_valor_mapeamento(segredo_atual, chave)
            if segredo_atual is None:
                return ""
            continue

        try:
            segredo_atual = segredo_atual[chave]  # type: ignore[index]
        except Exception:  # pragma: no cover - compatibilidade com objectos secrets customizados
            return ""

    if isinstance(segredo_atual, (str, int, float)):
        return str(segredo_atual)
    return ""


def _ler_credencial(*caminhos: Tuple[str, ...]) -> str:
    """Procura uma credencial nos secrets ou nas variáveis de ambiente."""

    for caminho in caminhos:
        valor = _valor_secreto(caminho)
        if valor:
            return valor

    if caminhos:
        env_key = caminhos[0][-1]
        return os.getenv(env_key, "")
    return ""


def obter_credenciais_do_ambiente() -> Tuple[str, str]:
    """Lê as credenciais do Airtable definidas em st.secrets ou no ambiente."""

    api_key = _ler_credencial((ENV_API_KEY,), ("airtable", "api_key"), ("api_key",))
    base_id = _ler_credencial((ENV_BASE_ID,), ("airtable", "base_id"), ("base_id",))
    missing = [nome for nome, valor in ((ENV_API_KEY, api_key), (ENV_BASE_ID, base_id)) if not valor]
    if missing:
        raise RuntimeError(
            "Credenciais do Airtable em falta: " + ", ".join(missing)
        )
    return api_key or "", base_id or ""


def _resolver_credenciais(
    api_key: Optional[str] = None, base_id: Optional[str] = None
) -> Tuple[str, str]:
    """Determina as credenciais a utilizar, recorrendo ao ambiente se necessário."""

    if api_key and base_id:
        return api_key, base_id

    env_api_key, env_base_id = obter_credenciais_do_ambiente()
    return api_key or env_api_key, base_id or env_base_id


def get_default_client(
    api_key: Optional[str] = None, base_id: Optional[str] = None
) -> AirtableClient:
    """Instancia um cliente Airtable reutilizando as credenciais fornecidas."""

    resolved_api_key, resolved_base_id = _resolver_credenciais(api_key, base_id)
    return AirtableClient(api_key=resolved_api_key, base_id=resolved_base_id)


def listar_tabelas(
    *, api_key: Optional[str] = None, base_id: Optional[str] = None
) -> List[Dict[str, str]]:
    """Devolve a lista de tabelas da base configurada no Airtable."""

    resolved_api_key, resolved_base_id = _resolver_credenciais(api_key, base_id)
    api = Api(resolved_api_key)
    url = api.build_url(f"meta/bases/{resolved_base_id}/tables")
    resposta = api.request("get", url)

    tabelas: List[Dict[str, str]] = []
    if isinstance(resposta, dict):
        for table in resposta.get("tables", []):
            if not isinstance(table, dict):
                continue
            nome = table.get("name")
            table_id = table.get("id")
            if isinstance(nome, str) and nome.strip() and isinstance(table_id, str) and table_id.strip():
                tabelas.append({"name": nome.strip(), "id": table_id.strip()})
    return tabelas


def listar_registos(
    table_name: str,
    *,
    campos: Optional[Iterable[str]] = None,
    formula: Optional[str] = None,
    max_registos: Optional[int] = None,
    vista: Optional[str] = None,
    api_key: Optional[str] = None,
    base_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lê registos de uma tabela utilizando o cliente configurado."""

    client = get_default_client(api_key=api_key, base_id=base_id)
    return client.list_records(
        table_name,
        fields=campos,
        formula=formula,
        max_records=max_registos,
        view=vista,
    )

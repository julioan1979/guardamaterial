from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

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


def obter_credenciais_do_ambiente() -> Tuple[str, str]:
    """Lê as credenciais do Airtable definidas nas variáveis de ambiente."""

    api_key = os.getenv(ENV_API_KEY)
    base_id = os.getenv(ENV_BASE_ID)
    missing = [
        nome
        for nome, valor in ((ENV_API_KEY, api_key), (ENV_BASE_ID, base_id))
        if not valor
    ]
    if missing:
        raise RuntimeError(
            "Variáveis de ambiente em falta para comunicar com o Airtable: "
            + ", ".join(missing)
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

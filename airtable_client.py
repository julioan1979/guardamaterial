"""Cliente simples para interação com a API do Airtable."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, Dict, Optional

import requests
import streamlit as st

API_BASE_URL = "https://api.airtable.com/v0"


def _obter_valor_mapeamento(mapeamento: Mapping[str, Any], chave: str) -> Any:
    """Lê uma chave de forma case-insensitive a partir de um mapeamento."""

    try:
        if chave in mapeamento:
            return mapeamento[chave]
    except Exception:  # pragma: no cover - depende da implementação de secrets
        return None

    chave_normalizada = chave.casefold()
    for chave_existente in mapeamento:
        if isinstance(chave_existente, str) and chave_existente.casefold() == chave_normalizada:
            return mapeamento[chave_existente]
    return None


def _valor_secreto(caminho: list[str]) -> str:
    """Tenta obter um valor do ``st.secrets`` percorrendo o caminho indicado."""

    try:
        segredo_atual: Any = st.secrets  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - depende do runtime
        return ""

    for chave in caminho:
        if isinstance(segredo_atual, Mapping):
            segredo_atual = _obter_valor_mapeamento(segredo_atual, chave)
            if segredo_atual is None:
                return ""
            continue

        try:
            segredo_atual = segredo_atual[chave]  # type: ignore[index]
        except Exception:  # pragma: no cover - compatibilidade com objectos personalizados
            return ""

    if isinstance(segredo_atual, (str, int, float)):
        return str(segredo_atual)
    return ""


def _ler_credencial(chaves_secrets: list[list[str]], env_key: str) -> str:
    """Obtém uma credencial a partir de ``st.secrets`` ou variáveis de ambiente."""

    for caminho in chaves_secrets:
        valor = _valor_secreto(caminho)
        if valor:
            return valor

    return os.getenv(env_key, "")


def _obter_credenciais() -> Dict[str, str]:
    """Obtém as credenciais do Airtable a partir de secrets ou variáveis de ambiente."""

    api_key = _ler_credencial([["AIRTABLE_API_KEY"], ["airtable", "api_key"], ["api_key"]], "AIRTABLE_API_KEY")
    base_id = _ler_credencial([["AIRTABLE_BASE_ID"], ["airtable", "base_id"], ["base_id"]], "AIRTABLE_BASE_ID")
    if not api_key or not base_id:
        raise EnvironmentError(
            "Defina AIRTABLE_API_KEY e AIRTABLE_BASE_ID em st.secrets ou como variáveis de ambiente."
        )
    return {"api_key": api_key, "base_id": base_id}


def _executar_requisicao(
    metodo: str,
    url: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Executa uma requisição HTTP e devolve o JSON ou erro correspondente."""

    credenciais = _obter_credenciais()
    headers = {
        "Authorization": f"Bearer {credenciais['api_key']}",
        "Content-Type": "application/json",
    }

    response = requests.request(metodo, url, headers=headers, json=payload, params=params, timeout=30)

    try:
        response.raise_for_status()
    except requests.HTTPError:
        try:
            corpo = response.json()
        except ValueError:
            corpo = {"erro": response.text}
        corpo.setdefault("status_code", response.status_code)
        return corpo

    try:
        return response.json()
    except ValueError:
        return {"status_code": response.status_code, "conteudo": response.text}


def listar_tabelas() -> Dict[str, Any]:
    """Lista todas as tabelas disponíveis na base Airtable configurada."""

    credenciais = _obter_credenciais()
    url = f"{API_BASE_URL}/meta/bases/{credenciais['base_id']}/tables"
    return _executar_requisicao("GET", url)


def listar_registos(tabela: str, parametros: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Obtém todos os registos de uma tabela específica."""

    credenciais = _obter_credenciais()
    url = f"{API_BASE_URL}/{credenciais['base_id']}/{tabela}"
    return _executar_requisicao("GET", url, params=parametros)


def obter_registo(tabela: str, record_id: str) -> Dict[str, Any]:
    """Obtém um registo específico de uma tabela do Airtable."""

    credenciais = _obter_credenciais()
    url = f"{API_BASE_URL}/{credenciais['base_id']}/{tabela}/{record_id}"
    return _executar_requisicao("GET", url)


def criar_registo(tabela: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    """Cria um novo registo com os dados fornecidos."""

    credenciais = _obter_credenciais()
    url = f"{API_BASE_URL}/{credenciais['base_id']}/{tabela}"
    payload = {"fields": dados}
    return _executar_requisicao("POST", url, payload=payload)


def atualizar_registo(tabela: str, record_id: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    """Atualiza um registo existente com os dados fornecidos."""

    credenciais = _obter_credenciais()
    url = f"{API_BASE_URL}/{credenciais['base_id']}/{tabela}/{record_id}"
    payload = {"fields": dados}
    return _executar_requisicao("PATCH", url, payload=payload)


def apagar_registo(tabela: str, record_id: str) -> Dict[str, Any]:
    """Apaga um registo específico da tabela indicada."""

    credenciais = _obter_credenciais()
    url = f"{API_BASE_URL}/{credenciais['base_id']}/{tabela}/{record_id}"
    return _executar_requisicao("DELETE", url)


if __name__ == "__main__":
    print("Tabelas disponíveis:")
    print(listar_tabelas())

    print("\nRegistos da tabela 'Materiais':")
    print(listar_registos("Materiais"))

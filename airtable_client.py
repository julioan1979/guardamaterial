"""Cliente simples para interação com a API do Airtable."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

API_BASE_URL = "https://api.airtable.com/v0"


def _obter_credenciais() -> Dict[str, str]:
    """Obtém as credenciais do Airtable a partir de variáveis de ambiente."""

    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    if not api_key or not base_id:
        raise EnvironmentError(
            "As variáveis de ambiente AIRTABLE_API_KEY e AIRTABLE_BASE_ID devem estar definidas."
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

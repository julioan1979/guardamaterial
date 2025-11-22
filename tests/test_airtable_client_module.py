from pathlib import Path
from typing import Any, Dict
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from inventario_escuteiros import airtable_client


class DummyApi:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.last_method: str | None = None
        self.last_url: str | None = None

    def build_url(self, path: str) -> str:
        return f"https://api.airtable.com/v0/{path}"

    def request(self, method: str, url: str) -> Dict[str, Any]:
        self.last_method = method
        self.last_url = url
        return {
            "tables": [
                {"name": "Itens", "id": "tbl1"},
                {"name": "  Movimentos  ", "id": "tbl2"},
                {"name": "Sem ID"},
                {"id": "tbl3"},
                "invalid",
            ]
        }


def test_obter_credenciais_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(airtable_client.ENV_API_KEY, "key123")
    monkeypatch.setenv(airtable_client.ENV_BASE_ID, "base123")

    assert airtable_client.obter_credenciais_do_ambiente() == ("key123", "base123")


def test_obter_credenciais_do_ambiente_com_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(airtable_client.ENV_API_KEY, raising=False)
    monkeypatch.delenv(airtable_client.ENV_BASE_ID, raising=False)
    monkeypatch.setattr(
        airtable_client.st,
        "secrets",
        {"AIRTABLE_API_KEY": "secret_key", "AIRTABLE_BASE_ID": "secret_base"},
        raising=False,
    )

    assert airtable_client.obter_credenciais_do_ambiente() == ("secret_key", "secret_base")


def test_obter_credenciais_do_ambiente_erro(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(airtable_client.ENV_API_KEY, raising=False)
    monkeypatch.delenv(airtable_client.ENV_BASE_ID, raising=False)

    with pytest.raises(RuntimeError) as exc:
        airtable_client.obter_credenciais_do_ambiente()

    assert airtable_client.ENV_API_KEY in str(exc.value)


def test_listar_tabelas_com_normalizacao(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(airtable_client.ENV_API_KEY, "token")
    monkeypatch.setenv(airtable_client.ENV_BASE_ID, "base")
    monkeypatch.setattr(airtable_client, "Api", DummyApi)

    tables = airtable_client.listar_tabelas()

    assert tables == [
        {"name": "Itens", "id": "tbl1"},
        {"name": "Movimentos", "id": "tbl2"},
    ]


def test_listar_registos_utiliza_cliente(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {}

    class DummyClient:
        def list_records(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
            called["args"] = args
            called["kwargs"] = kwargs
            return [
                {"id": "rec1", "fields": {"Nome": "Martelo"}},
                {"id": "rec2", "fields": {"Nome": "Serrote"}},
            ]

    def fake_get_default_client(*, api_key=None, base_id=None):
        called["api_key"] = api_key
        called["base_id"] = base_id
        return DummyClient()

    monkeypatch.setattr(airtable_client, "get_default_client", fake_get_default_client)

    result = airtable_client.listar_registos(
        "Materiais", campos=("Nome",), formula="{Nome} != ''", max_registos=3, vista="Principal"
    )

    assert called["api_key"] is None
    assert called["base_id"] is None
    assert called["args"] == ("Materiais",)
    assert called["kwargs"] == {
        "fields": ("Nome",),
        "formula": "{Nome} != ''",
        "max_records": 3,
        "view": "Principal",
    }
    assert result[0]["fields"]["Nome"] == "Martelo"

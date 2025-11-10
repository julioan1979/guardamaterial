"""Testes para o processamento de metadados do Airtable na aplicação principal."""

from importlib import util
from pathlib import Path
import sys
from types import SimpleNamespace


def _load_app_module():
    """Carrega o módulo ``app`` diretamente a partir do ficheiro fonte."""

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    app_path = project_root / "app.py"
    spec = util.spec_from_file_location("app_module_for_tests", app_path)
    if spec is None or spec.loader is None:  # pragma: no cover - proteção adicional
        raise RuntimeError("Não foi possível carregar o módulo app.py para os testes.")
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return module


app_module = _load_app_module()

BaseMetadata = app_module.BaseMetadata
TableMetadata = app_module.TableMetadata
_parse_metadata_tables = app_module._parse_metadata_tables
_build_airtable_metadata_url = app_module._build_airtable_metadata_url
_request_airtable_metadata = app_module._request_airtable_metadata


def test_parse_metadata_tables_extracts_tables_and_fields() -> None:
    response = {
        "tables": [
            {
                "name": "Inventário",
                "fields": [
                    {"name": "Artigo"},
                    {"name": "Quantidade"},
                    {"name": "Quantidade"},  # duplicado intencionalmente
                ],
            },
            {
                "name": "Movimentos",
                "fields": [
                    {"name": "Data"},
                    {"name": "Notas"},
                ],
            },
        ]
    }

    metadata = _parse_metadata_tables(response)

    assert metadata.nomes_tabelas == ["Inventário", "Movimentos"]
    inventario = metadata.obter_tabela("Inventário")
    assert inventario is not None
    assert inventario.campos_ordenados == ["Artigo", "Quantidade"]


def test_parse_metadata_tables_ignores_invalid_entries() -> None:
    response = {
        "tables": [
            None,
            {"name": "  "},
            {
                "name": "Secções",
                "fields": [
                    {"name": "Nome"},
                    {"name": ""},
                    {"nome": "Campo inválido"},
                ],
            },
        ]
    }

    metadata = _parse_metadata_tables(response)

    assert metadata.nomes_tabelas == ["Secções"]
    secoes = metadata.obter_tabela("Secções")
    assert secoes is not None
    assert secoes.campos_ordenados == ["Nome"]


def test_base_metadata_obter_tabela_returns_none_for_unknown() -> None:
    metadata = BaseMetadata(tabelas=(TableMetadata(nome="Inventário", campos=("Artigo",)),))

    assert metadata.obter_tabela("Inexistente") is None


def test_valor_secreto_supports_case_insensitive_lookup() -> None:
    original_st = app_module.st
    app_module.st = SimpleNamespace(secrets={"AIRTABLE": {"API_KEY": "Token-123"}})

    try:
        valor = app_module._valor_secreto(["airtable", "api_key"])
    finally:
        app_module.st = original_st

    assert valor == "Token-123"


def test_valor_secreto_supports_lowercase_top_level_keys() -> None:
    original_st = app_module.st
    app_module.st = SimpleNamespace(secrets={"airtable_base_id": "baseXYZ"})

    try:
        valor = app_module._valor_secreto(["AIRTABLE_BASE_ID"])
    finally:
        app_module.st = original_st

    assert valor == "baseXYZ"


def test_build_airtable_metadata_url_uses_api_build_url() -> None:
    class DummyApi:
        def __init__(self) -> None:
            self.called_with: str | None = None

        def build_url(self, path: str) -> str:
            self.called_with = path
            return f"https://example.test/{path}"

    api = DummyApi()

    url = _build_airtable_metadata_url(api, "base123")

    assert url == "https://example.test/meta/bases/base123/tables"
    assert api.called_with == "meta/bases/base123/tables"


def test_request_airtable_metadata_invokes_api_request(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class DummyApi:
        def build_url(self, path: str) -> str:
            return f"https://example.test/{path}"

        def request(self, method: str, url: str) -> object:
            captured["method"] = method
            captured["url"] = url
            return {"tables": []}

    api = DummyApi()

    response = _request_airtable_metadata(api, "baseXYZ")

    assert response == {"tables": []}
    assert captured == {
        "method": "get",
        "url": "https://example.test/meta/bases/baseXYZ/tables",
    }

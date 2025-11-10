"""Testes para o verificador de tabelas do Airtable."""

from scripts.check_airtable_tables import (
    DEFAULT_EXPECTED_TABLES,
    EXPECTED_FIELDS,
    AirtableTablesChecker,
)


def test_expected_tables_match_application_domain() -> None:
    """Validar que o conjunto de tabelas esperadas está atualizado."""

    assert DEFAULT_EXPECTED_TABLES == {"Inventário", "Movimentos", "Utilizadores"}


def test_expected_fields_for_each_table_are_defined() -> None:
    """Garantir que os campos esperados incluem as colunas críticas usadas pela app."""

    assert EXPECTED_FIELDS["Inventário"] == {
        "Artigo",
        "Secção",
        "Quantidade",
        "Stock Mínimo",
        "Localização",
        "Notas",
        "Atualizado em",
    }
    assert EXPECTED_FIELDS["Movimentos"] == {
        "Data",
        "Artigo",
        "Secção",
        "Quantidade",
        "Responsável",
        "Tipo",
        "Notas",
    }
    assert EXPECTED_FIELDS["Utilizadores"] == {
        "Email",
        "PasswordHash",
        "Palavra-passe",
    }


def test_table_comparison_reports_differences() -> None:
    """O relatório deve sinalizar tabelas e campos em falta ou inesperados."""

    checker = AirtableTablesChecker(
        api_key="key",
        base_id="base",
        expected_tables=DEFAULT_EXPECTED_TABLES,
        expected_fields=EXPECTED_FIELDS,
    )

    # Simula uma base com uma tabela adicional e outra em falta.
    checker.list_tables = lambda: {"Inventário", "Movimentos", "Extra"}  # type: ignore[assignment]
    checker.fetch_table_fields = lambda: {
        "Inventário": {"Artigo", "Quantidade", "Notas"},
        "Movimentos": {
            "Data",
            "Artigo",
            "Secção",
            "Quantidade",
            "Responsável",
            "Tipo",
            "Notas",
        },
        "Extra": {"Coluna"},
    }  # type: ignore[assignment]

    comparison = checker.compare()

    assert comparison.missing_tables == {"Utilizadores"}
    assert comparison.unexpected_tables == {"Extra"}

    inventario_diff = comparison.field_differences["Inventário"]
    assert inventario_diff.missing == {"Secção", "Stock Mínimo", "Localização", "Atualizado em"}
    assert inventario_diff.unexpected == set()

    extra_diff = comparison.field_differences["Extra"]
    assert extra_diff.expected == set()
    assert extra_diff.unexpected == {"Coluna"}


def test_fetch_tables_metadata_queries_meta_endpoint(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class DummyApi:
        def __init__(self, api_key: str) -> None:
            captured.setdefault("api_keys", []).append(api_key)

        def build_url(self, path: str) -> str:
            captured["path"] = path
            return f"https://example.test/{path}"

        def request(self, method: str, url: str) -> object:
            captured["method"] = method
            captured["url"] = url
            captured["requests"] = captured.get("requests", 0) + 1
            return {
                "tables": [
                    {
                        "name": "Inventário",
                        "fields": [
                            {"name": "Artigo"},
                            {"name": ""},
                            {"nome": "Inválido"},
                        ],
                    },
                    {"name": ""},
                    None,
                ]
            }

    monkeypatch.setattr("scripts.check_airtable_tables.Api", DummyApi)

    checker = AirtableTablesChecker(
        api_key="token123",
        base_id="baseXYZ",
        expected_tables=(),
    )

    metadata_first = checker.fetch_tables_metadata()
    metadata_second = checker.fetch_tables_metadata()

    assert metadata_first == metadata_second == [
        {"name": "Inventário", "fields": [{"name": "Artigo"}]}
    ]
    assert captured["path"] == "meta/bases/baseXYZ/tables"
    assert captured["method"] == "get"
    assert captured["url"] == "https://example.test/meta/bases/baseXYZ/tables"
    assert captured["requests"] == 1

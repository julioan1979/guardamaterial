"""Ferramenta de verificação da estrutura configurada no Airtable.

Este script liga-se à API do Airtable usando as credenciais expostas nas
variáveis de ambiente ``AIRTABLE_API_KEY`` e ``AIRTABLE_BASE_ID`` para listar
as tabelas existentes na base e recolher a respetiva configuração de campos.
A lista resultante é comparada com a estrutura esperada pela aplicação
Streamlit para confirmar se existe correspondência.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterable

from pyairtable import Api


EXPECTED_FIELDS: Dict[str, set[str]] = {
    "Secções": {"Nome"},
    "Locais": {"Nome", "Secção"},
    "Sublocais": {"Nome", "Local"},
    "Caixas e Armazéns": {"Nome", "Sublocal", "Estado"},
    "Itens": {"Nome", "Categoria", "Quantidade", "Unidade", "Descrição", "Caixa", "Contenção atual"},
    "Movimentos": {"Item", "De", "Para", "Data", "Observações"},
    "Auditorias": {"Caixa", "Data", "Responsável", "Resultado", "Observações", "Foto"},
    "Inventário": {"Item", "Quantidade", "Caixa"},
    "Utilizadores": {"Email", "PasswordHash", "Palavra-passe"},
}


DEFAULT_EXPECTED_TABLES = set(EXPECTED_FIELDS)


@dataclass(frozen=True)
class FieldComparison:
    """Resultado da comparação de colunas para uma tabela específica."""

    expected: set[str]
    actual: set[str]

    @property
    def missing(self) -> set[str]:
        """Campos esperados que não foram encontrados na tabela."""

        return self.expected - self.actual

    @property
    def unexpected(self) -> set[str]:
        """Campos presentes na tabela mas não previstos."""

        return self.actual - self.expected


@dataclass(frozen=True)
class TableComparison:
    """Resultado da comparação entre tabelas esperadas e encontradas."""

    expected_tables: set[str]
    actual_tables: set[str]
    field_differences: Dict[str, FieldComparison]

    @property
    def missing_tables(self) -> set[str]:
        """Tabelas esperadas que não foram encontradas na base."""

        return self.expected_tables - self.actual_tables

    @property
    def unexpected_tables(self) -> set[str]:
        """Tabelas presentes na base mas não previstas pelo código."""

        return self.actual_tables - self.expected_tables

    @property
    def has_field_discrepancies(self) -> bool:
        """Indicar se existe pelo menos uma tabela com diferenças de campos."""

        return any(diff.missing or diff.unexpected for diff in self.field_differences.values())

    @property
    def has_discrepancies(self) -> bool:
        """Determinar se existem divergências em tabelas ou campos."""

        return bool(self.missing_tables or self.unexpected_tables or self.has_field_discrepancies)


class AirtableTablesChecker:
    """Componente responsável por verificar as tabelas disponíveis no Airtable."""

    def __init__(
        self,
        api_key: str,
        base_id: str,
        expected_tables: Iterable[str],
        expected_fields: Dict[str, Iterable[str]] | None = None,
    ):
        self.api_key = api_key
        self.base_id = base_id
        self.expected_tables = set(expected_tables)
        self.expected_fields: Dict[str, set[str]] = {
            table: set(fields) for table, fields in (expected_fields or {}).items()
        }

    def list_tables(self) -> set[str]:
        """Lê a lista de tabelas disponíveis na base configurada."""

        api = Api(self.api_key)
        base = api.base(self.base_id)
        return {table.name for table in base.tables()}

    def fetch_table_fields(self) -> Dict[str, set[str]]:
        """Obter os campos configurados em cada tabela via API de metadados."""

        api = Api(self.api_key)
        response = api.request("get", f"/meta/bases/{self.base_id}/tables")
        tables_info = response.get("tables", []) if isinstance(response, dict) else []
        fields_by_table: Dict[str, set[str]] = {}
        for table in tables_info:
            name = table.get("name")
            if not isinstance(name, str) or not name:
                continue
            table_fields = {
                field.get("name")
                for field in table.get("fields", [])
                if isinstance(field, dict) and isinstance(field.get("name"), str)
            }
            fields_by_table[name] = {field for field in table_fields if field}
        return fields_by_table

    def compare(self) -> TableComparison:
        """Compara as tabelas esperadas com as detectadas via API."""

        actual_tables = self.list_tables()
        actual_fields = self.fetch_table_fields()

        tables_to_check = self.expected_tables | actual_tables | set(actual_fields)
        field_differences: Dict[str, FieldComparison] = {}
        for table in tables_to_check:
            expected_fields = self.expected_fields.get(table, set())
            actual_table_fields = actual_fields.get(table, set())
            field_differences[table] = FieldComparison(
                expected=expected_fields,
                actual=actual_table_fields,
            )

        return TableComparison(
            expected_tables=self.expected_tables,
            actual_tables=actual_tables,
            field_differences=field_differences,
        )


def _read_env_var(name: str) -> str:
    """Obtém uma variável de ambiente e falha explicitamente se estiver ausente."""

    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"A variável de ambiente '{name}' não está definida. Configure-a antes de continuar."
        )
    return value


def main() -> None:
    """Executa a verificação e apresenta um relatório resumido no terminal."""

    api_key = _read_env_var("AIRTABLE_API_KEY")
    base_id = _read_env_var("AIRTABLE_BASE_ID")
    checker = AirtableTablesChecker(
        api_key=api_key,
        base_id=base_id,
        expected_tables=DEFAULT_EXPECTED_TABLES,
        expected_fields=EXPECTED_FIELDS,
    )
    comparison = checker.compare()

    print("Tabelas esperadas:")
    for table in sorted(comparison.expected_tables):
        print(f"  - {table}")

    print("\nTabelas obtidas via API:")
    for table in sorted(comparison.actual_tables):
        print(f"  - {table}")

    if comparison.missing_tables:
        print("\n⚠️  Tabelas em falta:")
        for table in sorted(comparison.missing_tables):
            print(f"  - {table}")
    else:
        print("\n✅ Não há tabelas em falta.")

    if comparison.unexpected_tables:
        print("\nℹ️  Tabelas adicionais detectadas:")
        for table in sorted(comparison.unexpected_tables):
            print(f"  - {table}")
    else:
        print("\n✅ Não há tabelas inesperadas.")

    print("\nRelatório de campos por tabela:")
    for table in sorted(comparison.field_differences):
        field_diff = comparison.field_differences[table]
        print(f"\nTabela: {table}")
        if field_diff.expected:
            print("  Campos esperados:")
            for field in sorted(field_diff.expected):
                print(f"    - {field}")
        else:
            print("  (Sem campos definidos como obrigatórios.)")

        if field_diff.actual:
            print("  Campos existentes:")
            for field in sorted(field_diff.actual):
                print(f"    - {field}")
        else:
            print("  (Nenhum campo encontrado na API de metadados.)")

        if field_diff.missing:
            print("  ⚠️  Campos em falta:")
            for field in sorted(field_diff.missing):
                print(f"    - {field}")
        else:
            print("  ✅ Nenhum campo em falta.")

        if field_diff.unexpected:
            print("  ℹ️  Campos inesperados:")
            for field in sorted(field_diff.unexpected):
                print(f"    - {field}")
        else:
            print("  ✅ Nenhum campo inesperado.")

    if comparison.has_discrepancies:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

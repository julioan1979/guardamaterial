"""Ferramenta de verificação dos nomes de tabelas configurados no Airtable.

Este script liga-se à API do Airtable usando as credenciais expostas nas
variáveis de ambiente ``AIRTABLE_API_KEY`` e ``AIRTABLE_BASE_ID`` para listar
as tabelas existentes na base. A lista resultante é comparada com os nomes de
tabelas esperados pela aplicação Streamlit para confirmar se existe
correspondência.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

from pyairtable import Api


DEFAULT_EXPECTED_TABLES = {
    "Secções",
    "Locais",
    "Sublocais",
    "Caixas e Armazéns",
    "Itens",
    "Movimentos",
    "Auditorias",
    "Inventário",
    "Utilizadores",
}


@dataclass(frozen=True)
class TableComparison:
    """Resultado da comparação entre tabelas esperadas e encontradas."""

    expected: set[str]
    actual: set[str]

    @property
    def missing(self) -> set[str]:
        """Tabelas esperadas que não foram encontradas na base."""

        return self.expected - self.actual

    @property
    def unexpected(self) -> set[str]:
        """Tabelas presentes na base mas não previstas pelo código."""

        return self.actual - self.expected


class AirtableTablesChecker:
    """Componente responsável por verificar as tabelas disponíveis no Airtable."""

    def __init__(self, api_key: str, base_id: str, expected_tables: Iterable[str]):
        self.api_key = api_key
        self.base_id = base_id
        self.expected_tables = set(expected_tables)

    def list_tables(self) -> set[str]:
        """Lê a lista de tabelas disponíveis na base configurada."""

        api = Api(self.api_key)
        base = api.base(self.base_id)
        return {table.name for table in base.tables()}

    def compare(self) -> TableComparison:
        """Compara as tabelas esperadas com as detectadas via API."""

        actual_tables = self.list_tables()
        return TableComparison(expected=self.expected_tables, actual=actual_tables)


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
    )
    comparison = checker.compare()

    print("Tabelas esperadas:")
    for table in sorted(comparison.expected):
        print(f"  - {table}")

    print("\nTabelas obtidas via API:")
    for table in sorted(comparison.actual):
        print(f"  - {table}")

    if comparison.missing:
        print("\n⚠️  Tabelas em falta:")
        for table in sorted(comparison.missing):
            print(f"  - {table}")
    else:
        print("\n✅ Não há tabelas em falta.")

    if comparison.unexpected:
        print("\nℹ️  Tabelas adicionais detectadas:")
        for table in sorted(comparison.unexpected):
            print(f"  - {table}")
    else:
        print("\n✅ Não há tabelas inesperadas.")


if __name__ == "__main__":
    main()

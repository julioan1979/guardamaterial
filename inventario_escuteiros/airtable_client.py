from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from pyairtable import Table


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

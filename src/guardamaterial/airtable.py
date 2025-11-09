"""Simple Airtable REST API client."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterable, List, Mapping, Optional
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import AirtableConfig

_LOGGER = logging.getLogger(__name__)


class AirtableClient:
    """Client for interacting with Airtable."""

    api_url: str = "https://api.airtable.com/v0"

    def __init__(
        self,
        config: AirtableConfig,
        *,
        timeout: float = 10.0,
    ) -> None:
        self.config = config
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        query = f"?{urlencode(params, doseq=True)}" if params else ""
        url = f"{self.api_url}/{self.config.base_id}/{path}{query}"
        request = Request(
            url=url,
            method=method.upper(),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Accept": "application/json",
            },
        )
        _LOGGER.debug("Sending %s request to %s", method, url)

        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = response.read()
                encoding = response.headers.get_content_charset("utf-8")
                payload = json.loads(data.decode(encoding))
                _LOGGER.debug("Received response: %s", payload)
                return payload
        except HTTPError as exc:  # pragma: no cover - exercise actual HTTP errors
            message = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Airtable request failed with status {exc.code}: {message}") from exc

    def list_records(
        self,
        *,
        table: Optional[str] = None,
        view: Optional[str] = None,
        filter_formula: Optional[str] = None,
        fields: Optional[Iterable[str]] = None,
        max_records: Optional[int] = None,
        page_size: int = 100,
    ) -> List[Mapping[str, Any]]:
        """Return all records for the given table."""

        table_name = self.config.require_table(table)
        params: Dict[str, Any] = {"pageSize": page_size}
        if view or self.config.view:
            params["view"] = view or self.config.view
        if filter_formula:
            params["filterByFormula"] = filter_formula
        if fields:
            params["fields[]"] = list(fields)

        records: List[Mapping[str, Any]] = []
        offset: Optional[str] = None
        while True:
            if offset:
                params["offset"] = offset
            payload = self._request("GET", table_name, params=params)
            records.extend(payload.get("records", []))
            offset = payload.get("offset")
            if not offset:
                break
            if max_records is not None and len(records) >= max_records:
                break
        if max_records is not None:
            return records[:max_records]
        return records

    def get_record(self, record_id: str, *, table: Optional[str] = None) -> Mapping[str, Any]:
        """Fetch a single record by its Airtable record id."""

        table_name = self.config.require_table(table)
        return self._request("GET", f"{table_name}/{record_id}")


__all__ = ["AirtableClient"]

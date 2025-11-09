from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from guardamaterial.airtable import AirtableClient
from guardamaterial.config import AirtableConfig


@pytest.fixture
def config() -> AirtableConfig:
    return AirtableConfig(api_key="key", base_id="base", default_table="Table")


def test_list_records_handles_pagination(config: AirtableConfig) -> None:
    client = AirtableClient(config, timeout=1)
    client._request = MagicMock(  # type: ignore[assignment]
        side_effect=[
            {"records": [1], "offset": "next"},
            {"records": [2]},
        ]
    )
    records = client.list_records()

    assert records == [1, 2]
    assert client._request.call_count == 2  # type: ignore[attr-defined]
    first_call = client._request.call_args_list[0]  # type: ignore[attr-defined]
    assert first_call.kwargs["params"]["pageSize"] == 100


def test_list_records_respects_max_records(config: AirtableConfig) -> None:
    client = AirtableClient(config)
    client._request = MagicMock(  # type: ignore[assignment]
        side_effect=[
            {"records": [1, 2], "offset": "next"},
            {"records": [3, 4]},
        ]
    )
    records = client.list_records(max_records=3)

    assert records == [1, 2, 3]


def test_get_record_uses_record_id(config: AirtableConfig) -> None:
    client = AirtableClient(config)
    client._request = MagicMock(return_value={"id": "rec123"})  # type: ignore[assignment]
    record = client.get_record("rec123")

    assert record["id"] == "rec123"
    client._request.assert_called_once_with("GET", "Table/rec123")  # type: ignore[attr-defined]


def test_list_records_without_table_fails_when_no_default(config: AirtableConfig) -> None:
    config_without_default = AirtableConfig(api_key="key", base_id="base")
    client = AirtableClient(config_without_default)

    with pytest.raises(ValueError):
        client.list_records(table=None)


def test_request_builds_url_and_headers(monkeypatch: pytest.MonkeyPatch, config: AirtableConfig) -> None:
    client = AirtableClient(config)

    response = MagicMock()
    response.read.return_value = b"{}"
    response.headers.get_content_charset.return_value = "utf-8"

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False

    urlopen_mock = MagicMock(return_value=context_manager)
    monkeypatch.setattr("guardamaterial.airtable.urlopen", urlopen_mock)

    payload = client._request(
        "GET",
        "Table",
        params={"fields[]": ["Name"], "pageSize": 1},
    )

    assert payload == {}
    request_obj = urlopen_mock.call_args.args[0]
    assert "fields%5B%5D=Name" in request_obj.full_url
    assert "pageSize=1" in request_obj.full_url
    assert request_obj.headers["Authorization"] == "Bearer key"

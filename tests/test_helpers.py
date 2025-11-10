"""Testes unitários para ``inventario_escuteiros.utils.helpers``."""

from __future__ import annotations

import io
from datetime import datetime

import pandas as pd

from inventario_escuteiros.utils import helpers


class _DummyUploadedFile(io.BytesIO):
    """Simula o objecto devolvido pelo Streamlit ao carregar ficheiros."""

    def __init__(self, data: bytes, mime_type: str = "text/plain") -> None:
        super().__init__(data)
        self.type = mime_type


def test_records_to_dataframe_includes_identifier_column() -> None:
    records = [
        {"id": "rec1", "fields": {"Nome": "Corda", "Quantidade": 3}},
        {"id": "rec2", "fields": {"Nome": "Lanterna", "Quantidade": 2}},
    ]

    df = helpers.records_to_dataframe(records)

    assert list(df["id"]) == ["rec1", "rec2"]
    assert list(df["Quantidade"]) == [3, 2]


def test_get_display_value_prefers_named_columns() -> None:
    df = pd.DataFrame([
        {"id": "rec1", "Nome": "Tenda"},
        {"id": "rec2", "Name": "Lanterna"},
        {"id": "rec3", "Título": "Corda"},
    ])

    assert helpers.get_display_value(df.loc[0]) == "Tenda"
    assert helpers.get_display_value(df.loc[1]) == "Lanterna"
    assert helpers.get_display_value(df.loc[2]) == "Corda"


def test_get_display_value_falls_back_to_identifier() -> None:
    row = pd.Series({"id": "rec123"})

    assert helpers.get_display_value(row) == "rec123"


def test_build_lookup_uses_display_values() -> None:
    df = pd.DataFrame([
        {"id": "a", "Nome": "Item A"},
        {"id": "b", "Name": "Item B"},
    ])

    lookup = helpers.build_lookup(df)

    assert lookup == {"a": "Item A", "b": "Item B"}


def test_filter_by_link_matches_values_inside_lists() -> None:
    df = pd.DataFrame([
        {"id": "rec1", "Ligacoes": ["x", "y"]},
        {"id": "rec2", "Ligacoes": ["z"]},
    ])

    filtered = helpers.filter_by_link(df, "Ligacoes", "y")

    assert list(filtered["id"]) == ["rec1"]


def test_filter_by_link_returns_empty_dataframe_for_missing_column() -> None:
    df = pd.DataFrame([
        {"id": "rec1", "Ligacoes": ["x", "y"]},
    ])

    filtered = helpers.filter_by_link(df, "Inexistente", "y")

    assert filtered.empty


def test_ensure_list_normalises_values() -> None:
    assert helpers.ensure_list(None) == []
    assert helpers.ensure_list([1, 2]) == [1, 2]
    assert helpers.ensure_list("abc") == ["abc"]


def test_encode_file_to_data_url_restores_pointer_and_generates_data_url() -> None:
    dummy_file = _DummyUploadedFile(b"conteudo", mime_type="text/plain")
    dummy_file.seek(2)
    original_position = dummy_file.tell()

    data_url = helpers.encode_file_to_data_url(dummy_file)

    assert data_url.startswith("data:text/plain;base64,")
    assert dummy_file.tell() == original_position


def test_encode_file_to_data_url_returns_none_for_empty_payload() -> None:
    dummy_file = _DummyUploadedFile(b"", mime_type="application/json")

    assert helpers.encode_file_to_data_url(dummy_file) is None
    assert dummy_file.tell() == 0


def test_latest_timestamp_from_dataframes_returns_latest_datetime() -> None:
    df_material = pd.DataFrame(
        {"id": ["rec1"], "Última atualização": ["2024-01-10T12:00:00"]}
    )
    df_movimentos = pd.DataFrame(
        {"id": ["mov1"], "Last Modified": ["2024-01-15T09:30:00"]}
    )

    latest = helpers.latest_timestamp_from_dataframes(
        {"materiais": df_material, "movimentos": df_movimentos}
    )

    assert isinstance(latest, datetime)
    assert latest == datetime(2024, 1, 15, 9, 30)


def test_latest_timestamp_from_dataframes_returns_none_when_absent() -> None:
    df_empty = pd.DataFrame({"id": [], "Nome": []})

    latest = helpers.latest_timestamp_from_dataframes({"materiais": df_empty})

    assert latest is None


def test_month_name_formats_timestamp() -> None:
    timestamp = pd.Timestamp("2024-06-21 10:15:00")

    assert helpers.month_name(timestamp) == "2024-06"


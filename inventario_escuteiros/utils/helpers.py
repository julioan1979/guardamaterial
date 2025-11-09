from __future__ import annotations

import base64
from datetime import datetime
from typing import Dict, List, Optional, Sequence

import pandas as pd

DISPLAY_FIELDS: Sequence[str] = ("Nome", "Name", "Título", "Title", "Identificador")
TIMESTAMP_FIELDS: Sequence[str] = (
    "Última atualização",
    "Última Atualização",
    "Last Modified",
    "Last Modified Time",
    "Modified",
)


def records_to_dataframe(records: List[Dict]) -> pd.DataFrame:
    rows: List[Dict] = []
    for record in records:
        fields = record.get("fields", {})
        row = {"id": record.get("id")}
        row.update(fields)
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def get_display_value(row: pd.Series, fields: Sequence[str] = DISPLAY_FIELDS, default: str = "Sem nome") -> str:
    for field in fields:
        if field in row and pd.notna(row[field]):
            value = row[field]
            if isinstance(value, list):
                return ", ".join(str(item) for item in value)
            return str(value)
    if "id" in row and pd.notna(row["id"]):
        return str(row["id"])
    return default


def build_lookup(df: pd.DataFrame, label_fields: Sequence[str] = DISPLAY_FIELDS) -> Dict[str, str]:
    if df.empty:
        return {}
    return {row["id"]: get_display_value(row, label_fields) for _, row in df.iterrows()}


def filter_by_link(df: pd.DataFrame, column: str, target_id: str) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return df.iloc[0:0]

    def _matches(value: object) -> bool:
        if isinstance(value, list):
            return target_id in value
        return value == target_id

    mask = df[column].apply(_matches)
    return df[mask]


def ensure_list(value: Optional[object]) -> List[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def encode_file_to_data_url(uploaded_file) -> Optional[str]:
    if uploaded_file is None:
        return None
    bytes_buffer = uploaded_file.read()
    if not bytes_buffer:
        return None
    mime_type = uploaded_file.type or "application/octet-stream"
    base64_data = base64.b64encode(bytes_buffer).decode("utf-8")
    return f"data:{mime_type};base64,{base64_data}"


def latest_timestamp_from_dataframes(dataframes: Dict[str, pd.DataFrame]) -> Optional[datetime]:
    timestamps: List[pd.Timestamp] = []
    for df in dataframes.values():
        if df.empty:
            continue
        for field in TIMESTAMP_FIELDS:
            if field in df.columns:
                series = pd.to_datetime(df[field], errors="coerce")
                series = series.dropna()
                if not series.empty:
                    timestamps.append(series.max())
    if not timestamps:
        return None
    return max(timestamps).to_pydatetime()


def month_name(date_value: pd.Timestamp) -> str:
    return date_value.strftime("%Y-%m")

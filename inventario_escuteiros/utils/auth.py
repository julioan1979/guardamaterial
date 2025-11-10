"""Utilities for user authentication against the Airtable backend."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, Optional, Sequence

import bcrypt

from ..airtable_client import AirtableClient

try:  # pragma: no cover - streamlit may not be available during tests
    import streamlit as st  # type: ignore
except Exception:  # pragma: no cover - executed when Streamlit is not installed
    st = None  # type: ignore

_USERS_TABLE_ENV = "AIRTABLE_USERS_TABLE"
_DEFAULT_USERS_TABLE = "Utilizadores"


def _get_secret_value(*keys: str) -> Optional[str]:
    """Return a (possibly nested) value from ``st.secrets`` if available."""
    if st is None:  # Streamlit not available (e.g., running tests)
        return None

    try:
        value: Any = st.secrets
        for key in keys:
            value = value[key]
    except Exception:  # pragma: no cover - depends on runtime configuration
        return None

    if isinstance(value, (str, int, float)):
        return str(value)
    return None


def _get_config_value(
    key: str,
    *,
    secret_paths: Optional[Sequence[Sequence[str]]] = None,
    env_var: Optional[str] = None,
) -> Optional[str]:
    """Fetch a configuration value from Streamlit secrets or environment variables."""

    paths = secret_paths or ()
    for path in paths:
        secret_value = _get_secret_value(*path)
        if secret_value:
            return secret_value

    secret_value = _get_secret_value(key)
    if secret_value:
        return secret_value

    env_value = os.getenv(env_var or key)
    if env_value:
        return env_value
    return None


@lru_cache(maxsize=1)
def get_airtable_credentials() -> tuple[str, str]:
    """Return the Airtable credentials, raising an error when missing."""
    api_key = (
        _get_config_value(
            "AIRTABLE_API_KEY",
            secret_paths=(("airtable", "api_key"),),
        )
        or ""
    )
    base_id = (
        _get_config_value(
            "AIRTABLE_BASE_ID",
            secret_paths=(("airtable", "base_id"),),
        )
        or ""
    )
    if not api_key or not base_id:
        raise RuntimeError(
            "Credenciais do Airtable não configuradas. Defina AIRTABLE_API_KEY e AIRTABLE_BASE_ID "
            "em st.secrets ou como variáveis de ambiente."
        )
    return api_key, base_id


@lru_cache(maxsize=1)
def _get_client() -> AirtableClient:
    api_key, base_id = get_airtable_credentials()
    return AirtableClient(api_key=api_key, base_id=base_id)


def _get_users_table_name() -> str:
    return (
        _get_config_value(
            _USERS_TABLE_ENV,
            secret_paths=(("airtable", "users_table"),),
        )
        or _DEFAULT_USERS_TABLE
    )


def _escape_formula_value(value: str) -> str:
    """Escape apostrophes for safe usage in Airtable formulas."""
    return value.replace("'", "\\'")


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Validate the provided credentials against the Airtable ``Utilizadores`` table."""
    email = (email or "").strip()
    password = password or ""
    if not email or not password:
        return None

    client = _get_client()
    formula_email = _escape_formula_value(email)
    formula = f"{{Email}} = '{formula_email}'"

    try:
        records = client.list_records(
            _get_users_table_name(),
            formula=formula,
            max_records=1,
        )
    except Exception as exc:  # pragma: no cover - depends on Airtable responses
        raise RuntimeError(f"Erro ao comunicar com o Airtable: {exc}") from exc

    if not records:
        return None

    record = records[0]
    fields = dict(record.get("fields", {}))
    stored_hash = fields.get("PasswordHash")
    if not stored_hash:
        return None

    if isinstance(stored_hash, str):
        stored_hash_bytes = stored_hash.encode("utf-8")
    elif isinstance(stored_hash, bytes):
        stored_hash_bytes = stored_hash
    else:
        return None

    password_bytes = password.encode("utf-8")
    try:
        is_valid = bcrypt.checkpw(password_bytes, stored_hash_bytes)
    except ValueError:  # pragma: no cover - invalid hash format
        return None

    if not is_valid:
        return None

    fields.pop("PasswordHash", None)
    return {"id": record.get("id"), **fields}


__all__ = ["authenticate_user", "get_airtable_credentials"]

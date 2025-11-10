"""Utilities for user authentication against the Airtable backend."""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any, Dict, Iterable, Optional, Sequence

import bcrypt

from ..airtable_client import AirtableClient

try:  # pragma: no cover - streamlit may not be available during tests
    import streamlit as st  # type: ignore
except Exception:  # pragma: no cover - executed when Streamlit is not installed
    st = None  # type: ignore

logger = logging.getLogger(__name__)

_USERS_TABLE_ENV = "AIRTABLE_USERS_TABLE"
_DEFAULT_USERS_TABLES = ("Utilizadores", "Users")
_PLAINTEXT_PASSWORD_FIELD_ENV = "AIRTABLE_PLAINTEXT_PASSWORD_FIELD"
_DEFAULT_PLAINTEXT_PASSWORD_FIELD = "Palavra-passe"


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


def _get_users_table_config() -> tuple[tuple[str, ...], bool]:
    """Devolver os nomes de tabela candidatos e indicar se há configuração customizada."""

    configured = _get_config_value(
        _USERS_TABLE_ENV,
        secret_paths=(("airtable", "users_table"),),
    )
    if configured:
        return (configured,), True

    unique_defaults = tuple(dict.fromkeys(_DEFAULT_USERS_TABLES))
    return unique_defaults, False


@lru_cache(maxsize=1)
def _get_plaintext_password_field() -> str:
    """Obter o nome configurado para a coluna de palavra-passe em texto simples."""

    configured = _get_config_value(
        _PLAINTEXT_PASSWORD_FIELD_ENV,
        secret_paths=(
            ("airtable", "plaintext_password_field"),
            ("airtable", "password_field"),
        ),
    )
    if configured:
        sanitized = configured.strip()
        if sanitized:
            return sanitized
    return _DEFAULT_PLAINTEXT_PASSWORD_FIELD


def _notify_plaintext_password_usage(field_name: str) -> None:
    """Emitir um aviso sempre que a autenticação recorra a texto simples."""

    message_text = (
        f"Autenticação baseada na coluna '{field_name}' em texto simples. "
        "Recomenda-se migrar para o campo PasswordHash (Bcrypt)."
    )

    if st is not None and hasattr(st, "warning"):
        try:  # pragma: no cover - depende da implementação do Streamlit
            st.warning(message_text)  # type: ignore[operator]
        except Exception:  # pragma: no cover - evitar que um erro silencie o aviso
            logger.warning(message_text)
        else:
            logger.info(message_text)
    else:
        logger.warning(message_text)


def _escape_formula_value(value: str) -> str:
    """Escape apostrophes for safe usage in Airtable formulas."""
    return value.replace("'", "\\'")


def _format_airtable_error(
    exc: Exception,
    *,
    tables_tried: Iterable[str],
    base_id: str,
    has_custom_table: bool,
) -> RuntimeError:
    """Construir um erro contextualizado para falhas na consulta ao Airtable."""

    tables_list = ", ".join(tables_tried) or "<desconhecido>"
    hint = (
        "Defina AIRTABLE_USERS_TABLE ou st.secrets['airtable']['users_table'] com o nome da tabela de utilizadores "
        "visível na base do Airtable."
        if not has_custom_table
        else "Confirme se a tabela configurada existe na base e se o token possui permissões de leitura."
    )
    message = (
        "Erro ao comunicar com o Airtable: "
        f"{exc} (base: {base_id}; tabelas testadas: {tables_list}). {hint}"
    )
    return RuntimeError(message)


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Validate the provided credentials against the Airtable ``Utilizadores`` table."""
    email = (email or "").strip()
    password = password or ""
    if not email or not password:
        return None

    client = _get_client()
    formula_email = _escape_formula_value(email)
    formula = f"{{Email}} = '{formula_email}'"

    table_candidates, is_custom_table = _get_users_table_config()
    records = None
    last_exception: Exception | None = None

    tried_tables: list[str] = []
    for idx, table_name in enumerate(table_candidates):
        tried_tables.append(table_name)
        try:
            candidate_records = client.list_records(
                table_name,
                formula=formula,
                max_records=1,
            )
        except Exception as exc:  # pragma: no cover - depende da resposta do Airtable
            last_exception = exc
            is_last_candidate = idx == len(table_candidates) - 1
            if is_custom_table or is_last_candidate:
                raise _format_airtable_error(
                    exc,
                    tables_tried=tried_tables,
                    base_id=client.base_id,
                    has_custom_table=is_custom_table,
                ) from exc
            continue

        if candidate_records:
            records = candidate_records
            break

        if not is_custom_table and idx < len(table_candidates) - 1:
            continue
        return None

    if records is None:
        if last_exception is not None:  # pragma: no cover - dependente do Airtable
            raise _format_airtable_error(
                last_exception,
                tables_tried=tried_tables,
                base_id=client.base_id,
                has_custom_table=is_custom_table,
            ) from last_exception
        return None

    if not records:
        return None

    record = records[0]
    fields = dict(record.get("fields", {}))
    stored_hash = fields.get("PasswordHash")
    stored_hash_bytes: bytes | None = None
    if isinstance(stored_hash, str) and stored_hash:
        stored_hash_bytes = stored_hash.encode("utf-8")
    elif isinstance(stored_hash, bytes) and stored_hash:
        stored_hash_bytes = stored_hash

    if stored_hash_bytes is not None:
        password_bytes = password.encode("utf-8")
        try:
            is_valid = bcrypt.checkpw(password_bytes, stored_hash_bytes)
        except ValueError:  # pragma: no cover - invalid hash format
            return None

        if not is_valid:
            return None

        fields.pop("PasswordHash", None)
        fields.pop(_get_plaintext_password_field(), None)
        return {"id": record.get("id"), **fields}

    plaintext_field = _get_plaintext_password_field()
    plaintext_value = fields.get(plaintext_field)
    if isinstance(plaintext_value, str) and plaintext_value:
        if plaintext_value == password:
            fields.pop("PasswordHash", None)
            fields.pop(plaintext_field, None)
            _notify_plaintext_password_usage(plaintext_field)
            return {"id": record.get("id"), **fields}

    return None


__all__ = ["authenticate_user", "get_airtable_credentials"]

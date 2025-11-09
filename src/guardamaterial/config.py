"""Helpers for loading Airtable configuration from secrets or the environment."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping, Optional

try:  # Python 3.11 compatibility
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - only for Python <3.11
    tomllib = None  # type: ignore[assignment]


@dataclass(slots=True)
class AirtableConfig:
    """Configuration required to communicate with Airtable."""

    api_key: str
    base_id: str
    default_table: Optional[str] = None
    view: Optional[str] = None

    def require_table(self, table: Optional[str]) -> str:
        """Return the provided table name or fall back to the default one."""

        candidate = table or self.default_table
        if not candidate:
            raise ValueError(
                "No table provided. Pass a table name explicitly or set "
                "AIRTABLE_DEFAULT_TABLE in the secrets/environment."
            )
        return candidate


def _read_text_file(path: Path) -> Optional[str]:
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return None


def _load_structured_file(path: Path) -> Mapping[str, str]:
    if not path.exists() or not path.is_file():
        return {}
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() in {".toml", ".tml"} and tomllib is not None:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    else:
        return {}
    return {str(key): str(value) for key, value in data.items()}


def _candidate_filenames(key: str) -> tuple[str, ...]:
    lower = key.lower()
    upper = key.upper()
    prefixed_lower = f"airtable_{lower}"
    prefixed_upper = f"AIRTABLE_{upper}"
    return (
        lower,
        upper,
        f"{lower}.txt",
        f"{upper}.txt",
        prefixed_lower,
        prefixed_upper,
        f"{prefixed_lower}.txt",
        f"{prefixed_upper}.txt",
    )


def load_config(
    *,
    secrets_dir: Optional[Path | str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> AirtableConfig:
    """Load Airtable configuration.

    The loader tries, in order:

    1. Environment variables (``AIRTABLE_*``).
    2. Individual secret files in ``secrets_dir`` (default: ``Path("secrets")``).
    3. A structured file named ``airtable.json`` or ``airtable.toml``.
    """

    env_mapping: Mapping[str, str] = env or os.environ
    resolved_dir = Path(secrets_dir or env_mapping.get("SECRETS_DIR", "secrets"))

    structured_values: MutableMapping[str, str] = {}
    for candidate in ("airtable.json", "airtable.toml"):
        structured_values.update(_load_structured_file(resolved_dir / candidate))

    def _resolve_value(name: str, *, required: bool = True) -> Optional[str]:
        env_key = f"AIRTABLE_{name.upper()}"
        if env_key in env_mapping:
            return env_mapping[env_key]

        structured_key_variants = {
            name,
            name.lower(),
            name.upper(),
            env_key,
        }
        for variant in structured_key_variants:
            if variant in structured_values:
                return structured_values[variant]

        for filename in _candidate_filenames(name):
            value = _read_text_file(resolved_dir / filename)
            if value:
                return value

        if required:
            raise RuntimeError(
                f"Missing Airtable configuration value for '{name}'. "
                "Set the AIRTABLE_{name.upper()} environment variable or provide "
                "a matching secret file."
            )
        return None

    api_key = _resolve_value("api_key")
    base_id = _resolve_value("base_id")
    default_table = _resolve_value("default_table", required=False)
    view = _resolve_value("view", required=False)

    return AirtableConfig(
        api_key=api_key,
        base_id=base_id,
        default_table=default_table,
        view=view,
    )


__all__ = ["AirtableConfig", "load_config"]

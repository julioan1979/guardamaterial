"""Tests for configuration helpers in :mod:`inventario_escuteiros.utils.auth`."""

from __future__ import annotations

import os
from types import SimpleNamespace

import unittest

from inventario_escuteiros.utils import auth


class _EnvVarGuard:
    """Utility to save and restore environment variables inside tests."""

    def __init__(self, *keys: str) -> None:
        self._keys = keys
        self._original: dict[str, str | None] = {}

    def __enter__(self) -> "_EnvVarGuard":
        for key in self._keys:
            self._original[key] = os.environ.get(key)
        return self

    def __exit__(self, *exc_info: object) -> None:
        for key, value in self._original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class ConfigValueTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_st = auth.st

    def tearDown(self) -> None:
        auth.st = self._original_st

    def test_nested_secret_value_is_used(self) -> None:
        """The helper should read nested secrets before falling back to other sources."""

        auth.st = SimpleNamespace(secrets={"airtable": {"users_table": "CustomUsers"}})

        with _EnvVarGuard(auth._USERS_TABLE_ENV):
            os.environ.pop(auth._USERS_TABLE_ENV, None)
            value = auth._get_config_value(
                auth._USERS_TABLE_ENV,
                secret_paths=(("airtable", "users_table"),),
            )

        self.assertEqual(value, "CustomUsers")

    def test_env_var_used_when_secret_missing(self) -> None:
        auth.st = SimpleNamespace(secrets={})

        with _EnvVarGuard(auth._USERS_TABLE_ENV):
            os.environ[auth._USERS_TABLE_ENV] = "EnvUsers"
            value = auth._get_config_value(
                auth._USERS_TABLE_ENV,
                secret_paths=(("airtable", "users_table"),),
            )

        self.assertEqual(value, "EnvUsers")


class AirtableCredentialsTests(unittest.TestCase):
    """Tests for the ``get_airtable_credentials`` helper."""

    def setUp(self) -> None:
        self._original_st = auth.st
        auth.get_airtable_credentials.cache_clear()
        auth._get_client.cache_clear()

    def tearDown(self) -> None:
        auth.st = self._original_st
        auth.get_airtable_credentials.cache_clear()
        auth._get_client.cache_clear()

    def test_nested_airtable_secrets_are_prioritized(self) -> None:
        """Nested secrets should be used before top-level keys or environment variables."""

        auth.st = SimpleNamespace(
            secrets={
                "airtable": {"api_key": "nested-key", "base_id": "nested-base"},
                "AIRTABLE_API_KEY": "top-key",
                "AIRTABLE_BASE_ID": "top-base",
            }
        )

        with _EnvVarGuard("AIRTABLE_API_KEY", "AIRTABLE_BASE_ID"):
            os.environ.pop("AIRTABLE_API_KEY", None)
            os.environ.pop("AIRTABLE_BASE_ID", None)
            credentials = auth.get_airtable_credentials()

        self.assertEqual(credentials, ("nested-key", "nested-base"))

    def test_top_level_airtable_secrets_remain_supported(self) -> None:
        """Top-level secrets continue to be supported when nested ones are absent."""

        auth.st = SimpleNamespace(
            secrets={
                "AIRTABLE_API_KEY": "top-key",
                "AIRTABLE_BASE_ID": "top-base",
            }
        )

        with _EnvVarGuard("AIRTABLE_API_KEY", "AIRTABLE_BASE_ID"):
            os.environ.pop("AIRTABLE_API_KEY", None)
            os.environ.pop("AIRTABLE_BASE_ID", None)
            credentials = auth.get_airtable_credentials()

        self.assertEqual(credentials, ("top-key", "top-base"))


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()

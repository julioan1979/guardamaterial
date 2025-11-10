"""Tests for configuration helpers in :mod:`inventario_escuteiros.utils.auth`."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import unittest

import bcrypt

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


class UsersTableConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_st = auth.st

    def tearDown(self) -> None:
        auth.st = self._original_st

    def test_custom_table_from_secrets_is_prioritized(self) -> None:
        auth.st = SimpleNamespace(secrets={"airtable": {"users_table": "Custom"}})

        with _EnvVarGuard(auth._USERS_TABLE_ENV):
            os.environ.pop(auth._USERS_TABLE_ENV, None)
            tables, is_custom = auth._get_users_table_config()

        self.assertEqual(tables, ("Custom",))
        self.assertTrue(is_custom)

    def test_custom_table_from_env_is_used(self) -> None:
        auth.st = SimpleNamespace(secrets={})

        with _EnvVarGuard(auth._USERS_TABLE_ENV):
            os.environ[auth._USERS_TABLE_ENV] = "EnvTable"
            tables, is_custom = auth._get_users_table_config()

        self.assertEqual(tables, ("EnvTable",))
        self.assertTrue(is_custom)

    def test_default_tables_include_portuguese_and_english(self) -> None:
        auth.st = SimpleNamespace(secrets={})

        with _EnvVarGuard(auth._USERS_TABLE_ENV):
            os.environ.pop(auth._USERS_TABLE_ENV, None)
            tables, is_custom = auth._get_users_table_config()

        self.assertEqual(tables, ("Utilizadores", "Users"))
        self.assertFalse(is_custom)


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


class AirtableErrorFormattingTests(unittest.TestCase):
    """Testes para o formatação de erros ao comunicar com o Airtable."""

    def test_error_message_includes_context_and_hint(self) -> None:
        error = ValueError("INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND")

        formatted = auth._format_airtable_error(
            error,
            tables_tried=["Utilizadores", "Users"],
            base_id="app123",
            has_custom_table=False,
        )

        self.assertIsInstance(formatted, RuntimeError)
        self.assertIn("app123", str(formatted))
        self.assertIn("Utilizadores, Users", str(formatted))
        self.assertIn("AIRTABLE_USERS_TABLE", str(formatted))


class _DummyStreamlit:
    def __init__(self) -> None:
        self.secrets: dict[str, object] = {}
        self.warnings: list[str] = []

    def warning(self, message: str) -> None:  # pragma: no cover - simples encaminhamento
        self.warnings.append(message)


class AuthenticateUserTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_st = auth.st
        self._original_get_client = auth._get_client
        if hasattr(self._original_get_client, "cache_clear"):
            self._original_get_client.cache_clear()
        auth._get_plaintext_password_field.cache_clear()
        self._dummy_st = _DummyStreamlit()
        auth.st = self._dummy_st

    def tearDown(self) -> None:
        auth._get_client = self._original_get_client
        if hasattr(self._original_get_client, "cache_clear"):
            self._original_get_client.cache_clear()
        auth._get_plaintext_password_field.cache_clear()
        auth.st = self._original_st

    def test_authenticate_with_bcrypt_hash(self) -> None:
        """Um hash Bcrypt válido deve autenticar e limpar campos sensíveis."""

        password = "segredo"
        stored_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        record = {
            "id": "rec123",
            "fields": {
                "Email": "user@example.com",
                "PasswordHash": stored_hash,
                "Perfil": "admin",
            },
        }

        class _Client:
            base_id = "appTest"

            def list_records(self, table_name: str, formula: str, max_records: int) -> list[dict[str, object]]:
                return [record]

        auth._get_client = lambda: _Client()

        authenticated = auth.authenticate_user("user@example.com", password)

        self.assertIsNotNone(authenticated)
        assert authenticated is not None
        self.assertEqual(authenticated.get("id"), "rec123")
        self.assertEqual(authenticated.get("Email"), "user@example.com")
        self.assertEqual(authenticated.get("Perfil"), "admin")
        self.assertNotIn("PasswordHash", authenticated)
        self.assertEqual(self._dummy_st.warnings, [])

    def test_authenticate_with_plaintext_password(self) -> None:
        """A coluna 'Palavra-passe' permite autenticar enquanto a migração decorre."""

        record = {
            "id": "rec321",
            "fields": {
                "Email": "compat@example.com",
                "Palavra-passe": "legado",
                "Role": "viewer",
            },
        }

        class _Client:
            base_id = "appTest"

            def list_records(self, table_name: str, formula: str, max_records: int) -> list[dict[str, object]]:
                return [record]

        auth._get_client = lambda: _Client()

        with _EnvVarGuard(auth._PLAINTEXT_PASSWORD_FIELD_ENV):
            os.environ.pop(auth._PLAINTEXT_PASSWORD_FIELD_ENV, None)
            auth._get_plaintext_password_field.cache_clear()
            authenticated = auth.authenticate_user("compat@example.com", "legado")

        self.assertIsNotNone(authenticated)
        assert authenticated is not None
        self.assertEqual(authenticated.get("Role"), "viewer")
        self.assertNotIn("Palavra-passe", authenticated)
        self.assertGreaterEqual(len(self._dummy_st.warnings), 1)

if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()

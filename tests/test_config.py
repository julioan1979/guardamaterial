from __future__ import annotations

from pathlib import Path

import pytest

from guardamaterial.config import AirtableConfig, load_config


def test_load_config_from_env() -> None:
    env = {
        "AIRTABLE_API_KEY": "test-key",
        "AIRTABLE_BASE_ID": "base123",
        "AIRTABLE_DEFAULT_TABLE": "Table",
        "AIRTABLE_VIEW": "Grid view",
    }

    config = load_config(env=env)

    assert config == AirtableConfig(
        api_key="test-key",
        base_id="base123",
        default_table="Table",
        view="Grid view",
    )


def test_load_config_from_secret_files(tmp_path: Path) -> None:
    secrets_dir = tmp_path
    (secrets_dir / "airtable_api_key").write_text("key-123", encoding="utf-8")
    (secrets_dir / "airtable_base_id").write_text("base-456", encoding="utf-8")
    (secrets_dir / "airtable_default_table").write_text("Inventory", encoding="utf-8")

    config = load_config(secrets_dir=secrets_dir, env={})

    assert config.api_key == "key-123"
    assert config.base_id == "base-456"
    assert config.default_table == "Inventory"


def test_load_config_from_json(tmp_path: Path) -> None:
    secrets_dir = tmp_path
    (secrets_dir / "airtable.json").write_text(
        """
        {
            "api_key": "json-key",
            "base_id": "json-base",
            "default_table": "json-table"
        }
        """,
        encoding="utf-8",
    )

    config = load_config(secrets_dir=secrets_dir, env={})

    assert config.api_key == "json-key"
    assert config.base_id == "json-base"
    assert config.default_table == "json-table"


def test_missing_required_config_raises(tmp_path: Path) -> None:
    secrets_dir = tmp_path
    (secrets_dir / "airtable_base_id").write_text("base-456", encoding="utf-8")

    with pytest.raises(RuntimeError):
        load_config(secrets_dir=secrets_dir, env={})

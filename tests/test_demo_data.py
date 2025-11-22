"""Testes para os dados de demonstração carregados a partir dos CSV locais."""

import types

import pandas as pd

import app as app_module


def test_carregar_inventario_demo_normaliza_colunas() -> None:
    inventario = app_module.carregar_inventario_demo()

    assert list(inventario.columns) == [
        "id",
        "Artigo",
        "Secção",
        "Quantidade",
        "Stock Mínimo",
        "Localização",
        "Notas",
        "Atualizado",
    ]
    assert not inventario.empty
    assert inventario.iloc[0]["Artigo"] == "Cominhos"
    assert inventario["Quantidade"].dtype == int


def test_carregar_movimentos_demo_normaliza_quantidades() -> None:
    movimentos = app_module.carregar_movimentos_demo()

    assert set(movimentos.columns) == {
        "id",
        "Data",
        "Artigo",
        "Secção",
        "Quantidade",
        "Responsável",
        "Tipo",
        "Notas",
    }
    assert movimentos.iloc[0]["Quantidade"] == 1
    assert movimentos["Data"].notna().all()


def test_guardar_metadados_demo_atualiza_session_state(monkeypatch) -> None:
    fake_state: dict[str, object] = {}
    fake_st = types.SimpleNamespace(session_state=fake_state)

    original_st = app_module.st
    app_module.st = fake_st
    try:
        app_module._guardar_metadados_demo(
            pd.DataFrame({"Artigo": ["Exemplo"], "Quantidade": [1]}),
            pd.DataFrame({"Artigo": ["Exemplo"], "Quantidade": [1]}),
        )
    finally:
        app_module.st = original_st

    assert "_airtable_metadata" in fake_state
    assert "_airtable_metadata_error" in fake_state

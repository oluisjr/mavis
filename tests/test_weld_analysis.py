"""Casos sintéticos de sinais mascarados por médias e auditoria causal."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app import weld_analysis, weld_loader, config

def _curvas(total=25, oscilacao_final=False, measp_por_solda=None):
    registros = []
    for i in range(total):
        for ponto in range(40):
            corrente = 10.0
            if oscilacao_final and i == total - 1:
                corrente += 0.3 if ponto % 2 == 0 else -0.3
            registros.append({
                "WELDNº": i + 1,
                "ID_PONTO": ponto + 1,
                "DATAHORA": pd.Timestamp("2026-01-01") + pd.Timedelta(minutes=i),
                "code ENTRY": "1",
                "code EXIT": "2",
                "MeasP": str(measp_por_solda[i]) if measp_por_solda else "7",
                "CORRENTE": corrente,
            })
    return pd.DataFrame(registros)


def test_oscilar_sem_mudar_media_acende_evidencia():
    pontos = _curvas(oscilacao_final=True)
    solda = pontos.loc[pontos["WELDNº"].eq(25), "CORRENTE"]
    assert abs(solda.mean() - 10.0) < 1e-9  # média não vê a falha de forma.
    caracteristicas = weld_analysis.caracteristicas_por_solda(pontos, ("CORRENTE",))
    painel, alertas = weld_analysis.analisar_soldas(caracteristicas, ("CORRENTE",))
    alvo = painel.loc[painel["WELDNº"].eq(25)].iloc[0]
    assert alvo["n_evidencias"] >= 1
    assert alvo["situacao"] == "Investigação prioritária"
    assert "Oscilação entre pontos consecutivos" in set(alertas["evidencia"])


def test_baseline_somente_soldas_anteriores():
    simples = weld_analysis.caracteristicas_por_solda(_curvas(oscilacao_final=False), ("CORRENTE",))
    alterada = weld_analysis.caracteristicas_por_solda(_curvas(oscilacao_final=True), ("CORRENTE",))
    a, _ = weld_analysis.analisar_soldas(simples, ("CORRENTE",))
    b, _ = weld_analysis.analisar_soldas(alterada, ("CORRENTE",))
    pd.testing.assert_frame_equal(a.iloc[:-1].reset_index(drop=True), b.iloc[:-1].reset_index(drop=True))


def test_composicoes_nao_sao_misturadas():
    ctx = ["A"] * 10 + ["B"] * 15
    caracteristicas = weld_analysis.caracteristicas_por_solda(
        _curvas(total=25, oscilacao_final=True, measp_por_solda=ctx), ("CORRENTE",)
    )
    painel, alertas = weld_analysis.analisar_soldas(caracteristicas, ("CORRENTE",))
    # Grupo B tem só 14 referências anteriores, último B é elegível.
    assert painel.iloc[-1]["n_referencias"] > 0
    assert painel.iloc[10]["situacao"] == "Sem referência contextual"
    assert not alertas.loc[alertas["WELDNº"].eq(11)].shape[0]


def test_sem_referencia_nunca_equivale_a_normal():
    pouco = weld_analysis.caracteristicas_por_solda(_curvas(total=5), ("CORRENTE",))
    painel, alertas = weld_analysis.analisar_soldas(pouco, ("CORRENTE",))
    assert alertas.empty
    assert painel["situacao"].eq("Sem referência contextual").all()


def test_referencia_desenha_pontos_e_nao_inclui_futuro():
    pontos = _curvas(total=25, oscilacao_final=True)
    referencia, n = weld_analysis.perfil_com_referencia(pontos, 25, "CORRENTE")
    assert n == 24
    assert "Referência P50" in referencia
    assert referencia["Solda selecionada"].mean() == pytest.approx(10.0)
    assert referencia["Referência P50"].mean() == pytest.approx(10.0)
    antiga, n2 = weld_analysis.perfil_com_referencia(pontos, 1, "CORRENTE")
    assert n2 == 0
    assert "Referência P50" not in antiga


def test_pontos_duplicados_sao_evidenciados():
    amostra = _curvas(total=15)
    amostra.loc[amostra["WELDNº"].eq(15), "ID_PONTO"] = 1
    car = weld_analysis.caracteristicas_por_solda(amostra, ("CORRENTE",))
    painel, _ = weld_analysis.analisar_soldas(car, ("CORRENTE",))
    assert painel.iloc[-1]["situacao"] == "Qualidade de dados: pontos duplicados"


def test_pagina_solda_exige_login():
    path = Path(__file__).resolve().parents[1] / "pages" / "2_🔬_Análise_por_Solda.py"
    app = AppTest.from_file(str(path), default_timeout=20)
    app.session_state["authenticated"] = False
    app.run()
    assert not app.exception


@pytest.mark.integration
def test_historico_123_tem_multiplos_pontos_por_solda():
    if "123" not in weld_loader.listar_receitas_detalhadas():
        pytest.skip("Histórico industrial não presente.")
    import pyarrow.parquet as pq
    path = config.DATA_DIR / "dados_detalhados_123.parquet"
    tabela = pq.read_table(path, columns=[
        "WELDNº", "ID_PONTO", "DATAHORA", "MeasP", "code ENTRY", "code EXIT",
        "CORRENTE", "VELOCIDADE", "PRESSAO_SOLDA", "PRESSAO_MARTELADOR",
    ])
    dados = tabela.slice(0, 15000).to_pandas()
    for col in weld_loader.CONTEXT:
        dados[col] = dados[col].astype("string").fillna("N/D")
    for sensor in ("CORRENTE", "VELOCIDADE", "PRESSAO_SOLDA", "PRESSAO_MARTELADOR"):
        dados[sensor] = dados[sensor] / config.FATORES_ESCALA[sensor]
    completos = dados["WELDNº"].value_counts()
    dados = dados.loc[dados["WELDNº"].isin(completos[completos >= 100].index)]
    caracteristicas = weld_analysis.caracteristicas_por_solda(dados)
    assert len(caracteristicas) > 20
    painel, alertas = weld_analysis.analisar_soldas(caracteristicas)
    assert len(painel) == len(caracteristicas)
    assert set(painel["situacao"]).issubset({
        "Sem referência contextual", "Sem desvio sinalizado pela heurística",
        "Variação a investigar", "Investigação prioritária",
        "Qualidade de dados: pontos duplicados",
    })


def test_pequeno_desvio_persistente_aparece_no_painel():
    pontos = _curvas(total=28)
    mask = pontos["WELDNº"].ge(25)
    pontos.loc[mask, "CORRENTE"] += .1
    car = weld_analysis.caracteristicas_por_solda(pontos, ("CORRENTE",))
    painel, alertas = weld_analysis.analisar_soldas(car, ("CORRENTE",))
    assert painel.iloc[-1]["situacao"] == "Variação a investigar"
    assert any("persistente" in texto for texto in alertas["evidencia"].tolist())

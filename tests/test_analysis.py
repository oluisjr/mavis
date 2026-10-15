"""Testes determinísticos. Não dependem de amostras industriais confidenciais."""
import numpy as np
import pandas as pd
from app import analysis, data_loader


def _amostra(valores, datas=None):
    if datas is None:
        datas = pd.date_range("2026-01-01", periods=len(valores), freq="D")
    return pd.DataFrame({"DATA": datas, "VELOCIDADE": valores})


def test_tendencia_ordenada_cronologicamente():
    df = _amostra([10, 10, 10, 10, 15, 15, 15, 15])
    invertido = df.iloc[::-1].reset_index(drop=True)
    assert analysis.analisar_tendencia(invertido, "VELOCIDADE") == analysis.analisar_tendencia(df, "VELOCIDADE")
    assert "alta" in analysis.analisar_tendencia(df, "VELOCIDADE")


def test_tendencia_insuficiente():
    assert "insuficientes" in analysis.analisar_tendencia(_amostra([1, 2, 3]), "VELOCIDADE")


def test_valores_invalidos_nao_produzem_probabilidade():
    df = _amostra([1, np.nan, np.inf, 1, np.nan, 1])
    assert analysis.calcular_indice_desvio(df, "VELOCIDADE") is None
    assert "insuficientes" in analysis.detectar_anomalia(df, "VELOCIDADE")


def test_referencia_constante_sem_desvio():
    assert analysis.calcular_indice_desvio(_amostra([100] * 12), "VELOCIDADE") == 0.0


def test_mudanca_relevante_aumenta_indice():
    base = [100] * 10
    pequenos = _amostra(base + [100.1] * 4)
    grandes = _amostra(base + [115] * 4)
    assert analysis.calcular_indice_desvio(grandes, "VELOCIDADE") > analysis.calcular_indice_desvio(pequenos, "VELOCIDADE")


def test_heuristica_nao_atribui_falha_com_4_amostras():
    assert analysis.simular_risco_por_regras(_amostra([100, 100, 100, 115]), "VELOCIDADE") is None
    assert analysis.calcular_health_score(None) is None


def test_normalizacao_preserva_precisao_e_trata_nao_numerico():
    df = pd.DataFrame({"VELOCIDADE": ["105", "n/a"], "CORRENTE": [120.7, np.inf]})
    result = data_loader._normalizar_medidas(df)
    assert result["VELOCIDADE"].iloc[0] == 1.05
    assert np.isnan(result["VELOCIDADE"].iloc[1])
    assert abs(result["CORRENTE"].iloc[0] - 12.07) < 1e-8
    assert np.isnan(result["CORRENTE"].iloc[1])


def test_filtro_codigos_e_datas_completas():
    df = pd.DataFrame({
        "DATA": pd.to_datetime(["2026-01-01", "2026-02-01", "2026-02-02"]),
        "PROGRAM_Nº": pd.Series(["123", "123", "124"], dtype="string"),
        "code ENTRY": pd.Series(["A", "A", "B"], dtype="string"),
        "code EXIT": pd.Series(["X", "Y", "X"], dtype="string"),
        "VELOCIDADE": [100.0, 200.0, 300.0],
    })
    filt = {"receita_fmt": "123", "entry_code": "A", "exit_code": "Y",
            "anos": [2026], "dias": ["2026-02-01"]}
    dados = data_loader._filtrar_raw(df, filt)
    assert len(dados) == 1
    assert float(dados["VELOCIDADE"].iloc[0]) == 200.0


def test_agrupamento_diario_mensal_consistente():
    df = pd.DataFrame({
        "DATA": pd.to_datetime(["2026-01-05", "2026-01-06", "2026-02-02"]),
        "VELOCIDADE": [100.0, 200.0, 300.0],
    })
    visoes = data_loader._agregar_raw(df)
    assert len(visoes["diario"]) == 3
    assert len(visoes["mensal"]) == 2
    assert abs(visoes["mensal"]["VELOCIDADE"].iloc[0] - 1.5) < 1e-8
    assert visoes["semanal"]["SEMANA"].dt.weekday.eq(0).all()


def test_filtro_de_origem_nao_fabrica_dados():
    empty = pd.DataFrame({"DATA": pd.to_datetime([]), "VELOCIDADE": pd.Series(dtype=float)})
    resultado = data_loader._agregar_raw(empty)
    assert all(df.empty for df in resultado.values())


def test_hipoteses_nao_vazias():
    assert analysis.analisar_causa_raiz("SENSOR_INEXISTENTE")["acoes_recomendadas"]

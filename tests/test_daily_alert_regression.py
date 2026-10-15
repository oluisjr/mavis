"""Regressões: o dashboard não pode chamar de normal uma tendência visível."""
import numpy as np
import pandas as pd
from app import analysis


def _serie(valores):
    return pd.DataFrame({
        "DATA": pd.date_range("2026-06-01", periods=len(valores), freq="D"),
        "PRESSAO_MARTELADOR": valores,
    })


def test_queda_841_por_cento_nunca_recebe_indice_zero():
    valores = [5.20] * 5 + [5.02, 4.95, 4.88, 4.72, 4.65, 4.56, 4.43, 4.42, 4.38, 4.35, 4.75, 4.76, 4.76268, 4.76268]
    df = _serie(valores)
    resumo = analysis.resumir_desvio_agregado(df, "PRESSAO_MARTELADOR")
    assert resumo["mudanca"] < -8.0
    assert resumo["indice"] > 0
    assert resumo["estado"] == "relevante"
    assert "Investigar" in analysis.detectar_anomalia(df, "PRESSAO_MARTELADOR")


def test_queda_intermittente_se_recupera_mas_nao_e_ignorada():
    df = _serie([5.2] * 6 + [3.7] + [5.2] * 12)
    resumo = analysis.resumir_desvio_agregado(df, "PRESSAO_MARTELADOR")
    assert abs(resumo["mudanca"]) < 0.01
    assert resumo["excursao"] > 20
    assert resumo["estado"] == "relevante"


def test_pequenas_oscilacoes_nao_autorizam_normalidade():
    df = _serie([5.2] * 19)
    mensagem = analysis.detectar_anomalia(df, "PRESSAO_MARTELADOR")
    assert "Sem gatilho" in mensagem
    assert "Não significa que a operação esteja normal" in mensagem


def test_salto_em_um_unico_dia_gera_evidencia():
    df = _serie([5.0] * 8 + [4.5] + [5.0] * 10)
    resumo = analysis.resumir_desvio_agregado(df, "PRESSAO_MARTELADOR")
    assert resumo["salto"] >= 10
    assert resumo["estado"] == "relevante"


def test_referencia_nula_ou_amostra_insuficiente_ficam_inconclusivas():
    for valores in ([0.0] * 19, [1.0, 1.1, 1.2]):
        resumo = analysis.resumir_desvio_agregado(_serie(valores), "PRESSAO_MARTELADOR")
        assert resumo["indice"] is None
        assert resumo["estado"] == "indisponivel"


def test_indicadores_usam_a_ordenacao_por_data():
    dados = _serie([5.2] * 10 + [4.6] * 9)
    a = analysis.resumir_desvio_agregado(dados, "PRESSAO_MARTELADOR")
    b = analysis.resumir_desvio_agregado(dados.iloc[::-1].reset_index(drop=True), "PRESSAO_MARTELADOR")
    assert a == b

"""Indicadores DESCRITIVOS de processo. Não estimam probabilidade de falha.

Sem limites de engenharia, rótulos de falha e validação histórica, os resultados
não devem ser apresentados como risco preditivo nem usados para comando automático.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd
from . import config

MIN_AMOSTRAS_TENDENCIA = 4
MIN_AMOSTRAS_DESVIO = 8
COLUNAS_TEMPO = ("DATA", "SEMANA", "MES", "ANO")


def _serie_ordenada(df: pd.DataFrame, sensor: str) -> pd.Series:
    """Retorna valores numéricos finitos, ordenados cronologicamente quando possível."""
    if df is None or df.empty or sensor not in df:
        return pd.Series(dtype="float64")
    dados = df.copy()
    for coluna in COLUNAS_TEMPO:
        if coluna in dados.columns:
            datas = pd.to_datetime(dados[coluna], errors="coerce")
            dados = dados.assign(_ordem=datas).sort_values("_ordem", kind="stable")
            break
    serie = pd.to_numeric(dados[sensor], errors="coerce").replace(
        [np.inf, -np.inf], np.nan
    ).dropna()
    return serie.reset_index(drop=True).astype(float)


def _medianas_extremas(serie: pd.Series) -> tuple[float, float]:
    janela = max(2, math.ceil(len(serie) * 0.2))
    return float(serie.iloc[:janela].median()), float(serie.iloc[-janela:].median())


def analisar_tendencia(dados: pd.DataFrame, eixo_y: str, sensor: str | None = None) -> str:
    """Descreve a mudança entre janelas robustas, sem inferir causalidade."""
    serie = _serie_ordenada(dados, eixo_y)
    if len(serie) < MIN_AMOSTRAS_TENDENCIA:
        return "Dados insuficientes para avaliar tendência (mínimo: 4 registros válidos)."
    inicio, fim = _medianas_extremas(serie)
    delta = fim - inicio
    if math.isclose(inicio, 0.0, abs_tol=1e-12):
        mudanca = f"variação absoluta de {delta:+.3f} (base próxima de zero)"
    else:
        mudanca = f"variação de {delta / abs(inicio) * 100:+.2f}%"
    tolerancia = max(abs(inicio) * 0.005, 1e-9)
    direcao = "estável" if abs(delta) <= tolerancia else ("alta" if delta > 0 else "queda")
    return (
        f"Tendência descritiva de **{direcao}**: {mudanca}, "
        f"comparando a mediana dos primeiros e últimos 20% dos {len(serie)} "
        "registros válidos (mínimo de 2 por janela). "
        "Não indica, isoladamente, defeito ou falha iminente."
    )


def calcular_indice_desvio(df: pd.DataFrame, sensor: str) -> float | None:
    """Índice heurístico 0–100 de DESVIO em relação ao início da série.

    Usa os primeiros 60% dos registros como referência temporária, e os últimos
    20% como janela recente. Não há calibração probabilística ou limites de processo.
    A referência histórica NÃO substitui uma faixa operacional homologada.
    """
    serie = _serie_ordenada(df, sensor)
    n = len(serie)
    if n < MIN_AMOSTRAS_DESVIO:
        return None
    base = serie.iloc[:max(5, math.ceil(0.6 * n))]
    atual = serie.iloc[-max(3, math.ceil(0.2 * n)):]
    mediana = float(base.median())
    mad = float((base - mediana).abs().median())
    q25, q75 = np.percentile(base, [25, 75])
    escala = max(1.4826 * mad, (q75 - q25) / 1.349, abs(mediana) * 0.005, 1e-6)
    z_robusto = abs(float(atual.median()) - mediana) / escala
    return round(min(100.0, max(0.0, (z_robusto - 1.0) * 20.0)), 1)


def simular_risco_por_regras(df_dados: pd.DataFrame, sensor: str) -> float | None:
    """Compatibilidade: devolve índice de desvio, NÃO probabilidade de falha."""
    return calcular_indice_desvio(df_dados, sensor)


def detectar_anomalia(df_filtrado: pd.DataFrame, sensor: str) -> str:
    indice = calcular_indice_desvio(df_filtrado, sensor)
    if indice is None:
        return "⚪ **Dados insuficientes** para classificar desvio (mínimo: 8)."
    if indice >= 70:
        return f"🔴 **Desvio estatístico elevado** (índice {indice:.1f}/100)."
    if indice >= 40:
        return f"🟠 **Desvio estatístico relevante** (índice {indice:.1f}/100)."
    if indice >= 15:
        return f"🟡 **Variação a acompanhar** (índice {indice:.1f}/100)."
    return f"🟢 **Sem desvio relevante por esta heurística** ({indice:.1f}/100)."


def calcular_health_score(indice_desvio: float | None) -> float | None:
    """Compatibilidade: índice complementar de estabilidade, NÃO saúde do equipamento."""
    if indice_desvio is None or not math.isfinite(float(indice_desvio)):
        return None
    return round(100 - min(100.0, max(0.0, float(indice_desvio))), 1)


def analisar_causa_raiz(sensor_com_maior_risco: str) -> dict:
    """Retorna hipóteses técnicas gerais; não conclui causa raiz automaticamente."""
    base = config.BASE_CONHECIMENTO_CAUSA_RAIZ
    return base.get(sensor_com_maior_risco) or base.get("DEFAULT") or {
        "causas_provaveis": ["Base de hipóteses não configurada."],
        "acoes_recomendadas": ["Solicitar avaliação da equipe técnica."],
    }


def calcular_impacto_financeiro(riscos: dict) -> tuple[float, dict]:
    """Cenário ilustrativo legado, NÃO uma estimativa validada de perdas.

    Mantido apenas para compatibilidade: não chamar no painel operacional até
    existirem dados de custos, eventos de falha e metodologia aprovada.
    """
    estimativas = {
        sensor: round(float(valor) / 100 * config.CUSTOS_OPERACIONAIS[sensor], 2)
        for sensor, valor in riscos.items()
        if sensor in config.CUSTOS_OPERACIONAIS
        and isinstance(valor, (int, float))
        and math.isfinite(float(valor))
    }
    return round(sum(estimativas.values()), 2), estimativas

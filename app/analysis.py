"""Indicadores DESCRITIVOS de processo. Não estimam probabilidade de falha.

Sem limites de engenharia, rótulos de falha e validação histórica, os resultados
não devem ser apresentados como risco preditivo nem usados para comando automático.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd
from . import config
from .daily_metrics import metricas

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


def resumir_desvio_agregado(df: pd.DataFrame, sensor: str) -> dict:
    """Triagem de médias por período. Os resultados não diagnosticam falhas."""
    return metricas(_serie_ordenada(df, sensor))


def calcular_indice_desvio(df: pd.DataFrame, sensor: str) -> float | None:
    """Índice exploratório para priorização de investigação, não risco físico."""
    return resumir_desvio_agregado(df, sensor)["indice"]


def simular_risco_por_regras(df_dados: pd.DataFrame, sensor: str) -> float | None:
    """Compatibilidade: devolve índice de desvio, NÃO probabilidade de falha."""
    return calcular_indice_desvio(df_dados, sensor)


def detectar_anomalia(df_filtrado: pd.DataFrame, sensor: str) -> str:
    analise = resumir_desvio_agregado(df_filtrado, sensor)
    indice = analise["indice"]
    if indice is None:
        return "⚪ **Avaliação inconclusiva: dados insuficientes ou referência inválida.** " + analise["motivo"]
    detalhes = (
        f"tendência {analise['mudanca']:+.2f}%; "
        f"excursão máxima {analise['excursao']:.2f}%; "
        f"maior salto entre registros {analise['salto']:.2f}%"
    )
    if analise["estado"] == "relevante":
        return (f"🔴 **Mudança relevante no histórico agregado. Investigar.** "
                f"Índice exploratório: {indice:.1f}/100; {detalhes}. "
                "Não é diagnóstico de falha.")
    if analise["estado"] == "atencao":
        return (f"🟠 **Variação a investigar no histórico agregado.** "
                f"Índice exploratório: {indice:.1f}/100; {detalhes}.")
    return (f"⚪ **Sem gatilho nesta análise agregada** "
            f"(índice exploratório {indice:.1f}/100; {detalhes}). "
            "**Não significa que a operação esteja normal, nem exclui falha entre soldas.**")


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

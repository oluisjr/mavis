"""Detecção sensível de desvios nas curvas ponto a ponto de cada solda.

Indicadores experimentais para TRIAGEM. Nenhuma classificação estima a
probabilidade, o mecanismo físico ou a iminência de falha do equipamento.
Referência contextual usa exclusivamente soldas anteriores, sem vazamento futuro.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .weld_loader import CONTEXT

FEATURES = {
    "mediana": ("Mudança de patamar", "both"),
    "faixa90": ("Ampliação da oscilação", "high"),
    "passo95": ("Oscilação entre pontos consecutivos", "high"),
    "pico99": ("Picos locais de curta duração", "high"),
}
MIN_POINTS = 12
MIN_REFERENCE = 12
REFERENCE_WINDOW = 48
EVIDENCE_THRESHOLD = 3.5


def caracteristicas_por_solda(df: pd.DataFrame, sensores: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Métricas calculadas SEM médias diárias nem mistura de soldas.

    Retorna mediana, faixa P95-P05, P95 da variação entre pontos consecutivos,
    P99 dos resíduos em relação à mediana móvel local, contagem e qualidade.
    """
    if df.empty:
        return pd.DataFrame()
    sensores = tuple(s for s in (sensores or tuple(config.NOMES_SENSORES))
                    if s in df.columns and s not in config.SENSORES_INDISPONIVEIS)
    if not sensores:
        return pd.DataFrame()
    dados = df.sort_values(["DATAHORA", "WELDNº", "ID_PONTO"], kind="stable").reset_index(drop=True)
    agrupador = dados.groupby("WELDNº", sort=False, dropna=False)
    metadados = agrupador[["DATAHORA", *CONTEXT]].first()
    metadados["amostras"] = agrupador.size()
    metadados["pontos_unicos"] = agrupador["ID_PONTO"].nunique()
    metadados["pontos_duplicados"] = metadados["amostras"] - metadados["pontos_unicos"]
    resultado = metadados.copy()
    for sensor in sensores:
        sinal = pd.to_numeric(dados[sensor], errors="coerce").replace([np.inf, -np.inf], np.nan)
        serie = sinal.groupby(dados["WELDNº"], sort=False)
        resultado[f"{sensor}__validos"] = serie.count()
        resultado[f"{sensor}__mediana"] = serie.median()
        resultado[f"{sensor}__faixa90"] = serie.quantile(.95) - serie.quantile(.05)
        passos = sinal.groupby(dados["WELDNº"], sort=False).diff().abs()
        resultado[f"{sensor}__passo95"] = passos.groupby(dados["WELDNº"], sort=False).quantile(.95)
        mediana_local = (
            sinal.groupby(dados["WELDNº"], sort=False)
            .transform(lambda itens: itens.rolling(9, center=True, min_periods=3).median())
        )
        residuos = (sinal - mediana_local).abs()
        resultado[f"{sensor}__pico99"] = residuos.groupby(dados["WELDNº"], sort=False).quantile(.99)

    resultado = resultado.reset_index()
    resultado = resultado.sort_values(["DATAHORA", "WELDNº"], kind="stable").reset_index(drop=True)
    # IDs contextuais exatos. Nunca combinar programações e códigos distintos.
    resultado["contexto"] = resultado[list(CONTEXT)].fillna("N/D").astype(str).agg(" | ".join, axis=1)
    return resultado


def _referencia_historica(tabela: pd.DataFrame, coluna: str) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Mediana, dispersão interquartil e n de soldas ANTERIORES no mesmo contexto."""
    base = pd.Series(np.nan, index=tabela.index, dtype=float)
    spread = base.copy()
    quantidade = pd.Series(0.0, index=tabela.index)
    for _, indices in tabela.groupby("contexto", sort=False).indices.items():
        posicoes = list(indices)
        v = pd.to_numeric(tabela.iloc[posicoes][coluna], errors="coerce").reset_index(drop=True)
        anteriores = v.shift(1)
        janela = anteriores.rolling(REFERENCE_WINDOW, min_periods=MIN_REFERENCE)
        base.iloc[posicoes] = janela.median().to_numpy()
        spread.iloc[posicoes] = ((janela.quantile(.75) - janela.quantile(.25)) / 1.349).to_numpy()
        quantidade.iloc[posicoes] = anteriores.rolling(REFERENCE_WINDOW, min_periods=1).count().to_numpy()
    return base, spread, quantidade


def analisar_soldas(caracteristicas: pd.DataFrame, sensores: tuple[str, ...] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna painel de soldas e evidências por sensor/atributo (sem probabilidades).

    A dispersão mínima é derivada da resolução de aquisição presumida nos
    fatores de escala; validação metrológica é obrigatória antes de operar.
    """
    if caracteristicas.empty:
        return pd.DataFrame(), pd.DataFrame()
    lista = tuple(s for s in (sensores or tuple(config.NOMES_SENSORES))
                  if f"{s}__mediana" in caracteristicas and s not in config.SENSORES_INDISPONIVEIS)
    painel = caracteristicas[["WELDNº", "DATAHORA", "contexto", "amostras", "pontos_duplicados"]].copy()
    painel["situacao"] = "Sem referência contextual"
    painel["forca_maxima"] = 0.0
    painel["n_evidencias"] = 0
    painel["n_referencias"] = 0
    alertas = []
    if not lista:
        return painel, pd.DataFrame()

    for sensor in lista:
        valido = caracteristicas[f"{sensor}__validos"] >= MIN_POINTS
        for feature, (descricao, sentido) in FEATURES.items():
            coluna = f"{sensor}__{feature}"
            historico, dispersao, quant = _referencia_historica(caracteristicas, coluna)
            quantum = 1.0 / config.FATORES_ESCALA[sensor]
            # Não assumir precisão infinita: evita alarmes por ruído de quantização.
            escala = dispersao.clip(lower=quantum / 2)
            valor = pd.to_numeric(caracteristicas[coluna], errors="coerce")
            z = (valor - historico) / escala
            if sentido == "both":
                z = z.abs()
            else:
                z = z.clip(lower=0.0)
            # Leituras sem referência NÃO equivalem a estado normal.
            elegivel = valido & quant.ge(MIN_REFERENCE) & valor.notna() & historico.notna()
            painel.loc[elegivel, "n_referencias"] += 1
            painel.loc[elegivel, "situacao"] = "Sem desvio sinalizado pela heurística"
            indices = np.flatnonzero((elegivel & z.ge(EVIDENCE_THRESHOLD)).fillna(False).to_numpy())
            for idx in indices:
                potencia = float(z.iloc[idx])
                painel.at[idx, "n_evidencias"] += 1
                painel.at[idx, "forca_maxima"] = max(float(painel.at[idx, "forca_maxima"]), potencia)
                alertas.append({
                    "WELDNº": caracteristicas.at[idx, "WELDNº"],
                    "DATAHORA": caracteristicas.at[idx, "DATAHORA"],
                    "contexto": caracteristicas.at[idx, "contexto"],
                    "sensor": sensor,
                    "evidencia": descricao,
                    "magnitude_robusta": round(potencia, 2),
                    "valor_observado": float(valor.iloc[idx]),
                    "referencia_anterior": float(historico.iloc[idx]),
                    "soldas_referencia": int(quant.iloc[idx]),
                })

    alerta = painel["n_evidencias"].gt(0)
    painel.loc[alerta, "situacao"] = "Variação a investigar"
    # Escalonamento: múltiplas evidências independentes ou alteração extrema.
    prioridade = (painel["forca_maxima"] >= 8.0) | (
        (painel["forca_maxima"] >= 5.0) & (painel["n_evidencias"] >= 2)
    )
    painel.loc[alerta & prioridade, "situacao"] = "Investigação prioritária"
    painel.loc[painel["pontos_duplicados"] > 0, "situacao"] = "Qualidade de dados: pontos duplicados"
    painel["forca_maxima"] = painel["forca_maxima"].round(2)
    return painel, pd.DataFrame(alertas)


def perfil_com_referencia(
    pontos: pd.DataFrame, solda: int, sensor: str, janela: int = 30
) -> tuple[pd.DataFrame, int]:
    """Curva da solda e envelope empírico P05/P50/P95 de soldas anteriores comparáveis.

    Compara o mesmo ID_PONTO e não usa registros futuros na referência.
    """
    if sensor not in pontos or sensor in config.SENSORES_INDISPONIVEIS:
        return pd.DataFrame(), 0
    ordens = pontos[["WELDNº", "DATAHORA", *CONTEXT]].drop_duplicates("WELDNº")
    ordens = ordens.sort_values(["DATAHORA", "WELDNº"], kind="stable").reset_index(drop=True)
    alvo = ordens.loc[ordens["WELDNº"].eq(solda)]
    if alvo.empty:
        return pd.DataFrame(), 0
    i = int(alvo.index[-1])
    ctx = alvo.iloc[-1][list(CONTEXT)].astype("string").fillna("N/D").tolist()
    passado = ordens.iloc[:i]
    comparaveis = passado.loc[
        passado[list(CONTEXT)].astype("string").fillna("N/D").eq(ctx).all(axis=1)
    ].tail(janela)
    selecionados = pontos.loc[pontos["WELDNº"].eq(solda), ["ID_PONTO", sensor]]
    grafico = selecionados.groupby("ID_PONTO")[sensor].median().to_frame("Solda selecionada")
    if len(comparaveis) >= MIN_REFERENCE:
        anterior = pontos.loc[
            pontos["WELDNº"].isin(comparaveis["WELDNº"]), ["ID_PONTO", sensor]
        ]
        agr = anterior.groupby("ID_PONTO")[sensor]
        grafico["Referência P50"] = agr.median()
        grafico["Referência P05"] = agr.quantile(.05)
        grafico["Referência P95"] = agr.quantile(.95)
    return grafico.sort_index(), len(comparaveis)

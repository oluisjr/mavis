"""Leituras ponto a ponto, preservando a curva de cada solda.

Nenhuma média temporal é aplicada antes da análise. DATAHORA é o instante
do registro da solda, NÃO o timestamp individual de cada ponto.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from . import config

REQUIRED = ("WELDNº", "ID_PONTO", "DATAHORA", "MeasP", "code ENTRY", "code EXIT")
CONTEXT = ("code ENTRY", "code EXIT", "MeasP")
OPTIONAL = ("THICKN_ENTRY", "THICKN_EXIT", "WIDTH ENTRY", "WIDTH EXIT")
SENSORS = tuple(config.NOMES_SENSORES)


def listar_receitas_detalhadas() -> list[str]:
    receitas = []
    for arquivo in config.DATA_DIR.glob("dados_detalhados_*.parquet"):
        codigo = arquivo.stem.removeprefix("dados_detalhados_")
        if codigo.isdecimal():
            receitas.append(codigo)
    return sorted(receitas, key=lambda item: int(item))


@st.cache_data(ttl=1800, max_entries=2, show_spinner="Lendo registros individuais de soldagem...")
def carregar_pontos(receita: str) -> pd.DataFrame:
    """Carrega somente uma receita, nunca junta regimes de receitas diferentes."""
    if not re.fullmatch(r"[0-9]{1,8}", str(receita)):
        raise ValueError("Receita inválida.")
    caminho = (config.DATA_DIR / f"dados_detalhados_{receita}.parquet")
    if not caminho.is_file():
        raise FileNotFoundError(f"Sem dados detalhados para a receita {receita}.")
    try:
        import pyarrow.parquet as pq
        schema = pq.read_schema(caminho)
        cols = list(dict.fromkeys((*REQUIRED, *OPTIONAL, *SENSORS)))
        faltando = [nome for nome in REQUIRED if nome not in schema.names]
        if faltando:
            raise ValueError(f"Colunas essenciais ausentes: {', '.join(faltando)}")
        df = pd.read_parquet(caminho, columns=[c for c in cols if c in schema.names])
    except ImportError as erro:
        raise RuntimeError("Instale pyarrow para ler o histórico ponto a ponto.") from erro

    df["WELDNº"] = pd.to_numeric(df["WELDNº"], errors="coerce")
    df["ID_PONTO"] = pd.to_numeric(df["ID_PONTO"], errors="coerce")
    df["DATAHORA"] = pd.to_datetime(df["DATAHORA"], errors="coerce")
    df = df.dropna(subset=["WELDNº", "ID_PONTO", "DATAHORA"])
    for coluna in CONTEXT:
        df[coluna] = df[coluna].astype("string").fillna("N/D").str.strip()
    for sensor in SENSORS:
        if sensor in df:
            df[sensor] = pd.to_numeric(df[sensor], errors="coerce").replace(
                [np.inf, -np.inf], np.nan
            ) / config.FATORES_ESCALA[sensor]
    # Número da solda e índice da amostra são identificadores, não timestamps.
    return df.sort_values(["DATAHORA", "WELDNº", "ID_PONTO"], kind="stable").reset_index(drop=True)


def filtrar_soldas_recentes(pontos: pd.DataFrame, ultimas: int = 1000) -> pd.DataFrame:
    """Recorta soldas COMPLETAS; nunca recorta arbitrariamente as últimas linhas."""
    ultimas = max(30, int(ultimas))
    chaves = pontos[["WELDNº", "DATAHORA"]].drop_duplicates("WELDNº")
    recentes = set(chaves.sort_values(["DATAHORA", "WELDNº"]).tail(ultimas)["WELDNº"])
    return pontos.loc[pontos["WELDNº"].isin(recentes)].copy()


def faixa_contexto(df: pd.DataFrame, codigo_entrada="Todos", codigo_saida="Todos") -> pd.DataFrame:
    resultado = df
    if str(codigo_entrada) != "Todos":
        resultado = resultado[resultado["code ENTRY"].eq(str(codigo_entrada))]
    if str(codigo_saida) != "Todos":
        resultado = resultado[resultado["code EXIT"].eq(str(codigo_saida))]
    return resultado.copy()

"""Ingestão, saneamento e filtragem consistente dos dados industriais."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import pandas as pd
import numpy as np
import requests
import streamlit as st
from . import config

COLUNAS_DATA = {"diario": "DATA", "semanal": "SEMANA", "mensal": "MES", "anual": "ANO"}
SENSORES = tuple(config.NOMES_SENSORES)
FILTROS_CODIGOS = {"entry_code": "code ENTRY", "exit_code": "code EXIT"}


@st.cache_data(ttl=1800, show_spinner=False)
def _baixar_excel(url: str) -> bytes:
    resposta = requests.get(url, timeout=(10, 60))
    resposta.raise_for_status()
    return resposta.content


def _abrir_excel(origem: str) -> pd.ExcelFile:
    if origem.startswith(("https://", "http://")):
        return pd.ExcelFile(BytesIO(_baixar_excel(origem)), engine="openpyxl")
    arquivo = Path(origem).expanduser()
    if not arquivo.is_file():
        raise FileNotFoundError(f"Planilha de dados não encontrada: {arquivo}")
    return pd.ExcelFile(arquivo, engine="openpyxl")


def _sanear_base(df: pd.DataFrame) -> pd.DataFrame:
    dados = df.copy()
    if "DATA" not in dados:
        raise ValueError("A aba 'Dados Completos' não possui a coluna DATA.")
    dados["DATA"] = pd.to_datetime(dados["DATA"], errors="coerce")
    dados = dados.dropna(subset=["DATA"]).sort_values("DATA", kind="stable")
    if "PROGRAM_Nº" in dados:
        dados["PROGRAM_Nº"] = dados["PROGRAM_Nº"].astype("string").str.strip().str.replace(
            r"\.0$", "", regex=True
        )
    for codigo in FILTROS_CODIGOS.values():
        if codigo in dados:
            dados[codigo] = dados[codigo].astype("string").str.strip()
    return dados.reset_index(drop=True)


@st.cache_data(ttl=1800, show_spinner="Carregando histórico de produção...")
def carregar_dados_iniciais() -> pd.DataFrame:
    try:
        with _abrir_excel(config.CAMINHO_EXCEL_URL) as excel:
            if "Dados Completos" not in excel.sheet_names:
                raise ValueError("A aba 'Dados Completos' não existe na planilha.")
            return _sanear_base(pd.read_excel(excel, sheet_name="Dados Completos"))
    except (OSError, ValueError, requests.RequestException) as erro:
        st.error(f"Não foi possível carregar o histórico: {erro}")
        return pd.DataFrame()


def _normalizar_medidas(df: pd.DataFrame) -> pd.DataFrame:
    dados = df.copy()
    for sensor, fator in config.FATORES_ESCALA.items():
        if sensor in dados:
            dados[sensor] = pd.to_numeric(dados[sensor], errors="coerce").replace(
                [np.inf, -np.inf], np.nan
            ) / fator
    return dados


def _normalizar_agregado(df: pd.DataFrame, granularidade: str) -> pd.DataFrame:
    if df.empty:
        return df
    dados = df.copy()
    coluna = COLUNAS_DATA[granularidade]
    if coluna not in dados:
        return pd.DataFrame()
    if granularidade == "anual":
        anos = dados[coluna].astype("string").str.extract(r"(\d{4})", expand=False)
        dados[coluna] = pd.to_datetime(anos, format="%Y", errors="coerce")
    else:
        dados[coluna] = pd.to_datetime(dados[coluna], errors="coerce", utc=True).dt.tz_localize(None)
    dados = dados.dropna(subset=[coluna]).sort_values(coluna, kind="stable")
    return _normalizar_medidas(dados)


@st.cache_data(ttl=1800, show_spinner=False)
def carregar_dados_por_receita(receita_selecionada: str):
    """Compatibilidade com telas antigas: histórico, diário, semanal, mensal, anual."""
    vazio = pd.DataFrame()
    registros = carregar_dados_iniciais()
    avisos = []
    if registros.empty:
        return (vazio, vazio, vazio, vazio, vazio), [("error", "Histórico indisponível.")]
    receita = str(receita_selecionada).strip()
    if receita in ("", "Todas"):
        planilhas = ("Médias Diárias", "Médias Semanais", "Médias Mensais", "Médias Anuais")
    else:
        planilhas = (receita, f"{receita} - Semanal", f"{receita} - Mensal", f"{receita} - Anual")
    saidas = []
    try:
        with _abrir_excel(config.CAMINHO_EXCEL_URL) as excel:
            nomes = {str(aba).strip().casefold(): aba for aba in excel.sheet_names}
            for granularidade, nome in zip(COLUNAS_DATA, planilhas):
                nome_real = nomes.get(nome.casefold())
                if nome_real is None:
                    avisos.append(("warning", f"Aba '{nome}' não encontrada."))
                    saidas.append(vazio)
                else:
                    saidas.append(_normalizar_agregado(pd.read_excel(excel, sheet_name=nome_real), granularidade))
    except (OSError, ValueError, requests.RequestException) as erro:
        avisos.append(("error", f"Falha ao ler a planilha: {erro}"))
        saidas = [vazio] * 4
    return (registros, *saidas), avisos


def _filtrar_raw(registros: pd.DataFrame, filtros: dict) -> pd.DataFrame:
    dados = registros.copy()
    receita = str(filtros.get("receita_fmt") or "Todas")
    if receita != "Todas" and "PROGRAM_Nº" in dados:
        dados = dados.loc[dados["PROGRAM_Nº"].eq(receita).fillna(False)]
    for filtro, coluna in FILTROS_CODIGOS.items():
        escolhido = str(filtros.get(filtro) or "Todos")
        if escolhido != "Todos" and coluna in dados:
            dados = dados.loc[dados[coluna].eq(escolhido).fillna(False)]
    if filtros.get("anos"):
        dados = dados[dados["DATA"].dt.year.isin(filtros["anos"])]
    if filtros.get("meses"):
        dados = dados[dados["DATA"].dt.month.isin(filtros["meses"])]
    if filtros.get("semanas"):
        dados = dados[dados["DATA"].dt.isocalendar().week.isin(filtros["semanas"])]
    if filtros.get("dias"):
        # Trata dias como datas completas (AAAA-MM-DD), evitando agregar dia 1 de meses diferentes.
        dias = pd.to_datetime(filtros["dias"], errors="coerce")
        dados = dados[dados["DATA"].dt.normalize().isin(dias)]
    return dados


def _agregar_raw(dados: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Agrega leituras após TODOS os filtros, mantendo a mesma população de referência."""
    medidas = [nome for nome in SENSORES if nome in dados]
    if not medidas or dados.empty:
        return {nome: pd.DataFrame() for nome in COLUNAS_DATA}
    limpo = _normalizar_medidas(dados)
    limpo = limpo.assign(
        _dia=limpo["DATA"].dt.floor("D"),
        _semana=limpo["DATA"].dt.to_period("W-SUN").dt.start_time,
        _mes=limpo["DATA"].dt.to_period("M").dt.start_time,
        _ano=limpo["DATA"].dt.to_period("Y").dt.start_time,
    )
    chaves = {"diario": "_dia", "semanal": "_semana", "mensal": "_mes", "anual": "_ano"}
    retorno = {}
    for nivel, chave in chaves.items():
        agregado = limpo.groupby(chave, dropna=True)[medidas].mean().reset_index()
        retorno[nivel] = agregado.rename(columns={chave: COLUNAS_DATA[nivel]})
    return retorno


def obter_visoes_filtradas(filtros: dict) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Preferir histórico detalhado. Recusar filtros que não existam em médias pré-calculadas."""
    registros = carregar_dados_iniciais()
    vazios = {nome: pd.DataFrame() for nome in COLUNAS_DATA}
    if registros.empty:
        return vazios, ["Histórico de origem indisponível."]
    if set(SENSORES).intersection(registros.columns):
        ausentes = [nome for nome in SENSORES if nome not in registros]
        avisos = [f"Sem coluna de origem para: {', '.join(ausentes)}."] if ausentes else []
        for filtro, coluna in FILTROS_CODIGOS.items():
            if filtros.get(filtro, "Todos") != "Todos" and coluna not in registros:
                return vazios, [f"Filtro {coluna} não existe na origem. Não foram gerados indicadores."]
        return _agregar_raw(_filtrar_raw(registros, filtros)), avisos

    if any(filtros.get(k, "Todos") != "Todos" for k in FILTROS_CODIGOS):
        return vazios, ["Filtros de entrada/saída não podem ser aplicados: as médias não possuem essas dimensões."]
    (total, diario, semanal, mensal, anual), mensagens = carregar_dados_por_receita(filtros.get("receita_fmt", "Todas"))
    avisos = [mensagem for _, mensagem in mensagens]
    series = dict(zip(COLUNAS_DATA, (diario, semanal, mensal, anual)))
    for nivel, df in series.items():
        if df.empty:
            continue
        coluna = COLUNAS_DATA[nivel]
        mascara = pd.Series(True, index=df.index)
        if filtros.get("anos"):
            mascara &= df[coluna].dt.year.isin(filtros["anos"])
        if filtros.get("meses"):
            mascara &= df[coluna].dt.month.isin(filtros["meses"])
        if filtros.get("semanas"):
            # Semana e dia só são dimensões válidas nas séries diárias/semanais.
            if nivel in ("diario", "semanal"):
                mascara &= df[coluna].dt.isocalendar().week.isin(filtros["semanas"])
        if filtros.get("dias") and nivel == "diario":
            datas = pd.to_datetime(filtros["dias"], errors="coerce")
            mascara &= df[coluna].dt.normalize().isin(datas)
        series[nivel] = df.loc[mascara].reset_index(drop=True)
    avisos.append("Base agregada sem colunas de sensores no histórico: filtros de dias/semanas podem não refletir os totais mensais/anuais.")
    return series, avisos


@st.cache_data(ttl=1800, show_spinner=False)
def obter_top_4_receitas_formatadas() -> list[str]:
    registros = carregar_dados_iniciais()
    if registros.empty or "PROGRAM_Nº" not in registros:
        return ["Todas"]
    contagem = registros["PROGRAM_Nº"].dropna().value_counts().head(4)
    return ["Todas", *[f"{receita} ({valor})" for receita, valor in contagem.items()]]


@st.cache_data(ttl=1800, show_spinner=False)
def carregar_estatisticas() -> pd.DataFrame:
    try:
        with _abrir_excel(config.ESTATISTICA_URL) as excel:
            return pd.read_excel(excel, sheet_name=0)
    except (OSError, ValueError, requests.RequestException) as erro:
        st.warning(f"Estatísticas complementares não disponíveis: {erro}")
        return pd.DataFrame()

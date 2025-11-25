import pandas as pd
import streamlit as st
from pathlib import Path
import requests
from io import BytesIO

@st.cache_data(show_spinner="Carregando dados detalhados (Parquet)...")
def carregar_parquet_por_receita(receita_selecionada):
    """
    Carrega arquivos Parquet hospedados NO GITHUB.
    - Se receita_selecionada == "Todas": concatena todos os Parquets encontrados
    - Se receita specificada: tenta ler apenas dados_detalhados_{receita}.parquet
    """
    base_url = st.secrets["CAMINHO_PARQUETS"].rstrip("/")

    def baixar_parquet_via_http(url):
        """Baixa o parquet via HTTP (GitHub Raw) e retorna um DataFrame"""
        try:
            resp = requests.get(url, timeout=20)

            if resp.status_code != 200:
                st.warning(f"Não foi possível acessar: {url} (status {resp.status_code})")
                return pd.DataFrame()

            return pd.read_parquet(BytesIO(resp.content), engine="pyarrow")

        except Exception as e:
            st.error(f"Erro ao baixar parquet em {url}: {e}")
            return pd.DataFrame()

    # -------------------------------------------------------------------------
    # CASO 1 — Carregar TODAS as receitas
    # -------------------------------------------------------------------------
    if receita_selecionada == "Todas":

        if "LISTA_PARQUETS" not in st.secrets:
            st.error(
                "Você selecionou 'Todas', mas não definiu LISTA_PARQUETS no secrets.\n"
                "Adicione no secrets.toml:\n\n"
                'LISTA_PARQUETS = ["dados_detalhados_100.parquet", "dados_detalhados_200.parquet", ...]'
            )
            return pd.DataFrame()

        arquivos = st.secrets["LISTA_PARQUETS"]

        dfs = []
        for nome_arq in arquivos:
            parquet_url = f"{base_url}/{nome_arq}"
            df_temp = baixar_parquet_via_http(parquet_url)
            if not df_temp.empty:
                dfs.append(df_temp)

        if not dfs:
            st.warning("Nenhum parquet válido encontrado para 'Todas'.")
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

    # -------------------------------------------------------------------------
    # CASO 2 — Carregar apenas UMA receita
    # -------------------------------------------------------------------------
    parquet_url = f"{base_url}/dados_detalhados_{receita_selecionada}.parquet"

    df = baixar_parquet_via_http(parquet_url)
    if df.empty:
        st.warning(f"Nenhum parquet encontrado para a receita {receita_selecionada}.")
    return df

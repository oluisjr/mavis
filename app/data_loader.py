import pandas as pd
import streamlit as st
import requests
from io import BytesIO
from pathlib import Path
from . import config


# ============================================================
# 1. CARREGA O EXCEL PRINCIPAL ("Dados Completos")
# ============================================================
@st.cache_data(show_spinner="Carregando dados iniciais...")
def carregar_dados_iniciais():
    """Carrega o Excel principal (aba: Dados Completos)."""

    try:
        url = config.CAMINHO_EXCEL_URL

        if not url:
            st.error("Caminho do Excel não definido em st.secrets.")
            return pd.DataFrame()

        # 📌 CARREGAR REMOTO (GitHub RAW)
        if url.startswith("http"):
            resp = requests.get(url, timeout=30)

            if resp.status_code != 200:
                st.error(f"Erro ao acessar o arquivo Excel remoto (status {resp.status_code}).")
                return pd.DataFrame()

            content = BytesIO(resp.content)
            xls = pd.ExcelFile(content)

        # 📌 CARREGAR LOCAL (ambiente de desenvolvimento)
        else:
            caminho_excel = Path(url).expanduser().resolve()
            if not caminho_excel.exists():
                st.error(f"Arquivo Excel não encontrado: {caminho_excel}")
                return pd.DataFrame()

            xls = pd.ExcelFile(caminho_excel)

        # Detecta aba DataFrame independentemente de variações de letra
        nomes = [n.lower().strip() for n in xls.sheet_names]

        if "dados completos" in nomes:
            aba = xls.sheet_names[nomes.index("dados completos")]
        else:
            st.error("A aba 'Dados Completos' não foi encontrada no Excel.")
            return pd.DataFrame()

        df = pd.read_excel(xls, sheet_name=aba)

        # Normalização importante
        if "DATA" in df.columns:
            df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce")

        if "PROGRAM_Nº" in df.columns:
            df["PROGRAM_Nº"] = df["PROGRAM_Nº"].astype(str).str.strip()

        return df

    except Exception as e:
        st.error(f"Erro ao carregar o Excel: {e}")
        return pd.DataFrame()



# ============================================================
# 2. CARREGAR PARQUETS REMOTAMENTE (GitHub RAW)
# ============================================================
@st.cache_data(show_spinner="Carregando dados detalhados (Parquet)...")
def carregar_parquet_por_receita(receita_selecionada):
    """
    Carrega arquivos Parquet hospedados no GitHub Raw.
    - Se receita_selecionada == "Todas": concatena todos os arquivos da LISTA_PARQUETS
    - Se receita específica: carrega o parquet daquela receita
    """

    base_url = config.CAMINHO_PARQUETS.rstrip("/")

    def baixar_parquet(url):
        """Baixa via HTTP e retorna DataFrame."""
        try:
            resp = requests.get(url, timeout=30)

            if resp.status_code != 200:
                st.warning(f"Erro ao acessar {url} (status {resp.status_code})")
                return pd.DataFrame()

            return pd.read_parquet(BytesIO(resp.content), engine="pyarrow")

        except Exception as e:
            st.error(f"Erro ao baixar parquet em {url}: {e}")
            return pd.DataFrame()

    # ====== CASO 1 — CARREGAR TODOS OS PARQUETS ======
    if receita_selecionada == "Todas":

        if "LISTA_PARQUETS" not in st.secrets:
            st.error(
                "Você escolheu 'Todas', mas não definiu LISTA_PARQUETS no secrets.toml.\n"
                "Adicione algo assim:\n\n"
                'LISTA_PARQUETS = ["dados_detalhados_101.parquet", "dados_detalhados_102.parquet"]'
            )
            return pd.DataFrame()

        arquivos = st.secrets["LISTA_PARQUETS"]
        dfs = []

        for arq in arquivos:
            url = f"{base_url}/{arq}"
            df_temp = baixar_parquet(url)

            if not df_temp.empty:
                dfs.append(df_temp)

        if not dfs:
            st.warning("Nenhum arquivo Parquet válido encontrado.")
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

    # ====== CASO 2 — APENAS UMA RECEITA ======
    nome = f"dados_detalhados_{receita_selecionada}.parquet"
    url = f"{base_url}/{nome}"

    df = baixar_parquet(url)

    if df.empty:
        st.warning(f"Nenhum parquet encontrado para a receita {receita_selecionada}.")

    return df



# ============================================================
# 3. CARREGAR ESTATÍSTICAS
# ============================================================
@st.cache_data(show_spinner=False)
def carregar_estatisticas():
    """Carrega arquivo de estatísticas (Excel)."""
    try:
        url = config.ESTATISTICA_URL

        if url.startswith("http"):
            resp = requests.get(url, timeout=15)
            content = BytesIO(resp.content)
            return pd.read_excel(content, sheet_name="Sheet1")

        return pd.read_excel(url, sheet_name="Sheet1")

    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {e}")
        return pd.DataFrame()



# ============================================================
# 4. OBTÉM TOP 4 RECEITAS COM FORMATAÇÃO
# ============================================================
@st.cache_data(show_spinner="Calculando Top Receitas...")
def obter_top_4_receitas_formatadas():
    try:
        df = pd.read_excel(
            config.CAMINHO_EXCEL_URL,
            sheet_name="Dados Completos",
            usecols=["PROGRAM_Nº"]
        )

        contagem = df["PROGRAM_Nº"].astype(str).str.strip().value_counts()
        top4 = contagem.nlargest(4).index.tolist()

        return ["Todas"] + [f"{rec} ({contagem[rec]})" for rec in top4]

    except Exception as e:
        st.error(f"Erro ao carregar Top 4 receitas: {e}")
        return ["Todas"]



# ============================================================
# 5. CARREGA TODAS AS ABAS DE UMA ÚNICA RECEITA
# ============================================================
@st.cache_data(show_spinner="Carregando dados da receita...")
def carregar_dados_por_receita(receita_selecionada):
    """Carrega dados diários, semanais, mensais e anuais de uma receita."""

    mensagens = []
    vazio = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    try:
        df_total = pd.read_excel(config.CAMINHO_EXCEL_URL, sheet_name="Dados Completos")
        df_total["DATA"] = pd.to_datetime(df_total["DATA"], errors="coerce")

        if receita_selecionada == "Todas":
            abas = {
                "dia": "Médias Diárias",
                "semana": "Médias Semanais",
                "mes": "Médias Mensais",
                "ano": "Médias Anuais"
            }
        else:
            receita = str(receita_selecionada).strip()
            abas = {
                "dia": f"{receita}",
                "semana": f"{receita} - Semanal",
                "mes": f"{receita} - Mensal",
                "ano": f"{receita} - Anual"
            }

        def safe_load(sheet):
            try:
                return pd.read_excel(config.CAMINHO_EXCEL_URL, sheet_name=sheet)
            except:
                mensagens.append(("toast", f"Aba não encontrada: {sheet}"))
                return pd.DataFrame()

        df_dia = safe_load(abas["dia"])
        df_semana = safe_load(abas["semana"])
        df_mes = safe_load(abas["mes"])
        df_ano = safe_load(abas["ano"])

    except Exception as e:
        mensagens.append(("error", f"Erro ao ler arquivo Excel: {e}"))
        return vazio, mensagens

    return (df_total, df_dia, df_semana, df_mes, df_ano), mensagens

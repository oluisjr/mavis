import pandas as pd
import streamlit as st
import requests
from io import BytesIO
from pathlib import Path
from . import config
import tempfile
import traceback


# ============================================================
# 1. CARREGA O EXCEL PRINCIPAL ("Dados Completos")
# ============================================================
@st.cache_data(show_spinner="Carregando dados iniciais...")
def carregar_dados_iniciais():
    """Carrega a aba 'Dados Completos' do Excel inicial."""
    try:
        url = config.CAMINHO_EXCEL_URL

        if not url:
            st.error("CAMINHO_EXCEL_URL não definido em st.secrets.")
            return pd.DataFrame()

        # Remoto (GitHub RAW ou Releases)
        if url.startswith("http"):
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                st.error(f"Erro ao acessar arquivo Excel remoto ({resp.status_code})")
                return pd.DataFrame()
            content = BytesIO(resp.content)
            xls = pd.ExcelFile(content)

        # Local (desenvolvimento)
        else:
            caminho_excel = Path(url).expanduser().resolve()
            if not caminho_excel.exists():
                st.error(f"Arquivo Excel não encontrado: {caminho_excel}")
                return pd.DataFrame()
            xls = pd.ExcelFile(caminho_excel)

        # Identificar aba por nome aproximado
        nomes = [n.lower().strip() for n in xls.sheet_names]
        if "dados completos" in nomes:
            aba = xls.sheet_names[nomes.index("dados completos")]
        else:
            st.error("A aba 'Dados Completos' não existe no Excel.")
            return pd.DataFrame()

        df = pd.read_excel(xls, sheet_name=aba)

        if "DATA" in df.columns:
            df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce")
        if "PROGRAM_Nº" in df.columns:
            df["PROGRAM_Nº"] = df["PROGRAM_Nº"].astype(str).str.strip()

        return df

    except Exception as e:
        st.error(f"Erro ao carregar o Excel inicial: {e}")
        return pd.DataFrame()



# ============================================================
# 2. CARREGA PARQUET — otimização mínima (rápida e leve)
# ============================================================
@st.cache_data(show_spinner="Carregando detalhes da solda (Parquet)...")
def carregar_parquet_por_receita(receita_selecionada):
    """
    Carrega Parquet da Release:
    - Apenas colunas essenciais
    - Max ~15k linhas
    - Filtros aplicados dentro do loader
    - Headers adequados para GitHub Releases privados
    """
    base_url = config.CAMINHO_PARQUETS.rstrip("/")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*"
    }

    # -------------------------------------------
    # 🔥 Redução eficiente do DF
    # -------------------------------------------
    def reduzir_dataframe(df):
        colunas_essenciais = [
            "DATAHORA", "DATA",
            "VELOCIDADE", "CORRENTE",
            "PRESSAO_SOLDA", "PRESSAO_MARTELADOR",
            "TEMPERATURA"
        ]
        existentes = [c for c in colunas_essenciais if c in df.columns]
        df = df[existentes].copy()

        # filtros aplicados aqui
        filtros = st.session_state.get("filtros_aplicados", {})

        if "anos" in filtros and filtros["anos"]:
            df = df[df["DATAHORA"].dt.year.isin(filtros["anos"])]

        if "meses" in filtros and filtros["meses"]:
            df = df[df["DATAHORA"].dt.month.isin(filtros["meses"])]

        if "dias" in filtros and filtros["dias"]:
            df = df[df["DATAHORA"].dt.day.isin(filtros["dias"])]

        # limite de segurança para evitar travar o Streamlit Cloud
        if len(df) > 15000:
            df = df.sample(15000).sort_values("DATAHORA")

        return df

    # -------------------------------------------
    # Função auxiliar para baixar parquet
    # -------------------------------------------
    def baixar_parquet(url):
        try:
            resp = requests.get(
                url,
                headers=headers,
                timeout=60,
                allow_redirects=True,
                stream=True
            )

            if resp.status_code != 200:
                st.warning(f"Falha ao acessar {url} (status {resp.status_code})")
                return None

            data = resp.content
            df = pd.read_parquet(BytesIO(data), engine="pyarrow")

            # garantir datetime
            if "DATAHORA" in df.columns:
                df["DATAHORA"] = pd.to_datetime(df["DATAHORA"], errors="coerce")
                df["DATA"] = df["DATAHORA"].dt.date

            return df

        except Exception as e:
            st.error(f"Erro ao baixar/ler parquet: {e}")
            return None

    # -------------------------------------------
    # Caso: todas as receitas
    # -------------------------------------------
    if receita_selecionada == "Todas":
        nomes = config.LISTA_PARQUETS
        dfs = []

        for nome in nomes:
            url = f"{base_url}/{nome}"
            df_temp = baixar_parquet(url)
            if df_temp is not None and not df_temp.empty:
                dfs.append(df_temp)

        if not dfs:
            st.warning("Nenhum arquivo Parquet encontrado.")
            return pd.DataFrame()

        df_final = pd.concat(dfs, ignore_index=True)
        return reduzir_dataframe(df_final)

    # -------------------------------------------
    # Caso: receita única
    # -------------------------------------------
    nome = f"dados_detalhados_{receita_selecionada}.parquet"
    url = f"{base_url}/{nome}"

    df = baixar_parquet(url)
    if df is None or df.empty:
        st.warning(f"Nenhum dado detalhado encontrado para a receita {receita_selecionada}.")
        return pd.DataFrame()

    return reduzir_dataframe(df)



# ============================================================
# 3. CARREGA ESTATÍSTICAS
# ============================================================
@st.cache_data(show_spinner=False)
def carregar_estatisticas():
    try:
        url = config.ESTATISTICA_URL

        if url.startswith("http"):
            resp = requests.get(url, timeout=20)
            content = BytesIO(resp.content)
            return pd.read_excel(content, sheet_name="Sheet1")

        return pd.read_excel(url, sheet_name="Sheet1")

    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {e}")
        return pd.DataFrame()



# ============================================================
# 4. LISTA “Top Receitas”
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
        return ["Todas"] + [f"{r} ({contagem[r]})" for r in top4]

    except Exception as e:
        st.error(f"Erro ao obter Top Receitas: {e}")
        return ["Todas"]



# ============================================================
# 5. CARREGAMENTO POR RECEITA (Excel)
# ============================================================
@st.cache_data(show_spinner="Carregando dados da receita...")
def carregar_dados_por_receita(receita_selecionada):
    """Carrega as abas Diária, Semanal, Mensal e Anual do Excel."""
    msgs = []
    vazio = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    try:
        df_total = pd.read_excel(config.CAMINHO_EXCEL_URL, sheet_name="Dados Completos")
        df_total["DATA"] = pd.to_datetime(df_total["DATA"], errors="coerce")

        if receita_selecionada == "Todas":
            abas = {
                "dia": "Médias Diárias",
                "semana": "Médias Semanais",
                "mes": "Médias Mensais",
                "ano": "Médias Anuais",
            }
        else:
            r = str(receita_selecionada).strip()
            abas = {
                "dia": f"{r}",
                "semana": f"{r} - Semanal",
                "mes": f"{r} - Mensal",
                "ano": f"{r} - Anual",
            }

        def safe_load(sheet):
            try:
                return pd.read_excel(config.CAMINHO_EXCEL_URL, sheet_name=sheet)
            except:
                msgs.append(("toast", f"Aba não encontrada: {sheet}"))
                return pd.DataFrame()

        df_dia    = safe_load(abas["dia"])
        df_semana = safe_load(abas["semana"])
        df_mes    = safe_load(abas["mes"])
        df_ano    = safe_load(abas["ano"])

    except Exception as e:
        msgs.append(("error", f"Erro ao ler Excel: {e}"))
        return vazio, msgs

    return (df_total, df_dia, df_semana, df_mes, df_ano), msgs

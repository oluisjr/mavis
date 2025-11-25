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
    Leitura mais robusta de Parquet remoto (GitHub RAW).
    - Faz download em streaming para arquivo temporário.
    - Checa status_code e content-type.
    - Tenta leitura com pyarrow, se falhar tenta fastparquet.
    - Escreve logs no Streamlit para diagnóstico.
    """
    base_url = config.CAMINHO_PARQUETS.rstrip("/")
    st.info("Debug: iniciando leitura do parquet...")

    def baixar_para_tempfile(url, chunk_size=8192, timeout=60):
        st.write(f"Debug: tentando {url}")
        try:
            resp = requests.get(url, stream=True, timeout=timeout)
        except Exception as e:
            st.error(f"Erro de conexão ao requisitar {url}: {e}")
            st.write(traceback.format_exc())
            return None, None

        st.write(f"Debug: status_code = {resp.status_code}")
        st.write(f"Debug: headers = {dict(resp.headers)}")

        if resp.status_code != 200:
            st.error(f"Não foi possível baixar o arquivo (status {resp.status_code}).")
            return None, resp

        # tenta checar content-type
        content_type = resp.headers.get("Content-Type", "")
        st.write(f"Debug: content-type = {content_type}")

        # salva em tempfile
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
            tamanho_baixado = 0
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    tmp.write(chunk)
                    tamanho_baixado += len(chunk)
            tmp.flush()
            tmp.close()
            st.write(f"Debug: salvo em {tmp.name} ({tamanho_baixado} bytes)")
            return tmp.name, resp
        except Exception as e:
            st.error(f"Erro ao salvar em arquivo temporário: {e}")
            st.write(traceback.format_exc())
            return None, resp

    # === Caso: Todas ===
    if receita_selecionada == "Todas":
        if "LISTA_PARQUETS" not in st.secrets:
            st.error("LISTA_PARQUETS não definido no secrets. Não posso carregar 'Todas'.")
            return pd.DataFrame()

        arquivos = st.secrets["LISTA_PARQUETS"]
        dfs = []
        for arq in arquivos:
            url = f"{base_url}/{arq}"
            tmp_path, resp = baixar_para_tempfile(url)
            if not tmp_path:
                st.warning(f"Falha ao baixar {arq}, pulando.")
                continue

            # tenta ler o parquet
            df = None
            try:
                df = pd.read_parquet(tmp_path, engine="pyarrow")
                st.write(f"Debug: leitura pyarrow OK para {arq}")
            except Exception as e_py:
                st.warning(f"pyarrow falhou para {arq}: {e_py}")
                st.write(traceback.format_exc())
                try:
                    df = pd.read_parquet(tmp_path, engine="fastparquet")
                    st.write(f"Debug: leitura fastparquet OK para {arq}")
                except Exception as e_fp:
                    st.error(f"fastparquet também falhou para {arq}: {e_fp}")
                    st.write(traceback.format_exc())
                    df = None

            # remove temporário
            try:
                os.remove(tmp_path)
            except:
                pass

            if df is not None and not df.empty:
                dfs.append(df)

        if not dfs:
            st.warning("Nenhum parquet válido carregado.")
            return pd.DataFrame()
        return pd.concat(dfs, ignore_index=True)

    # === Caso: receita específica ===
    nome = f"dados_detalhados_{receita_selecionada}.parquet"
    url = f"{base_url}/{nome}"

    tmp_path, resp = baixar_para_tempfile(url)
    if not tmp_path:
        st.error("Falha ao baixar o parquet solicitado.")
        return pd.DataFrame()

    # tenta ler com pyarrow, depois fastparquet
    try:
        df = pd.read_parquet(tmp_path, engine="pyarrow")
        st.write("Debug: leitura com pyarrow OK.")
    except Exception as e1:
        st.warning(f"pyarrow falhou: {e1}")
        st.write(traceback.format_exc())
        try:
            df = pd.read_parquet(tmp_path, engine="fastparquet")
            st.write("Debug: leitura com fastparquet OK.")
        except Exception as e2:
            st.error(f"fastparquet falhou: {e2}")
            st.write(traceback.format_exc())
            df = pd.DataFrame()

    # cleanup
    try:
        os.remove(tmp_path)
    except:
        pass

    if df.empty:
        st.warning("Parquet lido, mas DataFrame vazio ou leitura falhou.")
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


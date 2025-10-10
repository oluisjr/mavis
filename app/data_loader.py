import pandas as pd
import streamlit as st
import requests
from io import BytesIO
from pathlib import Path
from . import config

@st.cache_data(show_spinner="Carregando dados iniciais...")
def carregar_dados_iniciais():
    """Carrega a planilha 'Dados Completos' a partir de uma URL ou caminho local."""
    try:
        if not config.CAMINHO_EXCEL_URL:
            st.error("O caminho do arquivo Excel não foi definido no .env (caminho_excel).")
            return pd.DataFrame()

        # Detecta se é URL (http/https) ou arquivo local
        if config.CAMINHO_EXCEL_URL.startswith("http://") or config.CAMINHO_EXCEL_URL.startswith("https://"):
            response = requests.get(config.CAMINHO_EXCEL_URL)
            response.raise_for_status()
            excel_content = BytesIO(response.content)
            df = pd.read_excel(excel_content, sheet_name="Dados Completos")
        else:
            caminho_excel = Path(config.CAMINHO_EXCEL_URL).expanduser().resolve()
            if not caminho_excel.exists():
                st.error(f"Arquivo não encontrado: {caminho_excel}")
                return pd.DataFrame()
            df = pd.read_excel(caminho_excel, sheet_name="Dados Completos")

        # Tratamento dos dados
        df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce")
        df["PROGRAM_Nº"] = df["PROGRAM_Nº"].astype(str).str.strip()
        return df

    except Exception as e:
        st.error(f"Erro ao carregar o arquivo Excel inicial: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Carregando dados da receita...")
def carregar_dados_por_receita(receita_selecionada):
    """Carrega os dados diários, semanais, mensais e anuais para uma receita específica."""
    messages = []
    empty_dfs = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    try:
        df_total = pd.read_excel(config.CAMINHO_EXCEL_URL, sheet_name='Dados Completos')
        df_total['DATA'] = pd.to_datetime(df_total['DATA'], errors='coerce')

        if config.CAMINHO_EXCEL_URL is None:
            messages.append(('error', "O caminho do arquivo Excel está indefinido (None)."))
            return empty_dfs, messages
            
        xls = pd.ExcelFile(config.CAMINHO_EXCEL_URL)
        sheet_names_from_file = {str(sheet).strip().lower(): str(sheet) for sheet in xls.sheet_names}

        if receita_selecionada == 'Todas':
            aba_diario, aba_semanal, aba_mensal, aba_anual = 'Médias Diárias', 'Médias Semanais', 'Médias Mensais', 'Médias Anuais'
        else:
            receita_str = str(receita_selecionada).strip()
            aba_diario = f"{receita_str}"
            aba_semanal = f"{receita_str} - Semanal"
            aba_mensal = f"{receita_str} - Mensal"
            aba_anual = f"{receita_str} - Anual"

        def carregar_aba_segura(nome_aba_procurada):
            nome_limpo = nome_aba_procurada.strip().lower()
            if nome_limpo in sheet_names_from_file:
                nome_original_da_aba = sheet_names_from_file[nome_limpo]
                return pd.read_excel(config.CAMINHO_EXCEL_URL, sheet_name=nome_original_da_aba)
            else:
                messages.append(('toast', f"Aviso: Planilha '{nome_aba_procurada}' não encontrada."))
                return pd.DataFrame()

        df_diario = carregar_aba_segura(aba_diario)
        df_semanal = carregar_aba_segura(aba_semanal)
        df_mensal = carregar_aba_segura(aba_mensal)
        df_anual = carregar_aba_segura(aba_anual)

    except FileNotFoundError:
        messages.append(('error', f"Arquivo Excel não encontrado no caminho: {config.CAMINHO_EXCEL_URL}"))
        return empty_dfs, messages
    except Exception as e:
        messages.append(('error', f"Erro inesperado ao ler o arquivo Excel: {e}"))
        return empty_dfs, messages

    # Processamento e normalização
    if not df_diario.empty: df_diario['DATA'] = pd.to_datetime(df_diario['DATA'], errors='coerce')
    if not df_semanal.empty: df_semanal['SEMANA'] = pd.to_datetime(df_semanal['SEMANA'].astype(str).str[:10], errors='coerce').dt.tz_localize(None)
    if not df_mensal.empty: df_mensal['MES'] = pd.to_datetime(df_mensal['MES'], errors='coerce')
    if not df_anual.empty: df_anual['ANO'] = pd.to_datetime(df_anual['ANO'], format='%Y', errors='coerce')

    for df in [df_diario, df_semanal, df_mensal, df_anual]:
        if not df.empty:
            if 'VELOCIDADE' in df.columns: df['VELOCIDADE'] = df['VELOCIDADE'].astype(int) / 100
            if 'CORRENTE' in df.columns: df['CORRENTE'] = df['CORRENTE'].astype(int) / 10
            if 'PRESSAO_SOLDA' in df.columns: df['PRESSAO_SOLDA'] = df['PRESSAO_SOLDA'].astype(int) / 10
            if 'TEMPERATURA' in df.columns: df['TEMPERATURA'] = (df['TEMPERATURA'].astype(int) / 10).round().astype(int)
            if 'PRESSAO_MARTELADOR' in df.columns: df['PRESSAO_MARTELADOR'] = df['PRESSAO_MARTELADOR'].astype(int) / 10

    return (df_total, df_diario, df_semanal, df_mensal, df_anual), messages
@st.cache_data(show_spinner="Calculando Top Receitas...")
def obter_top_4_receitas_formatadas():
    """Encontra as 4 receitas com mais registros e retorna uma lista formatada."""
    try:
        df = pd.read_excel(config.CAMINHO_EXCEL_URL, sheet_name='Dados Completos', usecols=['PROGRAM_Nº'])
        contagem = df['PROGRAM_Nº'].astype(str).str.strip().value_counts()
        top_4_receitas = contagem.nlargest(4).index.tolist()
        receitas_formatadas = ['Todas'] + [f"{rec} ({contagem[rec]})" for rec in top_4_receitas]
        return receitas_formatadas
    except Exception as e:
        st.error(f"Erro ao carregar a lista de receitas: {e}")
        return ['Todas']

@st.cache_data(show_spinner=False)
def carregar_estatisticas():
    """Carrega dados estatísticos de um arquivo Excel."""
    return pd.read_excel(config.ESTATISTICA_URL, sheet_name='Sheet1')
import pandas as pd
import streamlit as st
import requests
from io import BytesIO
from pathlib import Path
from . import config
import traceback

# ============================================================
# 1. CARREGA O EXCEL PRINCIPAL ("Dados Completos")
# ============================================================
@st.cache_data(show_spinner="Carregando dados iniciais...")
def carregar_dados_iniciais():
    """
    Carrega a aba 'Dados Completos' do Excel inicial.
    Retorna apenas o DataFrame principal.
    """
    try:
        url = config.CAMINHO_EXCEL_URL

        if not url:
            st.error("CAMINHO_EXCEL_URL não definido em st.secrets.")
            return pd.DataFrame()

        # Verifica se é URL (GitHub/Web) ou arquivo Local
        if url.startswith("http"):
            # Modo Remoto
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                st.error(f"Erro ao acessar arquivo Excel remoto ({resp.status_code})")
                return pd.DataFrame()
            content = BytesIO(resp.content)
            xls = pd.ExcelFile(content)
        else:
            # Modo Local
            caminho_excel = Path(url).expanduser().resolve()
            if not caminho_excel.exists():
                st.error(f"Arquivo Excel não encontrado: {caminho_excel}")
                return pd.DataFrame()
            xls = pd.ExcelFile(caminho_excel)

        # Lê a aba principal
        df = pd.read_excel(xls, sheet_name="Dados Completos")
        
        # Garante que DATA seja datetime
        if 'DATA' in df.columns:
            df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
            
        return df

    except Exception as e:
        st.error(f"Erro ao carregar dados iniciais: {e}")
        # Opcional: imprimir traceback no log do console
        # traceback.print_exc()
        return pd.DataFrame()

# ============================================================
# 2. CARREGA AS ABAS DE UMA RECEITA ESPECÍFICA (Diária, Semanal, etc)
# ============================================================
@st.cache_data(show_spinner="Carregando dados da receita...")
def carregar_dados_receita(receita_selecionada):
    """
    Carrega as abas Diária, Semanal, Mensal e Anual do Excel.
    Realiza a conversão de tipos (datas e strings) para evitar erros de .dt accessor.
    """
    
    # 1. Define os nomes das abas baseado na seleção
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

    # 2. Função auxiliar para carregar sem quebrar se a aba não existir
    def safe_load(sheet_name):
        try:
            url = config.CAMINHO_EXCEL_URL
            # Reutiliza a lógica de abrir o arquivo (o cache do streamlit otimiza isso)
            if url.startswith("http"):
                resp = requests.get(url, timeout=30)
                content = BytesIO(resp.content)
                return pd.read_excel(content, sheet_name=sheet_name)
            else:
                return pd.read_excel(url, sheet_name=sheet_name)
        except Exception:
            # Se a aba não existir, retorna vazio
            return pd.DataFrame()

    # 3. Carrega os DataFrames
    df_dia = safe_load(abas["dia"])
    df_semana = safe_load(abas["semana"])
    df_mensal = safe_load(abas["mes"])
    df_anual = safe_load(abas["ano"])

    # ============================================================
    # CORREÇÃO CRÍTICA DE DATAS (Onde ocorria o erro .dt)
    # ============================================================

    # 1. Diário: Converter coluna DATA
    if not df_dia.empty and 'DATA' in df_dia.columns:
        df_dia['DATA'] = pd.to_datetime(df_dia['DATA'], errors='coerce')

    # 2. Semanal: A coluna vem como "2023-09-11/2023-09-17" (Texto)
    # Precisamos pegar apenas a data inicial para converter em datetime
    if not df_semana.empty and 'SEMANA' in df_semana.columns:
        # Pega a parte antes da barra '/' e converte
        df_semana['SEMANA'] = pd.to_datetime(
            df_semana['SEMANA'].astype(str).str.split('/').str[0], 
            errors='coerce'
        )

    # 3. Mensal: Converter "YYYY-MM" para datetime
    if not df_mensal.empty and 'MES' in df_mensal.columns:
        df_mensal['MES'] = pd.to_datetime(df_mensal['MES'], errors='coerce')

    # 4. Anual: Garantir que ANO seja numérico (int) para filtros diretos
    if not df_anual.empty and 'ANO' in df_anual.columns:
        df_anual['ANO'] = pd.to_numeric(df_anual['ANO'], errors='coerce')

    # Retorna os 4 dataframes + 1 placeholder (para compatibilidade com unpack)
    return df_dia, df_semana, df_mensal, df_anual, pd.DataFrame()

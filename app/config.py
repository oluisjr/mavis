import os
import json
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

# ============================================================
# CARREGAMENTO DO .ENV (para ambiente local)
# ============================================================
load_dotenv()

# ------------------------------------------------------------
# CONTROLE DE ACESSO
# ------------------------------------------------------------
PASSWORDS_STRING = os.getenv("VALID_PASSWORDS", "")
VALID_PASSWORDS = [pwd.strip() for pwd in PASSWORDS_STRING.split(",") if pwd]

# ------------------------------------------------------------
# CAMINHOS BASE DO PROJETO
# ------------------------------------------------------------
BASE_DIR      = Path(__file__).resolve().parent.parent
CONFIG_DIR    = BASE_DIR / "config"
ASSETS_DIR    = BASE_DIR / "assets"
IA_DIR        = BASE_DIR / "IA"
DATA_DIR      = BASE_DIR / "data"

# ============================================================
# CAMINHOS DO EXCEL
# ============================================================
caminho_excel_env = os.getenv("caminho_excel")

# Se for URL (GitHub RAW no Streamlit Cloud)
if caminho_excel_env and caminho_excel_env.startswith("http"):
    CAMINHO_EXCEL_URL = caminho_excel_env
else:
    # Caso contrário, usa arquivo local para rodar localmente
    CAMINHO_EXCEL_URL = str(DATA_DIR / "dados_resumidos_gerado.xlsx")

# Caminho de estatísticas (mesma lógica)
estatistica_env = os.getenv("estatistica")
if estatistica_env and estatistica_env.startswith("http"):
    ESTATISTICA_URL = estatistica_env
else:
    ESTATISTICA_URL = str(DATA_DIR / "estatisticas_por_receita.xlsx")


# ============================================================
# CAMINHOS DOS PARQUETS VIA STREAMLIT CLOUD
# (VINDOS DO SECRETS.TOML)
# ============================================================
CAMINHO_PARQUETS = st.secrets.get("CAMINHO_PARQUETS", "")
LISTA_PARQUETS   = st.secrets.get("LISTA_PARQUETS", [])


# ============================================================
# CONSTANTES DE SENSOR
# ============================================================
CORES = {
    "VELOCIDADE": "blue",
    "CORRENTE": "green",
    "PRESSAO_SOLDA": "orange",
    "PRESSAO_MARTELADOR": "purple",
    "TEMPERATURA": "gray",
}

NOMES_SENSORES = {
    "VELOCIDADE": "VELOCIDADE (m/min)",
    "CORRENTE": "CORRENTE (KA)",
    "PRESSAO_SOLDA": "PRESSAO DA SOLDA (KN)",
    "PRESSAO_MARTELADOR": "PRESSAO DO MARTELADOR (KN)",
    "TEMPERATURA": "TEMPERATURA (ºC)",
}


# ============================================================
# FUNÇÃO PARA CARREGAR CONFIGS JSON
# ============================================================
def load_json_config(filename: str):
    try:
        with open(CONFIG_DIR / filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: Config '{filename}' não encontrado.")
        return {}


CUSTOS_OPERACIONAIS = load_json_config("operational_costs.json")
BASE_CONHECIMENTO_CAUSA_RAIZ = load_json_config("root_cause_analysis.json")


# ============================================================
# ASSETS
# ============================================================
LOGO_PATH        = str(ASSETS_DIR / "images" / "logo.png")
FAVICON_PATH     = str(ASSETS_DIR / "images" / "logo.png")
LOGO_ERRO_PATH   = str(ASSETS_DIR / "images" / "logo_erro.png")
FAVICON_ERRO_PATH = str(ASSETS_DIR / "images" / "logo_erro.png")

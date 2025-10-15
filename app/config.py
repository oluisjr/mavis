import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do .env
load_dotenv()

# --- Caminhos Base ---
PASSWORDS_STRING = os.getenv("VALID_PASSWORDS", "")
VALID_PASSWORDS = [pwd.strip() for pwd in PASSWORDS_STRING.split(',') if pwd]

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
ASSETS_DIR = BASE_DIR / "assets"
IA_DIR = BASE_DIR / "IA"
DATA_DIR = BASE_DIR / "data"

# --- URLs e Caminhos do .env ---
caminho_excel_env = os.getenv("caminho_excel")
estatistica_env = os.getenv("estatistica")

if caminho_excel_env and caminho_excel_env.startswith("http"):
    CAMINHO_EXCEL_URL = caminho_excel_env
else:
    # Ignora o .env e constrói um caminho absoluto para o arquivo na pasta /data
    CAMINHO_EXCEL_URL = str(DATA_DIR / "dados_resumidos_gerado.xlsx")

if estatistica_env and estatistica_env.startswith("http"):
    ESTATISTICA_URL = estatistica_env
else:
    # Faça o mesmo para o arquivo de estatísticas, se houver
    ESTATISTICA_URL = str(DATA_DIR / "estatisticas_por_receita.xlsx") # Ajuste o nome do arquivo se for diferente

# --- Constantes da Aplicação ---
CORES = {
    'VELOCIDADE': "blue", 'CORRENTE': "green", 'PRESSAO_SOLDA': "orange",
    'PRESSAO_MARTELADOR': "purple", 'TEMPERATURA': "gray"
}
NOMES_SENSORES = {
    'VELOCIDADE': 'VELOCIDADE (m/min)', 'CORRENTE': 'CORRENTE (KA)',
    'PRESSAO_SOLDA': 'PRESSAO DA SOLDA (KN)', 'PRESSAO_MARTELADOR': 'PRESSAO DO MARTELADOR (KN)',
    'TEMPERATURA': 'TEMPERATURA (ºC)'
}

# --- Carregadores de Configuração Externa ---
def load_json_config(filename: str):
    try:
        with open(CONFIG_DIR / filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: O arquivo de configuração '{filename}' não foi encontrado.")
        return {}

CUSTOS_OPERACIONAIS = load_json_config("operational_costs.json")
BASE_CONHECIMENTO_CAUSA_RAIZ = load_json_config("root_cause_analysis.json")

# --- Caminhos para Assets ---
LOGO_PATH = str(ASSETS_DIR / "images" / "logo.png")
FAVICON_PATH = str(ASSETS_DIR / "images" / "logo.png")
LOGO_ERRO_PATH = str(ASSETS_DIR / "images" / "logo_erro.png")
FAVICON_ERRO_PATH = str(ASSETS_DIR / "images" / "logo_erro.png")

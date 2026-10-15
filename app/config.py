"""Configuração central do MAVIS. Não armazene credenciais no repositório."""
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
IA_DIR = BASE_DIR / "IA"

def origem_arquivo(nome_env: str, padrao: str) -> str:
    return (os.getenv(nome_env) or str(DATA_DIR / padrao)).strip()

CAMINHO_EXCEL_URL = origem_arquivo("caminho_excel", "dados_resumidos_gerado.xlsx")
ESTATISTICA_URL = origem_arquivo("estatistica", "estatisticas_por_programa.xlsx")

CORES = {
    "VELOCIDADE": "#2563eb",
    "CORRENTE": "#059669",
    "PRESSAO_SOLDA": "#ea580c",
    "PRESSAO_MARTELADOR": "#7c3aed",
    "TEMPERATURA": "#64748b",
}
NOMES_SENSORES = {
    "VELOCIDADE": "Velocidade (m/min)",
    "CORRENTE": "Corrente (kA)",
    "PRESSAO_SOLDA": "Pressão de solda (kN)",
    "PRESSAO_MARTELADOR": "Pressão do martelador (kN)",
    "TEMPERATURA": "Temperatura (°C)",
}
FATORES_ESCALA = {
    "VELOCIDADE": 100.0,
    "CORRENTE": 10.0,
    "PRESSAO_SOLDA": 10.0,
    "PRESSAO_MARTELADOR": 10.0,
    "TEMPERATURA": 10.0,
}
# Antes de habilitar um sensor, confirmar formalmente sua condição operacional.
SENSORES_INDISPONIVEIS = {
    s.strip().upper()
    for s in os.getenv("SENSORES_INDISPONIVEIS", "TEMPERATURA").split(",")
    if s.strip()
}

def load_json_config(filename: str) -> dict:
    try:
        with (CONFIG_DIR / filename).open(encoding="utf-8") as arquivo:
            conteudo = json.load(arquivo)
        return conteudo if isinstance(conteudo, dict) else {}
    except (OSError, ValueError):
        return {}

CUSTOS_OPERACIONAIS = load_json_config("operational_costs.json")
BASE_CONHECIMENTO_CAUSA_RAIZ = load_json_config("root_cause_analysis.json")
LOGO_PATH = str(ASSETS_DIR / "images" / "logo.png")
FAVICON_PATH = LOGO_PATH
LOGO_ERRO_PATH = str(ASSETS_DIR / "images" / "logo_erro.png")
FAVICON_ERRO_PATH = LOGO_ERRO_PATH

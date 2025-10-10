import streamlit as st
import joblib
import pickle
from pathlib import Path
from . import config

def carregar_modelos_pickle():
    """Carrega modelos de machine learning de arquivos .pkl na pasta IA."""
    pasta_modelos = config.IA_DIR
    modelos_carregados = {}
    if not pasta_modelos.exists():
        st.warning(f"Pasta de modelos de IA '{pasta_modelos}' não encontrada.")
        return modelos_carregados

    for arquivo_ia in pasta_modelos.glob("*.pkl"):
        try:
            with open(arquivo_ia, "rb") as f:
                modelos_carregados[arquivo_ia.stem] = pickle.load(f)
                print(f"✔ Sucesso ao carregar: {arquivo_ia.name}")
        except Exception as e:
            print(f"❌ Erro em {arquivo_ia.name} - {e}")
    return modelos_carregados

def verificar_arquivos_ia():
    """Verifica a existência de todos os artefatos (modelo, scaler, features) por sensor."""
    pasta_modelos = config.IA_DIR
    if not pasta_modelos.exists() or not pasta_modelos.is_dir():
        st.error(f"Pasta '{pasta_modelos}' não encontrada.")
        st.stop()

    artefatos_carregados = {}
    sensores = ["VELOCIDADE", "CORRENTE", "PRESSAO_SOLDA", "PRESSAO_MARTELADOR", "TEMPERATURA"]
    
    for sensor in sensores:
        sensor_lower = sensor.lower()
        
        # Assume um padrão de nome de arquivo, ex: "modelo_velocidade_v1.pkl"
        arquivos_modelo = list(pasta_modelos.glob(f"modelo_{sensor_lower}_*.pkl"))
        arquivos_scaler = list(pasta_modelos.glob(f"scaler_{sensor_lower}_*.pkl"))
        arquivos_features = list(pasta_modelos.glob(f"features_{sensor_lower}_*.pkl"))
        
        if not (arquivos_modelo and arquivos_scaler and arquivos_features):
            artefatos_carregados[sensor] = None 
            continue
            
        arquivo_modelo_recente = max(arquivos_modelo, key=lambda p: p.stat().st_mtime)
        arquivo_scaler_recente = max(arquivos_scaler, key=lambda p: p.stat().st_mtime)
        arquivo_features_recente = max(arquivos_features, key=lambda p: p.stat().st_mtime)
        
        try:
            artefatos_carregados[sensor] = {
                'modelo': joblib.load(arquivo_modelo_recente),
                'scaler': joblib.load(arquivo_scaler_recente),
                'features': joblib.load(arquivo_features_recente)
            }
        except Exception as e:
            st.error(f"Erro ao carregar artefatos para o sensor {sensor}: {e}")
            artefatos_carregados[sensor] = None

    return artefatos_carregados

# Nota: A função 'prever_riscos_individuais' não estava no código-fonte, então não foi incluída.
# Se ela existir, deve ser adicionada aqui.
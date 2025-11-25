import streamlit as st
import pandas as pd
from app import config, ui_components, data_loader, session_manager
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
import json
from dotenv import load_dotenv

# ============================================================
# VERIFICA LOGIN
# ============================================================
if not st.session_state.get('authenticated', False):
    st.error("Acesso negado. Por favor, faça o login na página principal.")
    st.stop()

load_dotenv()
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH")

st.set_page_config(page_title="MAVIS - Manutenção", layout="wide", initial_sidebar_state="expanded", page_icon=config.FAVICON_PATH)

# --- Conexão com a Base de Dados ---
try:
    if not firebase_admin._apps:
        cred_obj = None
        key_content_str = FIREBASE_KEY_PATH

        # Tenta tratar a variável de ambiente como um caminho de ficheiro primeiro.
        if os.path.exists(key_content_str):
            cred_obj = credentials.Certificate(key_content_str)
            print("✅ Credenciais carregadas a partir do ficheiro de chave.")
        # Se não for um caminho, tenta tratar como uma string JSON (útil para segredos de implantação).
        else:
            try:
                key_dict = json.loads(key_content_str)
                cred_obj = credentials.Certificate(key_dict)
                print("✅ Credenciais carregadas a partir da string JSON.")
            except json.JSONDecodeError:
                raise ValueError("A variável FIREBASE_KEY_PATH não é um caminho de ficheiro válido nem uma string JSON bem formatada.")
        
        firebase_admin.initialize_app(cred_obj)

    db = firestore.client(database_id="mavis")
except Exception as e:
    st.error(f"Erro a conectar à base de dados: {e}")
    st.info("Verifique se a variável FIREBASE_KEY_PATH no seu ficheiro .env contém um caminho válido para a sua chave JSON ou o conteúdo JSON correto.")
    db = None

# --- Configurações da Página ---

ui_components.hide_main_page_nav_and_footer()
ui_components.render_mavis_header(theme=st.session_state.get('theme', 'light'))
st.subheader("Registo de Manutenção")

if not db:
    st.stop()

# --- Interface de Registo ---
st.markdown("Selecione o sensor e a data em que ocorreu a manutenção.")

col1, col2, col3 = st.columns(3)
with col1:
    sensor_selecionado = st.selectbox("Selecione o Sensor:", config.NOMES_SENSORES.keys())
with col2:
    data_falha = st.date_input("Data da Falha/Manutenção", datetime.now())
with col3:
    st.write("") # Espaçador
    if st.button("Registar Manutenção", use_container_width=True, type="primary"):
        try:
            doc_ref = db.collection('falhas').document(sensor_selecionado)
            # Usa 'array_union' para adicionar a data à lista sem duplicar
            doc_ref.set({
                'datas': firestore.ArrayUnion([str(data_falha)])
            }, merge=True)
            st.success(f"Falha para o sensor '{sensor_selecionado}' registada com sucesso!")
            st.toast("Pode agora executar o script de treino novamente para atualizar o modelo.")
        except Exception as e:
            st.error(f"Ocorreu um erro ao registar a falha: {e}")

# --- Tabela de Histórico de Falhas ---
st.markdown("---")
st.subheader("Histórico de Manutenções Registadas")

try:
    falhas_ref = db.collection('falhas').stream()
    historico = []
    for falha in falhas_ref:
        sensor = falha.id
        datas = falha.to_dict().get('datas', [])
        if datas:
            # Pega a data mais recente
            latest_date = max(pd.to_datetime(datas)).strftime('%d/%m/%Y')
            historico.append({"Sensor": sensor, "Última manutenção Registada": latest_date})
    
    if historico:
        st.dataframe(pd.DataFrame(historico), use_container_width=True)
    else:
        st.info("Nenhuma manutenção registada até ao momento.")
except Exception as e:
    st.error(f"Não foi possível carregar o histórico de falhas: {e}")

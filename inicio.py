"""Página inicial do MAVIS. Execute: streamlit run inicio.py."""
import hmac
import os
import streamlit as st
from app import config, session_manager, ui_components

st.set_page_config(page_title="MAVIS | Acesso", page_icon=config.FAVICON_PATH, layout="centered")
session_manager.initialize_session_state()
ui_components.hide_sidebar_nav()
ui_components.render_mavis_header()

def _senhas():
    try:
        valor = st.secrets.get("VALID_PASSWORDS", "")
    except (OSError, FileNotFoundError):
        valor = ""
    if isinstance(valor, (list, tuple)):
        candidatas = [str(item) for item in valor]
    else:
        candidatas = str(valor or os.getenv("VALID_PASSWORDS", "")).split(",")
    return [senha.strip() for senha in candidatas if senha.strip()]

if st.session_state.authenticated:
    st.switch_page("pages/0_🏠_Sumário_Executivo.py")

st.subheader("Acesso restrito")
st.caption("Dados industriais. Consulte somente com autorização.")
with st.form("login"):
    senha = st.text_input("Senha", type="password", autocomplete="off")
    entrar = st.form_submit_button("Entrar", use_container_width=True)

if entrar:
    configuradas = _senhas()
    if not configuradas:
        st.error("Autenticação não configurada. Defina VALID_PASSWORDS em Secrets ou no ambiente.")
    elif any(hmac.compare_digest(senha, válida) for válida in configuradas):
        st.session_state.authenticated = True
        st.switch_page("pages/0_🏠_Sumário_Executivo.py")
    else:
        st.error("Credenciais inválidas.")

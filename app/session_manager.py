"""Controle da sessão: não carrega histórico antes de autenticação."""
import streamlit as st

DEFAULT_FILTERS = {
    "receita_fmt": "Todas",
    "entry_code": "Todos",
    "exit_code": "Todos",
    "anos": [],
    "meses": [],
    "semanas": [],
    "dias": [],
}

def initialize_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "filtros_aplicados" not in st.session_state:
        st.session_state.filtros_aplicados = {
            k: list(v) if isinstance(v, list) else v
            for k, v in DEFAULT_FILTERS.items()
        }

def check_authentication():
    initialize_session_state()
    if not st.session_state.get("authenticated", False):
        st.warning("Acesso restrito. Faça login para consultar o histórico industrial.")
        st.stop()

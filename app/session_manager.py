import streamlit as st
from app import data_loader

def initialize_session_state():
    """
    Inicializa todas as chaves necessárias no st.session_state na primeira execução de uma sessão.
    Esta função deve ser chamada no topo de cada script de página.
    """
    # Inicializa o status de autenticação
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # Inicializa o dicionário de filtros
    if 'filtros_aplicados' not in st.session_state:
        st.session_state.filtros_aplicados = {
            'receita_fmt': '123',
            'entry_code': 'Todos',
            'exit_code': 'Todos',
            'anos': '2025', 
            'meses': [], 
            'semanas': [], 
            'dias': []
        }
        # Pré-popula a lista de anos padrão
        df_total_completo = data_loader.carregar_dados_iniciais()
        if not df_total_completo.empty:
            st.session_state.filtros_aplicados['anos'] = sorted(df_total_completo['DATA'].dt.year.unique())

def check_authentication():
    """
    Verifica se o utilizador está autenticado. Se não estiver, para a execução da página
    e mostra uma mensagem de erro. Esta função deve ser chamada no topo de cada
    página protegida.
    """
    initialize_session_state() # Garante que o estado existe antes de verificar
    if not st.session_state.get('authenticated', False):
        st.error("Acesso negado. Por favor, faça o login na página principal.")
        st.stop()

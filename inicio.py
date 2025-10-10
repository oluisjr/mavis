import streamlit as st
from app import config, ui_components, data_loader

# --- Configuração Global da Página ---
st.set_page_config(
    page_title="MAVIS",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=config.FAVICON_PATH
)

# Esconde o link "main" da lista de páginas
ui_components.hide_streamlit_elements()

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
# Este bloco é crucial e será executado uma vez no início da sessão.
# Ele garante que as chaves dos filtros sempre existam.
if 'filtros_aplicados' not in st.session_state:
    st.session_state.filtros_aplicados = {
        'receita_fmt': '123',
        'entry_code': 'Todos',
        'exit_code': 'Todos',
        'anos': [], 
        'meses': [], 
        'semanas': [], 
        'dias': []
    }

# Carrega os dados uma vez para ter a lista de anos para o estado inicial
df_total_completo = data_loader.carregar_dados_iniciais()
if not df_total_completo.empty and not st.session_state.filtros_aplicados['anos']:
    st.session_state.filtros_aplicados['anos'] = sorted(df_total_completo['DATA'].dt.year.unique())

# --- Página de Boas-Vindas e Redirecionamento ---
st.title("Carregando MAVIS...")
st.info("Você será redirecionado para o painel principal.")
st.switch_page("pages/0_🏠_Sumário_Executivo.py")


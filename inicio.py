import streamlit as st
from app import config, ui_components, session_manager

# --- Inicializa o Estado da Sessão ---
# Garante que as chaves de autenticação e filtros sempre existam
session_manager.initialize_session_state()

# --- Configuração da Página de Login ---
st.set_page_config(
    page_title="MAVIS - Login",
    layout="centered",
    initial_sidebar_state="collapsed", # A sidebar começa fechada
    page_icon=config.FAVICON_PATH
)

# --- CORREÇÃO DE SEGURANÇA APLICADA AQUI ---
# Esconde TODA a navegação da barra lateral nesta página.
ui_components.hide_sidebar_nav()


# --- Renderização do Cabeçalho ---
ui_components.render_mavis_header()
st.markdown("---")

# --- Formulário e Lógica de Login ---
def check_password():
    #Função que renderiza o campo de senha e verifica a autenticação.
    def password_entered():
        Função chamada sempre que o texto na caixa de senha muda.
        # st.secrets é a forma segura do Streamlit Cloud de ler as suas senhas
        valid_passwords = st.secrets.get("VALID_PASSWORDS", "").split(',')
        
        if st.session_state.get("password") in valid_passwords:
            st.session_state.authenticated = True
            if "password" in st.session_state:
                del st.session_state["password"]
        else:
            st.session_state.authenticated = False
            if st.session_state.get("password"):
                st.error("Senha incorreta. Tente novamente.")

    st.text_input(
        "Por favor, insira a senha para aceder ao dashboard:",
        type="password",
        on_change=password_entered,
        key="password"
    )

# --- Lógica de Acesso ---
if not st.session_state.get('authenticated', False):
    check_password()
else:
    st.success("Login bem-sucedido! A redirecionar...")
    st.switch_page("pages/0_🏠_Sumário_Executivo.py")




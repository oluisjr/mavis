import streamlit as st
from app import config, ui_components, session_manager, data_loader

# --- Inicializa o Estado da Sessão ---
session_manager.initialize_session_state()

# --- Configuração da Página de Login ---
st.set_page_config(
    page_title="MAVIS - Login",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon=config.FAVICON_PATH
)

# Esconde a navegação entre páginas na tela de login
ui_components.hide_streamlit_elements()

# --- Renderização do Cabeçalho ---
st.image(config.LOGO_PATH, width=150)
ui_components.render_mavis_header()
st.markdown("---")


# --- Formulário e Lógica de Login ---
def check_password():
    """Função que renderiza o campo de senha e verifica a autenticação."""
    def password_entered():
        """Função chamada sempre que o texto na caixa de senha muda."""
        if st.session_state.get("password") in config.VALID_PASSWORDS:
            st.session_state.authenticated = True
            # Limpa a senha da memória por segurança após a verificação
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
# Se o utilizador não estiver autenticado (o valor padrão), mostra o campo de senha.
if not st.session_state.get('authenticated', False):
    check_password()
# Se estiver autenticado, mostra uma mensagem de sucesso e redireciona.
else:
    st.success("Login bem-sucedido! A redirecionar...")
    st.switch_page("pages/0_🏠_Sumário_Executivo.py")


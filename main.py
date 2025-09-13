# main.py
import streamlit as st
from utils import login_form, main_app

# --- CAMINHOS DAS IMAGENS LOCAIS ---
LOGO_SYMBOL_PATH = "./images/cofrat-logo.png"
LOGO_EXTENDED_PATH = "./images/cofrat-logotipo.png"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="COFRAT - Plataforma de Gestão",
    page_icon=LOGO_SYMBOL_PATH,
    layout="wide",
    initial_sidebar_state="expanded"
)

# VERSÃO CORRIGIDA
def load_css(file_name):
    """Carrega um arquivo CSS externo para dentro do app Streamlit."""
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Carrega o nosso arquivo de estilos
load_css("style.css")

# --- GATEKEEPER PRINCIPAL ---
# Inicializa o estado de autenticação se ele não existir
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = False

# Verifica o estado de autenticação para decidir o que mostrar
if not st.session_state["authentication_status"]:
    # MODIFICAÇÃO: Passe o caminho do logo para a função
    login_form(logo_path=LOGO_EXTENDED_PATH) 
else:
    # Passa o caminho do logo para a função que renderiza o app principal
    main_app(logo_path=LOGO_EXTENDED_PATH)
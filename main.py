# main.py
import streamlit as st
from utils import login_form, main_app
import os

# --- CAMINHOS ABSOLUTOS (BOA PRÁTICA) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_SYMBOL_PATH = os.path.join(BASE_DIR, "images", "cofrat-logo.png")
LOGO_EXTENDED_PATH = os.path.join(BASE_DIR, "images", "cofrat-logotipo.png")
CSS_PATH = os.path.join(BASE_DIR, "style.css")

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Plataforma de Gestão dos Atendimentos",
    page_icon=LOGO_SYMBOL_PATH,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNÇÃO PARA CARREGAR CSS ---
def load_css(file_name):
    """Carrega um arquivo CSS externo para dentro do app Streamlit."""
    try:
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Arquivo CSS não encontrado em: {file_name}")

# Carrega o nosso arquivo de estilos
load_css(CSS_PATH)

# --- GATEKEEPER PRINCIPAL ---
# Inicializa o estado de autenticação se ele não existir
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = False

# Verifica o estado de autenticação para decidir o que mostrar
if not st.session_state["authentication_status"]:
    # Se não estiver logado, mostra o formulário de login
    login_form(logo_path=LOGO_EXTENDED_PATH) 
else:
    # Se estiver logado, renderiza o aplicativo principal
    main_app(logo_path=LOGO_EXTENDED_PATH)
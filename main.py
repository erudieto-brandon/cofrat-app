# main.py
import streamlit as st
from utils import login_form, main_app
import os # 1. Importe o módulo 'os'

# --- CAMINHOS DAS IMAGENS CORRIGIDOS ---
# Pega o caminho absoluto do diretório onde o script está rodando
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Constrói o caminho completo para cada arquivo
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

# VERSÃO CORRIGIDA
def load_css(file_name):
    """Carrega um arquivo CSS externo para dentro do app Streamlit."""
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Carrega o nosso arquivo de estilos usando o caminho absoluto
load_css(CSS_PATH)

# --- GATEKEEPER PRINCIPAL ---
# (O resto do seu código permanece o mesmo)
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
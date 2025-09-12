import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Login Prototipo", page_icon="🔑")

# --- FUNÇÃO DE LOGIN ---
def login_form():
    """Exibe o formulário de login e gerencia a lógica de autenticação."""
    st.header("Bem-vindo! Por favor, faça o login.")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            # Carrega as credenciais do arquivo de segredos
            try:
                correct_usernames = st.secrets["credentials"]["usernames"]
                correct_passwords = st.secrets["credentials"]["passwords"]
                credentials_dict = dict(zip(correct_usernames, correct_passwords))
            except Exception as e:
                st.error("Arquivo de segredos (secrets.toml) não encontrado ou mal configurado.")
                st.error(e) # Mostra o erro para facilitar o debug
                return

            # Verifica se o usuário existe e se a senha está correta
            if username in credentials_dict and credentials_dict[username] == password:
                st.session_state["authentication_status"] = True
                st.session_state["username"] = username
                st.success(f"Bem-vindo, {username}!")
                st.rerun()  # Recarrega a página para refletir o estado de login
            else:
                st.session_state["authentication_status"] = False
                st.error("Usuário ou senha incorretos.")

# --- FUNÇÃO DA PÁGINA PRINCIPAL ---
def main_page():
    """Exibe o conteúdo principal do aplicativo após o login."""
    st.sidebar.success(f"Logado como: **{st.session_state['username']}**")
    
    if st.sidebar.button("Logout"):
        st.session_state["authentication_status"] = False
        st.session_state["username"] = None
        st.rerun()

    st.title("Dashboard Principal 🚀")
    st.write("Aqui está o seu conteúdo super secreto e exclusivo!")
    st.info("Todo o conteúdo desta página só é visível para usuários autenticados.")
    
    # Adicione aqui o restante do seu aplicativo
    # Ex:
    st.line_chart([1, 2, 0, 4, 3])


# --- LÓGICA PRINCIPAL DO APLICATIVO (GATEKEEPER) ---

# Inicializa o estado de autenticação se ainda não existir
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = False

# Verifica o estado de autenticação para decidir qual página mostrar
if not st.session_state["authentication_status"]:
    login_form()
else:
    main_page()
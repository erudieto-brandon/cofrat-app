import streamlit as st
import streamlit_antd_components as sac

# --- FUNÇÃO DE LOGIN CENTRALIZADA ---
def login_form():
    """Exibe o formulário de login centralizado na página."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.header("Bem-vindo! Por favor, faça o login.")
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")
            if submitted:
                try:
                    correct_usernames = st.secrets["credentials"]["usernames"]
                    correct_passwords = st.secrets["credentials"]["passwords"]
                    credentials_dict = dict(zip(correct_usernames, correct_passwords))
                    if username in credentials_dict and credentials_dict[username] == password:
                        st.session_state["authentication_status"] = True
                        st.session_state["username"] = username
                        st.rerun()
                    else:
                        st.session_state["authentication_status"] = False
                        st.error("Usuário ou senha incorretos.")
                except Exception:
                    st.error("Arquivo de segredos (secrets.toml) não encontrado ou mal configurado.")

# --- PÁGINAS DO APLICATIVO ---

def home_page():
    """Exibe a Página Inicial, que agora é o dashboard."""
    st.markdown("""
    <div class="custom-title-container">
        <div class="custom-title-bar"></div>
        <div class="custom-title">
            <h1>Plataforma de Gestão de Agendamentos</h1>
            <p>Gerencie confirmações de agendamentos, profissionais e comunicação com pacientes</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.write("\n")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric(label="Pendentes", value="12", delta="Urgente: 3", delta_color="inverse")
    with col2: st.metric(label="Hoje", value="28", delta="+15% vs ontem")
    with col3: st.metric(label="Confirmados", value="24", delta="Taxa: 92.3%")
    with col4: st.metric(label="Profissionais", value="8", delta="Ativos no sistema")
    st.markdown("<br>", unsafe_allow_html=True)
    st.write("#### 📈 Resumo da Semana")
    col5, col6, col7, col8 = st.columns(4)
    with col5: st.metric(label="Total Agendamentos", value="156")
    with col6: st.metric(label="Confirmados", value="144")
    with col7: st.metric(label="Pendentes", value="9")
    with col8: st.metric(label="Cancelados", value="3")

# Funções placeholder para as outras páginas
def confirmation_queue_page(): st.title("Fila de Confirmação")
def daily_schedule_page(): st.title("Agenda do Dia")
def management_page(): st.title("Gestão Geral")
def confirmation_page(): st.title("Confirmação")
def patients_page(): st.title("Pacientes")
def reports_page(): st.title("Relatórios")

# --- LÓGICA PRINCIPAL DO APLICATIVO (LOGADO) ---
def main_app(logo_path):
    """Renderiza a sidebar e controla o roteamento de páginas."""
    with st.sidebar:
        st.image(logo_path, width=110)
        
        selected_page = sac.menu([
            sac.MenuItem('Página Inicial', icon='house'),
            sac.MenuItem('Agendamentos', type='group', children=[
                sac.MenuItem('Aprovação', icon='card-checklist'),
                sac.MenuItem('Agenda do Dia', icon='calendar-event'),
            ]),
            sac.MenuItem('Administrativo', type='group', children=[
                sac.MenuItem('Gestão', icon='gear'),
                sac.MenuItem('Pacientes', icon='people'),
                sac.MenuItem('Relatórios', icon='clipboard-data'),
            ]),
            sac.MenuItem('Comunicação', type='group', icon='chat-dots', children=[
                sac.MenuItem('Confirmação', icon='check2-square'),
                sac.MenuItem('Suporte', icon='whatsapp', href='https://wa.me/+5511959044561'),
            ]),
        ], color='#294960', open_all=False, return_index=False)
        
        st.sidebar.markdown("---")
        if st.sidebar.button("Logout"):
            st.session_state["authentication_status"] = False
            st.session_state["username"] = None
            st.rerun()

    # Roteamento de páginas
    if selected_page == 'Página Inicial': home_page()
    elif selected_page == 'Fila de Confirmação': confirmation_queue_page()
    elif selected_page == 'Agenda do Dia': daily_schedule_page()
    elif selected_page == 'Gestão': management_page()
    elif selected_page == 'Confirmação': confirmation_page()
    elif selected_page == 'Pacientes': patients_page()
    elif selected_page == 'Relatórios': reports_page()
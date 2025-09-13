import streamlit as st
import streamlit_antd_components as sac

# --- FUNÇÃO DE LOGIN CENTRALIZADA E ESTILIZADA ---
def login_form():
    """Exibe o formulário de login centralizado e com design customizado."""
    
    # Carrega o CSS dos ícones do Bootstrap para ser usado no cabeçalho
    st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:


        # --- Formulário Streamlit ---
        with st.form("login_form_styled"):
            # --- Cabeçalho do Formulário ---
            # Esta seção cria o título "Fazer Login" com o ícone e o subtítulo.
            # As cores e fontes são controladas pelo style.css
            st.markdown("""
                <div class="login-header">
                    <i class="bi bi-lock"></i>
                    <div>
                        <h2 class="login-title">Fazer login</h2>
                        <p class="login-subtitle">Entre com suas credenciais para acessar o sistema</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.write("\n"*3)  # Espaçamento entre o cabeçalho e os campos
            # --- Campo de Email ---
            # 1. Label customizado (controlado via CSS)
            st.markdown('<p class="input-label">Email</p>', unsafe_allow_html=True)
            # 2. Input do Streamlit (sem o label padrão)
            username = st.text_input(
                "Email", 
                placeholder="seu@email.com", 
                label_visibility="collapsed"
            )

            # --- Campo de Senha ---
            st.markdown('<p class="input-label">Senha</p>', unsafe_allow_html=True)
            password = st.text_input(
                "Senha", 
                placeholder="Sua senha", 
                type="password", 
                label_visibility="collapsed"
            )
            
            # --- Botão de Envio ---
            # use_container_width=True faz o botão ocupar todo o espaço do formulário
            submitted = st.form_submit_button("Entrar", use_container_width=True)

            # --- Lógica de Autenticação ---
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
        
        # --- Fim do Container do Formulário ---
        st.markdown('</div>', unsafe_allow_html=True)

# --- PÁGINAS DO APLICATIVO ---
# --- FUNÇÃO HELPER PARA CRIAR CARDS CUSTOMIZADOS ---
def create_metric_card(label, value, delta, delta_color):
    """Gera o HTML para um card de métrica customizado."""
    
    # Define a classe CSS para a cor do delta
    if delta_color == "normal":
        delta_class = "delta-positive"
    elif delta_color == "inverse":
        delta_class = "delta-negative"
    else: # "off"
        delta_class = "delta-neutral"

    # Monta o HTML do card
    card_html = f"""
        <div class="metric-card">
            <div>
                <div class="metric-card-label">{label}</div>
                <div class="metric-card-value">{value}</div>
            </div>
            <div class="metric-card-delta {delta_class}">{delta}</div>
        </div>
    """
    return card_html

# Adicione esta nova função em utils.py
def create_summary_card(label, value):
    """Gera o HTML para um card de resumo centralizado."""
    card_html = f"""
        <div class="summary-card">
            <div class="summary-card-value">{value}</div>
            <div class="summary-card-label">{label}</div>
        </div>
    """
    return card_html

# --- PÁGINA INICIAL (DASHBOARD) ---
def home_page():
    """Exibe a Página Inicial com cards de métricas customizados."""
    
    # Título da página
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

    # --- Primeira Linha de Cards ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(create_metric_card("Pendentes", "12", "Sem resposta faz tempo: 3 ", "inverse"), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric_card("Hoje", "28", "+15% vs ontem", "normal"), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card("Confirmados", "24", "Taxa: 92.3%", "off"), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card("Profissionais", "8", "Ativos no sistema", "off"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="custom-title">
        <h3>Resumo da Semana</h3>
    </div>
    """, unsafe_allow_html=True)

    # --- Segunda Linha de Cards (ATUALIZADA PARA USAR A NOVA FUNÇÃO) ---
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.markdown(create_summary_card("Total Agendamentos", "156"), unsafe_allow_html=True)
    with col6:
        st.markdown(create_summary_card("Confirmados", "144"), unsafe_allow_html=True)
    with col7:
        st.markdown(create_summary_card("Pendentes", "9"), unsafe_allow_html=True)
    with col8:
        st.markdown(create_summary_card("Cancelados", "3"), unsafe_allow_html=True)

def get_sample_appointments():
    """Retorna uma lista de dados de agendamentos fictícios."""
    return [
        {
            "name": "Maria Silva Santos", "initials": "MS", "phone": "(11) 99999-1234",
            "specialty": "Fisioterapia", "date": "domingo, 14 de janeiro de 2024", "time": "10:00",
            "professional": "Dra. Liliane Santos", "insurance": "Unimed",
            "card_number": "0 123 456789 00-1", "event": "Consulta",
            "notes": "Paciente com dor nas costas, primeira consulta."
        },
        {
            "name": "João Pereira Costa", "initials": "JP", "phone": "(21) 98888-5678",
            "specialty": "Ortopedia", "date": "segunda, 15 de janeiro de 2024", "time": "11:30",
            "professional": "Dr. Carlos Andrade", "insurance": "Bradesco Saúde",
            "card_number": "9 876 543210 99-8", "event": "Retorno",
            "notes": "Pós-operatório do joelho direito."
        },
        {
            "name": "Ana Beatriz Lima", "initials": "AB", "phone": "(31) 97777-4321",
            "specialty": "Fisioterapia", "date": "terça, 16 de janeiro de 2024", "time": "09:00",
            "professional": "Dra. Liliane Santos", "insurance": "Amil",
            "card_number": "1 112 223334 44-5", "event": "Primeira Avaliação",
            "notes": "Encaminhada para avaliação de RPG."
        }
    ]

def display_completion_message():
    """Exibe a mensagem de conclusão quando todos os agendamentos são processados."""
    st.markdown("""
    <div class="completion-container">
        <div class="completion-icon">✓</div>
        <h2 class="completion-title">Parabéns!</h2>
        <p class="completion-subtitle">Todos os agendamentos pendentes foram processados.</p>
    </div>
    """, unsafe_allow_html=True)

    # Centraliza o botão usando colunas
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        if st.button("Voltar à Página Inicial", use_container_width=True, key="reset_queue"):
            st.session_state.current_appointment_index = 0
            st.rerun()

def confirmation_queue_page():
    """Exibe a fila de aprovação usando st.dialog para os diálogos."""
    
    st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">', unsafe_allow_html=True)

    # --- Estado inicial ---
    if 'appointments' not in st.session_state:
        st.session_state.appointments = get_sample_appointments()
    if 'current_appointment_index' not in st.session_state:
        st.session_state.current_appointment_index = 0
    
    if 'show_approve_dialog' not in st.session_state:
        st.session_state.show_approve_dialog = False
    if 'show_cancel_dialog' not in st.session_state:
        st.session_state.show_cancel_dialog = False
    if 'show_reschedule_dialog' not in st.session_state:
        st.session_state.show_reschedule_dialog = False

    appointments = st.session_state.appointments
    current_index = st.session_state.current_appointment_index
    total_appointments = len(appointments)

    def go_to_next():
        st.session_state.current_appointment_index += 1
        st.session_state.show_approve_dialog = False
        st.session_state.show_cancel_dialog = False
        st.session_state.show_reschedule_dialog = False

    if current_index >= total_appointments:
        display_completion_message()
        return

    current_appointment = appointments[current_index]

    # Barra de progresso
    st.write("Progresso")
    st.progress((current_index + 1) / total_appointments)
    st.markdown(f"<p class='progress-label'>{current_index + 1} de {total_appointments}</p>", unsafe_allow_html=True)

    # Card de aprovação normal
    approval_card_html = f"""
    <div class="approval-card">
        <div class="approval-header">
            <div class="patient-info">
                <div class="patient-avatar">{current_appointment['initials']}</div>
                <div>
                    <div class="patient-name">{current_appointment['name']}</div>
                    <div class="patient-phone"><i class="bi bi-telephone-fill"></i> {current_appointment['phone']}</div>
                </div>
            </div>
            <div class="specialty-tag">{current_appointment['specialty']}</div>
        </div>
        <div class="details-grid">
            <div class="detail-item"><i class="bi bi-calendar-event"></i><div><div class="detail-label">Data</div><div class="detail-value">{current_appointment['date']}</div></div></div>
            <div class="detail-item"><i class="bi bi-person"></i><div><div class="detail-label">Profissional</div><div class="detail-value">{current_appointment['professional']}</div></div></div>
            <div class="detail-item"><i class="bi bi-clock"></i><div><div class="detail-label">Horário</div><div class="detail-value">{current_appointment['time']}</div></div></div>
            <div class="detail-item"><i class="bi bi-hospital"></i><div><div class="detail-label">Convênio</div><div class="detail-value">{current_appointment['insurance']}</div></div></div>
            <div class="detail-item"><i class="bi bi-credit-card-2-front"></i><div><div class="detail-label">Carteirinha</div><div class="detail-value">{current_appointment['card_number']}</div></div></div>
            <div class="detail-item"><i class="bi bi-tag"></i><div><div class="detail-label">Evento</div><div class="detail-value">{current_appointment['event']}</div></div></div>
        </div>
        <div class="observations-section">
            <div class="detail-label">Observações</div>
            <div class="detail-value">{current_appointment['notes']}</div>
        </div>
    </div>
    """
    st.markdown(approval_card_html, unsafe_allow_html=True)

    # Botões de ação principais
    st.markdown('<div class="action-buttons-container">', unsafe_allow_html=True)
    cols = st.columns(3)
    if cols[0].button("✓ Aprovar", use_container_width=True):
        st.session_state.show_approve_dialog = True
        st.rerun()
    if cols[1].button("↻ Reagendar", use_container_width=True):
        st.session_state.show_reschedule_dialog = True
        st.rerun()
    if cols[2].button("✕ Cancelar", use_container_width=True):
        st.session_state.show_cancel_dialog = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Diálogos via st.dialog ---

    # Diálogo de Aprovação
    @st.dialog("Confirmar Aprovação")
    def approve_dialog():
        st.write(f"Tem certeza que deseja aprovar o agendamento de **{current_appointment['name']}**?")
        if st.button("Sim, Aprovar", use_container_width=True):
            st.toast(f"{current_appointment['name']} aprovado(a)!", icon="✅")
            go_to_next()
            st.rerun()
        if st.button("Voltar", use_container_width=True):
            st.session_state.show_approve_dialog = False
            st.rerun()

    if st.session_state.show_approve_dialog:
        approve_dialog()

    # Diálogo de Cancelamento
    @st.dialog("Confirmar Cancelamento")
    def cancel_dialog():
        st.warning(f"Tem certeza que deseja cancelar o agendamento de **{current_appointment['name']}**?")

        motivo = st.selectbox(
            "Selecione o motivo do cancelamento:",
            [
                "Convênio não aprovado",
                "Paciente desistiu",
                "Profissional indisponível",
                "Erro no agendamento",
                "Outro motivo"
            ]
        )

        if st.button("Sim, Cancelar", use_container_width=True):
            st.toast(
                f"{current_appointment['name']} cancelado(a). Motivo: {motivo}",
                icon="🗑️"
            )
            go_to_next()
            st.rerun()

        if st.button("Voltar", use_container_width=True):
            st.session_state.show_cancel_dialog = False
            st.rerun()


    if st.session_state.show_cancel_dialog:
        cancel_dialog()

    # Diálogo de Reagendamento
    @st.dialog("Reagendar Consulta")
    def reschedule_dialog():
        st.markdown(f"**Paciente:** {current_appointment['name']}")
        st.markdown(f"**Agendamento atual:** {current_appointment['date'].split(', ')[1]} às {current_appointment['time']}")
        new_date = st.date_input("Nova Data")
        new_time = st.time_input("Novo Horário", step=1800)
        st.text_area("Mensagem para o Paciente (Opcional)")
        if st.button("Enviar Sugestão", use_container_width=True):
            st.toast("Sugestão de reagendamento enviada!", icon="👍")
            go_to_next()
            st.rerun()
        if st.button("Cancelar", use_container_width=True):
            st.session_state.show_reschedule_dialog = False
            st.rerun()

    if st.session_state.show_reschedule_dialog:
        reschedule_dialog()


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
            sac.MenuItem('Comunicação', type='group', children=[
                sac.MenuItem('Confirmação', icon='check2-square'),
                sac.MenuItem('Suporte', icon='whatsapp', href='https://wa.me/+5511959044561'),
            ]),
        ], color='#294960', open_all=True, return_index=False) # open_all=True para visualização
        

        if st.sidebar.button("Logout"):
            st.session_state["authentication_status"] = False
            st.session_state["username"] = None
            st.rerun()

    # Roteamento de páginas
    if selected_page == 'Página Inicial': home_page()
    elif selected_page == 'Aprovação': confirmation_queue_page()
    elif selected_page == 'Agenda do Dia': daily_schedule_page()
    elif selected_page == 'Gestão': management_page()
    elif selected_page == 'Confirmação': confirmation_page()
    elif selected_page == 'Pacientes': patients_page()
    elif selected_page == 'Relatórios': reports_page()
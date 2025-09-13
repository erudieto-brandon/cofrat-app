# utils.py
import streamlit as st
import streamlit_antd_components as sac
from datetime import date, timedelta
import pandas as pd
from dateutil.relativedelta import relativedelta
import numpy as np # Adicionado para dados de exemplo

# --- FUNÇÃO DE LOGIN CENTRALIZADA E ESTILIZADA ---
def login_form(logo_path): # MODIFICAÇÃO: Adicionado o parâmetro 'logo_path'
    """Exibe o logotipo e o formulário de login centralizado."""
    st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">', unsafe_allow_html=True)

    # --- [NOVO] CÓDIGO PARA EXIBIR O LOGOTIPO CENTRALIZADO ---
    logo_col1, logo_col2, logo_col3 = st.columns([1.4, 1, 1])
    with logo_col2:
        st.image(logo_path, width=200)
    
    st.write("\n") # Adiciona um espaço entre o logo e o formulário
    # --- FIM DO CÓDIGO NOVO ---

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form_styled"):
            st.markdown("""
                <div class="login-header">
                    <i class="bi bi-lock"></i>
                    <div>
                        <h2 class="login-title">Fazer login</h2>
                        <p class="login-subtitle">Entre com suas credenciais para acessar o sistema</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.write("\n"*3)
            st.markdown('<p class="input-label">Email</p>', unsafe_allow_html=True)
            username = st.text_input("Email", placeholder="seu@email.com", label_visibility="collapsed")
            st.markdown('<p class="input-label">Senha</p>', unsafe_allow_html=True)
            password = st.text_input("Senha", placeholder="Sua senha", type="password", label_visibility="collapsed")
            
            if st.form_submit_button("Entrar", use_container_width=True):
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

# --- FUNÇÕES HELPER PARA CARDS ---
def create_metric_card(label, value, delta, delta_color):
    delta_class = {"normal": "delta-positive", "inverse": "delta-negative"}.get(delta_color, "delta-neutral")
    return f'<div class="metric-card"><div><div class="metric-card-label">{label}</div><div class="metric-card-value">{value}</div></div><div class="metric-card-delta {delta_class}">{delta}</div></div>'

def create_summary_card(label, value):
    return f'<div class="summary-card"><div class="summary-card-value">{value}</div><div class="summary-card-label">{label}</div></div>'

# --- PÁGINA INICIAL (DASHBOARD) ---
def home_page():
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
    col1.markdown(create_metric_card("Pendentes", "12", "Sem resposta faz tempo: 3 ", "inverse"), unsafe_allow_html=True)
    col2.markdown(create_metric_card("Hoje", "28", "+15% vs ontem", "normal"), unsafe_allow_html=True)
    col3.markdown(create_metric_card("Confirmados", "24", "Taxa: 92.3%", "off"), unsafe_allow_html=True)
    col4.markdown(create_metric_card("Profissionais", "8", "Ativos no sistema", "off"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<h3>Resumo da Semana</h3>', unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)
    col5.markdown(create_summary_card("Total Agendamentos", "156"), unsafe_allow_html=True)
    col6.markdown(create_summary_card("Confirmados", "144"), unsafe_allow_html=True)
    col7.markdown(create_summary_card("Pendentes", "9"), unsafe_allow_html=True)
    col8.markdown(create_summary_card("Cancelados", "3"), unsafe_allow_html=True)

# --- PÁGINA DE APROVAÇÃO ---
def get_sample_appointments():
    return [
        {"name": "Maria Silva Santos", "initials": "MS", "phone": "(11) 99999-1234", "specialty": "Fisioterapia", "date": "domingo, 14 de janeiro de 2024", "time": "10:00", "professional": "Dra. Liliane Santos", "insurance": "Unimed", "card_number": "0 123 456789 00-1", "event": "Consulta", "notes": "Paciente com dor nas costas, primeira consulta."},
        {"name": "João Pereira Costa", "initials": "JP", "phone": "(21) 98888-5678", "specialty": "Ortopedia", "date": "segunda, 15 de janeiro de 2024", "time": "11:30", "professional": "Dr. Carlos Andrade", "insurance": "Bradesco Saúde", "card_number": "9 876 543210 99-8", "event": "Retorno", "notes": "Pós-operatório do joelho direito."}
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
        if st.button("Reiniciar a Fila de Aprovação", use_container_width=True, key="reset_queue"):
            st.session_state.current_appointment_index = 0
            st.rerun()

def confirmation_queue_page():
    """Exibe a fila de aprovação usando st.dialog para os diálogos."""
        # --- [LINHA ADICIONADA] ---
    # Este CSS específico para a página move o container para cima, sobrescrevendo o estilo global.
    st.markdown('<style>div.block-container {padding-top: 1.5rem;}</style>', unsafe_allow_html=True)
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


# --- DADOS E FUNÇÕES PARA A PÁGINA DE AGENDA DO DIA ---
def get_daily_agenda_for_dataframe():
    """Retorna dados fictícios para a tabela da agenda com mais variedade."""
    return [
        {"name": "Maria Silva Santos", "scheduled_date": "2025-01-15", "professional": "Dr. Carlos Mendes", "category": "Ortopedia", "status": "Confirmado"},
        {"name": "João Carlos Oliveira", "scheduled_date": "2025-01-15", "professional": "Dra. Ana Costa", "category": "Fisioterapia", "status": "Confirmado"},
        {"name": "Ana Paula Costa", "scheduled_date": "2025-01-16", "professional": "Dr. Carlos Mendes", "category": "Ortopedia", "status": "Cancelado"},
        {"name": "Pedro Lima Santos", "scheduled_date": "2025-01-22", "professional": "Dr. Roberto Lima", "category": "Nutrição", "status": "Reagendando"},
        {"name": "Carla Ferreira", "scheduled_date": "2025-02-10", "professional": "Dra. Ana Costa", "category": "Fisioterapia", "status": "Confirmado"},
        {"name": "Roberto Silva", "scheduled_date": "2025-02-18", "professional": "Dr. Roberto Lima", "category": "Nutrição", "status": "Confirmado"},
        {"name": "Beatriz Oliveira", "scheduled_date": "2025-03-05", "professional": "Dr. Carlos Mendes", "category": "Ortopedia", "status": "Confirmado"},
        {"name": "Gabriel Santos", "scheduled_date": "2025-04-01", "professional": "Dra. Ana Costa", "category": "Fisioterapia", "status": "Cancelado"},
    ]

def get_date_range(selected_date, view_mode):
    """Calcula o intervalo de datas com base no modo de visualização."""
    if view_mode == "Todo o período":
        return date.min, date.max
    if view_mode == "Dia":
        return selected_date, selected_date
    elif view_mode == "Semana":
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week, end_of_week
    elif view_mode == "Mês":
        start_of_month = selected_date.replace(day=1)
        end_of_month = start_of_month + relativedelta(months=1) - timedelta(days=1)
        return start_of_month, end_of_month
    elif view_mode == "Trimestre":
        current_quarter = (selected_date.month - 1) // 3 + 1
        start_month_of_quarter = 3 * current_quarter - 2
        start_of_quarter = date(selected_date.year, start_month_of_quarter, 1)
        end_of_quarter = start_of_quarter + relativedelta(months=3) - timedelta(days=1)
        return start_of_quarter, end_of_quarter

def clear_filters_callback():
    """Função de callback para limpar todos os filtros."""
    st.session_state.view_mode = "Todo o período"
    st.session_state.selected_date = date(2025, 1, 15)
    st.session_state.prof_filter = "Todos"
    st.session_state.cat_filter = "Todos"
    st.session_state.status_filter = "Todos"
    st.session_state.search_term = ""

def daily_schedule_page():
    """Exibe a agenda do dia com filtros interativos e o novo design na tabela."""
    st.subheader("Filtros")
    
    # --- INICIALIZAÇÃO DO SESSION STATE ---
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "Todo o período"
        st.session_state.selected_date = date(2025, 1, 15)
        st.session_state.prof_filter = "Todos"
        st.session_state.cat_filter = "Todos"
        st.session_state.status_filter = "Todos"
        st.session_state.search_term = ""

    df = pd.DataFrame(get_daily_agenda_for_dataframe())
    df['scheduled_date'] = pd.to_datetime(df['scheduled_date']).dt.date

    # --- BARRA DE FILTROS COMPLETA ---
    with st.container(border=False):
        col1, col2 = st.columns([3, 2])
        col1.radio("Visualização:", ["Dia", "Semana", "Mês", "Trimestre", "Todo o período"], horizontal=True, key="view_mode")
        col2.date_input("Data:", key="selected_date", disabled=(st.session_state.view_mode == "Todo o período"))

        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        f_col1.selectbox("Todos os profissionais", ["Todos"] + sorted(df['professional'].unique().tolist()), key="prof_filter")
        f_col2.selectbox("Todas as categorias", ["Todos"] + sorted(df['category'].unique().tolist()), key="cat_filter")
        f_col3.selectbox("Todos os status", ["Todos"] + sorted(df['status'].unique().tolist()), key="status_filter")
        f_col4.selectbox("Todos os pacientes", ["Todos"], key="patient_filter", disabled=True)

        search_col, btn_col = st.columns([4, 1.08])
        search_col.text_input("Buscar paciente...", placeholder="Buscar paciente...", label_visibility="collapsed", key="search_term")
        btn_col.button("Limpar Filtros", use_container_width=True, on_click=clear_filters_callback)

    # --- LÓGICA DE FILTRAGEM ---
    start_date, end_date = get_date_range(st.session_state.selected_date, st.session_state.view_mode)
    
    filtered_df = df
    if st.session_state.view_mode != "Todo o período":
        filtered_df = df[(df['scheduled_date'] >= start_date) & (df['scheduled_date'] <= end_date)]
    if st.session_state.prof_filter != "Todos":
        filtered_df = filtered_df[filtered_df['professional'] == st.session_state.prof_filter]
    if st.session_state.cat_filter != "Todos":
        filtered_df = filtered_df[filtered_df['category'] == st.session_state.cat_filter]
    if st.session_state.status_filter != "Todos":
        filtered_df = filtered_df[filtered_df['status'] == st.session_state.status_filter]
    if st.session_state.search_term:
        filtered_df = filtered_df[filtered_df['name'].str.contains(st.session_state.search_term, case=False, na=False)]

    # --- CABEÇALHO DINÂMICO ---
    if st.session_state.view_mode == "Dia":
        st.header(f"Agendamentos para {st.session_state.selected_date.strftime('%d/%m/%Y')}")
    elif st.session_state.view_mode == "Todo o período":
        st.header("Exibindo todos os agendamentos")
    else:
        st.header(f"Agendamentos de {start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}")

    # --- Tabela de Agendamentos com o novo container para estilização ---
    st.markdown('<div class="agenda-table-container">', unsafe_allow_html=True)
    st.dataframe(
        filtered_df.rename(columns={
            'name': 'Paciente',
            'scheduled_date': 'Data Agendada',
            'professional': 'Profissional',
            'category': 'Categoria',
            'status': 'Status'
        }),
        use_container_width=True,
        hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- PÁGINAS ADICIONAIS (PLACEHOLDERS) ---

def management_page():
    st.title("Gestão")
    st.write("Gerencie seus agendamentos de forma eficiente")

    selected_tab = sac.segmented(
        items=[
            sac.SegmentedItem(label='Médicos', icon='person-fill'),
            sac.SegmentedItem(label='Modalidades', icon='tags-fill'),
            sac.SegmentedItem(label='Agendas', icon='calendar-week-fill'),
        ],
        align='left',
        size='mid',
        return_index=False, # Retorna o label do item
        color='#28a745',
    )

    if selected_tab == 'Médicos':
        header_cols = st.columns([3, 1])
        with header_cols[0]:
            st.subheader("Profissionais de Saúde")
        with header_cols[1]:
            st.button("✚ Adicionar Profissional", type="primary", use_container_width=True)

        # Dados de exemplo
        professionals = [
            {"name": "Dra. Liliane Santos", "specialty": "Fisioterapia", "schedule": "Segunda a Sexta", "capacity": 10},
            {"name": "Dr. Roberto Silva", "specialty": "Ortopedia", "schedule": "Segunda a Sexta", "capacity": 8},
            {"name": "Dra. Carla Mendes", "specialty": "Fisioterapia Infantil", "schedule": "Segunda a Sexta", "capacity": 6},
        ]

        # Layout em colunas
        cols = st.columns(3)
        for i, prof in enumerate(professionals):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"##### 🩺 {prof['name']}")
                    st.write(prof['specialty'])
                    st.write(f"🕒 {prof['schedule']}")
                    st.write(f" kapacita: {prof['capacity']} pacientes/horário")
                    
                    btn_cols = st.columns(2)
                    btn_cols[0].button("Editar", key=f"edit_{i}", use_container_width=True)
                    btn_cols[1].button("Desativar", key=f"del_{i}", use_container_width=True)

    elif selected_tab == 'Modalidades':
        header_cols = st.columns([3, 1])
        with header_cols[0]:
            st.subheader("Modalidades de Atendimento")
        with header_cols[1]:
            st.button("✚ Adicionar Modalidade", type="primary", use_container_width=True)

        modalities = [
            {"name": "Fisioterapia", "desc": "Tratamento de reabilitação física"},
            {"name": "Ortopedia", "desc": "Consultas e tratamentos ortopédicos"},
            {"name": "Fisioterapia Infantil", "desc": "Fisioterapia especializada para crianças"},
        ]
        
        cols = st.columns(3)
        for i, mod in enumerate(modalities):
            with cols[i % 3]:
                with st.container(border=True, height=180):
                    st.markdown(f"##### {mod['name']}")
                    st.write(mod['desc'])
                    
                    st.write("") # Espaçador
                    
                    btn_cols = st.columns(2)
                    btn_cols[0].button("Editar", key=f"edit_mod_{i}", use_container_width=True)
                    btn_cols[1].button("🗑️", key=f"del_mod_{i}", use_container_width=True)

    elif selected_tab == 'Agendas':
        st.subheader("Configuração de Agendas")

        agendas = [
            {"name": "Dra. Liliane Santos", "specialty": "Fisioterapia", "schedule": [
                ("Segunda-feira", "08:00 - 17:00", 10), ("Terça-feira", "08:00 - 17:00", 10),
                ("Quarta-feira", "08:00 - 17:00", 10), ("Quinta-feira", "08:00 - 17:00", 10),
                ("Sexta-feira", "08:00 - 17:00", 10)
            ]},
            {"name": "Dr. Roberto Silva", "specialty": "Ortopedia", "schedule": [
                ("Segunda-feira", "09:00 - 16:00", 8), ("Quarta-feira", "09:00 - 16:00", 8),
                ("Sexta-feira", "09:00 - 16:00", 8)
            ]},
            {"name": "Dra. Carla Mendes", "specialty": "Fisioterapia Infantil", "schedule": [
                ("Terça-feira", "08:00 - 12:00", 6), ("Quinta-feira", "08:00 - 12:00", 6)
            ]},
        ]

        for i, agenda in enumerate(agendas):
            with st.container(border=True):
                header_cols = st.columns([3, 1])
                with header_cols[0]:
                    st.markdown(f"##### 🧑‍⚕️ {agenda['name']}")
                    st.caption(agenda['specialty'])
                with header_cols[1]:
                    st.button("Editar", key=f"edit_agenda_{i}", use_container_width=True, type="primary")
                
                st.write("") # Espaçador

                for day, time, cap in agenda['schedule']:
                    day_cols = st.columns([2, 2, 1])
                    day_cols[0].text(day)
                    day_cols[1].text(time)
                    day_cols[2].button(f"Cap: {cap}", key=f"cap_{i}_{day}", disabled=True, use_container_width=True)
            st.write("") # Espaço entre os cards

# --- [INÍCIO] CÓDIGO MODIFICADO ---
def confirmation_page():
    st.title("Comunicação")

    # --- DIÁLOGO DE PREVIEW (definido antes para poder ser chamado) ---
    @st.dialog("Preview da Mensagem")
    def preview_dialog():
        message_template = st.session_state.get('message_template', "Olá, {$primeiro_nome}! Confirmando seu agendamento de {$modalidade} para amanhã às {$horario}. Atenciosamente, COFRAT.")
        selected_patients_df = st.session_state.edited_df[st.session_state.edited_df['Selecionar']]

        if selected_patients_df.empty:
            st.warning("Nenhum paciente selecionado para visualizar.")
        else:
            for _, row in selected_patients_df.iterrows():
                with st.container(border=True):
                    st.markdown(f"**Para: {row['Paciente']}**")
                    
                    preview_message = message_template.replace('{$primeiro_nome}', str(row['Paciente']).split(' ')[0])
                    preview_message = preview_message.replace('{$modalidade}', str(row['Modalidade']))
                    preview_message = preview_message.replace('{$horario}', str(row['Horário']))
                    
                    # CSS CORRIGIDO: Removido margin-top negativo para evitar que o box saia do container.
                    st.markdown(f"""
                    <div style="background-color: #e9f7ef; padding: 10px; border-radius: 5px; color: #155724; margin-top: -5px; margin-bottom: 15px">
                        {preview_message}
                    </div>
                    """, unsafe_allow_html=True)

        if st.button("Fechar", use_container_width=True, key="close_preview"):
            st.session_state.show_preview_dialog = False
            st.rerun()

    # --- INICIALIZAÇÃO DO SESSION STATE ---
    if 'show_preview_dialog' not in st.session_state:
        st.session_state.show_preview_dialog = False
        
    if 'edited_df' not in st.session_state:
        data = {
            'Selecionar': [True, True, True, True, True],
            'Paciente': ['Maria Silva Santos', 'João Carlos Oliveira', 'Ana Beatriz Costa', 'Pedro Lima Silva', 'Fernanda Costa'],
            'Horário': ['08:00', '08:30', '09:00', '09:30', '10:00'],
            'Modalidade': ['Fisioterapia', 'Ortopedia', 'Fisioterapia Infantil', 'Fisioterapia', 'Ortopedia'],
            'Profissional': ['Dra. Liliane', 'Dr. Roberto', 'Dra. Marina', 'Dra. Liliane', 'Dr. Roberto'],
            'Status': ['Confirmado', 'Confirmado', 'Confirmado', 'Pendente', 'Confirmado'],
            'Telefone': ['(11) 99999-9999', '(11) 88888-8888', '(11) 77777-7777', '(11) 66666-6666', '(11) 55555-5555']
        }
        st.session_state.edited_df = pd.DataFrame(data)

    # --- NOVO LAYOUT DA PÁGINA EM DUAS COLUNAS ---
    left_col, right_col = st.columns([1, 2])

    with left_col:
        with st.container(border=True):
            st.subheader("🗓️ Selecionar Data")
            st.caption("Escolha o dia para visualizar os agendamentos")
            
            selected_date = st.date_input(
                "Selecione o dia", 
                date(2025, 9, 13),
                label_visibility="collapsed"
            )
            
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-top: 10px; margin-bottom: 10px">
                Data selecionada: <b>{selected_date.strftime('%d/%m/%Y')}</b>
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        with st.container(border=True):
            st.subheader("📋 Template de Mensagem")
            st.caption("Configure a mensagem que será enviada aos pacientes")
            
            message = st.text_area(
                "Mensagem:", 
                "Olá, {$primeiro_nome}! Confirmando seu agendamento de {$modalidade} para amanhã às {$horario}. Atenciosamente, COFRAT.",
                height=120,
                key='message_template'
            )

            st.markdown("**Variáveis Disponíveis:**")
            variables_html = """
            <div style="font-size: 0.9rem; line-height: 1.6;">
                <b>{$primeiro_nome}</b>: Primeiro nome do paciente<br>
                <b>{$modalidade}</b>: Tipo de consulta/tratamento<br>
                <b>{$horario}</b>: Horário do agendamento<br>
                <b>{$data}</b>: Data do agendamento<br>
                <b>{$profissional}</b>: Nome do profissional
            </div>
            """
            st.markdown(variables_html, unsafe_allow_html=True)
            st.write("")

            # PREVIEW DINÂMICO para o primeiro paciente da lista
            if not st.session_state.edited_df.empty:
                first_patient = st.session_state.edited_df.iloc[0]
                current_template = st.session_state.get('message_template', "")
                
                preview_text = current_template.replace('{$primeiro_nome}', str(first_patient['Paciente']).split(' ')[0])
                preview_text = preview_text.replace('{$modalidade}', str(first_patient['Modalidade']))
                preview_text = preview_text.replace('{$horario}', str(first_patient['Horário']))
                
                st.caption("Preview:")
                st.markdown(f"_{preview_text}_")
            
            st.write("")

            selected_count = int(st.session_state.edited_df['Selecionar'].sum())
            btn_cols = st.columns(2)
            if btn_cols[0].button("Visualizar Preview", use_container_width=True):
                st.session_state.show_preview_dialog = True
                st.rerun()
            
            btn_cols[1].button(f"✉️ Enviar Mensagens ({selected_count})", use_container_width=True, type="primary")

    # --- TABELA DE AGENDAMENTOS ---
    st.write("---")
    st.subheader(f"Agendamentos do Dia ({selected_date.strftime('%d/%m/%Y')})")

    all_selected = all(st.session_state.edited_df['Selecionar'])
    def toggle_all():
        new_value = not all_selected
        st.session_state.edited_df['Selecionar'] = new_value

    st.checkbox("Selecionar Todos", value=all_selected, on_change=toggle_all, key="select_all_checkbox")

    edited_df = st.data_editor(
        st.session_state.edited_df,
        use_container_width=True,
        hide_index=True,
        disabled=['Paciente', 'Horário', 'Modalidade', 'Profissional', 'Status', 'Telefone'],
        key='appointments_editor'
    )
    st.session_state.edited_df = edited_df

    if st.session_state.show_preview_dialog:
        preview_dialog()
# --- [FIM] CÓDIGO MODIFICADO ---

def patients_page():
    st.title("Pacientes")
    st.write("Gerencie informações e histórico dos pacientes.")

    header_cols = st.columns([3, 1])
    with header_cols[0]:
        st.subheader("Cadastro de Pacientes")
    with header_cols[1]:
        st.button("✚ Novo Paciente", type="primary", use_container_width=True)

    filter_cols = st.columns([3, 1])
    filter_cols[0].text_input("Buscar por nome, telefone ou email...", placeholder="🔍 Buscar por nome, telefone ou email...", label_visibility="collapsed")
    filter_cols[1].button("Filtros", use_container_width=True)

    # Dados de exemplo para a tabela de pacientes
    data = {
        'PACIENTE': ['Maria Silva Santos', 'João Carlos Oliveira', 'Ana Paula Costa', 'Pedro Lima Santos'],
        'CONTATO': ['maria.silva@email.com', 'joao.carlos@email.com', 'ana.paula@email.com', 'pedro.lima@email.com'],
        'CONVÊNIO': ['Unimed', 'Bradesco Saúde', 'SulAmérica', 'Amil'],
        'ÚLTIMO ATENDIMENTO': ['09/01/2024', '11/01/2024', '13/01/2024', '14/12/2023'],
        'TOTAL DE CONSULTAS': [15, 8, 3, 12],
        'STATUS': ['Ativo', 'Ativo', 'Ativo', 'Inativo']
    }
    df_patients = pd.DataFrame(data)

    st.dataframe(df_patients, use_container_width=True, hide_index=True)
    st.caption("Ações como editar e excluir podem ser adicionadas ao selecionar uma linha ou através de um menu de contexto em futuras implementações.")

def reports_page():
    st.title("Relatórios")
    st.write("Visualize métricas e dados importantes sobre os agendamentos.")

    # Métricas principais
    kpi_cols = st.columns(4)
    kpi_cols[0].metric("Consultas no Mês", "245", "+12% vs Mês Anterior")
    kpi_cols[1].metric("Novos Pacientes", "32", "+5%")
    kpi_cols[2].metric("Taxa de Confirmação", "93.5%", "1.2%")
    kpi_cols[3].metric("Taxa de Cancelamento", "4.1%", "-0.5%")
    
    st.write("---")

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.subheader("Agendamentos por Modalidade")
        # Dados de exemplo para o gráfico de barras
        chart_data = pd.DataFrame({
            "Modalidade": ["Fisioterapia", "Ortopedia", "Fisioterapia Inf.", "Pilates", "Acupuntura"],
            "Agendamentos": [110, 75, 30, 22, 8],
        })
        st.bar_chart(chart_data, x="Modalidade", y="Agendamentos", color="#0b9035")

    with chart_cols[1]:
        st.subheader("Evolução de Novos Pacientes (Últimos 6 Meses)")
        # Dados de exemplo para o gráfico de linha
        chart_data_line = pd.DataFrame(
            np.random.randint(15, 40, size=(6, 1)),
            columns=['Novos Pacientes'],
            index=pd.to_datetime(['2025-04-01', '2025-05-01', '2025-06-01', '2025-07-01', '2025-08-01', '2025-09-01'])
        )
        st.line_chart(chart_data_line)

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
        ], color='#28a745', open_all=True, return_index=False)
        
        if st.sidebar.button("Logout"):
            st.session_state["authentication_status"] = False
            st.session_state["username"] = None
            st.rerun()

    # Roteamento de páginas
    page_map = {
        'Página Inicial': home_page,
        'Aprovação': confirmation_queue_page,
        'Agenda do Dia': daily_schedule_page,
        'Gestão': management_page,
        'Confirmação': confirmation_page,
        'Pacientes': patients_page,
        'Relatórios': reports_page
    }
    page_function = page_map.get(selected_page, home_page)
    page_function()
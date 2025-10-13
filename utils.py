# utils.py
import streamlit as st
import streamlit_antd_components as sac
from datetime import date, timedelta
import pandas as pd
from dateutil.relativedelta import relativedelta
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import time
from datetime import datetime
import requests

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
            
            if st.form_submit_button("Entrar", width='stretch'):
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

# --- FUNÇÃO HELPER PARA SUMMARY CARDS ---
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
    """
    Retorna uma lista expandida de agendamentos fictícios para a fila de aprovação,
    conectando-se com os dados da página 'Agenda do Dia'.
    """
    today = date.today()
    
    # Dicionário para traduzir os dias da semana para português
    dias_semana = {
        0: "segunda-feira", 1: "terça-feira", 2: "quarta-feira", 
        3: "quinta-feira", 4: "sexta-feira", 5: "sábado", 6: "domingo"
    }
    meses = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
        7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
    }

    # Função auxiliar para formatar a data de forma amigável
    def format_date(d):
        dia_semana = dias_semana[d.weekday()]
        return f"{dia_semana}, {d.day} de {meses[d.month]} de {d.year}"

    return [
        # --- 3 Exemplos para a aba "Carteirinha" ---
        {
            "name": "Letícia Barros de Souza", "initials": "LB", "phone": "(31) 98765-4321", 
            "specialty": "Cardiologia", "date": format_date(today + timedelta(days=3)), "time": "14:30", 
            "professional": "Dr. Lucas Martins", "insurance": "SulAmérica", 
            "card_number": "2 345 678901 23-4", "event": "Check-up Anual", 
            "notes": "Paciente solicitou reagendamento da semana passada. Verificar histórico de pressão arterial.",
            "type": "Carteirinha"
        },
        {
            "name": "Pedro Lima Santos", "initials": "PL", "phone": "(11) 96543-2109", 
            "specialty": "Nutrição", "date": format_date(today - timedelta(days=22)), "time": "16:00", 
            "professional": "Dr. Roberto Lima", "insurance": "NotreDame Intermédica", 
            "card_number": "4 567 890123 45-6", "event": "Consulta de Acompanhamento", 
            "notes": "Paciente em processo de reeducação alimentar. Apresentar diário alimentar.",
            "type": "Carteirinha"
        },
        {
            "name": "Marcos Aurélio Bastos", "initials": "MA", "phone": "(61) 98234-5678", 
            "specialty": "Fisioterapia", "date": format_date(today + timedelta(days=2)), "time": "08:00", 
            "professional": "Dra. Ana Costa", "insurance": "Unimed", 
            "card_number": "5 678 901234 56-7", "event": "Sessão de Reabilitação", 
            "notes": "Paciente em reabilitação de cirurgia no ombro. 5ª sessão de 10.",
            "type": "Carteirinha"
        },

        # --- 4 Exemplos para a aba "Agendamento" ---
        {
            "name": "Ricardo Gomes Alves", "initials": "RG", "phone": "(81) 99876-5432", 
            "specialty": "Ortopedia", "date": format_date(today), "time": "09:00", 
            "professional": "Dr. Carlos Mendes", "insurance": "Amil", 
            "card_number": "1 234 567890 12-3", "event": "Primeira Consulta", 
            "notes": "Paciente encaminhado com suspeita de lesão no menisco. Trazer exames anteriores.",
            "type": "Agendamento"
        },
        {
            "name": "Patrícia Moreira Lima", "initials": "PM", "phone": "(21) 97654-3210", 
            "specialty": "Ortopedia", "date": format_date(today + timedelta(days=8)), "time": "11:00", 
            "professional": "Dr. Carlos Mendes", "insurance": "Bradesco Saúde", 
            "card_number": "3 456 789012 34-5", "event": "Retorno", 
            "notes": "Retorno para avaliação de fisioterapia pós-fratura no tornozelo.",
            "type": "Agendamento"
        },
        {
            "name": "Vanessa Ribeiro Costa", "initials": "VR", "phone": "(48) 99123-4567", 
            "specialty": "Psicologia", "date": format_date(today + timedelta(days=1)), "time": "10:30", 
            "professional": "Dra. Sofia Almeida", "insurance": "Particular", 
            "card_number": "N/A", "event": "Sessão de Terapia", 
            "notes": "Primeira sessão. Foco em ansiedade e estresse no trabalho.",
            "type": "Agendamento"
        },
        {
            "name": "Cláudia Ohana Dias", "initials": "CO", "phone": "(71) 99988-7766", 
            "specialty": "Cardiologia", "date": format_date(today + timedelta(days=5)), "time": "15:00", 
            "professional": "Dr. Lucas Martins", "insurance": "CASSI", 
            "card_number": "6 789 012345 67-8", "event": "Exame (MAPA)", 
            "notes": "Paciente precisa de instruções pré-exame. Entrar em contato para confirmar o recebimento das orientações.",
            "type": "Agendamento"
        }
    ]

# --- [NOVO] Função para exibir a mensagem de conclusão da CARTEIRINHA ---
def display_carteirinha_completion_message():
    """Exibe a mensagem de conclusão específica para a fila de Carteirinha."""
    st.markdown("""
    <div class="completion-container">
        <div class="completion-icon">✓</div>
        <h2 class="completion-title">Parabéns!</h2>
        <p class="completion-subtitle">Você completou todas as confirmações pendentes referente a carteirinha.</p>
    </div>
    """, unsafe_allow_html=True)

# --- [MODIFICADO] Função para exibir a mensagem de conclusão do AGENDAMENTO (com botão de reset) ---
def display_agendamento_completion_message():
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
        if st.button("Reiniciar Todas as Filas", width='stretch', key="reset_queues"):
            # Reinicializa todas as variáveis de estado das filas
            all_apps = get_sample_appointments()
            st.session_state.carteirinha_appointments = [app for app in all_apps if app.get('type') == 'Carteirinha']
            st.session_state.agendamento_appointments = [app for app in all_apps if app.get('type') == 'Agendamento']
            st.session_state.carteirinha_pending = len(st.session_state.carteirinha_appointments)
            st.session_state.agendamento_pending = len(st.session_state.agendamento_appointments)
            st.session_state.carteirinha_index = 0
            st.session_state.agendamento_index = 0
            st.rerun()

# --- DADOS E FUNÇÕES PARA A PÁGINA DE AGENDA DO DIA ---
def get_daily_agenda_for_dataframe():
    """Retorna dados fictícios para a tabela da agenda com mais variedade e datas dinâmicas."""
    today = date.today()
    # Função auxiliar para criar datas relativas ao dia de hoje
    def d(days_offset):
        return (today + timedelta(days=days_offset)).strftime('%Y-%m-%d')

    return [
        # --- Agendamentos para a semana atual ---
        {"name": "Juliana Martins", "scheduled_date": d(0), "professional": "Dra. Ana Costa", "category": "Fisioterapia", "status": "Confirmado"},
        {"name": "Ricardo Gomes", "scheduled_date": d(0), "professional": "Dr. Carlos Mendes", "category": "Ortopedia", "status": "Pendente"},
        {"name": "Fernanda Lima", "scheduled_date": d(1), "professional": "Dr. Roberto Lima", "category": "Nutrição", "status": "Confirmado"},
        {"name": "Bruno Azevedo", "scheduled_date": d(2), "professional": "Dra. Sofia Almeida", "category": "Psicologia", "status": "Confirmado"},
        {"name": "Letícia Barros", "scheduled_date": d(3), "professional": "Dr. Lucas Martins", "category": "Cardiologia", "status": "Reagendando"},
        {"name": "Vinicius Moraes", "scheduled_date": d(-1), "professional": "Dra. Ana Costa", "category": "Fisioterapia", "status": "Confirmado"},
        {"name": "Camila Rocha", "scheduled_date": d(-2), "professional": "Dr. Carlos Mendes", "category": "Ortopedia", "status": "Cancelado"},

        # --- Agendamentos de semanas anteriores ---
        {"name": "Daniela Vieira", "scheduled_date": d(-7), "professional": "Dra. Sofia Almeida", "category": "Psicologia", "status": "Confirmado"},
        {"name": "Gustavo Pereira", "scheduled_date": d(-10), "professional": "Dr. Lucas Martins", "category": "Cardiologia", "status": "Confirmado"},
        {"name": "Amanda Nunes", "scheduled_date": d(-12), "professional": "Dr. Roberto Lima", "category": "Nutrição", "status": "Cancelado"},
        {"name": "Felipe Arruda", "scheduled_date": d(-15), "professional": "Dra. Ana Costa", "category": "Fisioterapia", "status": "Confirmado"},

        # --- Agendamentos de semanas futuras ---
        {"name": "Patrícia Moreira", "scheduled_date": d(8), "professional": "Dr. Carlos Mendes", "category": "Ortopedia", "status": "Pendente"},
        {"name": "Thiago Brandão", "scheduled_date": d(11), "professional": "Dr. Roberto Lima", "category": "Nutrição", "status": "Confirmado"},
        {"name": "Larissa Farias", "scheduled_date": d(14), "professional": "Dra. Sofia Almeida", "category": "Psicologia", "status": "Confirmado"},
        {"name": "Eduardo Costa", "scheduled_date": d(20), "professional": "Dr. Lucas Martins", "category": "Cardiologia", "status": "Confirmado"},

        # --- Dados originais com datas ajustadas para o passado ---
        {"name": "Maria Silva Santos", "scheduled_date": d(-30), "professional": "Dr. Carlos Mendes", "category": "Ortopedia", "status": "Confirmado"},
        {"name": "João Carlos Oliveira", "scheduled_date": d(-29), "professional": "Dra. Ana Costa", "category": "Fisioterapia", "status": "Confirmado"},
        {"name": "Ana Paula Costa", "scheduled_date": d(-28), "professional": "Dr. Carlos Mendes", "category": "Ortopedia", "status": "Cancelado"},
        {"name": "Pedro Lima Santos", "scheduled_date": d(-22), "professional": "Dr. Roberto Lima", "category": "Nutrição", "status": "Reagendando"},
        {"name": "Carla Ferreira", "scheduled_date": d(-45), "professional": "Dra. Ana Costa", "category": "Fisioterapia", "status": "Confirmado"},
        {"name": "Roberto Silva", "scheduled_date": d(-40), "professional": "Dr. Roberto Lima", "category": "Nutrição", "status": "Confirmado"},
        {"name": "Beatriz Oliveira", "scheduled_date": d(-60), "professional": "Dr. Carlos Mendes", "category": "Ortopedia", "status": "Confirmado"},
        {"name": "Gabriel Santos", "scheduled_date": d(-50), "professional": "Dra. Ana Costa", "category": "Fisioterapia", "status": "Cancelado"},
    ]

# --- Função para calcular o intervalo de datas ---
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


# --- FUNÇÃO DEDICADA PARA BUSCAR METADADOS DO BANCO DE DADOS ---
def fetch_metadata_from_db(supabase_client):
    """
    Busca os metadados dos PDFs da tabela 'pdf_metadata' e retorna um DataFrame.
    """
    try:
        response = supabase_client.table('pdf_metadata').select(
            'id, created_at, data_upload, nome_arquivo, info_extraida'
        ).order('created_at', desc=True).execute()
        
        data = response.data
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df = df.rename(columns={'data_upload': 'upload_date', 'nome_arquivo': 'file_name', 'info_extraida': 'extracted'})
        return df

    except Exception as e:
        st.error(f"Não foi possível buscar os metadados do banco de dados: {e}")
        return pd.DataFrame()


def get_daily_agenda_from_baserow(api_key):
    """
    Busca TODOS os dados da agenda da API do Baserow, incluindo a coluna 'Status do Agendamento'.
    """
    if not api_key:
        st.error("A chave da API do Baserow (BASEROW_KEY) não foi configurada nos segredos do ambiente.")
        return pd.DataFrame()

    url = "https://api.baserow.io/api/database/rows/table/681080/?user_field_names=true&size=200"
    headers = {"Authorization": f"Token {api_key}"}
    all_rows = []

    try:
        while url:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            all_rows.extend(data.get('results', []))
            url = data.get('next')

        if not all_rows:
            st.warning("Nenhum dado de agendamento foi encontrado na tabela do Baserow.")
            return pd.DataFrame()

        df = pd.DataFrame(all_rows)

        # --- [MODIFICADO] Adicionada a coluna 'Status do Agendamento' ---
        expected_baserow_columns = [
            'Data do Agendamento', 'Horário', 'Nome do Paciente', 'Convênio', 
            'Evento', 'Profissional', 'Especialidade', 'Status do Agendamento'
        ]
        
        for col in expected_baserow_columns:
            if col not in df.columns:
                st.error(f"Erro Crítico: A coluna '{col}' não foi encontrada na sua tabela do Baserow. Verifique se o nome da coluna está exatamente correto.")
                return pd.DataFrame()

        # --- [MODIFICADO] Mapeamento da nova coluna para 'status' ---
        column_mapping = {
            'Data do Agendamento': 'scheduled_date',
            'Horário': 'time',
            'Nome do Paciente': 'name',
            'Convênio': 'insurance',
            'Evento': 'event', 
            'Profissional': 'professional',
            'Especialidade': 'category',
            'Status do Agendamento': 'status' # Mapeia a coluna do Baserow para a coluna 'status' do DataFrame
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # Remove a linha que definia um status padrão, pois agora ele vem do Baserow
        # df['status'] = 'Pendente' 
        
        df['scheduled_date'] = pd.to_datetime(df['scheduled_date'], dayfirst=True, errors='coerce')
        df.dropna(subset=['scheduled_date'], inplace=True)

        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao conectar com a API do Baserow: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao processar os dados do Baserow: {e}")
        return pd.DataFrame()

# --- Função para limpar todos os filtros ---
def clear_filters_callback():
    """Função de callback para limpar todos os filtros."""
    st.session_state.view_mode = "Todo o período"
    st.session_state.selected_date = date.today() # Modificado para usar a data atual
    st.session_state.prof_filter = "Todos"
    st.session_state.cat_filter = "Todos"
    st.session_state.status_filter = "Todos"
    st.session_state.patient_filter = "Todos"    # Adicionado para limpar o filtro de paciente
    st.session_state.insurance_filter = "Todos"  # Adicionado para limpar o filtro de convênio
    st.session_state.event_filter = "Todos"      # Adicionado para limpar o filtro de evento
    st.session_state.search_term = ""

# --- PÁGINAS ---
# --- PÁGINA DA AGENDA DO DIA ---
def daily_schedule_page():
    """Exibe a agenda do dia com filtros e funcionalidade de upload para o Supabase, utilizando o status real do Baserow."""
    
    if 'countdown_active' not in st.session_state:
        st.session_state.countdown_active = False
    if 'countdown_timer' not in st.session_state:
        st.session_state.countdown_timer = 0
    if 'extraction_status' not in st.session_state:
        st.session_state.extraction_status = {}

    load_dotenv()
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        BASEROW_KEY = os.getenv("BASEROW_KEY")
        if not supabase_url or not supabase_key:
            st.error("As credenciais do Supabase não foram encontradas.")
            st.stop()
        supabase: Client = create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error(f"Ocorreu um erro ao inicializar a conexão com o Supabase: {e}")
        st.stop()

    if 'files_df' not in st.session_state:
        with st.spinner("Buscando metadados dos arquivos..."):
            st.session_state.files_df = fetch_metadata_from_db(supabase)

    st.subheader("Filtros")
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "Semana"
        st.session_state.selected_date = date.today()
        st.session_state.prof_filter = "Todos"
        st.session_state.cat_filter = "Todos"
        st.session_state.status_filter = "Todos"
        st.session_state.search_term = ""
        st.session_state.patient_filter = "Todos"
        st.session_state.insurance_filter = "Todos"
        st.session_state.event_filter = "Todos"
    
    df = get_daily_agenda_from_baserow(BASEROW_KEY)

    if df.empty:
        st.warning("Não foi possível carregar os dados da agenda para aplicar os filtros.")
    else:
        df['scheduled_date'] = df['scheduled_date'].dt.date

        with st.container(border=False):
            col1, col2 = st.columns([3, 2])
            col1.radio("Visualização:", ["Dia", "Semana", "Mês", "Trimestre", "Todo o período"], horizontal=True, key="view_mode", index=4)
            col2.date_input("Data:", key="selected_date", disabled=(st.session_state.view_mode == "Todo o período"))
            
            f_col1, f_col2, f_col3, f_col4, f_col5, f_col6 = st.columns(6)
            f_col1.selectbox("Profissionais", ["Todos"] + sorted(df['professional'].unique().tolist()), key="prof_filter")
            f_col2.selectbox("Categorias", ["Todos"] + sorted(df['category'].unique().tolist()), key="cat_filter")
            
            # --- [MODIFICADO] O filtro de status agora é populado com os valores reais do Baserow ---
            status_options = ["Todos"] + sorted(df['status'].unique().tolist())
            f_col3.selectbox("Status", status_options, key="status_filter")
            
            f_col4.selectbox("Pacientes", ["Todos"] + sorted(df['name'].unique().tolist()), key="patient_filter")
            f_col5.selectbox("Convênios", ["Todos"] + sorted(df['insurance'].unique().tolist()), key="insurance_filter")
            f_col6.selectbox("Eventos", ["Todos"] + sorted(df['event'].unique().tolist()), key="event_filter")

            search_col, btn_col = st.columns([4, 1.08])
            search_col.text_input("Buscar paciente...", placeholder="Buscar paciente...", label_visibility="collapsed", key="search_term")
            btn_col.button("Limpar Filtros", width='stretch', on_click=clear_filters_callback)
        
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
        if st.session_state.patient_filter != "Todos":
            filtered_df = filtered_df[filtered_df['name'] == st.session_state.patient_filter]
        if st.session_state.insurance_filter != "Todos":
            filtered_df = filtered_df[filtered_df['insurance'] == st.session_state.insurance_filter]
        if st.session_state.event_filter != "Todos":
            filtered_df = filtered_df[filtered_df['event'] == st.session_state.event_filter]
        if st.session_state.search_term:
            filtered_df = filtered_df[filtered_df['name'].str.contains(st.session_state.search_term, case=False, na=False)]
        
        if st.session_state.view_mode == "Dia":
            st.header(f"Agendamentos para {st.session_state.selected_date.strftime('%d/%m/%Y')}")
        elif st.session_state.view_mode == "Todo o período":
            st.header("Exibindo todos os agendamentos")
        else:
            st.header(f"Agendamentos de {start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}")
        
        # As contagens agora refletem os status reais vindos do Baserow
        total_agendamentos = len(filtered_df)
        confirmados = len(filtered_df[filtered_df['status'] == 'Confirmado'])
        pendentes = len(filtered_df[filtered_df['status'] == 'Pendente'])
        reagendados = len(filtered_df[filtered_df['status'] == 'Reagendado'])
        cancelados = len(filtered_df[filtered_df['status'] == 'Cancelado'])
        
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 20px; font-size: 1.1rem; margin-bottom: 15px;">
                <span><i class="bi bi-people-fill"></i> <b>{total_agendamentos}</b> agendamentos</span>
                <span style="color: #28a745;"><b>{confirmados}</b> confirmados</span>
                <span style="color: darkorange;"><b>{pendentes}</b> pendentes</span>
                <span style="color: #007bff;"><b>{reagendados}</b> reagendados</span>
                <span style="color: #6c757d;"><b>{cancelados}</b> cancelados</span>
            </div>
        """, unsafe_allow_html=True)
        
        display_df = filtered_df.copy()
        display_df['scheduled_date'] = pd.to_datetime(display_df['scheduled_date']).dt.strftime('%d/%m/%Y')
        display_columns_order = ['scheduled_date', 'time', 'name', 'insurance', 'event', 'status']
        display_df = display_df[display_columns_order]
        display_df.rename(columns={
            'scheduled_date': 'Data Agendada',
            'time': 'Horário',
            'name': 'Paciente',
            'insurance': 'Convênio',
            'event': 'Evento',
            'status': 'Status'
        }, inplace=True)

        st.markdown('<div class="agenda-table-container">', unsafe_allow_html=True)
        st.dataframe(display_df, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # --- LÓGICA DE UPLOAD PARA O SUPABASE (STORAGE + DATABASE) ---
    if not st.session_state.countdown_active:
        uploaded_files = st.file_uploader(
            "Arraste e solte os arquivos aqui",
            type="pdf",
            accept_multiple_files=True
        )

        if uploaded_files:
            any_success = False
            for uploaded_file in uploaded_files:
                file_name_with_date = f"{date.today().strftime('%Y-%m-%d')}_{uploaded_file.name}"
                file_path_in_bucket = f"pdfs-agendamento/{file_name_with_date}"
                
                try:
                    with st.spinner(f'Enviando "{uploaded_file.name}" para o Storage...'):
                        supabase.storage.from_("cofrat").upload(
                            path=file_path_in_bucket,
                            file=uploaded_file.getvalue(),
                            file_options={"content-type": "application/pdf"}
                        )
                    
                    with st.spinner(f'Registrando "{uploaded_file.name}" no banco de dados...'):
                        supabase.table('pdf_metadata').insert({
                            'data_upload': date.today().isoformat(),
                            'nome_arquivo': file_name_with_date,
                            'info_extraida': 'Não'
                        }).execute()

                    st.success(f'✅ Arquivo "{uploaded_file.name}" processado com sucesso!')
                    any_success = True

                except Exception as e:
                    if "Duplicate" in str(e):
                         st.warning(f'⚠️ O arquivo "{uploaded_file.name}" já existe no storage ou no banco de dados.')
                         any_success = True
                    else:
                        st.error(f'❌ Ocorreu um erro no processo de upload: {e}')

            if any_success:
                st.session_state.countdown_active = True
                st.session_state.countdown_timer = 5
                st.rerun()

    # --- BLOCO DO CONTADOR (DELAY) ---
    if st.session_state.countdown_active:
        timer = st.session_state.countdown_timer

        if timer > 0:
            countdown_placeholder = st.empty()
            with countdown_placeholder.container():
                st.info(f"🔄 Processamento concluído. Atualizando a lista em {timer} segundos...")

            time.sleep(1)
            st.session_state.countdown_timer -= 1
            st.rerun()

        else:
            st.session_state.countdown_active = False
            with st.spinner("Atualizando lista de arquivos..."):
                st.session_state.files_df = fetch_metadata_from_db(supabase)
            st.rerun()

    # --- LISTA DE STATUS DE UPLOAD (LENDO DO DATAFRAME DO DB) ---
    st.write("---")
    
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.subheader("Status da Extração de Arquivos")
    with col_header2:
        is_any_extraction_pending = any(status == 'pending' for status in st.session_state.extraction_status.values())
        if st.button("🔄 Atualizar Lista", use_container_width=True):
            with st.spinner("Buscando metadados dos arquivos..."):
                st.session_state.files_df = fetch_metadata_from_db(supabase)
                for file_id, status in list(st.session_state.extraction_status.items()):
                    if status == 'pending':
                        if not st.session_state.files_df[st.session_state.files_df['id'] == file_id].empty and \
                           st.session_state.files_df[st.session_state.files_df['id'] == file_id]['extracted'].iloc[0] == 'Sim':
                            del st.session_state.extraction_status[file_id]
            st.rerun()

    files_df = st.session_state.files_df
    if files_df.empty:
        st.info("Nenhum metadado de arquivo encontrado no banco de dados.")
    else:
        # --- [LAYOUT MELHORADO] ---
        with st.container(border=True):
            # Cabeçalho da "tabela"
            header_cols = st.columns([2, 4, 2, 3])
            header_cols[0].markdown("**Data de upload**")
            header_cols[1].markdown("**Nome do arquivo**")
            header_cols[2].markdown("**Info Extraída**")
            header_cols[3].markdown("<div style='text-align: center;'><b>Ações</b></div>", unsafe_allow_html=True)

            # Linhas da "tabela"
            for index, row in files_df.iterrows():
                st.divider() # Adiciona uma linha divisória entre os registros
                col1, col2, col3, col4 = st.columns([2, 4, 2, 3])
                
                col1.write(datetime.strptime(row['upload_date'], '%Y-%m-%d').strftime('%d/%m/%Y'))
                col2.write(row['file_name'])
                
                current_extraction_status = st.session_state.extraction_status.get(row['id'], None)

                if current_extraction_status == 'pending':
                    col3.markdown("<span style='color: darkorange;'>Extraindo... <i class='bi bi-hourglass-split'></i></span>", unsafe_allow_html=True)
                elif row['extracted'] == 'Sim':
                    col3.markdown("<span style='color: green;'>Sim</span>", unsafe_allow_html=True)
                else:
                    col3.markdown("<span style='color: darkorange;'>Não</span>", unsafe_allow_html=True)
                
                with col4:
                    btn_cols = st.columns(2)
                    is_disabled = st.session_state.countdown_active or current_extraction_status == 'pending'

                    if row['extracted'] != 'Sim' and current_extraction_status != 'pending':
                        if btn_cols[0].button("Extrair", key=f"extract_{row['id']}", use_container_width=True, disabled=is_disabled):
                            WEBHOOK_URL = "https://webhook.erudieto.com.br/webhook/cofrat-pdf"
                            payload = {'fileName': row['file_name'], 'fileId': row['id']}
                            
                            st.session_state.extraction_status[row['id']] = 'pending'
                            
                            with st.spinner(f"Acionando automação para '{row['file_name']}'..."):
                                try:
                                    response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
                                    
                                    if response.status_code in [200, 202]:
                                        st.success(f"Extração para '{row['file_name']}' iniciada. O status será atualizado em breve.")
                                        st.rerun()
                                    else:
                                        st.error(f"Falha ao iniciar extração (código {response.status_code}): {response.text}")
                                        st.session_state.extraction_status[row['id']] = 'failed'
                                        st.rerun()
                                except requests.exceptions.RequestException as e:
                                    st.error(f"Erro de conexão com o webhook: {e}")
                                    st.session_state.extraction_status[row['id']] = 'failed'
                                    st.rerun()
                    elif current_extraction_status == 'pending':
                        btn_cols[0].markdown('<div style="text-align: center; color: darkorange; font-size: 0.85em;">Extraindo...</div>', unsafe_allow_html=True)
                    else:
                        btn_cols[0].button("Extraído", key=f"extracted_disabled_{row['id']}", use_container_width=True, disabled=True)
                    
                    if btn_cols[1].button("🗑️", key=f"delete_{row['id']}", help=f"Deletar {row['file_name']}", use_container_width=True, disabled=is_disabled):
                        st.session_state.file_to_delete = row
                        st.rerun()

    if 'file_to_delete' in st.session_state and st.session_state.file_to_delete is not None:
        file_info = st.session_state.file_to_delete
        
        @st.dialog("Confirmar Deleção")
        def confirm_delete():
            st.warning(f"Você tem certeza que deseja deletar permanentemente o arquivo **{file_info['file_name']}**?")
            st.write("Esta ação removerá o arquivo do armazenamento e seu registro do banco de dados. Não pode ser desfeita.")
            
            if st.button("Sim, deletar agora", type="primary"):
                try:
                    supabase.storage.from_("cofrat").remove([f"pdfs-agendamento/{file_info['file_name']}"])
                    supabase.table('pdf_metadata').delete().eq('id', file_info['id']).execute()
                    
                    st.success("Arquivo deletado com sucesso!")
                    st.session_state.file_to_delete = None
                    st.session_state.files_df = fetch_metadata_from_db(supabase)
                    if file_info['id'] in st.session_state.extraction_status:
                        del st.session_state.extraction_status[file_info['id']]
                    st.rerun()

                except Exception as e:
                    st.error(f"Erro ao deletar o arquivo: {e}")
                    st.session_state.file_to_delete = None
                    st.rerun()

            if st.button("Cancelar"):
                st.session_state.file_to_delete = None
                st.rerun()
        
        confirm_delete()
    
# --- PÁGINA DE GESTÃO ---
def management_page():
    st.write('##### Organize cadastros, especialidades e agendas com eficiência')
    st.write('Esta página permite o cadastro e edição dos médicos, com controle de status (Ativo/Inativo) conforme disponibilidade de agenda. Também é possível gerenciar as modalidades de atendimento — como Fisioterapia, Ortopedia, RPG e outras — e configurar os horários de disponibilidade de cada profissional. Tudo em um só lugar, para garantir uma operação fluida e organizada.')
    st.write('')
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
            st.button("✚ Adicionar Profissional", type="primary", width='stretch')

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
                    btn_cols[0].button("Editar", key=f"edit_{i}", width='stretch')
                    btn_cols[1].button("Desativar", key=f"del_{i}", width='stretch')

    elif selected_tab == 'Modalidades':
        header_cols = st.columns([3, 1])
        with header_cols[0]:
            st.subheader("Modalidades de Atendimento")
        with header_cols[1]:
            st.button("✚ Adicionar Modalidade", type="primary", width='stretch')

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
                    btn_cols[0].button("Editar", key=f"edit_mod_{i}", width='stretch')
                    btn_cols[1].button("🗑️", key=f"del_mod_{i}", width='stretch')

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
                    st.button("Editar", key=f"edit_agenda_{i}", width='stretch', type="primary")
                
                st.write("") # Espaçador

                for day, time, cap in agenda['schedule']:
                    day_cols = st.columns([2, 2, 1])
                    day_cols[0].text(day)
                    day_cols[1].text(time)
                    day_cols[2].button(f"Cap: {cap}", key=f"cap_{i}_{day}", disabled=True, width='stretch')
            st.write("") # Espaço entre os cards

# --- [TOTALMENTE REFEITA] PÁGINA DE CONFIRMAÇÃO DE AGENDAMENTOS ---
def confirmation_queue_page():
    """Exibe as filas de aprovação de forma independente para Carteirinha e Agendamento."""
    st.markdown('<style>div.block-container {padding-top: 1.5rem;}</style>', unsafe_allow_html=True)
    st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">', unsafe_allow_html=True)

    # --- Bloco de inicialização robusto para as filas separadas ---
    if 'carteirinha_appointments' not in st.session_state:
        all_apps = get_sample_appointments()
        st.session_state.carteirinha_appointments = [app for app in all_apps if app.get('type') == 'Carteirinha']
        st.session_state.agendamento_appointments = [app for app in all_apps if app.get('type') == 'Agendamento']
        st.session_state.carteirinha_pending = len(st.session_state.carteirinha_appointments)
        st.session_state.agendamento_pending = len(st.session_state.agendamento_appointments)
        st.session_state.carteirinha_index = 0
        st.session_state.agendamento_index = 0

    if 'approval_view' not in st.session_state:
        st.session_state.approval_view = 'Carteirinha'
    if 'show_approve_dialog' not in st.session_state:
        st.session_state.show_approve_dialog = False
    if 'show_approve_carteirinha_dialog' not in st.session_state:
        st.session_state.show_approve_carteirinha_dialog = False
    if 'show_cancel_dialog' not in st.session_state:
        st.session_state.show_cancel_dialog = False
    if 'show_reschedule_dialog' not in st.session_state:
        st.session_state.show_reschedule_dialog = False

    # --- Função para avançar para o próximo item na fila ATIVA ---
    def go_to_next():
        active_queue = st.session_state.approval_view
        if active_queue == 'Carteirinha' and st.session_state.carteirinha_index < len(st.session_state.carteirinha_appointments):
            st.session_state.carteirinha_pending -= 1
            st.session_state.carteirinha_index += 1
        elif active_queue == 'Agendamento' and st.session_state.agendamento_index < len(st.session_state.agendamento_appointments):
            st.session_state.agendamento_pending -= 1
            st.session_state.agendamento_index += 1
        
        # Fecha todos os diálogos
        st.session_state.show_approve_dialog = False
        st.session_state.show_approve_carteirinha_dialog = False
        st.session_state.show_cancel_dialog = False
        st.session_state.show_reschedule_dialog = False

    # --- [INÍCIO DA CORREÇÃO] ---
    # Determina o índice da aba que deve ser exibida com base no session_state
    # Isso garante que a aba correta permaneça selecionada após um st.rerun()
    tab_options = ['Carteirinha', 'Agendamento']
    try:
        active_tab_index = tab_options.index(st.session_state.approval_view)
    except ValueError:
        active_tab_index = 0 # Padrão para a primeira aba se o estado for inválido
    # --- [FIM DA CORREÇÃO] ---

    # Abas para alternar a visualização
    selected_view_label = sac.segmented(
        items=[
            sac.SegmentedItem(label=f"Carteirinha ({st.session_state.carteirinha_pending})"),
            sac.SegmentedItem(label=f"Agendamento ({st.session_state.agendamento_pending})"),
        ],
        index=active_tab_index,  # <-- [CORREÇÃO APLICADA AQUI] Usa o índice calculado
        return_index=False,
        align='left',
        size='sm',
        color='#28a745'
    )
    # Atualiza o estado da sessão caso o usuário clique em uma nova aba
    st.session_state.approval_view = selected_view_label.split(' ')[0]

    # --- Lógica de Exibição para a Fila de CARTEIRINHA ---
    if st.session_state.approval_view == 'Carteirinha':
        carteirinha_index = st.session_state.carteirinha_index
        carteirinha_appointments = st.session_state.carteirinha_appointments
        
        if carteirinha_index >= len(carteirinha_appointments):
            display_carteirinha_completion_message()
            return
        
        current_appointment = carteirinha_appointments[carteirinha_index]
        
        # Barra de progresso da Carteirinha
        st.write("Progresso da Carteirinha")
        st.progress((carteirinha_index + 1) / len(carteirinha_appointments))
        st.markdown(f"<p class='progress-label'>{carteirinha_index + 1} de {len(carteirinha_appointments)}</p>", unsafe_allow_html=True)

        # Card da Carteirinha
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
            </div>
            <div class="details-grid">
                <div class="detail-item"><i class="bi bi-person"></i><div><div class="detail-label">Profissional</div><div class="detail-value">{current_appointment['professional']}</div></div></div>
                <div class="detail-item"><i class="bi bi-hospital"></i><div><div class="detail-label">Convênio</div><div class="detail-value">{current_appointment['insurance']}</div></div></div>
                <div class="detail-item"><i class="bi bi-credit-card-2-front"></i><div><div class="detail-label">Carteirinha</div><div class="detail-value">{current_appointment['card_number']}</div></div></div>
                <div class="detail-item"><i class="bi bi-tag"></i><div><div class="detail-label">Modalidade</div><div class="detail-value">{current_appointment['specialty']}</div></div></div>
            </div>
            <div class="observations-section">
                <div class="detail-label">Observações</div>
                <div class="detail-value">{current_appointment['notes']}</div>
            </div>
        </div>
        """
        st.markdown(approval_card_html, unsafe_allow_html=True)

        # Botões de ação da Carteirinha
        st.markdown('<div class="action-buttons-container">', unsafe_allow_html=True)
        cols = st.columns(2)
        if cols[0].button("✓ Aprovar início de agendamento", width='stretch'):
            st.session_state.show_approve_carteirinha_dialog = True
            st.rerun()
        if cols[1].button("✕ Cancelar", width='stretch'):
            st.session_state.show_cancel_dialog = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Lógica de Exibição para a Fila de AGENDAMENTO ---
    elif st.session_state.approval_view == 'Agendamento':
        agendamento_index = st.session_state.agendamento_index
        agendamento_appointments = st.session_state.agendamento_appointments

        if agendamento_index >= len(agendamento_appointments):
            display_agendamento_completion_message()
            return

        current_appointment = agendamento_appointments[agendamento_index]

        # Barra de progresso do Agendamento
        st.write("Progresso do Agendamento")
        st.progress((agendamento_index + 1) / len(agendamento_appointments))
        st.markdown(f"<p class='progress-label'>{agendamento_index + 1} de {len(agendamento_appointments)}</p>", unsafe_allow_html=True)

        # Card de aprovação completo
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
            </div>
            <div class="details-grid">
                <div class="detail-item"><i class="bi bi-calendar-event"></i><div><div class="detail-label">Data</div><div class="detail-value">{current_appointment['date']}</div></div></div>
                <div class="detail-item"><i class="bi bi-person"></i><div><div class="detail-label">Profissional</div><div class="detail-value">{current_appointment['professional']}</div></div></div>
                <div class="detail-item"><i class="bi bi-clock"></i><div><div class="detail-label">Horário</div><div class="detail-value">{current_appointment['time']}</div></div></div>
                <div class="detail-item"><i class="bi bi-hospital"></i><div><div class="detail-label">Convênio</div><div class="detail-value">{current_appointment['insurance']}</div></div></div>
                <div class="detail-item"><i class="bi bi-credit-card-2-front"></i><div><div class="detail-label">Carteirinha</div><div class="detail-value">{current_appointment['card_number']}</div></div></div>
                <div class="detail-item"><i class="bi bi-tag"></i><div><div class="detail-label">Modalidade</div><div class="detail-value">{current_appointment['specialty']}</div></div></div>
            </div>
            <div class="observations-section">
                <div class="detail-label">Observações</div>
                <div class="detail-value">{current_appointment['notes']}</div>
            </div>
        </div>
        """
        st.markdown(approval_card_html, unsafe_allow_html=True)

        # Botões de ação do Agendamento
        st.markdown('<div class="action-buttons-container">', unsafe_allow_html=True)
        cols = st.columns(3)
        if cols[0].button("✓ Aprovar", width='stretch'):
            st.session_state.show_approve_dialog = True
            st.rerun()
        if cols[1].button("↻ Reagendar", width='stretch'):
            st.session_state.show_reschedule_dialog = True
            st.rerun()
        if cols[2].button("✕ Cancelar", width='stretch'):
            st.session_state.show_cancel_dialog = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Diálogos (Modificados para obter o current_appointment correto) ---
    # Determina qual é o agendamento atual com base na view ativa para os diálogos
    active_view = st.session_state.approval_view
    if active_view == 'Carteirinha' and st.session_state.carteirinha_index < len(st.session_state.carteirinha_appointments):
        current_appointment_for_dialog = st.session_state.carteirinha_appointments[st.session_state.carteirinha_index]
    elif active_view == 'Agendamento' and st.session_state.agendamento_index < len(st.session_state.agendamento_appointments):
        current_appointment_for_dialog = st.session_state.agendamento_appointments[st.session_state.agendamento_index]
    else:
        current_appointment_for_dialog = None # Fila vazia, nenhum diálogo será mostrado

    if current_appointment_for_dialog:
        @st.dialog("Confirmar Aprovação")
        def approve_dialog():
            st.warning(f"Tem certeza que deseja aprovar o agendamento de **{current_appointment_for_dialog['name']}**?")
            st.write("---")
            st.radio("Acionar Julia?", ["Sim", "Não"], index=0, horizontal=True, key="acionar_julia_approve")
            st.write("")
            
            if st.button("Sim, Aprovar", width='stretch'):
                st.toast(f"{current_appointment_for_dialog['name']} aprovado(a)!", icon="✅")
                go_to_next()
                st.rerun()
            if st.button("Voltar", width='stretch'):
                st.session_state.show_approve_dialog = False
                st.rerun()

        if st.session_state.show_approve_dialog:
            approve_dialog()

        @st.dialog("Confirmar Início de Agendamento")
        def approve_carteirinha_dialog():
            st.warning(f"Tem certeza que deseja aprovar o início do agendamento para **{current_appointment_for_dialog['name']}**?")
            st.write("---")
            st.radio("Acionar Julia?", ["Sim", "Não"], index=0, horizontal=True, key="acionar_julia_carteirinha")
            st.write("")

            if st.button("Sim, Aprovar Início", width='stretch'):
                st.toast(f"Início de agendamento para {current_appointment_for_dialog['name']} aprovado!", icon="✅")
                go_to_next()
                st.rerun()
            if st.button("Voltar", width='stretch'):
                st.session_state.show_approve_carteirinha_dialog = False
                st.rerun()

        if st.session_state.show_approve_carteirinha_dialog:
            approve_carteirinha_dialog()

        @st.dialog("Confirmar Cancelamento")
        def cancel_dialog():
            st.warning(f"Tem certeza que deseja cancelar o agendamento de **{current_appointment_for_dialog['name']}**?")
            motivo = st.selectbox(
                "Selecione o motivo do cancelamento:",
                ["Convênio não aprovado", "Paciente desistiu", "Profissional indisponível", "Erro no agendamento", "Outro motivo"]
            )
            st.write("")
            st.radio("Acionar Julia?", ["Sim", "Não"], index=0, horizontal=True, key="acionar_julia_cancel")
            st.write("")

            if st.button("Sim, Cancelar", width='stretch'):
                st.toast(f"{current_appointment_for_dialog['name']} cancelado(a). Motivo: {motivo}", icon="🗑️")
                go_to_next()
                st.rerun()
            if st.button("Voltar", width='stretch'):
                st.session_state.show_cancel_dialog = False
                st.rerun()

        if st.session_state.show_cancel_dialog:
            cancel_dialog()

        @st.dialog("Reagendar Consulta")
        def reschedule_dialog():
            st.markdown(f"**Paciente:** {current_appointment_for_dialog['name']}")
            st.markdown(f"**Agendamento atual:** {current_appointment_for_dialog['date'].split(', ')[1]} às {current_appointment_for_dialog['time']}")
            new_date = st.date_input("Nova Data")
            new_time = st.time_input("Novo Horário", step=1800)
            st.text_area("Mensagem para o Paciente (Opcional)")
            st.write("---")
            st.radio("Acionar Julia?", ["Sim", "Não"], index=0, horizontal=True, key="acionar_julia_reschedule")
            st.write("")

            if st.button("Enviar Sugestão", width='stretch'):
                st.toast("Sugestão de reagendamento enviada!", icon="👍")
                go_to_next()
                st.rerun()
            if st.button("Cancelar", width='stretch'):
                st.session_state.show_reschedule_dialog = False
                st.rerun()

        if st.session_state.show_reschedule_dialog:
            reschedule_dialog()

# --- [AJUSTADA] PÁGINA DE CONFIRMAÇÃO DE AGENDAMENTOS ---
def confirmation_page():
    """
    Exibe a página de confirmação em massa com filtros avançados, resumo de dados e preview corrigido.
    """
    st.write('##### Comunicação em massa para agendamentos')
    st.write('Esta página permite confirmar ou cancelar agendamentos em massa. Use os filtros para selecionar um período e refinar a lista de pacientes antes de enviar as comunicações.')
    st.write('')

    # --- CONEXÃO COM BASEROW E BUSCA DE DADOS ---
    def get_confirmation_data_from_baserow(api_key):
        if not api_key:
            st.error("A chave da API do Baserow (BASEROW_KEY) não foi configurada.")
            return pd.DataFrame()

        url = "https://api.baserow.io/api/database/rows/table/681080/?user_field_names=true&size=200"
        headers = {"Authorization": f"Token {api_key}"}
        all_rows = []

        try:
            while url:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                all_rows.extend(data.get('results', []))
                url = data.get('next')

            if not all_rows:
                return pd.DataFrame()

            df = pd.DataFrame(all_rows)
            
            expected_columns = [
                'Data do Agendamento', 'Horário', 'Nome do Paciente', 'Convênio', 
                'Evento', 'Profissional', 'Especialidade', 'Telefone', 'Status do Agendamento'
            ]
            for col in expected_columns:
                if col not in df.columns:
                    st.error(f"Erro Crítico: A coluna '{col}' não foi encontrada na sua tabela do Baserow.")
                    return pd.DataFrame()

            column_mapping = {
                'Data do Agendamento': 'scheduled_date', 'Horário': 'time',
                'Nome do Paciente': 'name', 'Convênio': 'insurance',
                'Evento': 'event', 'Profissional': 'professional',
                'Especialidade': 'category', 'Telefone': 'phone',
                'Status do Agendamento': 'status'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            df['scheduled_date'] = pd.to_datetime(df['scheduled_date'], dayfirst=True, errors='coerce').dt.date
            df.dropna(subset=['scheduled_date'], inplace=True)
            return df

        except Exception as e:
            st.error(f"Ocorreu um erro ao buscar os dados do Baserow: {e}")
            return pd.DataFrame()

    load_dotenv()
    BASEROW_KEY = os.getenv("BASEROW_KEY")
    df = get_confirmation_data_from_baserow(BASEROW_KEY)

    # --- INICIALIZAÇÃO DO SESSION STATE ---
    if 'conf_start_date' not in st.session_state:
        st.session_state.conf_start_date = date.today()
        st.session_state.conf_end_date = date.today() + timedelta(days=7)
        st.session_state.conf_prof_filter = "Todos"
        st.session_state.conf_cat_filter = "Todos"
        st.session_state.conf_status_filter = "Todos"
        st.session_state.conf_patient_filter = "Todos"
        st.session_state.conf_insurance_filter = "Todos"
        st.session_state.conf_event_filter = "Todos"
        st.session_state.show_preview_dialog = False

    # --- LÓGICA DE FILTRAGEM (executada antes para que filtered_df esteja disponível para o dialog) ---
    filtered_df = df.copy()
    if not df.empty:
        if st.session_state.conf_start_date > st.session_state.conf_end_date:
            st.error("A data inicial não pode ser posterior à data final.")
            # Evita que o dataframe filtrado fique vazio indevidamente
            filtered_df = pd.DataFrame() 
        else:
            filtered_df = filtered_df[(filtered_df['scheduled_date'] >= st.session_state.conf_start_date) & (filtered_df['scheduled_date'] <= st.session_state.conf_end_date)]
            if st.session_state.conf_prof_filter != "Todos": filtered_df = filtered_df[filtered_df['professional'] == st.session_state.conf_prof_filter]
            if st.session_state.conf_cat_filter != "Todos": filtered_df = filtered_df[filtered_df['category'] == st.session_state.conf_cat_filter]
            if st.session_state.conf_status_filter != "Todos": filtered_df = filtered_df[filtered_df['status'] == st.session_state.conf_status_filter]
            if st.session_state.conf_patient_filter != "Todos": filtered_df = filtered_df[filtered_df['name'] == st.session_state.conf_patient_filter]
            if st.session_state.conf_insurance_filter != "Todos": filtered_df = filtered_df[filtered_df['insurance'] == st.session_state.conf_insurance_filter]
            if st.session_state.conf_event_filter != "Todos": filtered_df = filtered_df[filtered_df['event'] == st.session_state.conf_event_filter]

    # --- [CORRIGIDO] DIÁLOGO DE PREVIEW ---
    @st.dialog("Preview da Mensagem")
    def preview_dialog():
        message_template = st.session_state.get('message_template', "Olá, {$primeiro_nome}!")
        
        if 'edited_df' in st.session_state and not st.session_state.edited_df.empty:
            selected_patients_df = st.session_state.edited_df[st.session_state.edited_df['Selecionar']]
            
            if selected_patients_df.empty:
                st.warning("Nenhum paciente selecionado para visualizar.")
            else:
                # Pega a primeira linha da tabela de exibição que foi selecionada
                first_selected_row_display = selected_patients_df.iloc[0]
                
                # Usa o índice dessa linha para encontrar os dados completos no dataframe original filtrado
                original_index = first_selected_row_display.name
                full_data_row = filtered_df.loc[original_index]

                st.markdown(f"**Para: {full_data_row['name']}**")
                
                # Popula as variáveis usando os dados completos e corretos
                preview_message = message_template
                preview_message = preview_message.replace('{$primeiro_nome}', str(full_data_row['name']).split(' ')[0])
                preview_message = preview_message.replace('{$modalidade}', str(full_data_row['category']))
                preview_message = preview_message.replace('{$horario}', str(full_data_row['time']))
                preview_message = preview_message.replace('{$data}', full_data_row['scheduled_date'].strftime('%d/%m/%Y'))
                preview_message = preview_message.replace('{$profissional}', str(full_data_row['professional']))
                
                st.markdown(f"""
                <div style="background-color: #e9f7ef; padding: 10px; border-radius: 5px; color: #155724; margin-bottom: 15px">
                    {preview_message}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Não há dados de agendamento para visualizar.")

        if st.button("Fechar", use_container_width=True, key="close_preview"):
            st.session_state.show_preview_dialog = False
            st.rerun()

    # --- SEÇÃO DE FILTROS ---
    st.subheader("Filtros de Agendamento")
    with st.container(border=True):
        date_col1, date_col2 = st.columns(2)
        date_col1.date_input("Data Inicial:", key="conf_start_date")
        date_col2.date_input("Data Final:", key="conf_end_date")

        f_col1, f_col2, f_col3 = st.columns(3)
        if not df.empty:
            f_col1.selectbox("Profissionais", ["Todos"] + sorted(df['professional'].unique().tolist()), key="conf_prof_filter")
            f_col2.selectbox("Categorias", ["Todos"] + sorted(df['category'].unique().tolist()), key="conf_cat_filter")
            f_col3.selectbox("Status", ["Todos"] + sorted(df['status'].unique().tolist()), key="conf_status_filter")
            
            f_col4, f_col5, f_col6 = st.columns(3)
            f_col4.selectbox("Pacientes", ["Todos"] + sorted(df['name'].unique().tolist()), key="conf_patient_filter")
            f_col5.selectbox("Convênios", ["Todos"] + sorted(df['insurance'].unique().tolist()), key="conf_insurance_filter")
            f_col6.selectbox("Eventos", ["Todos"] + sorted(df['event'].unique().tolist()), key="conf_event_filter")

    # --- CABEÇALHO E RESUMO DE AGENDAMENTOS ---
    st.write("---")
    start_date_str = st.session_state.conf_start_date.strftime('%d/%m/%Y')
    end_date_str = st.session_state.conf_end_date.strftime('%d/%m/%Y')
    st.header(f"Agendamentos de {start_date_str} até {end_date_str}")

    total_agendamentos = len(filtered_df)
    confirmados = len(filtered_df[filtered_df['status'] == 'Confirmado'])
    pendentes = len(filtered_df[filtered_df['status'] == 'Pendente'])
    reagendados = len(filtered_df[filtered_df['status'] == 'Reagendado'])
    cancelados = len(filtered_df[filtered_df['status'] == 'Cancelado'])
    
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 20px; font-size: 1.1rem; margin-bottom: 15px;">
            <span><b>{total_agendamentos}</b> agendamentos</span>
            <span style="color: #28a745;"><b>{confirmados}</b> confirmados</span>
            <span style="color: darkorange;"><b>{pendentes}</b> pendentes</span>
            <span style="color: #007bff;"><b>{reagendados}</b> reagendados</span>
            <span style="color: #6c757d;"><b>{cancelados}</b> cancelados</span>
        </div>
    """, unsafe_allow_html=True)

    # --- TABELA DE AGENDAMENTOS ---
    if filtered_df.empty:
        st.warning("Nenhum agendamento encontrado para os filtros selecionados.")
        st.session_state.edited_df = pd.DataFrame()
    else:
        base_df = filtered_df[['name', 'time', 'category', 'professional', 'status', 'phone']].copy()
        base_df.rename(columns={
            'name': 'Paciente', 'time': 'Horário', 'category': 'Modalidade',
            'professional': 'Profissional', 'status': 'Status', 'phone': 'Telefone'
        }, inplace=True)

        # Lógica robusta para resetar as seleções quando os filtros mudam
        if 'edited_df' not in st.session_state or not st.session_state.edited_df.index.equals(base_df.index):
            base_df.insert(0, 'Selecionar', False)
            st.session_state.edited_df = base_df

        def toggle_all():
            new_value = st.session_state.select_all_checkbox
            df_copy = st.session_state.edited_df.copy()
            df_copy['Selecionar'] = new_value
            st.session_state.edited_df = df_copy

        action_col1, action_col2 = st.columns([3, 1])
        with action_col1:
            all_selected = all(st.session_state.edited_df['Selecionar']) if not st.session_state.edited_df.empty else False
            st.checkbox("Selecionar Todos", value=all_selected, on_change=toggle_all, key="select_all_checkbox")
        with action_col2:
            if st.button("🔄 Atualizar Tabela", use_container_width=True, help="Recarregar dados do Baserow"):
                st.rerun()

        edited_df_output = st.data_editor(
            st.session_state.edited_df,
            use_container_width=True,
            hide_index=True,
            disabled=['Paciente', 'Horário', 'Modalidade', 'Profissional', 'Status', 'Telefone'],
            key='appointments_editor'
        )
        st.session_state.edited_df = edited_df_output

    # --- LAYOUT DE AÇÕES E TEMPLATE ---
    st.write("---")
    with st.container(border=True):
        st.subheader("📋 Template e Envio de Mensagem")
        st.caption("Configure a mensagem que será enviada aos pacientes selecionados na tabela acima.")
        
        message = st.text_area(
            "Mensagem:", 
            "Olá, {$primeiro_nome}! Confirmando seu agendamento de {$modalidade} para o dia {$data} às {$horario}. Atenciosamente, COFRAT.",
            height=120,
            key='message_template'
        )
        st.markdown("""
        **Variáveis:** `{$primeiro_nome}`, `{$modalidade}`, `{$horario}`, `{$data}`, `{$profissional}`
        """, unsafe_allow_html=True)
        
        st.write("")
        btn_cols = st.columns(2)
        btn_cols[0].button("Visualizar Preview", use_container_width=True, on_click=lambda: st.session_state.update(show_preview_dialog=True))
        
        selected_count = int(st.session_state.edited_df['Selecionar'].sum()) if 'edited_df' in st.session_state and not st.session_state.edited_df.empty else 0
        btn_cols[1].button(f"✉️ Enviar Mensagens ({selected_count})", use_container_width=True, type="primary")

    if st.session_state.get('show_preview_dialog', False):
        preview_dialog()

# --- PÁGINA DE PACIENTES ---
def patients_page():
    st.write('##### Gerencie os cadastros de pacientes com praticidade')
    st.write('Esta página permite o cadastro e edição dos dados dos pacientes, garantindo que todas as informações estejam organizadas e acessíveis para os atendimentos.')
    st.write('')


    header_cols = st.columns([3, 1])
    with header_cols[0]:
        st.subheader("Cadastro de Pacientes")
    with header_cols[1]:
        st.button("✚ Novo Paciente", type="primary", width='stretch')

    filter_cols = st.columns([3, 1])
    filter_cols[0].text_input("Buscar por nome, telefone ou email...", placeholder="🔍 Buscar por nome, telefone ou email...", label_visibility="collapsed")
    filter_cols[1].button("Filtros", width='stretch')

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

    st.dataframe(df_patients, width='stretch', hide_index=True)
    st.caption("Ações como editar e excluir podem ser adicionadas ao selecionar uma linha ou através de um menu de contexto em futuras implementações.")


def chatwoot_page():
    """
    Exibe a página de integração com o Chatwoot, permitindo marcar todas as conversas como lidas.
    """
    st.title("Chatwoot")
    st.write("Gerencie ações rápidas para as conversas do Chatwoot diretamente daqui.")
    st.write("---")

    st.subheader("Marcar todas as conversas como lidas")
    st.write("Clique no botão abaixo para acionar a automação no n8n que marcará todas as conversas pendentes como lidas na sua caixa de entrada do Chatwoot.")

    # Use colunas para centralizar o botão e dar um espaçamento melhor
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        if st.button("🚀 Marcar todas como lidas", use_container_width=True, type="primary"):
            # Substitua pela URL real do seu webhook no n8n
            WEBHOOK_URL = "https://n8n.erudieto.com.br/webhook-test/mark-all-as-read"
            
            with st.spinner("Aguarde, acionando o fluxo no n8n..."):
                try:
                    # O método POST é geralmente usado para acionar webhooks
                    response = requests.post(WEBHOOK_URL, timeout=123456)
                    
                    # Verifica se a requisição foi bem-sucedida (código 2xx)
                    if response.status_code >= 200 and response.status_code < 300:
                        st.success("✅ Fluxo acionado com sucesso! As conversas serão marcadas como lidas em breve.")
                    else:
                        st.error(f"❌ Falha ao acionar o fluxo. O n8n retornou o código de status: {response.status_code}")
                        st.code(response.text, language="text")

                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Ocorreu um erro de conexão ao tentar acionar o webhook: {e}")
                    st.warning("Verifique se a URL do webhook está correta e se o seu fluxo no n8n está ativo.")

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
                # --- [MODIFICADO] A página Relatórios foi trocada pela Chatwoot ---
                sac.MenuItem('Chatwoot', icon='chat'),
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
        # --- [MODIFICADO] O mapeamento agora aponta para a nova função chatwoot_page ---
        'Chatwoot': chatwoot_page
    }
    page_function = page_map.get(selected_page, home_page)
    page_function()
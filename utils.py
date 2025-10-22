# utils.py
import streamlit as st
from streamlit_option_menu import option_menu
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
import base64

# --- FUNÇÃO PARA CARREGAR IMAGEM (LOCAL E ONLINE) ---
def load_image_as_base64(image_path):
    """Carrega imagem local e converte para base64."""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

def display_logo(logo_path, width=200, use_column=True):
    """Exibe logo com fallback para base64 se o caminho não funcionar."""
    # Tenta carregar como base64
    img_base64 = load_image_as_base64(logo_path)
    
    if use_column:
        logo_col1, logo_col2, logo_col3 = st.columns([1.4, 1, 1])
        with logo_col2:
            if img_base64:
                st.markdown(
                    f'<img src="data:image/png;base64,{img_base64}" width="{width}">',
                    unsafe_allow_html=True
                )
            else:
                # Fallback: tenta carregar diretamente
                try:
                    st.image(logo_path, width=width)
                except:
                    st.warning("Logo não encontrado")
    else:
        if img_base64:
            st.markdown(
                f'<img src="data:image/png;base64,{img_base64}" width="{width}">',
                unsafe_allow_html=True
            )
        else:
            try:
                st.image(logo_path, width=width)
            except:
                st.warning("Logo não encontrado")

# --- FUNÇÃO DE LOGIN CENTRALIZADA E ESTILIZADA ---
def login_form(logo_path):
    """Exibe o logotipo e o formulário de login centralizado."""
    st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">', unsafe_allow_html=True)

    # Exibe o logo
    display_logo(logo_path, width=200, use_column=True)
    st.write("\n")

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

# --- FUNÇÃO HELPER PARA SUMMARY CARDS ---
def create_summary_card(label, value):
    return f'<div class="summary-card"><div class="summary-card-value">{value}</div><div class="summary-card-label">{label}</div></div>'

# --- PÁGINA INICIAL (DASHBOARD COM CARD DE PACIENTES ÚNICOS) ---
def home_page():
    """
    Exibe um dashboard estável e informativo, com uma linha adicional de cards
    numéricos, incluindo o total de pacientes únicos no período.
    """
    st.markdown("""
    <div class="custom-title-container">
        <div class="custom-title-bar"></div>
        <div class="custom-title">
            <h1>Painel de Performance da Clínica</h1>
            <p>Use os filtros para analisar a operação em diferentes períodos</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- BUSCA E PREPARAÇÃO DOS DADOS ---
    load_dotenv()
    BASEROW_KEY = os.getenv("BASEROW_KEY")
    
    @st.cache_data(ttl=600) # Cache de 10 minutos
    def load_data_from_baserow():
        df = get_daily_agenda_from_baserow(BASEROW_KEY)
        if not df.empty:
            df['scheduled_date'] = pd.to_datetime(df['scheduled_date']).dt.date
        return df

    df = load_data_from_baserow()

    if df.empty:
        st.warning("Não foi possível carregar os dados para o dashboard. Verifique a conexão ou a fonte de dados.")
        return

    # --- FILTROS DE DATA INTERATIVOS ---
    today = date.today()
    
    with st.expander("🗓️ Selecionar Período", expanded=True):
        periodo_selecionado = st.selectbox(
            "Filtro rápido",
            options=["Este Mês", "Esta Semana", "Últimos 30 dias", "Hoje", "Período Customizado"],
            key="period_filter"
        )

        if periodo_selecionado == "Hoje":
            start_date = today
            end_date = today
        elif periodo_selecionado == "Esta Semana":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif periodo_selecionado == "Este Mês":
            start_date = today.replace(day=1)
            end_date = today.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
        elif periodo_selecionado == "Últimos 30 dias":
            start_date = today - timedelta(days=29)
            end_date = today
        else: # Período Customizado
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Data Inicial", today - timedelta(days=6))
            end_date = col2.date_input("Data Final", today)

    df_filtered = df[(df['scheduled_date'] >= start_date) & (df['scheduled_date'] <= end_date)]

    if df_filtered.empty:
        st.info(f"Nenhum agendamento encontrado para o período de {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}.")
        return

    # --- CÁLCULO DAS MÉTRICAS DE INSIGHT (KPIs) ---
    total_agendamentos = len(df_filtered)
    confirmados = len(df_filtered[df_filtered['status'] == 'Confirmado'])
    cancelados = len(df_filtered[df_filtered['status'] == 'Cancelado'])
    
    taxa_confirmacao = (confirmados / total_agendamentos * 100) if total_agendamentos > 0 else 0
    taxa_cancelamento = (cancelados / total_agendamentos * 100) if total_agendamentos > 0 else 0
    
    num_dias = (end_date - start_date).days + 1
    media_diaria = total_agendamentos / num_dias if num_dias > 0 else 0

    # --- EXIBIÇÃO DOS KPIs ---
    st.markdown(f"#### Indicadores de {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
    kpi_cols = st.columns(4)
    kpi_cols[0].markdown(create_metric_card("Taxa de Confirmação", f"{taxa_confirmacao:.1f}%", "Eficiência da comunicação", "normal"), unsafe_allow_html=True)
    kpi_cols[1].markdown(create_metric_card("Taxa de Cancelamento", f"{taxa_cancelamento:.1f}%", "Agendamentos perdidos", "inverse"), unsafe_allow_html=True)
    kpi_cols[2].markdown(create_metric_card("Total de Atendimentos", f"{total_agendamentos}", "Volume no período", "off"), unsafe_allow_html=True)
    kpi_cols[3].markdown(create_metric_card("Média Diária", f"{media_diaria:.1f}", "Atendimentos / dia", "off"), unsafe_allow_html=True)

    st.divider()

    # --- RESUMO OPERACIONAL COM CARDS ---
    st.markdown("#### Resumo Operacional do Período")
    
    # Cálculos para os novos cards
    pendentes = len(df_filtered[df_filtered['status'] == 'Pendente'])
    
    # [NOVO CARD] Calcula o número de pacientes únicos (contando nomes distintos)
    pacientes_unicos = df_filtered['name'].nunique()

    # Exibição da nova linha de cards
    summary_cols = st.columns(4)
    summary_cols[0].markdown(create_summary_card("Confirmados", f"{confirmados}"), unsafe_allow_html=True)
    summary_cols[1].markdown(create_summary_card("Pendentes", f"{pendentes}"), unsafe_allow_html=True)
    summary_cols[2].markdown(create_summary_card("Cancelados", f"{cancelados}"), unsafe_allow_html=True)
    summary_cols[3].markdown(create_summary_card("Pacientes Únicos", f"{pacientes_unicos}"), unsafe_allow_html=True)

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
    
    # Inicialização de session_state
    if 'extraction_status' not in st.session_state:
        st.session_state.extraction_status = {}
    if 'files_df' not in st.session_state:
        st.session_state.files_df = None
    if 'last_upload_time' not in st.session_state:
        st.session_state.last_upload_time = None

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

    # Carrega metadados apenas uma vez
    if st.session_state.files_df is None:
        with st.spinner("Carregando metadados dos arquivos..."):
            st.session_state.files_df = fetch_metadata_from_db(supabase)

    # [MODIFICADO] Adicionado botão de atualização ao lado do título do filtro
    header_cols = st.columns([3, 1])
    with header_cols[0]:
        st.subheader("Filtros")
    with header_cols[1]:
        if st.button("🔄 Atualizar Página", use_container_width=True, help="Recarrega os dados da agenda do Baserow"):
            st.rerun()
    
    # Inicialização dos filtros (apenas uma vez)
    if "view_mode" not in st.session_state:
        # [MODIFICADO] Alterado o filtro padrão para "Todo o período"
        st.session_state.view_mode = "Todo o período"
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
            # O index=4 corresponde a "Todo o período" na lista de opções
            col1.radio("Visualização:", ["Dia", "Semana", "Mês", "Trimestre", "Todo o período"], horizontal=True, key="view_mode", index=4)
            col2.date_input("Data:", key="selected_date", disabled=(st.session_state.view_mode == "Todo o período"))
            
            f_col1, f_col2, f_col3, f_col4, f_col5, f_col6 = st.columns(6)
            f_col1.selectbox("Profissionais", ["Todos"] + sorted(df['professional'].unique().tolist()), key="prof_filter")
            f_col2.selectbox("Categorias", ["Todos"] + sorted(df['category'].unique().tolist()), key="cat_filter")
            
            status_options = ["Todos"] + sorted(df['status'].unique().tolist())
            f_col3.selectbox("Status", status_options, key="status_filter")
            
            f_col4.selectbox("Pacientes", ["Todos"] + sorted(df['name'].unique().tolist()), key="patient_filter")
            f_col5.selectbox("Convênios", ["Todos"] + sorted(df['insurance'].unique().tolist()), key="insurance_filter")
            f_col6.selectbox("Eventos", ["Todos"] + sorted(df['event'].unique().tolist()), key="event_filter")

            search_col, btn_col = st.columns([4, 1.08])
            search_col.text_input("Buscar paciente...", placeholder="Buscar paciente...", label_visibility="collapsed", key="search_term")
            btn_col.button("Limpar Filtros", on_click=clear_filters_callback)
        
        # Remove possíveis duplicatas ANTES de filtrar
        df = df.drop_duplicates(subset=['scheduled_date', 'time', 'name'], keep='first')
        
        # Aplicação dos filtros
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
        
        # Remove linhas com valores nulos críticos
        filtered_df = filtered_df.dropna(subset=['scheduled_date', 'name'])
        
        # Cabeçalho
        if st.session_state.view_mode == "Dia":
            st.header(f"Agendamentos para {st.session_state.selected_date.strftime('%d/%m/%Y')}")
        elif st.session_state.view_mode == "Todo o período":
            st.header("Exibindo todos os agendamentos")
        else:
            st.header(f"Agendamentos de {start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}")
        
        # Estatísticas
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
        
        # Exibição da tabela
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
    
    # --- UPLOAD DE ARQUIVOS (SEM CONTADOR) ---
    st.write("---")
    
    uploaded_files = st.file_uploader(
        "Arraste e solte os arquivos aqui",
        type="pdf",
        accept_multiple_files=True,
        key="file_uploader"
    )

    if uploaded_files:
        upload_button = st.button("📤 Fazer Upload dos Arquivos", type="primary", use_container_width=True)
        
        if upload_button:
            success_count = 0
            error_count = 0
            duplicate_count = 0
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, uploaded_file in enumerate(uploaded_files):
                file_name_with_date = f"{date.today().strftime('%Y-%m-%d')}_{uploaded_file.name}"
                file_path_in_bucket = f"pdfs-agendamento/{file_name_with_date}"
                
                status_text.text(f"Processando {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")
                
                try:
                    # Upload para o Storage
                    supabase.storage.from_("cofrat").upload(
                        path=file_path_in_bucket,
                        file=uploaded_file.getvalue(),
                        file_options={"content-type": "application/pdf"}
                    )
                    
                    # Registro no banco de dados
                    supabase.table('pdf_metadata').insert({
                        'data_upload': date.today().isoformat(),
                        'nome_arquivo': file_name_with_date,
                        'info_extraida': 'Não'
                    }).execute()

                    success_count += 1

                except Exception as e:
                    if "Duplicate" in str(e) or "already exists" in str(e).lower():
                        duplicate_count += 1
                    else:
                        error_count += 1
                        st.error(f'❌ Erro ao processar "{uploaded_file.name}": {e}')
                
                progress_bar.progress((idx + 1) / len(uploaded_files))
            
            # Limpa a barra de progresso
            progress_bar.empty()
            status_text.empty()
            
            # Mensagem de resultado
            if success_count > 0:
                st.success(f'✅ {success_count} arquivo(s) enviado(s) com sucesso!')
            if duplicate_count > 0:
                st.warning(f'⚠️ {duplicate_count} arquivo(s) já existia(m) no sistema.')
            if error_count > 0:
                st.error(f'❌ {error_count} arquivo(s) com erro no upload.')
            
            # Atualiza a lista de arquivos apenas se houve sucesso
            if success_count > 0 or duplicate_count > 0:
                st.session_state.files_df = fetch_metadata_from_db(supabase)
                st.session_state.last_upload_time = time.time()
                st.rerun()

    # --- LISTA DE ARQUIVOS ---
    st.write("---")
    
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.subheader("Status da Extração de Arquivos")
    with col_header2:
        if st.button("🔄 Atualizar Lista", use_container_width=True):
            st.session_state.files_df = fetch_metadata_from_db(supabase)
            # Limpa status de extração para arquivos já extraídos
            for file_id in list(st.session_state.extraction_status.keys()):
                if not st.session_state.files_df[st.session_state.files_df['id'] == file_id].empty:
                    if st.session_state.files_df[st.session_state.files_df['id'] == file_id]['extracted'].iloc[0] == 'Sim':
                        del st.session_state.extraction_status[file_id]
            st.rerun()

    files_df = st.session_state.files_df
    if files_df.empty:
        st.info("Nenhum metadado de arquivo encontrado no banco de dados.")
    else:
        with st.container(border=True):
            # Cabeçalho
            header_cols = st.columns([2, 4, 2, 3])
            header_cols[0].markdown("**Data de upload**")
            header_cols[1].markdown("**Nome do arquivo**")
            header_cols[2].markdown("**Info Extraída**")
            header_cols[3].markdown("<div style='text-align: center;'><b>Ações</b></div>", unsafe_allow_html=True)

            # Linhas
            for index, row in files_df.iterrows():
                st.divider()
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
                    is_disabled = current_extraction_status == 'pending'

                    if row['extracted'] != 'Sim' and current_extraction_status != 'pending':
                        if btn_cols[0].button("Extrair", key=f"extract_{row['id']}", use_container_width=True, disabled=is_disabled):
                            WEBHOOK_URL = "https://webhook.erudieto.com.br/webhook/cofrat-pdf"
                            payload = {'fileName': row['file_name'], 'fileId': row['id']}
                            
                            st.session_state.extraction_status[row['id']] = 'pending'
                            
                            try:
                                response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
                                
                                if response.status_code in [200, 202]:
                                    st.success(f"✅ Extração iniciada para '{row['file_name']}'")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Falha ao iniciar extração (código {response.status_code})")
                                    st.session_state.extraction_status[row['id']] = 'failed'
                                    st.rerun()
                            except requests.exceptions.RequestException as e:
                                st.error(f"❌ Erro de conexão: {e}")
                                st.session_state.extraction_status[row['id']] = 'failed'
                                st.rerun()
                    elif current_extraction_status == 'pending':
                        btn_cols[0].markdown('<div style="text-align: center; color: darkorange; font-size: 0.85em;">Extraindo...</div>', unsafe_allow_html=True)
                    else:
                        btn_cols[0].button("Extraído", key=f"extracted_disabled_{row['id']}", use_container_width=True, disabled=True)
                    
                    if btn_cols[1].button("🗑️", key=f"delete_{row['id']}", help=f"Deletar {row['file_name']}", use_container_width=True, disabled=is_disabled):
                        st.session_state.file_to_delete = row
                        st.rerun()

    # --- MODAL DE CONFIRMAÇÃO DE DELEÇÃO ---
    if 'file_to_delete' in st.session_state and st.session_state.file_to_delete is not None:
        file_info = st.session_state.file_to_delete
        
        @st.dialog("Confirmar Deleção")
        def confirm_delete():
            st.warning(f"Você tem certeza que deseja deletar permanentemente o arquivo **{file_info['file_name']}**?")
            st.write("Esta ação removerá o arquivo do armazenamento e seu registro do banco de dados. Não pode ser desfeita.")
            
            col1, col2 = st.columns(2)
            
            if col1.button("✅ Sim, deletar", type="primary", use_container_width=True):
                try:
                    supabase.storage.from_("cofrat").remove([f"pdfs-agendamento/{file_info['file_name']}"])
                    supabase.table('pdf_metadata').delete().eq('id', file_info['id']).execute()
                    
                    st.success("✅ Arquivo deletado com sucesso!")
                    st.session_state.file_to_delete = None
                    st.session_state.files_df = fetch_metadata_from_db(supabase)
                    if file_info['id'] in st.session_state.extraction_status:
                        del st.session_state.extraction_status[file_info['id']]
                    time.sleep(0.5)
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao deletar: {e}")
                    st.session_state.file_to_delete = None
                    st.rerun()

            if col2.button("❌ Cancelar", use_container_width=True):
                st.session_state.file_to_delete = None
                st.rerun()
        
        confirm_delete()
    
# --- [AJUSTADA] PÁGINA DE GESTÃO ---
def management_page():
    """
    Página de gestão com abas para Médicos, Modalidades e Agendas, usando st.tabs.
    """
    st.write('##### Organize cadastros, especialidades e agendas com eficiência')
    st.write('Esta página permite o cadastro e edição dos médicos, com controle de status (Ativo/Inativo) conforme disponibilidade de agenda. Também é possível gerenciar as modalidades de atendimento — como Fisioterapia, Ortopedia, RPG e outras — e configurar os horários de disponibilidade de cada profissional. Tudo em um só lugar, para garantir uma operação fluida e organizada.')
    st.write('')

    # Substituído sac.segmented por st.tabs para uma solução nativa do Streamlit
    tab1, tab2, tab3 = st.tabs(["🧑‍⚕️ Médicos", "🏷️ Modalidades", "🗓️ Agendas"])

    with tab1:
        header_cols = st.columns([3, 1])
        with header_cols[0]:
            st.subheader("Profissionais de Saúde")
        with header_cols[1]:
            st.button("✚ Adicionar Profissional", type="primary", use_container_width=True)

        professionals = [
            {"name": "Dra. Liliane Santos", "specialty": "Fisioterapia", "schedule": "Segunda a Sexta", "capacity": 10},
            {"name": "Dr. Roberto Silva", "specialty": "Ortopedia", "schedule": "Segunda a Sexta", "capacity": 8},
            {"name": "Dra. Carla Mendes", "specialty": "Fisioterapia Infantil", "schedule": "Segunda a Sexta", "capacity": 6},
        ]

        cols = st.columns(3)
        for i, prof in enumerate(professionals):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"##### 🩺 {prof['name']}")
                    st.write(prof['specialty'])
                    st.write(f"🕒 {prof['schedule']}")
                    st.write(f"Capacidade: {prof['capacity']} pacientes/horário")
                    
                    btn_cols = st.columns(2)
                    btn_cols[0].button("Editar", key=f"edit_{i}", use_container_width=True)
                    btn_cols[1].button("Desativar", key=f"del_{i}", use_container_width=True)

    with tab2:
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
                    st.write("")
                    
                    btn_cols = st.columns(2)
                    btn_cols[0].button("Editar", key=f"edit_mod_{i}", use_container_width=True)
                    btn_cols[1].button("🗑️", key=f"del_mod_{i}", use_container_width=True)

    with tab3:
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
                
                st.write("")

                for day, time, cap in agenda['schedule']:
                    day_cols = st.columns([2, 2, 1])
                    day_cols[0].text(day)
                    day_cols[1].text(time)
                    day_cols[2].button(f"Cap: {cap}", key=f"cap_{i}_{day}", disabled=True, use_container_width=True)
            st.write("")

# --- [NOVA PÁGINA OTIMIZADA PARA UX - VERSÃO CORRIGIDA E NATIVA] ---
def approval_workflow_page():
    """
    Exibe uma interface de fluxo de trabalho otimizada para aprovações,
    construída inteiramente com componentes nativos do Streamlit para máxima
    estabilidade e com keys únicas para evitar erros de ID.
    """
    st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">', unsafe_allow_html=True)

    # --- Bloco de inicialização do estado da sessão ---
    if 'carteirinha_appointments' not in st.session_state:
        all_apps = get_sample_appointments()
        st.session_state.carteirinha_appointments = [app for app in all_apps if app.get('type') == 'Carteirinha']
        st.session_state.agendamento_appointments = [app for app in all_apps if app.get('type') == 'Agendamento']
    
    if 'active_carteirinha_idx' not in st.session_state:
        st.session_state.active_carteirinha_idx = 0
    if 'active_agendamento_idx' not in st.session_state:
        st.session_state.active_agendamento_idx = 0
    
    if 'reschedule_mode' not in st.session_state:
        st.session_state.reschedule_mode = False

    # --- Títulos e Abas Principais ---
    st.subheader("Fluxo de Aprovação")
    st.caption("Selecione um item pendente na lista à esquerda para ver os detalhes e tomar uma ação à direita.")

    carteirinha_count = len(st.session_state.carteirinha_appointments)
    agendamento_count = len(st.session_state.agendamento_appointments)

    tab1, tab2 = st.tabs([
        f"📥 Carteirinhas Pendentes ({carteirinha_count})",
        f"🗓️ Agendamentos Pendentes ({agendamento_count})"
    ])

    # --- Aba de Carteirinhas ---
    with tab1:
        if not st.session_state.carteirinha_appointments:
            display_carteirinha_completion_message()
        else:
            if st.session_state.active_carteirinha_idx >= len(st.session_state.carteirinha_appointments):
                st.session_state.active_carteirinha_idx = 0

            col_list, col_detail = st.columns([1, 2], gap="large")

            # Coluna da Lista de Itens
            with col_list:
                st.markdown("##### Na Fila")
                for idx, app in enumerate(st.session_state.carteirinha_appointments):
                    with st.container(border=True):
                        is_selected = (idx == st.session_state.active_carteirinha_idx)
                        st.write(f"**{app['name']}**" if is_selected else app['name'])
                        st.caption(app['specialty'])
                        if st.button("Ver Detalhes", key=f"view_cart_{idx}", use_container_width=True):
                            st.session_state.active_carteirinha_idx = idx
                            st.rerun()
            
            # Coluna de Detalhes e Ações
            with col_detail:
                active_idx = st.session_state.active_carteirinha_idx
                current_appointment = st.session_state.carteirinha_appointments[active_idx]

                st.markdown("##### Detalhes para Aprovação")
                
                # Card de detalhes com componentes nativos
                with st.container(border=True):
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        st.subheader(current_appointment['initials'])
                    with c2:
                        st.subheader(current_appointment['name'])
                        st.caption(f"📞 {current_appointment['phone']}")
                    
                    st.divider()
                    
                    dc1, dc2 = st.columns(2)
                    with dc1:
                        st.caption("Profissional")
                        st.write(f"🧑‍⚕️ {current_appointment['professional']}")
                        st.caption("Convênio")
                        st.write(f"🏢 {current_appointment['insurance']}")
                    with dc2:
                        st.caption("Carteirinha")
                        st.write(f"💳 {current_appointment['card_number']}")
                        st.caption("Modalidade")
                        st.write(f"🏷️ {current_appointment['specialty']}")
                    
                    st.divider()
                    st.caption("Observações")
                    st.info(current_appointment['notes'])

                st.write("")
                st.markdown("##### Ações")
                action_cols = st.columns(2)
                if action_cols[0].button("✓ Aprovar Início de Agendamento", key="approve_carteirinha", use_container_width=True, type="primary"):
                    st.toast(f"Início de agendamento para {current_appointment['name']} aprovado!", icon="✅")
                    st.session_state.carteirinha_appointments.pop(active_idx)
                    st.rerun()
                
                if action_cols[1].button("✕ Cancelar", key="cancel_carteirinha", use_container_width=True):
                    st.toast(f"Item de {current_appointment['name']} cancelado.", icon="🗑️")
                    st.session_state.carteirinha_appointments.pop(active_idx)
                    st.rerun()

    # --- Aba de Agendamentos ---
    with tab2:
        if not st.session_state.agendamento_appointments:
            display_agendamento_completion_message()
        else:
            if st.session_state.active_agendamento_idx >= len(st.session_state.agendamento_appointments):
                st.session_state.active_agendamento_idx = 0

            col_list, col_detail = st.columns([1, 2], gap="large")

            # Coluna da Lista de Itens
            with col_list:
                st.markdown("##### Na Fila")
                for idx, app in enumerate(st.session_state.agendamento_appointments):
                    with st.container(border=True):
                        is_selected = (idx == st.session_state.active_agendamento_idx)
                        st.write(f"**{app['name']}**" if is_selected else app['name'])
                        st.caption(f"{app['date']} às {app['time']}")
                        if st.button("Ver Detalhes", key=f"view_agend_{idx}", use_container_width=True):
                            st.session_state.active_agendamento_idx = idx
                            st.session_state.reschedule_mode = False
                            st.rerun()
            
            # Coluna de Detalhes e Ações
            with col_detail:
                active_idx = st.session_state.active_agendamento_idx
                current_appointment = st.session_state.agendamento_appointments[active_idx]

                st.markdown("##### Detalhes para Aprovação")
                # Card de detalhes com componentes nativos
                with st.container(border=True):
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        st.subheader(current_appointment['initials'])
                    with c2:
                        st.subheader(current_appointment['name'])
                        st.caption(f"📞 {current_appointment['phone']}")
                    
                    st.divider()
                    
                    dc1, dc2, dc3 = st.columns(3)
                    with dc1:
                        st.caption("Data")
                        st.write(f"🗓️ {current_appointment['date']}")
                    with dc2:
                        st.caption("Horário")
                        st.write(f"🕒 {current_appointment['time']}")
                    with dc3:
                        st.caption("Modalidade")
                        st.write(f"🏷️ {current_appointment['specialty']}")

                    st.caption("Profissional")
                    st.write(f"🧑‍⚕️ {current_appointment['professional']}")
                    
                    st.divider()
                    st.caption("Observações")
                    st.info(current_appointment['notes'])

                st.write("")
                st.markdown("##### Ações")
                if st.session_state.reschedule_mode:
                    with st.container(border=True):
                        st.markdown(f"**Reagendando para:** {current_appointment['name']}")
                        st.date_input("Nova Data", key="new_date")
                        st.time_input("Novo Horário", key="new_time")
                        
                        reschedule_cols = st.columns(2)
                        if reschedule_cols[0].button("Confirmar Reagendamento", key="confirm_reschedule", use_container_width=True, type="primary"):
                            st.toast("Sugestão de reagendamento enviada!", icon="👍")
                            st.session_state.agendamento_appointments.pop(active_idx)
                            st.session_state.reschedule_mode = False
                            st.rerun()
                        if reschedule_cols[1].button("Cancelar Ação", key="cancel_reschedule", use_container_width=True):
                            st.session_state.reschedule_mode = False
                            st.rerun()
                else:
                    action_cols = st.columns(3)
                    if action_cols[0].button("✓ Aprovar", key="approve_agendamento", use_container_width=True, type="primary"):
                        st.toast(f"Agendamento de {current_appointment['name']} aprovado!", icon="✅")
                        st.session_state.agendamento_appointments.pop(active_idx)
                        st.rerun()
                    if action_cols[1].button("↻ Reagendar", key="reschedule_agendamento", use_container_width=True):
                        st.session_state.reschedule_mode = True
                        st.rerun()
                    if action_cols[2].button("✕ Cancelar", key="cancel_agendamento", use_container_width=True):
                        st.toast(f"Agendamento de {current_appointment['name']} cancelado.", icon="🗑️")
                        st.session_state.agendamento_appointments.pop(active_idx)
                        st.rerun()


# --- [AJUSTADA] PÁGINA DE CONFIRMAÇÃO DE AGENDAMENTOS ---
def confirmation_page():
    """
    Exibe a página de confirmação em massa com formatação de preview aprimorada, 
    layout ajustado, filtros e CRUD de templates.
    """
    # --- Importações necessárias ---
    import pandas as pd
    import os
    from datetime import date, timedelta
    import requests
    
    st.write('##### Comunicação em massa para agendamentos')
    st.write('Esta página permite confirmar ou cancelar agendamentos em massa. Use os filtros para selecionar um período e refinar a lista de pacientes antes de enviar as comunicações.')
    st.write('')

    # --- FUNÇÕES HELPER ---
    
    # Função para carregar dados do Baserow
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
            if not all_rows: return pd.DataFrame()
            df = pd.DataFrame(all_rows)
            expected_columns = ['Data do Agendamento', 'Horário', 'Nome do Paciente', 'Convênio', 'Evento', 'Profissional', 'Especialidade', 'Telefone', 'Status do Agendamento']
            for col in expected_columns:
                if col not in df.columns:
                    st.error(f"Erro Crítico: A coluna '{col}' não foi encontrada na sua tabela do Baserow.")
                    return pd.DataFrame()
            column_mapping = {'Data do Agendamento': 'scheduled_date', 'Horário': 'time', 'Nome do Paciente': 'name', 'Convênio': 'insurance', 'Evento': 'event', 'Profissional': 'professional', 'Especialidade': 'category', 'Telefone': 'phone', 'Status do Agendamento': 'status'}
            df.rename(columns=column_mapping, inplace=True)
            df['scheduled_date'] = pd.to_datetime(df['scheduled_date'], dayfirst=True, errors='coerce').dt.date
            df.dropna(subset=['scheduled_date'], inplace=True)
            return df
        except Exception as e:
            st.error(f"Ocorreu um erro ao buscar os dados do Baserow: {e}")
            return pd.DataFrame()

    # Funções para CRUD de templates locais
    DATA_DIR = "data"
    TEMPLATES_FILE = os.path.join(DATA_DIR, "message_templates.csv")

    def load_templates():
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        if not os.path.exists(TEMPLATES_FILE):
            return pd.DataFrame(columns=["area", "message"])
        return pd.read_csv(TEMPLATES_FILE)

    def save_templates(df):
        df.to_csv(TEMPLATES_FILE, index=False)

    # --- INICIALIZAÇÃO E CARGA DE DADOS ---
    load_dotenv()
    BASEROW_KEY = os.getenv("BASEROW_KEY")
    df = get_confirmation_data_from_baserow(BASEROW_KEY)
    templates_df = load_templates()

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
        st.session_state.conf_search_term = ""
        st.session_state.show_preview_dialog = False
        st.session_state.show_send_confirmation = False
        st.session_state.template_area = ""

    if 'message_template' not in st.session_state:
        st.session_state.message_template = "Olá {$primeiro_nome}!\n\nSua consulta está agendada para o dia {$data}, às {$horario}, com Dr. {$profissional}.\n\nCaso não possa comparecer, por favor, avise com antecedência."

    # --- LÓGICA DE FILTRAGEM ---
    filtered_df = df.copy()
    if not df.empty:
        if st.session_state.conf_start_date > st.session_state.conf_end_date:
            st.error("A data inicial não pode ser posterior à data final.")
            filtered_df = pd.DataFrame() 
        else:
            date_mask = (filtered_df['scheduled_date'] >= st.session_state.conf_start_date) & (filtered_df['scheduled_date'] <= st.session_state.conf_end_date)
            filtered_df = filtered_df[date_mask]
            if st.session_state.conf_prof_filter != "Todos": filtered_df = filtered_df[filtered_df['professional'] == st.session_state.conf_prof_filter]
            if st.session_state.conf_cat_filter != "Todos": filtered_df = filtered_df[filtered_df['category'] == st.session_state.conf_cat_filter]
            if st.session_state.conf_status_filter != "Todos": filtered_df = filtered_df[filtered_df['status'] == st.session_state.conf_status_filter]
            if st.session_state.conf_patient_filter != "Todos": filtered_df = filtered_df[filtered_df['name'] == st.session_state.conf_patient_filter]
            if st.session_state.conf_insurance_filter != "Todos": filtered_df = filtered_df[filtered_df['insurance'] == st.session_state.conf_insurance_filter]
            if st.session_state.conf_event_filter != "Todos": filtered_df = filtered_df[filtered_df['event'] == st.session_state.conf_event_filter]
            if st.session_state.conf_search_term:
                filtered_df = filtered_df[filtered_df['name'].str.contains(st.session_state.conf_search_term, case=False, na=False)]

    # --- DIÁLOGOS ---
    @st.dialog("Preview da Mensagem")
    def preview_dialog():
        # Função auxiliar para formatar o horário
        def format_time_for_preview(time_str):
            try:
                hour, minute = map(int, time_str.split(':'))
                rounded_minute = (minute // 10) * 10
                return f"{hour:02d}:{rounded_minute:02d}"
            except:
                return time_str # Retorna o original se houver erro de formato

        message_template = st.session_state.get('message_template', "Olá, {$primeiro_nome}!")
        if 'edited_df' in st.session_state and not st.session_state.edited_df.empty:
            selected_patients_df = st.session_state.edited_df[st.session_state.edited_df['Selecionar']]
            if selected_patients_df.empty:
                st.warning("Nenhum paciente selecionado para visualizar.")
            else:
                first_selected_row_display = selected_patients_df.iloc[0]
                original_index = first_selected_row_display.name
                full_data_row = filtered_df.loc[original_index]
                st.markdown(f"**Para: {full_data_row['name']}**")

                # [MODIFICADO] Aplica as novas formatações
                patient_name = str(full_data_row['name']).split(' ')[0].capitalize()
                professional_name = str(full_data_row['professional']).title()
                formatted_time = format_time_for_preview(str(full_data_row['time']))

                preview_message = message_template.replace('{$primeiro_nome}', patient_name)\
                                                  .replace('{$modalidade}', str(full_data_row['category']))\
                                                  .replace('{$horario}', formatted_time)\
                                                  .replace('{$data}', full_data_row['scheduled_date'].strftime('%d/%m/%Y'))\
                                                  .replace('{$profissional}', professional_name)
                
                # [MODIFICADO] Substitui \n por <br> para renderizar quebras de linha
                html_message = preview_message.replace('\n', '<br>')
                
                st.markdown(f'<div style="background-color: #e9f7ef; padding: 10px; border-radius: 5px; color: #155724; margin-bottom: 15px">{html_message}</div>', unsafe_allow_html=True)
        else:
            st.warning("Não há dados de agendamento para visualizar.")
        if st.button("Fechar", use_container_width=True, key="close_preview"):
            st.session_state.show_preview_dialog = False
            st.rerun()

    @st.dialog("Confirmar Envio")
    def confirm_send_dialog(selected_count):
        st.warning(f"Você tem certeza que deseja enviar a mensagem para {selected_count} paciente(s) selecionado(s)?")
        
        col1, col2 = st.columns(2)
        if col1.button("Sim, Enviar Agora", type="primary", use_container_width=True):
            selected_contacts_df = st.session_state.edited_df[st.session_state.edited_df['Selecionar']]
            message_to_send = st.session_state.get('message_template', "")
            selected_indices = selected_contacts_df.index
            full_data_of_selected = filtered_df.loc[selected_indices]
            full_data_of_selected['scheduled_date'] = full_data_of_selected['scheduled_date'].astype(str)
            contacts_payload = full_data_of_selected.to_dict(orient='records')
            final_payload = {"message_template": message_to_send, "contacts": contacts_payload}
            WEBHOOK_URL = "https://webhook.erudieto.com.br/webhook/disparo-em-massa"
            
            with st.spinner(f"Enviando {len(contacts_payload)} mensagens..."):
                try:
                    response = requests.post(WEBHOOK_URL, json=final_payload, timeout=30)
                    if 200 <= response.status_code < 300:
                        st.success(f"✅ Sucesso! A automação foi acionada para {len(contacts_payload)} contatos.")
                    else:
                        st.error(f"❌ Falha ao enviar. O servidor respondeu com: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Erro de conexão ao tentar acionar o webhook: {e}")
            
            st.session_state.show_send_confirmation = False
            st.rerun()

        if col2.button("Cancelar", use_container_width=True):
            st.session_state.show_send_confirmation = False
            st.rerun()

    # --- SEÇÃO DE FILTROS RETRÁTIL ---
    with st.expander("🔍 Filtros de Agendamento", expanded=True):
        search_col, btns_col = st.columns([3, 1.2])
        search_col.text_input(
            "Buscar paciente por nome:", 
            key="conf_search_term", 
            placeholder="Digite o nome do paciente para buscar..."
        )
        
        with btns_col:
            b1, b2 = st.columns(2)
            def clear_confirmation_filters():
                st.session_state.conf_start_date = date.today()
                st.session_state.conf_end_date = date.today() + timedelta(days=7)
                st.session_state.conf_prof_filter = "Todos"
                st.session_state.conf_cat_filter = "Todos"
                st.session_state.conf_status_filter = "Todos"
                st.session_state.conf_patient_filter = "Todos"
                st.session_state.conf_insurance_filter = "Todos"
                st.session_state.conf_event_filter = "Todos"
                st.session_state.conf_search_term = ""
            b1.button("Limpar", on_click=clear_confirmation_filters, use_container_width=True, help="Limpar todos os filtros")
            
            if b2.button("Atualizar", use_container_width=True, help="Atualizar dados da página"):
                st.rerun()
        
        st.divider()

        date_col1, date_col2 = st.columns(2)
        date_col1.date_input("Data Inicial:", key="conf_start_date")
        date_col2.date_input("Data Final:", key="conf_end_date")

        if not df.empty:
            f_col1, f_col2, f_col3 = st.columns(3)
            f_col1.selectbox("Profissionais", ["Todos"] + sorted(df['professional'].unique().tolist()), key="conf_prof_filter")
            f_col2.selectbox("Categorias", ["Todos"] + sorted(df['category'].unique().tolist()), key="conf_cat_filter")
            f_col3.selectbox("Status", ["Todos"] + sorted(df['status'].unique().tolist()), key="conf_status_filter")
            
            f_col4, f_col5, f_col6 = st.columns(3)
            f_col4.selectbox("Pacientes (lista completa)", ["Todos"] + sorted(df['name'].unique().tolist()), key="conf_patient_filter")
            f_col5.selectbox("Convênios", ["Todos"] + sorted(df['insurance'].unique().tolist()), key="conf_insurance_filter")
            f_col6.selectbox("Eventos", ["Todos"] + sorted(df['event'].unique().tolist()), key="conf_event_filter")

    # --- CABEÇALHO E RESUMO DE AGENDAMENTOS ---
    st.write("---")
    start_date_str = st.session_state.conf_start_date.strftime('%d/%m/%Y')
    end_date_str = st.session_state.conf_end_date.strftime('%d/%m/%Y')
    st.header(f"Agendamentos de {start_date_str} até {end_date_str}")

    # --- [CORRIGIDO] TABELA DE AGENDAMENTOS E ESTATÍSTICAS ---
    if filtered_df.empty:
        st.warning("Nenhum agendamento encontrado para os filtros selecionados.")
        st.session_state.edited_df = pd.DataFrame()
    else:
        # [CORRIGIDO] O cálculo das estatísticas foi movido para DENTRO deste bloco 'else'.
        # Isso garante que o código só tente acessar a coluna 'status' se o DataFrame não estiver vazio.
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

        base_df = filtered_df[['name', 'time', 'category', 'professional', 'status', 'phone']].copy()
        base_df.rename(columns={
            'name': 'Paciente', 'time': 'Horário', 'category': 'Modalidade',
            'professional': 'Profissional', 'status': 'Status', 'phone': 'Telefone'
        }, inplace=True)

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
        
        content = st.text_area(
            "Mensagem:",
            value=st.session_state.message_template,
            height=250,
            key='message_template_input'
        )
        st.session_state.message_template = content

        st.text_input("Área/Categoria do Template:", key="template_area")
        
        st.markdown("**Variáveis:** `{$primeiro_nome}`, `{$modalidade}`, `{$horario}`, `{$data}`, `{$profissional}`")
        st.write("")

        btn_cols = st.columns(3)
        
        if btn_cols[0].button("Salvar Template", use_container_width=True):
            if st.session_state.template_area and st.session_state.message_template:
                new_template = pd.DataFrame([{"area": st.session_state.template_area, "message": st.session_state.message_template}])
                updated_templates_df = pd.concat([templates_df, new_template], ignore_index=True)
                save_templates(updated_templates_df)
                st.toast("Template salvo com sucesso!")
                st.rerun()
            else:
                st.warning("Preencha a Área e a Mensagem para salvar o template.")

        btn_cols[1].button("Visualizar Preview", use_container_width=True, on_click=lambda: st.session_state.update(show_preview_dialog=True))
        
        selected_count = int(st.session_state.edited_df['Selecionar'].sum()) if 'edited_df' in st.session_state and not st.session_state.edited_df.empty else 0
        
        if btn_cols[2].button(f"✉️ Enviar Mensagens ({selected_count})", use_container_width=True, type="primary"):
            if selected_count > 0:
                st.session_state.show_send_confirmation = True
                st.rerun()
            else:
                st.warning("Nenhum paciente selecionado para o envio.")

    st.divider()

    st.subheader("Templates Salvos")
    st.caption("Delete mensagens pré-definidas.")
    
    if not templates_df.empty:
        template_cols = st.columns(3)
        for index, row in templates_df.iterrows():
            with template_cols[index % 3]:
                with st.container(border=True):
                    st.markdown(f"**Área:** {row['area']}")
                    st.code(row['message'], language=None)
                    
                    # [MODIFICADO] Botão Deletar agora ocupa a largura total
                    if st.button("Deletar", key=f"del_{index}", use_container_width=True):
                        updated_templates_df = templates_df.drop(index)
                        save_templates(updated_templates_df)
                        st.toast(f"Template '{row['area']}' deletado!")
                        st.rerun()
    else:
        st.info("Nenhum template salvo ainda. Crie um acima para começar.")

    # --- Execução dos diálogos ---
    if st.session_state.get('show_preview_dialog', False):
        preview_dialog()
    
    if st.session_state.get('show_send_confirmation', False):
        selected_count = int(st.session_state.edited_df['Selecionar'].sum())
        confirm_send_dialog(selected_count)

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


def automations_page():
    """
    Exibe a página de Automações, permitindo acionar fluxos de trabalho externos.
    """
    st.title("Automações")
    st.write("Gerencie e acione fluxos de trabalho e automações diretamente desta página.")
    st.divider()

    # --- AUTOMAÇÃO 1: MARCAR CONVERSAS COMO LIDAS ---
    st.subheader("Marcar todas as conversas do Chatwoot como lidas")
    st.write("Clique no botão abaixo para acionar a automação que marcará todas as conversas pendentes como lidas na sua caixa de entrada do Chatwoot.")

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.button("🚀 Marcar todas como lidas", use_container_width=True, type="primary"):
            WEBHOOK_URL_CHATWOOT = "https://webhook.erudieto.com.br/webhook/mark-all-as-read"
            
            with st.spinner("Aguarde, acionando o fluxo no n8n..."):
                try:
                    response = requests.post(WEBHOOK_URL_CHATWOOT, timeout=30)
                    if 200 <= response.status_code < 300:
                        st.success("✅ Fluxo acionado com sucesso! As conversas serão marcadas como lidas em breve.")
                    else:
                        st.error(f"❌ Falha ao acionar o fluxo. O servidor retornou o código: {response.status_code}")
                        st.code(response.text, language="text")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Ocorreu um erro de conexão ao tentar acionar o webhook: {e}")

    st.divider()

    # --- AUTOMAÇÃO 2: PADRONIZAR NÚMEROS DE TELEFONE ---
    st.subheader("Padronizar Números de Telefone na Base de Dados")
    st.write("Clique no botão abaixo para iniciar a automação que busca e ajusta todos os números de telefone para um formato padronizado (ex: +5531999998888).")

    col4, col5, col6 = st.columns([1, 1.5, 1])
    with col5:
        if st.button("🚀 Iniciar Padronização de Telefones", use_container_width=True, type="primary"):
            WEBHOOK_URL_PHONES = "https://webhook.erudieto.com.br/webhook/transformar-numeros"

            with st.spinner("Aguarde, acionando a automação de telefones..."):
                try:
                    response = requests.post(WEBHOOK_URL_PHONES, timeout=30)
                    if 200 <= response.status_code < 300:
                        st.success("✅ Automação iniciada com sucesso! Os números de telefone serão padronizados em segundo plano.")
                    else:
                        st.error(f"❌ Falha ao acionar a automação. O servidor retornou o código: {response.status_code}")
                        st.code(response.text, language="text")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Ocorreu um erro de conexão ao tentar acionar o webhook: {e}")

    st.divider()

    # --- AUTOMAÇÃO 3: DELETAR AGORA ---
    st.subheader("Deletar Agora")
    st.write("Clique no botão abaixo para acionar a automação de deleção. Esta ação executará o processo de limpeza conforme configurado no webhook.")

    col7, col8, col9 = st.columns([1, 1.5, 1])
    with col8:
        if st.button("🗑️ Deletar Agora", use_container_width=True, type="primary"):
            WEBHOOK_URL_DELETE = "https://webhook.erudieto.com.br/webhook/delete"

            with st.spinner("Aguarde, acionando a automação de deleção..."):
                try:
                    response = requests.post(WEBHOOK_URL_DELETE, timeout=30)
                    if 200 <= response.status_code < 300:
                        st.success("✅ Automação de deleção iniciada com sucesso! O processo será executado em segundo plano.")
                    else:
                        st.error(f"❌ Falha ao acionar a automação. O servidor retornou o código: {response.status_code}")
                        st.code(response.text, language="text")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Ocorreu um erro de conexão ao tentar acionar o webhook: {e}")


# --- LÓGICA PRINCIPAL DO APLICATIVO (LOGADO) COM MENU st.radio ---
def main_app(logo_path):
    """
    Renderiza a sidebar e controla o roteamento de páginas usando um menu st.radio
    nativo para garantir máxima estabilidade e compatibilidade.
    """
    with st.sidebar:
        display_logo(logo_path, width=110, use_column=False)
        st.write("---")

        # --- [MENU SIMPLIFICADO] Substituído por st.radio para máxima estabilidade ---
        # Lista de todas as páginas disponíveis na aplicação
        page_options = [
            "Página Inicial",
            "Aprovação",
            "Agenda do Dia",
            "Gestão",
            "Pacientes",
            "Automações",
            "Confirmação",
            "Suporte"
        ]

        # O st.radio agora controla a página selecionada
        selected_page = st.radio(
            "Menu de Navegação",  # Rótulo do menu
            page_options,
            label_visibility="collapsed" # Oculta o rótulo para um visual mais limpo
        )
        
        st.write("---")
        if st.button("Logout", use_container_width=True):
            st.session_state["authentication_status"] = False
            st.session_state["username"] = None
            st.rerun()

    # O roteamento de páginas continua funcionando da mesma forma
    if selected_page == "Suporte":
        st.info("Redirecionando para o WhatsApp...")
        st.markdown("### 📱 Suporte via WhatsApp")
        st.markdown("[Clique aqui para abrir o WhatsApp](https://wa.me/+5511959044561)")
        st.stop()
    
    page_map = {
        'Página Inicial': home_page,
        'Aprovação': approval_workflow_page,
        'Agenda do Dia': daily_schedule_page,
        'Gestão': management_page,
        'Confirmação': confirmation_page,
        'Pacientes': patients_page,
        'Automações': automations_page
    }
    
    # Chama a função da página selecionada
    page_function = page_map.get(selected_page, home_page)
    page_function()
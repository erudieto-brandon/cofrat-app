import streamlit as st
import pandas as pd
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Agendamentos",
    page_icon="🗓️",
    layout="wide"
)

# --- CSS Customizado para Estética Aprimorada ---
st.markdown("""
<style>
    /* --- GERAL --- */
    body {
        background-color: #F0F2F5; /* Fundo cinza claro para contraste */
    }
    /* Remove o espaçamento superior do Streamlit */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Estilo dos botões principais */
    div[data-testid="stButton"] > button {
        border-radius: 8px;
    }

    /* --- CABEÇALHO --- */
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .header h1, .header h3 {
        margin: 0;
    }
    .header-buttons {
        display: flex;
        gap: 0.5rem;
    }

    /* --- CARTÕES DE MÉTRICAS --- */
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 1.25rem;
        border-left: 6px solid;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        display: flex;
        flex-direction: column;
        justify-content: center;
        height: 100%;
    }
    .metric-card-confirmado { border-color: #28a745; }
    .metric-card-cancelado { border-color: #dc3545; }
    .metric-card-aguardando { border-color: #ffc107; }
    .metric-card-atendimento { border-color: #007bff; }
    .metric-card-concluido { border-color: #6c757d; }

    .metric-card h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1rem;
        color: #5a6a85;
        font-weight: 600;
    }
    .metric-card p {
        margin: 0;
        font-size: 2.25rem;
        font-weight: 700;
        color: #1e293b;
    }

    /* --- CONTAINER DE FILTROS --- */
    .filters-container {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 1.5rem;
        border: 1px solid #E2E8F0;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
    }
    .filters-container h5 {
        margin-bottom: 1rem;
        font-size: 1.1rem;
    }

    /* --- LISTA DE AGENDAMENTOS --- */
    .appointment-list-header {
        font-weight: 600;
        color: #64748B;
        font-size: 0.8rem;
        text-transform: uppercase;
        padding: 0 1rem;
        margin-bottom: 0.5rem;
    }
    .appointment-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
        transition: box-shadow 0.2s ease-in-out, border-color 0.2s ease-in-out;
    }
    .appointment-card:hover {
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border-color: #CBD5E1;
    }
    /* Alinhamento vertical dos itens no card */
    div[data-testid="stHorizontalBlock"] {
        align-items: center;
    }

    /* --- BADGES DE STATUS --- */
    .status-badge {
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 600;
        color: white;
        text-align: center;
        display: inline-block;
    }
    .status-confirmado { background-color: #28a745; }
    .status-cancelado { background-color: #dc3545; }
    .status-aguardando { background-color: #ffc107; color: #333; }
    .status-em-atendimento { background-color: #007bff; }
    .status-concluído { background-color: #6c757d; }

    /* --- BOTÕES DE AÇÃO NA LISTA --- */
    .action-buttons {
        display: flex;
        gap: 1rem;
        justify-content: flex-start;
    }
    /* Remove o estilo padrão dos botões de ação para parecerem links */
    .action-buttons div[data-testid="stButton"] > button {
        background-color: transparent;
        color: #007BFF;
        border: none;
        padding: 0;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .action-buttons div[data-testid="stButton"] > button:hover {
        text-decoration: underline;
        color: #0056b3;
    }
    .action-buttons div[data-testid="stButton"] > button.repor-button {
        color: #5a6a85;
    }
    .action-buttons div[data-testid="stButton"] > button.repor-button:hover {
        color: #1e293b;
    }

</style>
""", unsafe_allow_html=True)


# --- Dados de Amostra ---
data = {
    'Horário': ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30'],
    'Paciente': ['Maria Silva', 'João Santos', 'Ana Costa', 'Pedro Oliveira', 'Carla Mendes', 'Lucas Pereira', 'Fernanda Lima', 'Ricardo Alves', 'Beatriz Souza', 'Tiago Martins'],
    'Contato': ['+55 11 98765-4321', '+55 11 98765-4322', '+55 11 98765-4323', '+55 11 98765-4324', '+55 11 98765-4325', '+55 11 98765-4326', '+55 11 98765-4327', '+55 11 98765-4328', '+55 11 98765-4329', '+55 11 98765-4330'],
    'Tipo': ['Fisioterapia', 'Ortopedia', 'Fisioterapia', 'Terapia', 'Ortopedia', 'Fisioterapia', 'Terapia', 'Fisioterapia', 'Terapia', 'Ortopedia'],
    'Terapeuta': ['Dr. Carlos Mendes', 'Dra. Ana Paula', 'Dr. Carlos Mendes', 'Dr. Roberto Lima', 'Dra. Ana Paula', 'Dr. Carlos Mendes', 'Dr. Roberto Lima', 'Dr. Carlos Mendes', 'Dr. Roberto Lima', 'Dra. Ana Paula'],
    'Sala': ['Sala 1', 'Sala 2', 'Sala 1', 'Sala 3', 'Sala 2', 'Sala 1', 'Sala 3', 'Sala 1', 'Sala 3', 'Sala 2'],
    'Status': ['Confirmado', 'Cancelado', 'Confirmado', 'Aguardando', 'Em Atendimento', 'Confirmado', 'Cancelado', 'Confirmado', 'Aguardando', 'Concluído']
}
df = pd.DataFrame(data)

# --- CABEÇALHO ---
st.markdown("""
<div class="header">
    <div>
        <h1>Agendamentos do Dia</h1>
        <h3>Sábado, 25 de Outubro de 2025</h3>
    </div>
    <div class="header-buttons">
        <!-- Os botões reais são criados abaixo com st.button -->
    </div>
</div>
""", unsafe_allow_html=True)

# Colocando os botões do cabeçalho em colunas para alinhá-los à direita
_, btn_col = st.columns([0.8, 0.2])
with btn_col:
    btn1, btn2 = st.columns(2)
    btn1.button("Ver Disparos", key="ver_disparos", use_container_width=True)
    btn2.button("🔄 Atualizar", type="primary", key="atualizar", use_container_width=True)


# --- CARTÕES DE RESUMO ---
status_counts = df['Status'].value_counts()
confirmados = status_counts.get('Confirmado', 0)
cancelados = status_counts.get('Cancelado', 0)
aguardando = status_counts.get('Aguardando', 0)
em_atendimento = status_counts.get('Em Atendimento', 0)
concluidos = status_counts.get('Concluído', 0)

cols = st.columns(5)
with cols[0]:
    st.markdown(f'<div class="metric-card metric-card-confirmado"><h3>Confirmados</h3><p>✅ {confirmados}</p></div>', unsafe_allow_html=True)
with cols[1]:
    st.markdown(f'<div class="metric-card metric-card-cancelado"><h3>Cancelados</h3><p>❌ {cancelados}</p></div>', unsafe_allow_html=True)
with cols[2]:
    st.markdown(f'<div class="metric-card metric-card-aguardando"><h3>Aguardando</h3><p>🕒 {aguardando}</p></div>', unsafe_allow_html=True)
with cols[3]:
    st.markdown(f'<div class="metric-card metric-card-atendimento"><h3>Em Atendimento</h3><p>➡️ {em_atendimento}</p></div>', unsafe_allow_html=True)
with cols[4]:
    st.markdown(f'<div class="metric-card metric-card-concluido"><h3>Concluídos</h3><p>✔️ {concluidos}</p></div>', unsafe_allow_html=True)

st.write("") # Espaçamento

# --- FILTROS ---
with st.container():
    st.markdown('<div class="filters-container">', unsafe_allow_html=True)
    st.write("<h5>🇾 Filtros</h5>", unsafe_allow_html=True)
    
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1, 1, 1])
    with f_col1:
        busca = st.text_input("Buscar", placeholder="Nome, telefone ou terapeuta...", label_visibility="collapsed")
    with f_col2:
        status_filter = st.selectbox("Status", ["Todos"] + list(df['Status'].unique()), label_visibility="collapsed")
    with f_col3:
        tipo_sessao_filter = st.selectbox("Tipo de Sessão", ["Todos"] + list(df['Tipo'].unique()), label_visibility="collapsed")
    with f_col4:
        terapeuta_filter = st.selectbox("Terapeuta", ["Todos"] + list(df['Terapeuta'].unique()), label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

# --- LÓGICA DE FILTRAGEM ---
df_filtrado = df.copy()
if busca:
    df_filtrado = df_filtrado[df_filtrado.apply(lambda row: busca.lower() in str(row).lower(), axis=1)]
if status_filter != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Status'] == status_filter]
if tipo_sessao_filter != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Tipo'] == tipo_sessao_filter]
if terapeuta_filter != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Terapeuta'] == terapeuta_filter]

# --- LISTA DE AGENDAMENTOS ---
st.header(f"Lista de Agendamentos ({len(df_filtrado)} de {len(df)})")
st.caption("Todos os agendamentos programados para hoje")

# Cabeçalho da lista customizado
header_cols = st.columns([0.8, 1.5, 1.5, 1, 1.5, 0.8, 1, 1.5])
headers = ['Horário', 'Paciente', 'Contato', 'Tipo', 'Terapeuta', 'Sala', 'Status', 'Ações']
for col, header in zip(header_cols, headers):
    col.markdown(f'<div class="appointment-list-header">{header}</div>', unsafe_allow_html=True)

# Função para criar o badge de status
def status_to_html(status):
    status_class = status.lower().replace(" ", "-").replace("í", "i").replace("ç", "c")
    return f'<div class="status-badge status-{status_class}">{status}</div>'

# Exibindo os dados em cards
if df_filtrado.empty:
    st.info("Nenhum agendamento encontrado com os filtros selecionados.")
else:
    for index, row in df_filtrado.iterrows():
        with st.container():
            st.markdown('<div class="appointment-card">', unsafe_allow_html=True)
            cols = st.columns([0.8, 1.5, 1.5, 1, 1.5, 0.8, 1, 1.5])
            cols[0].markdown(f"🕒 {row['Horário']}")
            cols[1].markdown(f"**{row['Paciente']}**")
            cols[2].text(row['Contato'])
            cols[3].text(row['Tipo'])
            cols[4].text(f"👨‍⚕️ {row['Terapeuta']}")
            cols[5].text(row['Sala'])
            cols[6].markdown(status_to_html(row['Status']), unsafe_allow_html=True)
            
            with cols[7]:
                st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
                action_cols = st.columns([1, 1])
                if row['Status'] == 'Cancelado':
                    action_cols[0].button("Repor", key=f"repor_{index}", help="Repor este agendamento")
                action_cols[1].button("Ver Disparo", key=f"disparo_{index}", help="Ver detalhes do disparo de mensagem")
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
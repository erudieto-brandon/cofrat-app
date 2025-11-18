# utils.py
import streamlit as st
import streamlit_antd_components as sac
import pandas as pd
import requests
import base64

# --- FUNÇÃO PARA CARREGAR IMAGEM ---
def load_image_as_base64(image_path):
    """Carrega imagem local e converte para base64."""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

# --- FUNÇÃO PARA EXIBIR LOGO NO CORPO PRINCIPAL (PARA LOGIN) ---
def display_logo(logo_path, width=200, use_column=True):
    """Exibe o logo da aplicação no corpo principal."""
    img_base64 = load_image_as_base64(logo_path)
    
    if use_column:
        _, logo_col, _ = st.columns([1.4, 1, 1])
        with logo_col:
            if img_base64:
                st.markdown(
                    f'<img src="data:image/png;base64,{img_base64}" width="{width}">',
                    unsafe_allow_html=True
                )
            else:
                st.warning("Logo não encontrado")
    else:
        if img_base64:
            st.markdown(
                f'<img src="data:image/png;base64,{img_base64}" width="{width}">',
                unsafe_allow_html=True
            )
        else:
            st.warning("Logo não encontrado")

# --- FUNÇÃO DE LOGIN ---
def login_form(logo_path):
    """Exibe o logotipo e o formulário de login centralizado."""
    st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">', unsafe_allow_html=True)

    display_logo(logo_path, width=200, use_column=True)
    st.write("\n")

    _, col, _ = st.columns([1, 2, 1])
    with col:
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

# --- PÁGINA DE CONFIRMAÇÃO DE AGENDAMENTOS (CONTEÚDO COMPLETO) ---
def confirmation_page():
    def process_clean_excel(df):
        if 'Data' in df.columns:
            df['Data'] = df['Data'].astype(str)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('ú', 'u').str.replace('é', 'e').str.replace('ç', 'c').str.replace('ã', 'a')
        required_columns = ['data', 'horario', 'medico', 'paciente', 'numero_de_telefone_ajustado']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"As colunas obrigatórias a seguir não foram encontradas: {', '.join(missing_cols)}.")
        df.rename(columns={'paciente': 'nome_do_paciente', 'medico': 'nome_do_medico', 'horario': 'horario_ajustado', 'numero_de_telefone_ajustado': 'telefone_ajustado'}, inplace=True)
        return df

    if 'edited_df' not in st.session_state:
        st.session_state.edited_df = None
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None

    st.title("Central de Disparos")
    st.caption("Clínica de Ortopedia e Terapia")
    st.divider()

    st.subheader("1. Carregar Arquivo de Agendamentos (.xlsx)")
    uploaded_file = st.file_uploader("Selecione o arquivo Excel", type=["xlsx"], key="excel_uploader")

    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.uploaded_file_name:
            st.session_state.edited_df = None
            st.session_state.uploaded_file_name = uploaded_file.name
        if st.session_state.edited_df is None and st.button("⚙️ Processar Arquivo", use_container_width=True, type="primary"):
            with st.spinner("Processando..."):
                try:
                    df = pd.read_excel(uploaded_file, dtype={'Data': str})
                    processed_df = process_clean_excel(df)
                    processed_df.insert(0, 'Selecionar', False)
                    st.session_state.edited_df = processed_df
                    st.success("Arquivo processado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar o arquivo: {e}")

    if st.session_state.edited_df is not None:
        st.header("Agendamentos Carregados")
        st.subheader("2. Selecione os Pacientes para Envio")
        
        def toggle_all():
            new_value = st.session_state.select_all_checkbox
            df_copy = st.session_state.edited_df.copy()
            df_copy['Selecionar'] = new_value
            st.session_state.edited_df = df_copy

        all_selected = st.session_state.edited_df['Selecionar'].all() if not st.session_state.edited_df.empty else False
        st.checkbox("Selecionar Todos", value=all_selected, on_change=toggle_all, key="select_all_checkbox")
        
        edited_df_output = st.data_editor(st.session_state.edited_df, use_container_width=True, hide_index=True, disabled=st.session_state.edited_df.columns.drop('Selecionar'))
        st.session_state.edited_df = edited_df_output

        st.divider()
        st.subheader("3. Escolha o Template e Envie")
        templates = {
            "Confirmacao_Agendamento": "Olá, {nome_do_paciente}! Sua consulta com Dr(a). {nome_do_medico} está confirmada para o dia {data} às {horario_ajustado}. Até breve!",
            "Lembrete_48h": "Lembrete: sua consulta com Dr(a). {nome_do_medico} é depois de amanhã, dia {data} às {horario_ajustado}. Contamos com sua presença!",
        }
        selected_template_name = st.selectbox("Selecione o template:", options=list(templates.keys()))
        st.code(templates[selected_template_name], language="text")

        selected_count = int(st.session_state.edited_df['Selecionar'].sum())
        if st.button(f"✉️ Enviar Mensagens ({selected_count})", use_container_width=True, type="primary"):
            if selected_count > 0:
                selected_rows_df = st.session_state.edited_df[st.session_state.edited_df['Selecionar']].copy().fillna('')
                contacts_payload = selected_rows_df.to_dict(orient='records')
                final_payload = {"template_name": selected_template_name, "contacts": contacts_payload}
                WEBHOOK_URL = "https://webhook.erudieto.com.br/webhook/disparo-em-massa"
                with st.spinner(f"Enviando {len(contacts_payload)} mensagens..."):
                    try:
                        response = requests.post(WEBHOOK_URL, json=final_payload, timeout=30)
                        if 200 <= response.status_code < 300:
                            st.success(f"✅ Sucesso! Automação acionada para {len(contacts_payload)} contatos.")
                        else:
                            st.error(f"❌ Falha ao enviar: {response.status_code} - {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Erro de conexão: {e}")
            else:
                st.warning("Nenhum paciente selecionado.")

# --- PÁGINA DE AUTOMAÇÕES (CONTEÚDO COMPLETO) ---
def automations_page():
    st.title("Automações")
    st.write("Gerencie e acione fluxos de trabalho e automações diretamente desta página.")
    st.divider()

    st.subheader("Marcar todas as conversas do Chatwoot como lidas")
    if st.button("🚀 Marcar todas como lidas", use_container_width=True):
        WEBHOOK_URL_CHATWOOT = "https://webhook.erudieto.com.br/webhook/mark-all-as-read"
        with st.spinner("Acionando o fluxo..."):
            try:
                response = requests.post(WEBHOOK_URL_CHATWOOT, timeout=30)
                if 200 <= response.status_code < 300:
                    st.success("✅ Fluxo acionado com sucesso!")
                else:
                    st.error(f"❌ Falha ao acionar o fluxo: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Erro de conexão: {e}")

    st.divider()
    st.subheader("Padronizar Números de Telefone na Base de Dados")
    if st.button("🚀 Iniciar Padronização de Telefones", use_container_width=True):
        WEBHOOK_URL_PHONES = "https://webhook.erudieto.com.br/webhook/transformar-numeros"
        with st.spinner("Acionando a automação..."):
            try:
                response = requests.post(WEBHOOK_URL_PHONES, timeout=30)
                if 200 <= response.status_code < 300:
                    st.success("✅ Automação iniciada com sucesso!")
                else:
                    st.error(f"❌ Falha ao acionar a automação: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Erro de conexão: {e}")

    st.divider()
    st.subheader("Deletar Agora")
    if st.button("🗑️ Deletar Agora", use_container_width=True):
        WEBHOOK_URL_DELETE = "https://webhook.erudieto.com.br/webhook/delete"
        with st.spinner("Acionando a automação..."):
            try:
                response = requests.post(WEBHOOK_URL_DELETE, timeout=30)
                if 200 <= response.status_code < 300:
                    st.success("✅ Automação de deleção iniciada com sucesso!")
                else:
                    st.error(f"❌ Falha ao acionar a automação: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Erro de conexão: {e}")

# --- LÓGICA PRINCIPAL DO APLICATIVO COM MENU LATERAL ---
def main_app(logo_path):
    """
    Função principal que renderiza a interface do usuário,
    incluindo a barra lateral com logo e menu, e a página selecionada.
    """
    with st.sidebar:
        # Adiciona o logotipo no topo da barra lateral com o tamanho exato
        st.image(logo_path, width=125)

        # Cria o menu de navegação
        selected = sac.menu(
            items=[
                sac.MenuItem('Confirmação', icon='send-check'),
                sac.MenuItem('Automações', icon='lightning-charge'),
            ],
            color='#08b13c',
            open_all=False,
            index=0
        )

    # Renderiza a página selecionada no menu
    if selected == 'Confirmação':
        confirmation_page()
    elif selected == 'Automações':
        automations_page()
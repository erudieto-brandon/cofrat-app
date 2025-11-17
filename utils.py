# utils.py
import streamlit as st
from streamlit_option_menu import option_menu
from datetime import date, timedelta, datetime, time
import pandas as pd
from dateutil.relativedelta import relativedelta
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import requests
import base64
import streamlit_antd_components as sac
import re
import io



# --- FUNÇÃO PARA CARREGAR IMAGEM (LOCAL E ONLINE) ---
def load_image_as_base64(image_path):
    """Carrega imagem local e converte para base64."""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

# --- FUNÇÃO PARA EXIBIR LOGO COM FALLBACK ---
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

# --- PÁGINA DE CONFIRMAÇÃO DE AGENDAMENTOS ---
def confirmation_page():
    """
    Exibe a Central de Disparos para ler o arquivo Excel 'agenda_do_dia',
    validar, preparar os dados e enviá-los via POST.
    Nesta versão, a coluna 'data' é tratada como texto para evitar erros de conversão.
    """
    # --- Importações e Configurações ---
    import pandas as pd
    import requests
    import streamlit as st

    # --- FUNÇÃO HELPER AJUSTADA PARA O ARQUIVO EXCEL DA IMAGEM ---
    def process_clean_excel(df):
        """
        Valida e prepara o DataFrame. Normaliza os nomes das colunas e os alinha
        com os templates de mensagem.
        """
        # Garante que a coluna 'data' seja lida como texto desde o início
        if 'Data' in df.columns:
            df['Data'] = df['Data'].astype(str)

        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('ú', 'u').str.replace('é', 'e').str.replace('ç', 'c').str.replace('ã', 'a')
        
        required_columns = ['data', 'horario', 'medico', 'paciente', 'numero_de_telefone_ajustado']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"As colunas obrigatórias a seguir não foram encontradas no arquivo: {', '.join(missing_cols)}. Verifique o arquivo Excel.")

        df.rename(columns={
            'paciente': 'nome_do_paciente',
            'medico': 'nome_do_medico',
            'horario': 'horario_ajustado',
            'numero_de_telefone_ajustado': 'telefone_ajustado'
        }, inplace=True)
        
        return df

    # --- INICIALIZAÇÃO DO SESSION STATE ---
    if 'edited_df' not in st.session_state:
        st.session_state.edited_df = None
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None

    # --- LAYOUT DO CABEÇALHO ---
    st.title("Central de Disparos")
    st.caption("Clínica de Ortopedia e Terapia")
    st.divider()

    # --- SEÇÃO DE UPLOAD E PROCESSAMENTO ---
    st.subheader("1. Carregar Arquivo de Agendamentos (.xlsx)")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo Excel gerado (ex: agenda_do_dia_...)",
        type=["xlsx"],
        key="excel_uploader"
    )

    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.uploaded_file_name:
            st.session_state.edited_df = None
            st.session_state.uploaded_file_name = uploaded_file.name

        if st.session_state.edited_df is None:
            if st.button("⚙️ Processar Arquivo", use_container_width=True, type="primary"):
                with st.spinner("Lendo e processando o arquivo..."):
                    try:
                        # Lê o Excel, garantindo que a coluna de data seja tratada como texto
                        df = pd.read_excel(uploaded_file, dtype={'Data': str})
                        
                        processed_df = process_clean_excel(df)
                        
                        processed_df.insert(0, 'Selecionar', False)
                        st.session_state.edited_df = processed_df
                        
                        st.success("Arquivo processado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

    # --- SEÇÃO DE VISUALIZAÇÃO E FILTROS ---
    if st.session_state.edited_df is not None:
        # REMOVIDO: Bloco que calculava data de início e fim.
        st.header("Agendamentos Carregados")
        st.caption("Revise os dados e selecione os pacientes para o envio.")

        st.subheader("2. Selecione os Pacientes para Envio")

        def toggle_all():
            new_value = st.session_state.select_all_checkbox
            df_copy = st.session_state.edited_df.copy()
            df_copy['Selecionar'] = new_value
            st.session_state.edited_df = df_copy

        all_selected = st.session_state.edited_df['Selecionar'].all() if not st.session_state.edited_df.empty else False

        st.checkbox("Selecionar Todos", value=all_selected, on_change=toggle_all, key="select_all_checkbox")
        
        edited_df_output = st.data_editor(
            st.session_state.edited_df,
            use_container_width=True,
            hide_index=True,
            disabled=st.session_state.edited_df.columns.drop('Selecionar'),
            key='appointments_editor'
        )
        st.session_state.edited_df = edited_df_output

        st.divider()
        st.subheader("3. Escolha o Template e Envie")

        templates = {
            "Confirmacao_Agendamento": "Olá, {nome_do_paciente}! Sua consulta com Dr(a). {nome_do_medico} está confirmada para o dia {data} às {horario_ajustado}. Até breve!",
            "Lembrete_48h": "Lembrete: sua consulta com Dr(a). {nome_do_medico} é depois de amanhã, dia {data} às {horario_ajustado}. Contamos com sua presença!",
        }
        selected_template_name = st.selectbox("Selecione o template de mensagem:", options=list(templates.keys()))
        
        st.info("Pré-visualização do template selecionado:")
        st.code(templates[selected_template_name], language="text")

        btn_cols = st.columns(2)
        
        with btn_cols[0]:
            if st.button("Visualizar Preview", use_container_width=True):
                st.info("Funcionalidade de preview a ser implementada.")

        with btn_cols[1]:
            selected_count = int(st.session_state.edited_df['Selecionar'].sum())
            if st.button(f"✉️ Enviar Mensagens ({selected_count})", use_container_width=True, type="primary"):
                if selected_count > 0:
                    selected_rows_df = st.session_state.edited_df[st.session_state.edited_df['Selecionar']].copy()
                    
                    # REMOVIDO: Qualquer conversão de data. A coluna já é texto.
                    
                    selected_rows_df = selected_rows_df.fillna('')
                    contacts_payload = selected_rows_df.to_dict(orient='records')
                    
                    final_payload = {
                        "template_name": selected_template_name,
                        "contacts": contacts_payload
                    }
                    
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
                else:
                    st.warning("Nenhum paciente selecionado para o envio.")

# --- PÁGINA DE AUTOMAÇÕES ---
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

# --- LÓGICA PRINCIPAL DO APLICATIVO COM MENU LATERAL ---
def main_app(logo_path):
    """
    Função principal que renderiza a interface do usuário,
    incluindo o menu lateral e a página selecionada.
    """
    # --- Definição do Menu Lateral ---
    with st.sidebar:
        st.write("\n")
        selected = sac.menu(
            items=[
                sac.MenuItem('Confirmação', icon='send'),
                sac.MenuItem('Automações', icon='lightning-charge'),
                sac.MenuItem('Aprovação', icon='card-checklist', tag=sac.Tag('Em breve', color='purple', bordered=False), disabled=True),
                sac.MenuItem('Agenda', icon='calendar', tag=sac.Tag('Em breve', color='purple', bordered=False), disabled=True),
                sac.MenuItem('Emails', icon='envelope', tag=sac.Tag('Em breve', color='purple', bordered=False), disabled=True),
                sac.MenuItem('Ligações', icon='telephone', tag=sac.Tag('Em breve', color='purple', bordered=False), disabled=True),
                sac.MenuItem('Uso', icon='pie-chart', tag=sac.Tag('Em breve', color='purple', bordered=False), disabled=True),
            ],
            color='#08b13c',
            open_all=False,
            index=0
        )

    if selected == 'Confirmação':
        confirmation_page()
    elif selected == 'Automações':
        automations_page()



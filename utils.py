# utils.py
import streamlit as st
import streamlit_antd_components as sac
import pandas as pd
import requests
import base64
import csv
import re
import io

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
    # As funções de ajuda do Colab foram movidas para cá
    def adjust_phone_number(phone_number):
        """Ajusta o número de telefone para o formato com código do país (55) e DDD."""
        digits_only = re.sub(r'\D', '', str(phone_number))
        if len(digits_only) > 10:
            if not digits_only.startswith('55'):
                return '55' + digits_only
            return digits_only
        elif len(digits_only) == 10:
            return '55' + digits_only
        elif len(digits_only) >= 8:
            return '5511' + digits_only
        else:
            return '' # Retorna vazio se o número for inválido

    def adjust_time(time_str):
        """Ajusta a string de horário para o formato HH:MM e arredonda para baixo a cada 10 minutos."""
        if pd.isna(time_str):
            return time_str
        try:
            time_obj = pd.to_datetime(time_str, format='%H:%M').time()
            full_datetime = pd.to_datetime(f"1970-01-01 {time_obj}")
            rounded_time = full_datetime.floor('10min')
            return rounded_time.strftime('%H:%M')
        except (ValueError, TypeError):
            return time_str

    def process_and_clean_csv(uploaded_file, file_type):
        """
        Lê um arquivo CSV, processa os dados com base no TIPO DE ARQUIVO, calcula estatísticas, 
        separa registros bons, ruins e repetidos (por nome), e retorna DataFrames e estatísticas.
        """
        file_content = uploaded_file.getvalue().decode('latin1')
        csv_file = io.StringIO(file_content)

        columns = [
            'Data', 'Especialidade', 'Hora', 'Medico', 'Convenio',
            'Evento', 'Paciente', 'Telefone', 'Prontuario'
        ]
        processed_rows = []
        time_regex = re.compile(r'^\d{2}:\d{2}$')
        
        reader = csv.reader(csv_file)

        # --- LÓGICA DE EXTRAÇÃO BASEADA NO TIPO DE ARQUIVO ---
        
        if file_type == "Consultas":
            # Lógica Original para Consultas
            current_date = None
            current_specialty = None
            
            for row in reader:
                if not row: continue
                if row[0] == 'Data:' and 'Especialidade: ' in row:
                    current_date, current_specialty = row[1], row[3]
                    try:
                        start_index = next(i for i, field in enumerate(row) if time_regex.match(field))
                        data_fields = row[start_index:]
                        # Estrutura Consultas: Data, Esp, Hora, Medico, Convenio, Evento, Paciente, Tel, Pront
                        processed_rows.append([current_date, current_specialty] + data_fields[:7])
                    except StopIteration: continue
                elif 'Página :' in row[0]:
                    try:
                        start_index = next(i for i, field in enumerate(row) if time_regex.match(field))
                        data_fields = row[start_index:]
                        processed_rows.append([current_date, current_specialty] + data_fields[:7])
                    except StopIteration: continue

        elif file_type in ["Acupuntura", "RPG"]:
            # Nova Lógica para Acupuntura e RPG (Layout de Serviços)
            current_date = None
            current_specialty = None
            current_doctor = None

            for row in reader:
                if not row: continue

                # 1. Captura de Contexto: Médico e Especialidade
                if 'Médico:' in row:
                    try:
                        if 'Agenda de:' in row:
                            spec_index = row.index('Agenda de:') + 1
                            current_specialty = row[spec_index]
                        
                        doc_index = row.index('Médico:') + 1
                        current_doctor = row[doc_index]
                    except (ValueError, IndexError):
                        pass
                
                # 2. Captura de Contexto: Data
                if len(row) > 1 and row[0] == 'Data:':
                    current_date = row[1]
                
                # 3. Extração dos Dados do Paciente
                try:
                    start_index = next(i for i, field in enumerate(row) if time_regex.match(field))
                    data_fields = row[start_index:]
                    
                    # Mapeamento Acupuntura/RPG:
                    # [0] Hora, [2] Paciente, [4] Evento, [5] Fone, [6] Pront, [7] Convenio
                    if len(data_fields) >= 8:
                        new_row = [
                            current_date,       # Data
                            current_specialty,  # Especialidade
                            data_fields[0],     # Hora
                            current_doctor,     # Medico (do cabeçalho)
                            data_fields[7],     # Convenio
                            data_fields[4],     # Evento
                            data_fields[2],     # Paciente
                            data_fields[5],     # Telefone
                            data_fields[6]      # Prontuario
                        ]
                        processed_rows.append(new_row)
                except StopIteration:
                    continue

        # --- FIM DA LÓGICA DE EXTRAÇÃO ---

        df = pd.DataFrame(processed_rows, columns=columns)
        if df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}

        # --- TRATAMENTO DE DADOS (COMUM A TODOS) ---
        df['Número de Telefone Ajustado'] = df['Telefone'].apply(adjust_phone_number)
        df['Horario'] = df['Hora'].apply(adjust_time)
        
        # Converte data para string formatada (garante consistência)
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')

        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('ú', 'u').str.replace('é', 'e').str.replace('ç', 'c').str.replace('ã', 'a')
        df.rename(columns={
            'paciente': 'nome_do_paciente', 'medico': 'nome_do_medico',
            'horario': 'horario_ajustado', 'numero_de_telefone_ajustado': 'telefone_ajustado'
        }, inplace=True)

        # Estatísticas gerais
        total_records = len(df)
        phone_counts = df['telefone_ajustado'].value_counts()
        unique_appointments = len(phone_counts[phone_counts.index != ''])
        
        patient_name_counts = df['nome_do_paciente'].value_counts()
        repeated_appointments = len(patient_name_counts[patient_name_counts > 1])

        # Critérios e contagem de qualidade de dados
        is_phone_empty = df['telefone_ajustado'] == ''
        is_phone_length_wrong = (~is_phone_empty) & (df['telefone_ajustado'].str.len() != 13)
        
        bad_data_mask = is_phone_empty | is_phone_length_wrong
        
        stats = {
            'total': total_records,
            'unique': unique_appointments,
            'repeated': repeated_appointments,
            'bad_total': bad_data_mask.sum(),
            'bad_empty': is_phone_empty.sum(),
            'bad_length': is_phone_length_wrong.sum()
        }

        df_bad = df[bad_data_mask]
        df_good = df[~bad_data_mask]

        # Adicionar registros estáticos ao DataFrame de dados bons
        static_data = [
            {'data': '15/02/2026', 'horario_ajustado': '13:10', 'nome_do_paciente': 'BRANDON AGUIAR', 'nome_do_medico': 'LEANDRO TETSUO OKAMURA', 'telefone': '(11) 95904 4561', 'telefone_ajustado': '5511959044561'},
            {'data': '20/03/2026', 'horario_ajustado': '08:40', 'nome_do_paciente': 'KARINE COFRAT', 'nome_do_medico': 'LEANDRO TETSUO OKAMURA', 'telefone': '(11) 97140-2433', 'telefone_ajustado': '5511971402433'}
        ]
        df_static = pd.DataFrame(static_data)
        df_good = pd.concat([df_static, df_good], ignore_index=True)

        # Identificar pacientes com múltiplos agendamentos pelo NOME
        good_name_counts = df_good['nome_do_paciente'].value_counts()
        repeated_names = good_name_counts[good_name_counts > 1].index
        df_repeated = df_good[df_good['nome_do_paciente'].isin(repeated_names)].sort_values(by=['nome_do_paciente', 'data', 'horario_ajustado'])

        final_columns_order = [
            'data', 'horario_ajustado', 'nome_do_paciente',
            'nome_do_medico', 'telefone', 'telefone_ajustado'
        ]
        
        # Garante que todos os dataframes tenham as colunas na ordem correta
        available_cols = [c for c in final_columns_order if c in df_good.columns]
        
        df_good_final = df_good[available_cols]
        df_bad_final = df_bad[available_cols] if not df_bad.empty else pd.DataFrame(columns=available_cols)
        df_repeated_final = df_repeated[available_cols] if not df_repeated.empty else pd.DataFrame(columns=available_cols)

        return df_good_final, df_bad_final, df_repeated_final, stats

    # --- Interface do Streamlit ---

    if 'edited_df' not in st.session_state:
        st.session_state.edited_df = None
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None
    if 'bad_df' not in st.session_state:
        st.session_state.bad_df = None
    if 'stats' not in st.session_state:
        st.session_state.stats = None
    if 'repeated_df' not in st.session_state:
        st.session_state.repeated_df = None

    st.title("Central de Disparos")
    st.caption("Clínica de Ortopedia e Terapia")
    st.divider()

    st.subheader("1. Carregar Arquivo de Agendamentos (.csv)")
    
    # --- NOVO: Dropdown para selecionar o tipo de arquivo (Incluindo RPG) ---
    file_type_option = st.selectbox(
        "Selecione o tipo de arquivo:",
        options=["Consultas", "Acupuntura", "RPG"],
        index=0,
        help="Escolha 'Consultas' para o layout padrão ou 'Acupuntura'/'RPG' para o layout de serviços."
    )
    # -------------------------------------------------------

    uploaded_file = st.file_uploader("Selecione o arquivo CSV", type=["csv"], key="csv_uploader")

    if uploaded_file is not None:
        # Reseta o estado se mudar o arquivo OU o tipo de arquivo
        current_file_key = f"{uploaded_file.name}_{file_type_option}"
        
        if current_file_key != st.session_state.uploaded_file_name:
            st.session_state.edited_df = None
            st.session_state.bad_df = None
            st.session_state.stats = None
            st.session_state.repeated_df = None
            st.session_state.uploaded_file_name = current_file_key
        
        if st.session_state.edited_df is None and st.button("⚙️ Processar Arquivo", use_container_width=True, type="primary"):
            with st.spinner("Processando e analisando a qualidade dos dados..."):
                try:
                    # Passa o file_type_option para a função
                    good_df, bad_df, repeated_df, stats = process_and_clean_csv(uploaded_file, file_type_option)
                    
                    if good_df.empty and bad_df.empty:
                        st.warning("Nenhum dado foi encontrado. Verifique se selecionou o 'Tipo de Arquivo' correto.")
                    else:
                        good_df.insert(0, 'Selecionar', False)
                        st.session_state.edited_df = good_df
                        st.session_state.bad_df = bad_df
                        st.session_state.repeated_df = repeated_df
                        st.session_state.stats = stats
                        st.success("Arquivo processado!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar o arquivo: {e}")

    if st.session_state.edited_df is not None:
        st.header("Visão Geral dos Agendamentos")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Registros Carregados", st.session_state.stats.get('total', 0))
        col2.metric("Pacientes Únicos (por telefone)", st.session_state.stats.get('unique', 0))
        col3.metric("Pacientes com Múltiplos Agendamentos", st.session_state.stats.get('repeated', 0))
        
        st.header("Agendamentos Válidos para Envio")
        st.subheader("2. Selecione os Pacientes")
        
        def toggle_all():
            new_value = st.session_state.select_all_checkbox
            df_copy = st.session_state.edited_df.copy()
            df_copy['Selecionar'] = new_value
            st.session_state.edited_df = df_copy

        all_selected = st.session_state.edited_df['Selecionar'].all() if not st.session_state.edited_df.empty else False
        st.checkbox("Selecionar Todos", value=all_selected, on_change=toggle_all, key="select_all_checkbox")
        
        edited_df_output = st.data_editor(st.session_state.edited_df, use_container_width=True, hide_index=True, disabled=st.session_state.edited_df.columns.drop('Selecionar'))
        st.session_state.edited_df = edited_df_output

        # --- SEÇÃO: TABELA DE PACIENTES COM MÚLTIPLOS AGENDAMENTOS ---
        if st.session_state.repeated_df is not None and not st.session_state.repeated_df.empty:
            st.subheader("Pacientes com Múltiplos Agendamentos na Mesma Carga")
            st.write("A tabela abaixo destaca os pacientes que possuem mais de um agendamento no arquivo carregado, para facilitar a verificação.")
            
            # Seleciona colunas relevantes para exibição
            display_cols_repeated = ['data', 'horario_ajustado', 'nome_do_paciente', 'nome_do_medico', 'telefone_ajustado']
            # Filtra colunas que realmente existem
            display_cols_repeated = [c for c in display_cols_repeated if c in st.session_state.repeated_df.columns]
            
            st.dataframe(
                st.session_state.repeated_df[display_cols_repeated],
                use_container_width=True,
                hide_index=True
            )
        # --- FIM DA SEÇÃO ---

        st.divider()

        # Estatísticas de Qualidade e Tabela de Dados Ruins
        if st.session_state.bad_df is not None and not st.session_state.bad_df.empty:
            st.subheader("Análise de Qualidade dos Dados")
            total_records = st.session_state.stats.get('total', 0)
            bad_records = st.session_state.stats.get('bad_total', 0)
            percentage_bad = (bad_records / total_records) * 100 if total_records > 0 else 0
            
            col_dq1, col_dq2 = st.columns(2)
            col_dq1.metric("Total de Registros com Problemas", f"{bad_records}")
            col_dq2.metric("Percentual de Problemas", f"{percentage_bad:.2f}%")

            col_dq3, col_dq4 = st.columns(2)
            col_dq3.metric("Problema: Telefone Nulo/Vazio", f"{st.session_state.stats.get('bad_empty', 0)}")
            col_dq4.metric("Problema: Comprimento Inválido", f"{st.session_state.stats.get('bad_length', 0)}")

            st.write("Os registros abaixo foram removidos da lista de envio devido aos problemas de dados identificados.")
            st.dataframe(st.session_state.bad_df, use_container_width=True, hide_index=True)
            st.divider()

        # --- ALTERAÇÃO AQUI: Removida a seleção de template ---
        st.subheader("3. Enviar Mensagens")
        st.write(f"O disparo será realizado considerando o tipo: **{file_type_option}**.")
        
        selected_count = int(st.session_state.edited_df['Selecionar'].sum())
        if st.button(f"✉️ Enviar Mensagens ({selected_count})", use_container_width=True, type="primary"):
            if selected_count > 0:
                selected_rows_df = st.session_state.edited_df[st.session_state.edited_df['Selecionar']].copy().fillna('')
                contacts_payload = selected_rows_df.to_dict(orient='records')
                
                # Payload sem template_name, apenas appointment_type
                final_payload = {
                    "appointment_type": file_type_option,
                    "contacts": contacts_payload
                }
                
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
        # ------------------------------------------------------
                
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
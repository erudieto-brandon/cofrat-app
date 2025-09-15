import streamlit as st
import pika
import json
import uuid
from supabase import create_client, Client
import time

# --- Configurações ---
st.set_page_config(page_title="Chat Assíncrono", layout="wide")

# Conexão com Supabase (deve estar nos seus secrets)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Erro ao conectar com o Supabase. Verifique suas credenciais em secrets.toml.")
    st.stop()

st.title("🤖 Chat Assíncrono com n8n e RabbitMQ")
st.write("Este é um exemplo de arquitetura assíncrona. A pergunta é enviada para uma fila e processada em segundo plano.")

# --- Funções com Autenticação Correta ---

def send_question_to_queue(question_text, task_id):
    """Publica a pergunta na fila do RabbitMQ com autenticação."""
    try:
        user = st.secrets["RABBITMQ_USER"]
        password = st.secrets["RABBITMQ_PASS"]
        host = st.secrets["RABBITMQ_HOST"]
        port = st.secrets["RABBITMQ_PORT"]
        vhost = st.secrets["RABBITMQ_VHOST"]

        rabbitmq_url = f"amqp://{user}:{password}@{host}:{port}/{vhost}"
        params = pika.URLParameters(rabbitmq_url)
        
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue='ai_questions', durable=True)

        message = {'task_id': task_id, 'question': question_text}
        
        channel.basic_publish(
            exchange='',
            routing_key='ai_questions',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
            
        connection.close()
        st.success(f"Sua pergunta foi enviada para a fila com o ID: {task_id}")
        return True
    except Exception as e:
        st.error(f"Falha ao conectar ou enviar mensagem para o RabbitMQ: {e}")
        return False

def check_for_response(task_id):
    """Verifica no Supabase se a resposta já chegou."""
    try:
        # Supondo que você tenha uma tabela 'ai_responses' com colunas 'task_id' e 'answer'
        response = supabase.table('ai_responses').select('answer').eq('task_id', task_id).execute()
        if response.data:
            return response.data[0]['answer']
        return None
    except Exception as e:
        st.warning(f"Não foi possível verificar a resposta no Supabase: {e}")
        return None

# --- Interface do Usuário ---
col1, col2 = st.columns(2)

with col1:
    st.header("Enviar Pergunta")
    user_question = st.text_area("Digite sua pergunta aqui:", height=150)

    if st.button("Enviar para Processamento 🚀"):
        if user_question:
            task_id = str(uuid.uuid4())
            st.session_state['last_task_id'] = task_id
            send_question_to_queue(user_question, task_id)
        else:
            st.warning("Por favor, digite uma pergunta.")

with col2:
    st.header("Verificar Resposta")
    if 'last_task_id' in st.session_state:
        st.write(f"ID da última tarefa enviada: `{st.session_state['last_task_id']}`")
        
        if st.button("Verificar Resposta Agora 🔄"):
            with st.spinner("Buscando resposta no banco de dados..."):
                task_id = st.session_state['last_task_id']
                answer = check_for_response(task_id)
                
                if answer:
                    st.balloons()
                    st.subheader("🎉 Resposta Recebida:")
                    st.markdown(answer)
                    # Opcional: limpar o ID da tarefa após receber a resposta
                    # del st.session_state['last_task_id']
                else:
                    st.info("A resposta ainda não está pronta. Tente novamente em alguns segundos.")
    else:
        st.info("Envie uma pergunta primeiro para poder verificar a resposta.")
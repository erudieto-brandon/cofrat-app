# test_supabase.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv # Instale com: pip install python-dotenv

# Carrega as variáveis de ambiente de um arquivo .env
# Crie um arquivo .env na mesma pasta com suas credenciais
# SUPABASE_URL=SUA_URL
# SUPABASE_KEY=SUA_SERVICE_KEY
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Erro: Certifique-se de criar um arquivo .env com SUPABASE_URL e SUPABASE_KEY")
else:
    try:
        print("Tentando conectar ao Supabase...")
        supabase: Client = create_client(url, key)
        print("Cliente Supabase criado com sucesso.")

        bucket_name = "s3" # Use o nome exato do seu bucket

        print(f"Listando buckets para verificar a conexão...")
        buckets = supabase.storage.list_buckets()
        print("Conexão bem-sucedida! Buckets encontrados:")
        for bucket in buckets:
            print(f"- {bucket.name}")

    except Exception as e:
        print(f"Ocorreu um erro durante o teste: {e}")
        print(f"Tipo do erro: {type(e)}")
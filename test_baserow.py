# Salve como test_baserow.py
import requests
import pandas as pd
import os
from dotenv import load_dotenv

def test_baserow_connection():
    """
    Função para testar a conexão com o Baserow e a transformação dos dados.
    """
    load_dotenv()
    BASEROW_KEY = os.getenv("BASEROW_KEY")

    if not BASEROW_KEY:
        print("Erro: A variável de ambiente BASEROW_KEY não está definida.")
        return

    url = "https://api.baserow.io/api/database/rows/table/681080/?user_field_names=true"
    headers = {"Authorization": f"Token {BASEROW_KEY}"}

    try:
        print("Fazendo a requisição para a API do Baserow...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print("Requisição bem-sucedida!")

        data = response.json().get('results', [])
        if not data:
            print("A API não retornou dados.")
            return

        df = pd.DataFrame(data)
        print("\n--- Colunas Originais Recebidas da API ---")
        print(df.columns.tolist())
        
        print("\n--- Primeiras 5 Linhas (Dados Originais) ---")
        print(df.head())

        column_mapping = {
            'Paciente': 'name',
            'Data Agendada': 'scheduled_date',
            'Profissional': 'professional',
            'Categoria': 'category',
            'Status': 'status'
        }
        
        df.rename(columns=column_mapping, inplace=True)

        required_cols = ['name', 'scheduled_date', 'professional', 'category', 'status']
        if not all(col in df.columns for col in required_cols):
            print("\nERRO: Nem todas as colunas necessárias foram encontradas após o mapeamento.")
            print(f"Colunas encontradas: {df.columns.tolist()}")
            return

        df['scheduled_date'] = pd.to_datetime(df['scheduled_date']).dt.date

        print("\n--- Primeiras 5 Linhas (Dados Prontos para o App) ---")
        print(df[required_cols].head())

    except requests.exceptions.HTTPError as e:
        print(f"Erro HTTP ao acessar a API: {e.response.status_code}")
        print(f"Resposta: {e.response.text}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == '__main__':
    # Para executar este teste:
    # 1. Crie um arquivo .env no mesmo diretório do script.
    # 2. Adicione sua chave ao arquivo .env: BASEROW_KEY="sua_chave_aqui"
    # 3. Instale as dependências: pip install requests pandas python-dotenv
    # 4. Execute o script no terminal: python test_baserow.py
    test_baserow_connection()
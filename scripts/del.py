import requests

# Dados da API
url = 'https://graph.facebook.com/v22.0/801077859762875/messages'  # Substitua pelo seu phone_number_id
access_token = 'EAAqlbxdDZBOgBPz9JCyf7WdcEV9dnr1iqoAlTNVhPMbcIFJpNvaTpXHHFoFPCPC1jUqV1ZAz2bgNVsLpswpkyvaOH7f7CVT0soSSIYOSeNCLfefku07ucjj6exltjuVdqnXbPbw5R9QCXpeFfUkOThLT9nbBM8smLcXADS36lapTfeL3zlqY45U2YpjAZDZD'  # Substitua pelo seu token de acesso

# Corpo da requisição
payload = {
    "messaging_product": "whatsapp",
    "to": "5511959044561",  # Número do destinatário com código do país
    "type": "text",
    "text": {
        "body":
        """
Olá, Brandon! Se você recebeu essa mensagem, então funcionou.
        """
    }
}

# Cabeçalhos
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Envio da requisição
response = requests.post(url, json=payload, headers=headers)

# Resultado
if response.status_code == 200:
    print("Mensagem enviada com sucesso!")
else:
    print(f"Erro ao enviar mensagem: {response.status_code}")
    print(response.text)

import requests

# Substitua pelos seus dados reais
waba_id = '1345055953751400'
access_token = 'EAAqlbxdDZBOgBP3TFNaaNgI19DwHRN6Lj4h4oY2DEkLZAvznGisfdAZARrw7MYh49onwZAp1hZCvJ8ZBtaxK8xuShae06zFHCfR7ZCLqeQyIH1VWVpwXYW4yJmlNQnKYNxVvfxAtBpZAWh9xgRrsszKnMjZBRCmF9KuZBMkrRxaW2d5YEfnvjarQ6NVN2RZAHM4H7itiYaI7imoUrhFjzpVkUaQLZC0JzqPFCtlxFqqv2fOIbAZDZD'  # Seu token de acesso

# URL da requisição
url = f'https://graph.facebook.com/v24.0/{waba_id}?fields=marketing_messages_onboarding_status'

# Cabeçalhos
headers = {
    'Authorization': f'Bearer {access_token}'
}

# Envio da requisição
response = requests.get(url, headers=headers)

# Resultado
if response.status_code == 200:
    data = response.json()
    status = data.get('marketing_messages_onboarding_status')
    print(f"Status de elegibilidade: {status}")
else:
    print(f"Erro ao consultar elegibilidade: {response.status_code}")
    print(response.text)

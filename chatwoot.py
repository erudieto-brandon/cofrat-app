import requests

url = "https://dev-chatwoot.vldzc8.easypanel.host/api/v1/accounts/2/conversations/10/labels"

payload = { "labels": ["label 1", "label 2"] }
headers = {
    "api_access_token": "etC1hQDDNdkp2n9nDnoHLJob",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
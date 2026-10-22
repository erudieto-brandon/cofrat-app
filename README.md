# Cofrat App

Aplicação Streamlit para gestão de atendimentos.

## Executando localmente

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute:
   ```bash
   streamlit run main.py
   ```
3. Abra `http://127.0.0.1:8501`.

## Deploy na Vercel

Este repositório agora inclui:
- [`vercel.json`](./vercel.json): roteia todo o tráfego para uma função Python.
- [`api/index.py`](./api/index.py): adapta o runtime da Vercel para iniciar o Streamlit e fazer proxy de HTTP/WebSocket para o app em [`main.py`](./main.py).

### Variáveis opcionais

- `STREAMLIT_ENTRYPOINT` (padrão: `main.py`)
- `STREAMLIT_INTERNAL_PORT` (padrão: `8501`)
- `STREAMLIT_BOOT_TIMEOUT_SECONDS` (padrão: `30`)

## Deploy alternativo (Railway)

O projeto mantém compatibilidade com Railway via [`railway.json`](./railway.json).

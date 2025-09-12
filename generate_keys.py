import streamlit_authenticator as stauth
import pickle
from pathlib import Path

# Lista de senhas em texto plano
passwords_to_hash = ['senha123']

# O método generate() recebe a lista de senhas
hashed_passwords = stauth.Hasher('ofkdaofkdosf').generate()

print(hashed_passwords)
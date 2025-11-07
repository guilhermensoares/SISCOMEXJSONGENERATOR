import streamlit as st
import json
import hashlib
import os

USERS_FILE = "users.json"

# Cria o arquivo se não existir
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

# Funções auxiliares
def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    users = load_users()
    if username in users:
        return users[username] == hash_password(password)
    return False

def add_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = hash_password(password)
    save_users(users)
    return True

# Interface de login
def login_screen():
    st.title("🔐 SISCOMEX JSON Generator - Login")

    menu = st.sidebar.radio("Menu", ["Login", "Cadastrar"])

    if menu == "Login":
        st.subheader("Acesse sua conta")
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if check_login(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha inválidos.")

    elif menu == "Cadastrar":
        st.subheader("Criar nova conta")
        new_user = st.text_input("Novo usuário")
        new_pass = st.text_input("Nova senha", type="password")
        if st.button("Criar conta"):
            if add_user(new_user, new_pass):
                st.success("Usuário criado com sucesso! Faça login no menu lateral.")
            else:
                st.warning("Este usuário já existe.")

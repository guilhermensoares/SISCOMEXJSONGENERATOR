import streamlit as st

# Simula um banco de dados de usuários
if "users" not in st.session_state:
    st.session_state["users"] = {"admin": "admin123"}

def login_screen():
    st.title("🔐 Login - SISCOMEX JSON Generator")

    aba = st.radio("Selecione uma opção:", ["Login", "Criar conta"])

    if aba == "Login":
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            users = st.session_state["users"]
            if username in users and users[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("Login realizado com sucesso!")
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    else:
        new_user = st.text_input("Novo usuário")
        new_pass = st.text_input("Nova senha", type="password")
        if st.button("Criar conta"):
            if new_user in st.session_state["users"]:
                st.warning("Usuário já existe.")
            else:
                st.session_state["users"][new_user] = new_pass
                st.success("Usuário criado! Faça login na aba anterior.")

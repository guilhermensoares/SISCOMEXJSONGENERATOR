import streamlit as st
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_screen():
    # Inicializa as variáveis da sessão, se ainda não existirem
    if "users" not in st.session_state:
        st.session_state["users"] = {"admin": hash_password("admin123")}
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""

    st.markdown("## 🔐 Login - SISCOMEX JSON Generator")
    option = st.radio("Selecione uma opção:", ["Login", "Criar conta"])

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar" if option == "Login" else "Criar"):
        if option == "Login":
            users = st.session_state["users"]
            if username in users and users[username] == hash_password(password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("Login realizado com sucesso!")
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        else:
            users = st.session_state["users"]
            if username in users:
                st.warning("Este usuário já existe.")
            else:
                st.session_state["users"][username] = hash_password(password)
                st.success("Conta criada com sucesso! Faça login.")

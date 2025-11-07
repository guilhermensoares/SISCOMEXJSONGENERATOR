import streamlit as st
import json
import os

def login_screen():
    if "users" not in st.session_state:
        st.session_state["users"] = {}

    users = st.session_state["users"]

    # Tenta carregar os usuários do arquivo
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            st.session_state["users"] = json.load(f)
            users = st.session_state["users"]

    st.markdown("## 🔐 Login - SISCOMEX JSON Generator")
    option = st.radio("Selecione uma opção:", ("Login", "Criar conta"))

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if option == "Login":
            if username in users and users[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("Login realizado com sucesso!")
                st.rerun()  # <- substituto de experimental_rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        else:  # Criar conta
            if username in users:
                st.error("Usuário já existe.")
            else:
                users[username] = password
                with open("users.json", "w") as f:
                    json.dump(users, f)
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("Conta criada e login realizado!")
                st.rerun()  # <- substituto de experimental_rerun()

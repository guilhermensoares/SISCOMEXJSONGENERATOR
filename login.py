import streamlit as st

def login_screen():
    if "users" not in st.session_state:
        st.session_state.users = {"admin": "admin123"}

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    st.markdown("<h2 style='text-align: center;'>🔐 Login - SISCOMEX JSON Generator</h2>", unsafe_allow_html=True)

    option = st.radio("Selecione uma opção:", ("Login", "Criar conta"))

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if option == "Login":
            if username in st.session_state.users and st.session_state.users[username] == password:
                st.success("Login realizado com sucesso!")
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        elif option == "Criar conta":
            if username in st.session_state.users:
                st.warning("Usuário já existe. Escolha outro nome.")
            else:
                st.session_state.users[username] = password
                st.success("Conta criada com sucesso! Você já pode fazer login.")

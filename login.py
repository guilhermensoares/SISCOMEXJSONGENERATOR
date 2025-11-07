import streamlit as st

# Dicionário de usuários (você pode expandir isso depois)
def get_users():
    return {
        "admin": "admin123"
    }

def login_screen():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.markdown("## 🔐 Login - SISCOMEX JSON Generator")
        opcao = st.radio("Selecione uma opção:", ["Login", "Criar conta"])

        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            users = get_users()
            if username in users and users[username] == password:
                st.success("Login realizado com sucesso!")
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        st.stop()

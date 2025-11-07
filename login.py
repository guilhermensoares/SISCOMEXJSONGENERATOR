import streamlit as st

def login_screen():
    st.markdown("<h2 style='text-align: center;'>🔐 Login - SISCOMEX JSON Generator</h2>", unsafe_allow_html=True)

    opcao = st.radio("Selecione uma opção:", ("Login", "Criar conta"), horizontal=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        usuario = st.text_input("Usuário", key="usuario")
        senha = st.text_input("Senha", type="password", key="senha")

        if st.button("Entrar"):
            if usuario == "admin" and senha == "admin123":
                st.success("Login realizado com sucesso!")
                st.session_state["logged_in"] = True
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha inválidos.")

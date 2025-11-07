from PIL import Image
import streamlit as st
from process_catalogo import processar_catalogo
from process_vinculos import processar_vinculos
from login import login_screen

st.set_page_config(page_title="SISCOMEX JSON Generator", layout="centered")

# Tela de login
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login_screen()
    st.stop()

# Cabeçalho
col1, col2 = st.columns([1, 4])
with col1:
    st.image("logo-novo-preto.png", width=120)
with col2:
    st.title("SISCOMEX JSON Generator")
    st.caption("Transforme planilhas em JSONs válidos com facilidade 🚀")

# Menu principal
aba = st.tabs(["📦 Gerar Catálogo", "🔗 Gerar Vínculos"])

with aba[0]:
    st.header("📁 Entrada de dados")
    excel_file = st.file_uploader("Arquivo Excel", type=["xlsx"])
    cnpj = st.text_input("CNPJ", value="04307549")
    tamanho = st.number_input("Tamanho do lote", min_value=1, value=5)

    if st.button("🚀 Gerar JSONs"):
        if not excel_file:
            st.warning("Por favor, envie um arquivo Excel.")
        else:
            resultados = processar_catalogo(excel_file, cnpj, tamanho)
            for i, (nome, conteudo) in enumerate(resultados.items()):
                st.download_button(
                    label=f"📥 Baixar JSON - Lote {i+1}",
                    file_name=nome,
                    mime="application/json",
                    data=conteudo.encode("utf-8"),
                    key=f"catalogo_{i}"
                )

with aba[1]:
    st.header("🔗 Geração de vínculos")
    excel_vinc = st.file_uploader("Arquivo Excel de Vínculos", type=["xlsx"], key="vinc")
    if st.button("🔗 Gerar JSON de Vínculos"):
        if not excel_vinc:
            st.warning("Envie um arquivo Excel com os vínculos.")
        else:
            nome, conteudo = processar_vinculos(excel_vinc)
            st.download_button(
                label="📥 Baixar JSON de Vínculos",
                file_name=nome,
                mime="application/json",
                data=conteudo.encode("utf-8"),
                key="vinculo"
            )

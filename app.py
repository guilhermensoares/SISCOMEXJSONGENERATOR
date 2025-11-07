import streamlit as st
from PIL import Image
from login import login_screen
from process_catalogo import processar_catalogo
from process_vinculos import processar_vinculos

# Logo
logo = Image.open("logo-novo-preto.png")
st.image(logo, width=130)
st.markdown("<h1 style='text-align: center;'>SISCOMEX JSON Generator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Transforme planilhas em JSONs válidos com facilidade 🚀</p>", unsafe_allow_html=True)

# Autenticação
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    login_screen()
    st.stop()

# Tabs
aba = st.tabs(["📁 Gerar Catálogo", "🔗 Gerar Vínculos"])

# 📁 Aba 1: Catálogo
with aba[0]:
    st.markdown("### 📥 Entrada de dados")

    file = st.file_uploader("Arquivo Excel", type=["xlsx"])
    cnpj = st.text_input("CNPJ", value="04307549", max_chars=14)
    lote = st.number_input("Tamanho do lote", min_value=1, step=1, value=100)

    if st.button("🚀 Gerar JSONs"):
        if file and cnpj:
            processar_catalogo(file, cnpj, lote)
        else:
            st.warning("Por favor, preencha todos os campos e selecione um arquivo.")

# 🔗 Aba 2: Vínculos
with aba[1]:
    st.markdown("### 🔄 Geração de vínculos")

    cnpj_vinculos = st.text_input("CNPJ", value="04307549", max_chars=14)
    file_siscomex = st.file_uploader("CSV exportado do SISCOMEX", type=["csv"])
    file_base = st.file_uploader("Sua base de dados", type=["xlsx"])

    if st.button("🔗 Gerar JSON de Vínculos"):
        if file_siscomex and file_base and cnpj_vinculos:
            processar_vinculos(file_siscomex, file_base, cnpj_vinculos)
        else:
            st.warning("Por favor, preencha todos os campos e envie os arquivos.")

# Rodapé com crédito
st.markdown("""
<hr style="margin-top: 2rem; margin-bottom: 1rem;">
<div style='text-align: center;'>
    Desenvolvido por <a href="https://br.linkedin.com/in/guilhermensoares" target="_blank">
    <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" width="15" style="vertical-align: middle; margin-right: 4px;">
    Guilherme N. Soares</a>
</div>
""", unsafe_allow_html=True)

import streamlit as st
from PIL import Image
from login import login_screen
from process_catalogo import processar_catalogo
from process_vinculos import processar_vinculos

# Login
login_screen()

# Logo
logo = Image.open("logo-novo-preto.png")
st.image(logo, width=130)
st.markdown('<h1 style="text-align: center;">SISCOMEX JSON Generator</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center;">Transforme planilhas em JSONs válidos com facilidade 🚀</p>', unsafe_allow_html=True)

# Abas
aba = st.tabs(["📁 Gerar Catálogo", "🔗 Gerar Vínculos"])

# ==========================
# Aba 1: Catálogo
# ==========================
with aba[0]:
    st.markdown("### 📝 Entrada de dados")

    file = st.file_uploader("Arquivo Excel", type=["xlsx"])
    cnpj = st.text_input("CNPJ", value="04307549", max_chars=14)
    lote = st.number_input("Tamanho do lote", min_value=1, step=1, value=100)

    if st.button("🚀 Gerar JSONs"):
        if file and cnpj:
            processar_catalogo(file, cnpj, lote)
        else:
            st.warning("Por favor, preencha todos os campos e selecione um arquivo.")

# ==========================
# Aba 2: Vínculos
# ==========================
with aba[1]:
    st.markdown("### 🔁 Geração de vínculos")

    st.markdown("**CSV exportado do SISCOMEX**")
    csv_siscomex = st.file_uploader("Drag and drop file here", type=["csv"], key="csv1")

    st.markdown("**Sua base de dados**")
    excel_base = st.file_uploader("Drag and drop file here", type=["xlsx"], key="xlsx2")

    cnpj_vinculos = st.text_input("CNPJ", value="04307549", max_chars=14, key="cnpj_vinculos")

    if st.button("🔗 Gerar JSON de Vínculos"):
        if csv_siscomex and excel_base and cnpj_vinculos:
            processar_vinculos(csv_siscomex, excel_base, cnpj_vinculos)
        else:
            st.warning("Por favor, preencha todos os campos e selecione os arquivos.")

# ==========================
# Rodapé com LinkedIn
# ==========================
st.markdown(
    """
    <hr style="margin-top: 3rem; margin-bottom: 1rem;">
    <div style="text-align: center;">
        Desenvolvido por <a href="https://br.linkedin.com/in/guilhermensoares" target="_blank">
        <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg" width="18" style="vertical-align: middle; margin-bottom: 2px;">
        Guilherme N. Soares</a>
    </div>
    """,
    unsafe_allow_html=True
)

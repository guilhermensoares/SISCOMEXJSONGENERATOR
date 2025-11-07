import streamlit as st
from PIL import Image
from login import login_screen
from process_catalogo import processar_catalogo
from process_vinculos import processar_vinculos

# Inicializa as variáveis de sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "users" not in st.session_state:
    st.session_state.users = {"admin": "admin123"}

# Verifica se está logado
if not st.session_state.authenticated:
    login_screen()
    st.stop()

# Logo
logo = Image.open("logo-novo-preto.png")
st.image(logo, width=130)
st.markdown(
    "<h1 style='text-align: center;'>SISCOMEX JSON Generator</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center;'>Transforme planilhas em JSONs válidos com facilidade 🚀</p>",
    unsafe_allow_html=True
)

aba = st.tabs(["📁 Gerar Catálogo", "🔗 Gerar Vínculos"])

# Aba 1: Catálogo
with aba[0]:
    st.markdown("### 🗂️ Entrada de dados")
    file = st.file_uploader("Arquivo Excel", type=["xlsx"])
    cnpj = st.text_input("CNPJ", max_chars=14)
    lote = st.number_input("Tamanho do lote", min_value=1, step=1, value=5)

    if st.button("⚙️ Gerar JSONs"):
        if file and cnpj:
            processar_catalogo(file, cnpj, lote)
        else:
            st.warning("Por favor, preencha todos os campos e selecione um arquivo.")

# Aba 2: Vínculos
with aba[1]:
    st.markdown("### 🔗 Geração de vínculos")
    siscomex_file = st.file_uploader("Arquivo CSV exportado do SISCOMEX", type=["csv"], key="csv1")
    base_file = st.file_uploader("Base de dados Excel", type=["xlsx"], key="xlsx2")

    if st.button("📎 Gerar JSON de Vínculos"):
        if siscomex_file and base_file:
            processar_vinculos(siscomex_file, base_file)
        else:
            st.warning("Por favor, selecione os dois arquivos.")

# Rodapé com créditos e LinkedIn
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; font-size: 14px;'>
        Desenvolvido por <strong>Guilherme Nascimento Soares</strong><br>
        <a href='https://br.linkedin.com/in/guilhermensoares' target='_blank'>
            <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' width='16' style='vertical-align:middle; margin-right:4px;'>LinkedIn
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

from PIL import Image
import streamlit as st
from process_catalogo import processar_catalogo
from process_vinculos import processar_vinculos

# Configuração da página
st.set_page_config(page_title="SISCOMEX JSON Generator", layout="centered")

# Tela de login
from login import login_screen

# Inicializa o estado do login
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login_screen()
else:
    st.sidebar.success(f"🔓 Logado como: {st.session_state['username']}")

    # Logo
    logo = Image.open("logo_king.png")
    st.image(logo, width=130)
    st.markdown("<h1 style='text-align: center;'>SISCOMEX JSON Generator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Transforme planilhas em JSONs válidos com facilidade 🚀</p>", unsafe_allow_html=True)

    aba = st.tabs(["📦 Gerar Catálogo", "🔗 Gerar Vínculos"])

    # 📦 Aba 1: Catálogo
    with aba[0]:
        st.markdown("### 📁 Entrada de dados")
        file = st.file_uploader("Arquivo Excel", type=["xlsx"])
        cnpj = st.text_input("CNPJ", max_chars=14)
        lote = st.number_input("Tamanho do lote", min_value=1, step=1, value=5)

        if st.button("⚙️ Gerar JSONs"):
            if file and cnpj:
                processar_catalogo(file, cnpj, lote)
            else:
                st.warning("Por favor, preencha todos os campos e selecione um arquivo.")

    # 🔗 Aba 2: Vínculos
    with aba[1]:
        st.markdown("### 🔗 Geração de vínculos")
        arquivo_siscomex = st.file_uploader("Arquivo Excel de Vínculos (exportado do SISCOMEX)", type=["xlsx"], key="vinc1")
        arquivo_base = st.file_uploader("Arquivo Excel com Base de Dados (NCM, etc)", type=["xlsx"], key="vinc2")

        if st.button("🔗 Gerar JSON de Vínculos"):
            if arquivo_siscomex and arquivo_base:
                processar_vinculos(arquivo_siscomex, arquivo_base)
            else:
                st.warning("Por favor, selecione os dois arquivos necessários.")

    # Rodapé com créditos
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; font-size: 14px;'>
            Desenvolvido por <strong>Guilherme Soares</strong> |
            <a href='https://br.linkedin.com/in/guilhermensoares' target='_blank'>
                <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' width='16' style='vertical-align:middle;'> LinkedIn
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

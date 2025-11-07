import streamlit as st
from PIL import Image
from login import login_screen
from process_catalogo import processar_catalogo
from process_vinculos import processar_vinculos

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_screen()
    else:
        render_app()

def render_app():
    logo = Image.open("logo-novo-preto.png")
    st.image(logo, width=130)

    st.markdown("<h1 style='text-align: center;'>SISCOMEX JSON Generator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Transforme planilhas em JSONs válidos com facilidade 🚀</p>", unsafe_allow_html=True)

    aba = st.tabs(["📁 Gerar Catálogo", "🔗 Gerar Vínculos"])

    with aba[0]:
        st.markdown("### 📥 Entrada de dados")
        file = st.file_uploader("Arquivo Excel", type=["xlsx"])
        cnpj = st.text_input("CNPJ", value="04307549", max_chars=14, key="cnpj_catalogo")
        lote = st.number_input("Tamanho do lote", min_value=1, step=1, value=100)

        if st.button("🚀 Gerar JSONs"):
            if file and cnpj:
                processar_catalogo(file, cnpj, lote)
            else:
                st.warning("Por favor, preencha todos os campos e selecione um arquivo.")

    with aba[1]:
        st.markdown("### 🔄 Geração de vínculos")
        csv_file = st.file_uploader("CSV exportado do SISCOMEX", type=["csv"])
        excel_file = st.file_uploader("Sua base de dados", type=["xlsx"])
        cnpj_vinculos = st.text_input("CNPJ", value="04307549", max_chars=14, key="cnpj_vinculos")

        if st.button("🔗 Gerar JSON de Vínculos"):
            if csv_file and excel_file and cnpj_vinculos:
                processar_vinculos(csv_file, excel_file, cnpj_vinculos)
            else:
                st.warning("Por favor, preencha todos os campos e selecione os arquivos.")

    st.markdown("""
    <hr>
    <div style='text-align: center; font-size: 14px;'>
        Desenvolvido por <b>Guilherme Soares</b> 🧠 | Supply Chain | Versão 1.0 <br>
        🔧 Powered by Python + Streamlit <br><br>
        <a href='https://br.linkedin.com/in/guilhermensoares' target='_blank'>
            <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' width='20' style='vertical-align:middle; margin-right:8px;'/>
            LinkedIn
        </a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

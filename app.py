import streamlit as st
from login import login_form
from process_catalogo import processar_catalogo
from process_vinculos import processar_vinculos

st.set_page_config(
    page_title="Gerador SISCOMEX JSON",
    layout="wide",
)

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    login_form()
else:
    # Interface
    st.markdown("<h1 style='text-align: center;'>📦 Gerador de JSON SISCOMEX</h1>", unsafe_allow_html=True)

    aba = st.selectbox("Escolha a função desejada:", ["Gerar Catálogo de Produtos", "Gerar Vínculos Fabricante–Exportador"])

    if aba == "Gerar Catálogo de Produtos":
        st.header("📁 Upload da planilha de produtos")
        excel_file = st.file_uploader("Selecione o arquivo Excel com os produtos", type=["xlsx"])

        col1, col2 = st.columns(2)
        with col1:
            cnpj = st.text_input("CNPJ Raiz (8 dígitos)", value="04307549")
        with col2:
            tamanho = st.number_input("Tamanho do lote", min_value=1, value=100, step=1)

        if excel_file and st.button("📤 Gerar JSONs de Catálogo"):
            with st.spinner("Processando catálogo..."):
                resultados = processar_catalogo(excel_file, cnpj, tamanho)
                st.success(f"{len(resultados)} lote(s) gerado(s).")
                for nome, buffer in resultados:
                    st.download_button(label=f"📥 Baixar {nome}", data=buffer, file_name=nome, mime="application/json")

    elif aba == "Gerar Vínculos Fabricante–Exportador":
        st.header("📁 Upload dos arquivos necessários")
        csv_file = st.file_uploader("CSV exportado do SISCOMEX", type=["csv"])
        excel_file = st.file_uploader("Planilha base de produtos", type=["xlsx"])

        col1, col2 = st.columns(2)
        with col1:
            cnpj = st.text_input("CNPJ Raiz (8 dígitos)", value="04307549", key="cnpj_vinculos")
        with col2:
            tamanho = st.number_input("Tamanho do lote", min_value=1, value=100, step=1, key="lote_vinculos")

        if csv_file and excel_file and st.button("📤 Gerar JSONs de Vínculos"):
            with st.spinner("Processando vínculos..."):
                resultados = processar_vinculos(csv_file, excel_file, cnpj, tamanho)
                st.success(f"{len(resultados)} lote(s) gerado(s).")
                for nome, buffer in resultados:
                    st.download_button(label=f"📥 Baixar {nome}", data=buffer, file_name=nome, mime="application/json")

    # Créditos no rodapé
    st.markdown("""
        <hr>
        <div style='text-align: center; font-size: 14px;'>
            Desenvolvido por <b>Guilherme Soares</b> – Supply Chain | Versão 1.0 <br>
            🛠️ Powered by Python + Streamlit <br><br>
            <a href='https://br.linkedin.com/in/guilhermensoares' target='_blank'>
                <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' width='20' style='vertical-align:middle; margin-right:5px;'>
                LinkedIn
            </a>
        </div>
    """, unsafe_allow_html=True)

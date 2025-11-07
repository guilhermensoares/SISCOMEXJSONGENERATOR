from PIL import Image
import streamlit as st
from process_catalogo import processar_catalogo
from process_vinculos import processar_vinculos
from login import login_screen

st.set_page_config(page_title="SISCOMEX JSON Generator", layout="centered")

if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login_screen()
    st.stop()

col1, col2 = st.columns([1, 4])
with col1:
    st.image("logo-novo-preto.png", width=120)
with col2:
    st.title("SISCOMEX JSON Generator")
    st.caption("Transforme planilhas em JSONs válidos com facilidade 🚀")

abas = st.tabs(["📦 Gerar Catálogo", "🔗 Gerar Vínculos"])

with abas[0]:
    st.header("📁 Entrada de dados")
    excel_file = st.file_uploader("Arquivo Excel", type=["xlsx"])
    cnpj = st.text_input("CNPJ", value="04307549")
    tamanho = st.number_input("Tamanho do lote", min_value=1, value=5)

    if st.button("🚀 Gerar JSONs"):
        if not excel_file:
            st.warning("Por favor, envie um arquivo Excel.")
        else:
            resultados = processar_catalogo(excel_file, cnpj, tamanho)
            for nome, buffer in resultados:
                st.download_button(
                    label=f"📥 Baixar {nome}",
                    file_name=nome,
                    mime="application/json",
                    data=buffer,
                    key=nome
                )

with abas[1]:
    st.header("🔗 Geração de vínculos")
    csv_file = st.file_uploader("CSV exportado do SISCOMEX", type=["csv"])
    excel_vinc = st.file_uploader("Base de dados (Excel)", type=["xlsx"], key="vinc")
    cnpj = st.text_input("CNPJ da empresa", value="04307549", key="vinc_cnpj")
    tamanho = st.number_input("Tamanho do lote", min_value=1, value=5, key="vinc_lote")

    if st.button("🔗 Gerar JSONs de Vínculos"):
        if not csv_file or not excel_vinc:
            st.warning("Envie ambos os arquivos.")
        else:
            arquivos = processar_vinculos(csv_file, excel_vinc, cnpj, tamanho)
            for nome, conteudo in arquivos:
                ext = "csv" if nome.endswith(".csv") else "json"
                st.download_button(
                    label=f"📥 Baixar {nome}",
                    file_name=nome,
                    mime="text/csv" if ext == "csv" else "application/json",
                    data=conteudo,
                    key=nome
                )

# Rodapé com créditos
st.markdown(
    """
    <hr style='margin-top: 3rem;'>
    <div style='text-align: center; color: gray; font-size: 0.9rem;'>
        Desenvolvido por <strong>Guilherme Soares</strong> – Supply Chain<br>
        <em>Versão 1.3 | 🛠️ Powered by Python + Streamlit</em><br><br>
        <a href="https://br.linkedin.com/in/guilhermensoares" target="_blank" style="text-decoration: none;">
            <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg" alt="LinkedIn" width="22" style="vertical-align: middle; margin-right: 6px;">
            <span style="vertical-align: middle;">LinkedIn</span>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)


from PIL import Image
import streamlit as st
from process_catalogo import processar_catalogo
from process_vinculos import processar_vinculos

st.set_page_config(page_title="SISCOMEX JSON Generator", layout="centered")

from PIL import Image

# === LOGO CENTRALIZADA COM TÍTULO ===
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    logo = Image.open("logo-novo-preto.png")  # ou "logo.png"
    st.image(logo, width=260)
    st.markdown("<h1 style='text-align:center;'>SISCOMEX JSON Generator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Transforme planilhas em JSONs válidos com facilidade 🚀</p>", unsafe_allow_html=True)

# === ABAS ===
aba_catalogo, aba_vinculos = st.tabs(["📦 Gerar Catálogo", "🔗 Gerar Vínculos"])

# === ABA 1 – CATÁLOGO ===
with aba_catalogo:
    st.subheader("📁 Entrada de dados")
    excel_file = st.file_uploader("Arquivo Excel", type=["xls", "xlsx"])
    cnpj = st.text_input("CNPJ", value="04307549")
    tamanho = st.number_input("Tamanho do lote", min_value=1, value=5)
    
    if st.button("🚀 Gerar JSONs", key="catalogo"):
        if not excel_file or not cnpj:
            st.error("Por favor, preencha todos os campos.")
        else:
            with st.spinner("Gerando JSONs de catálogo..."):
                resultados = processar_catalogo(excel_file, cnpj, tamanho)
            st.success(f"✅ {len(resultados)} arquivos gerados!")
            for nome, dados in resultados:
                st.download_button(f"⬇️ Baixar {nome}", data=dados, file_name=nome, mime="application/json")

    st.markdown(
        "<div style='background-color:#f9f9f9;padding:10px;border-radius:8px;'>"
        "💡 <b>Dica:</b> Use planilhas atualizadas e revise os dados antes de gerar o JSON.</div>",
        unsafe_allow_html=True
    )

# === ABA 2 – VÍNCULOS ===
with aba_vinculos:
    st.subheader("📁 Entrada de dados")
    csv_file = st.file_uploader("Arquivo CSV do SISCOMEX", type=["csv"])
    planilha_file = st.file_uploader("Planilha base Excel", type=["xls", "xlsx"])
    cnpj_v = st.text_input("CNPJ", value="04307549", key="cnpjv")
    tamanho_v = st.number_input("Tamanho do lote", min_value=1, value=100, key="tamanhov")
    
    if st.button("🚀 Gerar JSONs", key="vinculos"):
        if not csv_file or not planilha_file or not cnpj_v:
            st.error("Por favor, preencha todos os campos.")
        else:
            with st.spinner("Gerando JSONs de vínculos..."):
                resultados = processar_vinculos(csv_file, planilha_file, cnpj_v, tamanho_v)
            st.success(f"✅ {len(resultados)} arquivos gerados!")
            for nome, dados in resultados:
                st.download_button(f"⬇️ Baixar {nome}", data=dados, file_name=nome, mime="application/json")

    st.markdown(
        "<div style='background-color:#f9f9f9;padding:10px;border-radius:8px;'>"
        "💡 <b>Dica:</b> O CSV deve vir diretamente do SISCOMEX, sem alterações nos nomes das colunas.</div>",
        unsafe_allow_html=True
    )

# === RODAPÉ ===
st.markdown("""
---
<p style='text-align:center; font-size: 0.9em; color: grey'>
Desenvolvido por <b>Guilherme Soares - Supply Chain</b> | Versão 1.1 | 🛠️ Powered by Python + Streamlit
</p>
""", unsafe_allow_html=True)

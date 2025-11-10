import streamlit as st
from process_catalogo import processar_catalogo
from process_vinculos import processar_vinculos
from io import BytesIO
import base64

# Configuração da página
st.set_page_config(page_title="King Imports - SISCOMEX JSON Generator", layout="centered")

# Logo centralizado
def exibir_logo():
    try:
        with open("Logo_branca_600px.png", "rb") as img_file:
            logo_bytes = img_file.read()
            logo_base64 = base64.b64encode(logo_bytes).decode()
        st.markdown(
            f"""
            <div style="text-align:center">
                <img src="data:image/png;base64,{logo_base64}" width="250"/>
                <h2 style="margin-top: 10px;">SISCOMEX JSON Generator</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.warning("Logo não encontrada.")

# Autenticação básica
def autenticar(usuario, senha):
    usuarios_validos = {
        "admin": "1234",
        "estagiaria": "1234"
    }
    return usuarios_validos.get(usuario) == senha

# Tela de login
def tela_login():
    st.markdown("## Acesso Restrito")
    usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
    senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
    if st.button("Entrar"):
        if autenticar(usuario, senha):
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

# Tela principal
def tela_principal():
    exibir_logo()

    aba = st.radio("Escolha o tipo de geração:", ["Catálogo de Produtos", "Vínculo Fabricante–Exportador"], horizontal=True)

    resultados = []

    with st.form("form_json"):
        cnpj = st.text_input("CNPJ Raiz", value="04307549", max_chars=8)
        tamanho = st.number_input("Quantidade por lote", min_value=1, value=100)

        # Inputs de arquivos
        if aba == "Catálogo de Produtos":
            st.markdown("### Upload da Planilha de Itens (Excel - Base Atualizada)")
            planilha = st.file_uploader("Selecione a planilha (.xlsx)", type=["xlsx"], key="planilha")
        else:
            st.markdown("### Upload dos Arquivos de Vínculo")
            csv = st.file_uploader("CSV exportado do SISCOMEX", type=["csv"], key="csv_vinculo")
            excel = st.file_uploader("Base de dados King Imports (planilha Excel)", type=["xlsx"], key="excel_vinculo")

        gerar = st.form_submit_button("Gerar JSON")

    # ⚠️ Processamento e download FORA do form
    if gerar:
        if not cnpj:
            st.error("Por favor, preencha o CNPJ.")
            return

        try:
            if aba == "Catálogo de Produtos":
                if not planilha:
                    st.error("Por favor, envie a planilha.")
                else:
                    resultados = processar_catalogo(planilha, cnpj, tamanho)

            else:  # Vínculo Fabricante–Exportador
                if not csv or not excel:
                    st.error("Por favor, envie ambos os arquivos.")
                else:
                    resultados = processar_vinculos(csv, excel, cnpj, tamanho)

            # Download fora do form
            for nome_arquivo, buffer in resultados:
                st.download_button(
                    label=f"📥 Baixar {nome_arquivo}",
                    data=buffer,
                    file_name=nome_arquivo,
                    mime="application/json"
                )

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar: {e}")

    # Rodapé com créditos
    st.markdown("""
        <hr style="margin-top: 40px; margin-bottom: 10px;">
        <div style='text-align: center; font-size: 14px;'>
            Desenvolvido por Guilherme Soares - Supply Chain | Versão 1.7<br>
            🛠️ Powered by Python + Streamlit |
            <a href='https://br.linkedin.com/in/guilhermensoares' target='_blank' style='text-decoration: none;'>
                <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' width='16' style='vertical-align: middle;'/> Acompanhe o criador no Linkedin
            </a>
        </div>
    """, unsafe_allow_html=True)

# Controle de acesso
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    tela_login()
else:
    tela_principal()

import base64
from pathlib import Path

import streamlit as st

from process_catalogo import processar_catalogo
from process_edicao_json import editar_jsons_catalogo
from process_vinculos import processar_vinculos

# Configuração da página
st.set_page_config(page_title="King Imports - SISCOMEX JSON Generator", layout="centered")


# Logo centralizado
def exibir_logo():
    caminhos_logo = [
        "Logo_branca_600px.png",
        "Logo_branca_600px(1).png",
        "logo-novo-preto.png",
        "logo-novo-preto(1).png",
    ]

    caminho_encontrado = next((Path(c) for c in caminhos_logo if Path(c).exists()), None)

    if not caminho_encontrado:
        st.warning("Logo não encontrada.")
        return

    with open(caminho_encontrado, "rb") as img_file:
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


def _render_download_jsons(resultados):
    for nome_arquivo, buffer in resultados:
        st.download_button(
            label=f"📥 Baixar {nome_arquivo}",
            data=buffer,
            file_name=nome_arquivo,
            mime="application/json"
        )


# Tela principal
def tela_principal():
    exibir_logo()

    aba = st.radio(
        "Escolha o tipo de operação:",
        [
            "Catálogo de Produtos",
            "Vínculo Fabricante–Exportador",
            "Editar JSON Gerado"
        ],
        horizontal=True
    )

    resultados = []

    with st.form("form_json"):
        if aba in ["Catálogo de Produtos", "Vínculo Fabricante–Exportador"]:
            cnpj = st.text_input("CNPJ Raiz", value="04307549", max_chars=8)
            tamanho = st.number_input("Quantidade por lote", min_value=1, value=100)
        else:
            cnpj = ""
            tamanho = 100

        # Inputs de arquivos
        if aba == "Catálogo de Produtos":
            st.markdown("### Upload da Planilha de Itens (Excel - Base Atualizada)")
            planilha = st.file_uploader("Selecione a planilha (.xlsx)", type=["xlsx"], key="planilha")
            gerar = st.form_submit_button("Gerar JSON")

        elif aba == "Vínculo Fabricante–Exportador":
            st.markdown("### Upload dos Arquivos de Vínculo")
            csv = st.file_uploader("CSV exportado do SISCOMEX", type=["csv"], key="csv_vinculo")
            excel = st.file_uploader("Base de dados King Imports (planilha Excel)", type=["xlsx"], key="excel_vinculo")
            gerar = st.form_submit_button("Gerar JSON")

        else:
            st.markdown("### Edição em Massa de JSON já Gerado")
            st.caption(
                "Use esta rotina para corrigir o campo codigosInterno em arquivos JSON de catálogo. "
                "Ela remove o sufixo .0, preserva 5 dígitos e também permite um de/para opcional."
            )
            json_files = st.file_uploader(
                "Selecione um ou mais JSONs de catálogo",
                type=["json"],
                accept_multiple_files=True,
                key="json_edicao"
            )

            st.markdown("#### De/Para opcional")
            usar_de_para = st.checkbox("Aplicar uma planilha de de/para além da normalização automática")
            if usar_de_para:
                arquivo_de_para = st.file_uploader(
                    "Planilha de de/para (.xlsx ou .csv)",
                    type=["xlsx", "csv"],
                    key="de_para_codigos"
                )
                coluna_de = st.text_input("Coluna do código atual/original", value="SKU_ORIGINAL")
                coluna_para = st.text_input("Coluna do código novo/final", value="SKU_NOVO")
            else:
                arquivo_de_para = None
                coluna_de = "SKU_ORIGINAL"
                coluna_para = "SKU_NOVO"

            gerar = st.form_submit_button("Processar JSON")

    # Processamento e download fora do form
    if gerar:
        try:
            if aba == "Catálogo de Produtos":
                if not cnpj:
                    st.error("Por favor, preencha o CNPJ.")
                    return
                if not planilha:
                    st.error("Por favor, envie a planilha.")
                    return
                resultados = processar_catalogo(planilha, cnpj, tamanho)
                _render_download_jsons(resultados)

            elif aba == "Vínculo Fabricante–Exportador":
                if not cnpj:
                    st.error("Por favor, preencha o CNPJ.")
                    return
                if not csv or not excel:
                    st.error("Por favor, envie ambos os arquivos.")
                    return
                resultados = processar_vinculos(csv, excel, cnpj, tamanho)
                _render_download_jsons(resultados)

            else:
                if not json_files:
                    st.error("Por favor, envie ao menos um JSON para editar.")
                    return
                if arquivo_de_para is None and usar_de_para:
                    st.error("Você marcou de/para, mas não enviou a planilha.")
                    return

                resultados, log_df, zip_buffer = editar_jsons_catalogo(
                    json_files,
                    arquivo_de_para=arquivo_de_para,
                    coluna_de=coluna_de,
                    coluna_para=coluna_para
                )

                st.success(f"Processamento concluído. Códigos alterados: {len(log_df)}")
                st.dataframe(log_df, use_container_width=True)

                st.download_button(
                    label="📦 Baixar todos os JSONs corrigidos + log (.zip)",
                    data=zip_buffer,
                    file_name="jsons_catalogo_corrigidos.zip",
                    mime="application/zip"
                )

                _render_download_jsons(resultados)

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar: {e}")

    # Rodapé com créditos
    st.markdown("""
        <hr style="margin-top: 40px; margin-bottom: 10px;">
        <div style='text-align: center; font-size: 14px;'>
            Desenvolvido por Guilherme Soares - Supply Chain | Versão 1.9<br>
             Powered by Python + Streamlit |
            <a href='https://br.linkedin.com/in/guilhermensoares' target='_blank' style='text-decoration: none;'>
                <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' width='16' style='vertical-align: middle;'/> Acompanhe o criador no Linkedin
            </a>
        </div>
    """, unsafe_allow_html=True)


# Entrada direta no aplicativo, sem tela de login
tela_principal()

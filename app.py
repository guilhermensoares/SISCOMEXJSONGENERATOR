import base64
from pathlib import Path

import streamlit as st

from process_catalogo import processar_catalogo
from process_edicao_json import editar_jsons_catalogo, gerar_bodies_retificacao
from process_vinculos import processar_vinculos


st.set_page_config(page_title="King Imports - SISCOMEX JSON Generator", layout="centered")


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
        unsafe_allow_html=True,
    )


def _render_download_jsons(resultados):
    for nome_arquivo, buffer in resultados:
        st.download_button(
            label=f"📥 Baixar {nome_arquivo}",
            data=buffer,
            file_name=nome_arquivo,
            mime="application/json",
        )


def tela_principal():
    exibir_logo()

    aba = st.radio(
        "Escolha o tipo de operação:",
        [
            "Catálogo de Produtos",
            "Vínculo Fabricante–Exportador",
            "Corrigir JSON de Lote",
            "Gerar Body de Retificação",
        ],
        horizontal=False,
    )

    with st.form("form_json"):
        if aba in ["Catálogo de Produtos", "Vínculo Fabricante–Exportador"]:
            cnpj = st.text_input("CNPJ Raiz", value="04307549", max_chars=8)
            tamanho = st.number_input("Quantidade por lote", min_value=1, value=100)
        else:
            cnpj = ""
            tamanho = 100

        if aba == "Catálogo de Produtos":
            st.markdown("### Upload da Planilha de Itens (Excel - Base Atualizada)")
            planilha = st.file_uploader("Selecione a planilha (.xlsx)", type=["xlsx"], key="planilha")
            gerar = st.form_submit_button("Gerar JSON")

        elif aba == "Vínculo Fabricante–Exportador":
            st.markdown("### Upload dos Arquivos de Vínculo")
            csv = st.file_uploader("CSV exportado do SISCOMEX", type=["csv"], key="csv_vinculo")
            excel = st.file_uploader("Base de dados King Imports (planilha Excel)", type=["xlsx"], key="excel_vinculo")
            gerar = st.form_submit_button("Gerar JSON")

        elif aba == "Corrigir JSON de Lote":
            st.markdown("### Corrigir JSON de lote já gerado")
            st.caption(
                "Mantém a mesma estrutura de cadastro em lote, mas corrige codigosInterno. "
                "Exemplo: 53907.0 → 53907."
            )
            json_files = st.file_uploader(
                "Selecione um ou mais JSONs de catálogo",
                type=["json"],
                accept_multiple_files=True,
                key="json_edicao_lote",
            )

            st.markdown("#### De/Para opcional")
            usar_de_para = st.checkbox("Aplicar planilha de de/para")
            if usar_de_para:
                arquivo_de_para = st.file_uploader(
                    "Planilha de de/para (.xlsx ou .csv)",
                    type=["xlsx", "csv"],
                    key="de_para_codigos_lote",
                )
                coluna_de = st.text_input("Coluna do código atual/original", value="SKU_ORIGINAL")
                coluna_para = st.text_input("Coluna do código novo/final", value="SKU_NOVO")
            else:
                arquivo_de_para = None
                coluna_de = "SKU_ORIGINAL"
                coluna_para = "SKU_NOVO"

            gerar = st.form_submit_button("Corrigir JSON")

        else:
            st.markdown("### Gerar body de edição/retificação")
            st.caption(
                "Converte o JSON de lote para o body aceito na edição/retificação de produto existente. "
                "Remove seq, cpfCnpjRaiz, situacao e fabricantesProdutores. "
                "Também corrige codigosInterno."
            )
            json_files = st.file_uploader(
                "Selecione um ou mais JSONs de lote do catálogo",
                type=["json"],
                accept_multiple_files=True,
                key="json_retificacao",
            )

            st.markdown("#### De/Para opcional de SKU")
            usar_de_para = st.checkbox("Aplicar planilha de de/para para codigosInterno", key="chk_de_para_ret")
            if usar_de_para:
                arquivo_de_para = st.file_uploader(
                    "Planilha de de/para (.xlsx ou .csv)",
                    type=["xlsx", "csv"],
                    key="de_para_codigos_ret",
                )
                coluna_de = st.text_input("Coluna do código atual/original", value="SKU_ORIGINAL", key="col_de_ret")
                coluna_para = st.text_input("Coluna do código novo/final", value="SKU_NOVO", key="col_para_ret")
            else:
                arquivo_de_para = None
                coluna_de = "SKU_ORIGINAL"
                coluna_para = "SKU_NOVO"

            st.markdown("#### Path da API opcional")
            st.caption(
                "Para gerar pacote com path + body, envie uma planilha com SKU, código do produto Siscomex e versão. "
                "Se não enviar, o app gera apenas os bodies."
            )
            usar_path = st.checkbox("Tenho planilha com Código Produto Siscomex e Versão", key="chk_path_ret")
            if usar_path:
                arquivo_path = st.file_uploader(
                    "Planilha de path (.xlsx ou .csv)",
                    type=["xlsx", "csv"],
                    key="path_ret",
                )
                coluna_sku_path = st.text_input("Coluna SKU", value="SKU")
                coluna_codigo_path = st.text_input("Coluna Código Produto Siscomex", value="CODIGO_PRODUTO_SISCOMEX")
                coluna_versao_path = st.text_input("Coluna Versão", value="VERSAO")
            else:
                arquivo_path = None
                coluna_sku_path = "SKU"
                coluna_codigo_path = "CODIGO_PRODUTO_SISCOMEX"
                coluna_versao_path = "VERSAO"

            gerar = st.form_submit_button("Gerar body de retificação")

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

            elif aba == "Corrigir JSON de Lote":
                if not json_files:
                    st.error("Por favor, envie ao menos um JSON para corrigir.")
                    return
                if usar_de_para and arquivo_de_para is None:
                    st.error("Você marcou de/para, mas não enviou a planilha.")
                    return

                resultados, log_df, zip_buffer = editar_jsons_catalogo(
                    json_files,
                    arquivo_de_para=arquivo_de_para,
                    coluna_de=coluna_de,
                    coluna_para=coluna_para,
                )

                st.success(f"Processamento concluído. Códigos alterados: {len(log_df)}")
                st.dataframe(log_df, use_container_width=True)

                st.download_button(
                    label="📦 Baixar JSONs corrigidos + log (.zip)",
                    data=zip_buffer,
                    file_name="jsons_catalogo_corrigidos.zip",
                    mime="application/zip",
                )
                _render_download_jsons(resultados)

            else:
                if not json_files:
                    st.error("Por favor, envie ao menos um JSON de lote.")
                    return
                if usar_de_para and arquivo_de_para is None:
                    st.error("Você marcou de/para, mas não enviou a planilha.")
                    return
                if usar_path and arquivo_path is None:
                    st.error("Você marcou path da API, mas não enviou a planilha.")
                    return

                bodies, manifest_df, log_df, zip_buffer = gerar_bodies_retificacao(
                    json_files,
                    arquivo_de_para=arquivo_de_para,
                    coluna_de=coluna_de,
                    coluna_para=coluna_para,
                    arquivo_path=arquivo_path,
                    coluna_sku_path=coluna_sku_path,
                    coluna_codigo_path=coluna_codigo_path,
                    coluna_versao_path=coluna_versao_path,
                )

                st.success(f"Bodies gerados: {len(bodies)}")
                st.markdown("#### Manifesto")
                st.dataframe(manifest_df, use_container_width=True)
                st.markdown("#### Log de normalização")
                st.dataframe(log_df, use_container_width=True)

                st.download_button(
                    label="📦 Baixar pacote de retificação (.zip)",
                    data=zip_buffer,
                    file_name="pacote_bodies_retificacao_siscomex.zip",
                    mime="application/zip",
                )

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar: {e}")

    st.markdown(
        """
        <hr style="margin-top: 40px; margin-bottom: 10px;">
        <div style='text-align: center; font-size: 14px;'>
            Desenvolvido por Guilherme Soares - Supply Chain | Versão 2.0<br>
            Powered by Python + Streamlit |
            <a href='https://br.linkedin.com/in/guilhermensoares' target='_blank' style='text-decoration: none;'>
                <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' width='16' style='vertical-align: middle;'/> Acompanhe o criador no Linkedin
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )


tela_principal()

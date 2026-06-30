import base64
from pathlib import Path

import streamlit as st

from process_catalogo import LIMITE_REGISTROS_POR_ARQUIVO as LIMITE_CATALOGO
from process_catalogo import processar_catalogo
from process_edicao_json import editar_jsons_catalogo, gerar_bodies_retificacao
from process_vinculos import LIMITE_REGISTROS_POR_ARQUIVO as LIMITE_VINCULOS
from process_vinculos import processar_vinculos


LIMITE_REGISTROS_POR_ARQUIVO = 100
DOWNLOAD_CACHE_KEY = "downloads_gerados_siscomex"

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


def _buffer_para_bytes(buffer) -> bytes:
    """Converte BytesIO/bytes em bytes para manter downloads após o rerun do Streamlit."""
    if isinstance(buffer, bytes):
        return buffer
    if isinstance(buffer, bytearray):
        return bytes(buffer)
    if hasattr(buffer, "getvalue"):
        return buffer.getvalue()
    return bytes(buffer)


def _normalizar_resultados_para_cache(resultados):
    return [(nome_arquivo, _buffer_para_bytes(buffer)) for nome_arquivo, buffer in resultados]


def _render_download_jsons(resultados):
    for nome_arquivo, buffer in resultados:
        st.download_button(
            label=f"📥 Baixar {nome_arquivo}",
            data=buffer,
            file_name=nome_arquivo,
            mime="application/json",
        )


def _salvar_downloads(aba, mensagem_sucesso, jsons=None, zip_info=None, tabelas=None):
    """Guarda os arquivos gerados para que os botões de download permaneçam na tela."""
    st.session_state[DOWNLOAD_CACHE_KEY] = {
        "aba": aba,
        "mensagem_sucesso": mensagem_sucesso,
        "jsons": _normalizar_resultados_para_cache(jsons or []),
        "zip_info": zip_info,
        "tabelas": tabelas or [],
    }


def _render_downloads_salvos(aba):
    cache = st.session_state.get(DOWNLOAD_CACHE_KEY)
    if not cache or cache.get("aba") != aba:
        return

    st.success(cache.get("mensagem_sucesso", "Arquivos gerados."))

    for titulo, dataframe in cache.get("tabelas", []):
        if titulo:
            st.markdown(titulo)
        st.dataframe(dataframe, use_container_width=True)

    zip_info = cache.get("zip_info")
    if zip_info:
        st.download_button(
            label=zip_info["label"],
            data=zip_info["data"],
            file_name=zip_info["file_name"],
            mime=zip_info["mime"],
        )

    _render_download_jsons(cache.get("jsons", []))


def _alerta_loteamento():
    st.info(
        f"Regra fixa: todos os arquivos consolidados são gerados com no máximo "
        f"{LIMITE_REGISTROS_POR_ARQUIVO} registros por arquivo."
    )


def tela_principal():
    exibir_logo()
    _alerta_loteamento()

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

    cache_atual = st.session_state.get(DOWNLOAD_CACHE_KEY)
    if cache_atual and cache_atual.get("aba") != aba:
        st.session_state.pop(DOWNLOAD_CACHE_KEY, None)

    with st.form("form_json"):
        if aba in ["Catálogo de Produtos", "Vínculo Fabricante–Exportador"]:
            cnpj = st.text_input("CNPJ Raiz", value="04307549", max_chars=8)
            st.caption(
                "Quantidade por lote travada em 100 registros por arquivo, conforme limite operacional do Siscomex."
            )
        else:
            cnpj = ""

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
                "Mantém a estrutura de cadastro em lote, corrige codigosInterno e quebra a saída em arquivos de até 100 registros. "
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
                "Também corrige codigosInterno e quebra pacotes consolidados em arquivos de até 100 registros."
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
                resultados = processar_catalogo(planilha, cnpj)
                mensagem = f"Arquivos gerados: {len(resultados)} | Limite: {LIMITE_CATALOGO} registros por arquivo"
                _salvar_downloads(aba, mensagem, jsons=resultados)
                _render_downloads_salvos(aba)

            elif aba == "Vínculo Fabricante–Exportador":
                if not cnpj:
                    st.error("Por favor, preencha o CNPJ.")
                    return
                if not csv or not excel:
                    st.error("Por favor, envie ambos os arquivos.")
                    return
                resultados = processar_vinculos(csv, excel, cnpj)
                mensagem = f"Arquivos gerados: {len(resultados)} | Limite: {LIMITE_VINCULOS} registros por arquivo"
                _salvar_downloads(aba, mensagem, jsons=resultados)
                _render_downloads_salvos(aba)

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

                mensagem = (
                    f"Processamento concluído. Arquivos gerados: {len(resultados)} | "
                    f"Códigos alterados: {len(log_df)}"
                )
                _salvar_downloads(
                    aba,
                    mensagem,
                    jsons=resultados,
                    zip_info={
                        "label": "📦 Baixar JSONs corrigidos + log (.zip)",
                        "data": _buffer_para_bytes(zip_buffer),
                        "file_name": "jsons_catalogo_corrigidos.zip",
                        "mime": "application/zip",
                    },
                    tabelas=[("", log_df)],
                )
                _render_downloads_salvos(aba)

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

                mensagem = (
                    f"Bodies individuais gerados: {len(bodies)} | "
                    "Pacotes consolidados quebrados em lotes de até 100 registros"
                )
                _salvar_downloads(
                    aba,
                    mensagem,
                    zip_info={
                        "label": "📦 Baixar pacote de retificação (.zip)",
                        "data": _buffer_para_bytes(zip_buffer),
                        "file_name": "pacote_bodies_retificacao_siscomex.zip",
                        "mime": "application/zip",
                    },
                    tabelas=[("#### Manifesto", manifest_df), ("#### Log de normalização", log_df)],
                )
                _render_downloads_salvos(aba)

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar: {e}")

    if not gerar:
        _render_downloads_salvos(aba)

    st.markdown(
        """
        <hr style="margin-top: 40px; margin-bottom: 10px;">
        <div style='text-align: center; font-size: 14px;'>
            Desenvolvido por Guilherme Soares - Supply Chain | Versão 2.2<br>
            Powered by Python + Streamlit |
            <a href='https://br.linkedin.com/in/guilhermensoares' target='_blank' style='text-decoration: none;'>
                <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' width='16' style='vertical-align: middle;'/> Acompanhe o criador no Linkedin
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )


tela_principal()

import base64
from pathlib import Path

import streamlit as st

from process_catalogo import LIMITE_REGISTROS_POR_ARQUIVO as LIMITE_CATALOGO
from process_catalogo import processar_catalogo
from process_compactador_aplicacoes import processar_planilha_aplicacoes
from process_vinculador_siscomex import processar_csvs_siscomex
from process_vinculos import LIMITE_REGISTROS_POR_ARQUIVO as LIMITE_VINCULOS
from process_vinculos import processar_vinculos


LIMITE_REGISTROS_POR_ARQUIVO = 100
DOWNLOAD_CACHE_KEY = "downloads_gerados_siscomex"

st.set_page_config(page_title="King Imports - SISCOMEX JSON Generator", layout="centered")


def exibir_logo():
    caminhos_logo = [
        "Logo_branca_600px.png",
        "Logo_branca_600px(1).png",
        "Logo_branca_600px(2).png",
        "logo-novo-preto.png",
        "logo-novo-preto(1).png",
        "logo-novo-preto(2).png",
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


def _normalizar_arquivos_para_cache(arquivos):
    arquivos_normalizados = []
    for arquivo in arquivos or []:
        arquivos_normalizados.append({
            "label": arquivo["label"],
            "data": _buffer_para_bytes(arquivo["data"]),
            "file_name": arquivo["file_name"],
            "mime": arquivo["mime"],
        })
    return arquivos_normalizados


def _render_download_jsons(resultados):
    for nome_arquivo, buffer in resultados:
        st.download_button(
            label=f"📥 Baixar {nome_arquivo}",
            data=buffer,
            file_name=nome_arquivo,
            mime="application/json",
        )


def _render_download_arquivos(arquivos):
    for arquivo in arquivos:
        st.download_button(
            label=arquivo["label"],
            data=arquivo["data"],
            file_name=arquivo["file_name"],
            mime=arquivo["mime"],
        )


def _salvar_downloads(aba, mensagem_sucesso, jsons=None, arquivos=None, zip_info=None, tabelas=None):
    """Guarda os arquivos gerados para que os botões de download permaneçam na tela."""
    st.session_state[DOWNLOAD_CACHE_KEY] = {
        "aba": aba,
        "mensagem_sucesso": mensagem_sucesso,
        "jsons": _normalizar_resultados_para_cache(jsons or []),
        "arquivos": _normalizar_arquivos_para_cache(arquivos or []),
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

    _render_download_arquivos(cache.get("arquivos", []))
    _render_download_jsons(cache.get("jsons", []))


def _alerta_loteamento():
    st.info(
        f"Regra fixa: os JSONs de Catálogo e Vínculo são gerados com no máximo "
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
            "Compactador de Aplicações",
            "Vinculador Código Siscomex",
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

        elif aba == "Compactador de Aplicações":
            st.markdown("### Compactar aplicações na descrição da DUIMP")
            st.caption(
                "Lê a coluna de descrição e reduz repetições de aplicação por ano. "
                "Exemplo: BMW X1 2012 / BMW X1 2013 / BMW X1 2014 → BMW X1 2012 a 2014."
            )
            planilha_compactador = st.file_uploader(
                "Selecione a planilha de itens (.xlsx)",
                type=["xlsx"],
                key="planilha_compactador",
            )
            coluna_descricao = st.text_input("Coluna de descrição", value="DESCRIÇÃO")
            gerar = st.form_submit_button("Compactar aplicações")

        else:
            st.markdown("### Vincular SKU x Código Siscomex")
            st.caption(
                "Recebe um ou mais CSVs exportados do Catálogo de Produtos Siscomex, "
                "filtra apenas Situação = Ativado e gera a planilha SKU x código SISCOMEX."
            )
            csvs_siscomex = st.file_uploader(
                "Selecione os CSVs exportados do Siscomex",
                type=["csv"],
                accept_multiple_files=True,
                key="csvs_siscomex_vinculador",
            )
            gerar = st.form_submit_button("Gerar planilha SKU x Siscomex")

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

            elif aba == "Compactador de Aplicações":
                if not planilha_compactador:
                    st.error("Por favor, envie a planilha.")
                    return

                buffer_excel, df_compactado, log_df, qtd_alteradas = processar_planilha_aplicacoes(
                    planilha_compactador,
                    coluna_descricao=coluna_descricao,
                )

                mensagem = f"Planilha processada. Descrições alteradas: {qtd_alteradas}"
                _salvar_downloads(
                    aba,
                    mensagem,
                    arquivos=[{
                        "label": "📥 Baixar planilha com aplicações compactadas",
                        "data": buffer_excel,
                        "file_name": "planilha_aplicacoes_compactadas.xlsx",
                        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    }],
                    tabelas=[
                        ("#### Prévia da planilha processada", df_compactado.head(100)),
                        ("#### Log de descrições alteradas", log_df.head(200)),
                    ],
                )
                _render_downloads_salvos(aba)

            else:
                if not csvs_siscomex:
                    st.error("Por favor, envie ao menos um CSV exportado do Siscomex.")
                    return

                buffer_excel, df_final, log_df, arquivos_processados, arquivos_encontrados = processar_csvs_siscomex(
                    csvs_siscomex
                )

                mensagem = (
                    f"Planilha SKU x Siscomex gerada. Registros ativos: {len(df_final)} | "
                    f"CSVs processados: {arquivos_processados}/{arquivos_encontrados}"
                )
                tabelas = [("#### Prévia da vinculação SKU x código SISCOMEX", df_final.head(200))]
                if not log_df.empty:
                    tabelas.append(("#### Arquivos com inconsistência", log_df))

                _salvar_downloads(
                    aba,
                    mensagem,
                    arquivos=[{
                        "label": "📥 Baixar SKU_SISCOMEX_ATIVADOS_TODOS_ARQUIVOS.xlsx",
                        "data": buffer_excel,
                        "file_name": "SKU_SISCOMEX_ATIVADOS_TODOS_ARQUIVOS.xlsx",
                        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    }],
                    tabelas=tabelas,
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
            Desenvolvido por Guilherme Soares - Supply Chain | Versão 2.3<br>
            Powered by Python + Streamlit |
            <a href='https://br.linkedin.com/in/guilhermensoares' target='_blank' style='text-decoration: none;'>
                <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' width='16' style='vertical-align: middle;'/> Acompanhe o criador no Linkedin
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )


tela_principal()

from io import BytesIO

import pandas as pd


COL_CODIGO_PRODUTO = "Código do produto"
COL_CODIGO_INTERNO = "Código interno do produto"
COL_SITUACAO = "Situação"


def ler_csv_siscomex(arquivo_csv):
    """
    Lê o CSV do Siscomex usando vírgula como separador.
    Tenta primeiro utf-8-sig, depois utf-8 e latin-1.
    """
    encodings_tentar = ["utf-8-sig", "utf-8", "latin-1"]

    ultimo_erro = None
    for enc in encodings_tentar:
        try:
            if hasattr(arquivo_csv, "seek"):
                arquivo_csv.seek(0)

            return pd.read_csv(
                arquivo_csv,
                sep=",",
                encoding=enc,
                dtype=str,
            )
        except Exception as e:
            ultimo_erro = e
            continue

    raise ultimo_erro


def processar_csvs_siscomex(arquivos_csv):
    """
    Consolida os CSVs exportados do Catálogo Siscomex e retorna uma planilha
    SKU x código SISCOMEX apenas com registros em Situação = Ativado.

    Esta é a adaptação do script original de pasta/Tkinter para upload múltiplo no Streamlit.
    """
    if not arquivos_csv:
        raise ValueError("Envie ao menos um arquivo CSV exportado do Siscomex.")

    dfs = []
    erros = []

    for arquivo in arquivos_csv:
        nome_arquivo = getattr(arquivo, "name", "arquivo.csv")

        try:
            df = ler_csv_siscomex(arquivo)
            df.columns = [str(c).strip() for c in df.columns]

            colunas_necessarias = [COL_CODIGO_INTERNO, COL_CODIGO_PRODUTO, COL_SITUACAO]
            faltando = [c for c in colunas_necessarias if c not in df.columns]

            if faltando:
                erros.append({
                    "arquivo": nome_arquivo,
                    "erro": f"Colunas necessárias não encontradas: {faltando}",
                })
                continue

            df_ativos = df[
                df[COL_SITUACAO]
                .astype(str)
                .str.strip()
                .str.upper()
                .eq("ATIVADO")
            ].copy()

            df_filtrado = df_ativos[[COL_CODIGO_INTERNO, COL_CODIGO_PRODUTO]].copy()
            df_filtrado["arquivo_origem"] = nome_arquivo
            dfs.append(df_filtrado)

        except Exception as e:
            erros.append({"arquivo": nome_arquivo, "erro": str(e)})

    if not dfs:
        raise ValueError(
            "Nenhum arquivo pôde ser processado com itens 'Ativado'. "
            "Verifique se os CSVs possuem registros ativos e as colunas corretas."
        )

    df_final = pd.concat(dfs, ignore_index=True)
    df_final = df_final[[COL_CODIGO_INTERNO, COL_CODIGO_PRODUTO]].copy()
    df_final.columns = ["SKU", "código SISCOMEX"]

    buffer = BytesIO()
    df_final.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    log_df = pd.DataFrame(erros)
    if log_df.empty:
        log_df = pd.DataFrame(columns=["arquivo", "erro"])

    return buffer, df_final, log_df, len(dfs), len(arquivos_csv)

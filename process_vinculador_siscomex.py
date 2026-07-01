from io import BytesIO
from pathlib import Path
import re

import pandas as pd


COL_CODIGO_PRODUTO = "Código do produto"
COL_CODIGO_INTERNO = "Código interno do produto"
COL_SITUACAO = "Situação"
NOME_PLANILHA_VINCULOS = "SKU_SISCOMEX_ATIVADOS_TODOS_ARQUIVOS.xlsx"
COL_SKU_SAIDA = "SKU"
COL_CODIGO_SISCOMEX_SAIDA = "código SISCOMEX"


def _valor_vazio(valor) -> bool:
    try:
        return valor is None or pd.isna(valor)
    except Exception:
        return valor is None


def normalizar_sku_king(valor, tamanho: int = 5) -> str:
    """Normaliza SKU/código interno para evitar 12345.0 e preservar 5 dígitos."""
    if _valor_vazio(valor):
        return ""

    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if float(valor).is_integer():
            texto = str(int(valor))
        else:
            texto = str(valor)
    else:
        texto = str(valor)

    texto = texto.strip().replace("\u00a0", "")
    if re.fullmatch(r"\d+[\.,]0+", texto):
        texto = re.split(r"[\.,]", texto, maxsplit=1)[0]
    if texto.isdigit() and len(texto) < tamanho:
        texto = texto.zfill(tamanho)
    return texto


def normalizar_codigo_siscomex(valor) -> str:
    """Normaliza o código do produto Siscomex sem transformar em notação/decimal."""
    if _valor_vazio(valor):
        return ""

    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if float(valor).is_integer():
            texto = str(int(valor))
        else:
            texto = str(valor)
    else:
        texto = str(valor)

    texto = texto.strip().replace("\u00a0", "")
    if re.fullmatch(r"\d+[\.,]0+", texto):
        texto = re.split(r"[\.,]", texto, maxsplit=1)[0]
    return texto


def _resolver_coluna(df: pd.DataFrame, nome_desejado: str) -> str | None:
    """Resolve coluna por nome exato ou comparação case-insensitive."""
    if nome_desejado in df.columns:
        return nome_desejado

    alvo = str(nome_desejado).strip().upper()
    for coluna in df.columns:
        if str(coluna).strip().upper() == alvo:
            return coluna
    return None


def ler_csv_siscomex(arquivo_csv):
    """
    Lê CSV do Siscomex usando vírgula como separador.
    Aceita caminho de arquivo ou objeto de upload/arquivo.
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


def _extrair_vinculos_ativos_de_csvs(caminhos_csv) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    """Lê todos os CSVs e retorna vínculos ativos + log de erros + qtd processada."""
    dfs = []
    erros = []
    arquivos_processados = 0

    for caminho_csv in sorted(caminhos_csv, key=lambda p: str(p).lower()):
        nome_arquivo = getattr(caminho_csv, "name", str(caminho_csv))
        nome_arquivo = Path(nome_arquivo).name

        try:
            df = ler_csv_siscomex(caminho_csv)
            df.columns = [str(c).strip() for c in df.columns]

            col_codigo_interno = _resolver_coluna(df, COL_CODIGO_INTERNO)
            col_codigo_produto = _resolver_coluna(df, COL_CODIGO_PRODUTO)
            col_situacao = _resolver_coluna(df, COL_SITUACAO)

            faltando = []
            if not col_codigo_interno:
                faltando.append(COL_CODIGO_INTERNO)
            if not col_codigo_produto:
                faltando.append(COL_CODIGO_PRODUTO)
            if not col_situacao:
                faltando.append(COL_SITUACAO)

            if faltando:
                erros.append({
                    "arquivo": nome_arquivo,
                    "tipo": "erro_csv",
                    "mensagem": f"Colunas necessárias não encontradas: {faltando}",
                    "SKU": "",
                    "codigo_siscomex_csv": "",
                    "codigo_siscomex_planilha": "",
                })
                continue

            df_ativos = df[
                df[col_situacao]
                .astype(str)
                .str.strip()
                .str.upper()
                .eq("ATIVADO")
            ].copy()

            if df_ativos.empty:
                arquivos_processados += 1
                continue

            df_filtrado = df_ativos[[col_codigo_interno, col_codigo_produto]].copy()
            df_filtrado.columns = [COL_SKU_SAIDA, COL_CODIGO_SISCOMEX_SAIDA]
            df_filtrado[COL_SKU_SAIDA] = df_filtrado[COL_SKU_SAIDA].apply(normalizar_sku_king)
            df_filtrado[COL_CODIGO_SISCOMEX_SAIDA] = df_filtrado[COL_CODIGO_SISCOMEX_SAIDA].apply(normalizar_codigo_siscomex)
            df_filtrado["arquivo_origem"] = nome_arquivo
            df_filtrado = df_filtrado[
                df_filtrado[COL_SKU_SAIDA].ne("") &
                df_filtrado[COL_CODIGO_SISCOMEX_SAIDA].ne("")
            ].copy()

            dfs.append(df_filtrado)
            arquivos_processados += 1

        except Exception as e:
            erros.append({
                "arquivo": nome_arquivo,
                "tipo": "erro_csv",
                "mensagem": str(e),
                "SKU": "",
                "codigo_siscomex_csv": "",
                "codigo_siscomex_planilha": "",
            })

    if dfs:
        df_vinculos = pd.concat(dfs, ignore_index=True)
    else:
        df_vinculos = pd.DataFrame(columns=[COL_SKU_SAIDA, COL_CODIGO_SISCOMEX_SAIDA, "arquivo_origem"])

    log_df = pd.DataFrame(erros)
    if log_df.empty:
        log_df = pd.DataFrame(columns=[
            "arquivo", "tipo", "mensagem", "SKU", "codigo_siscomex_csv", "codigo_siscomex_planilha"
        ])

    return df_vinculos, log_df, arquivos_processados


def _ler_planilha_existente(caminho_planilha: Path) -> pd.DataFrame:
    """Lê a planilha SKU x Siscomex existente; se não existir, cria estrutura vazia."""
    if not caminho_planilha.exists():
        return pd.DataFrame(columns=[COL_SKU_SAIDA, COL_CODIGO_SISCOMEX_SAIDA])

    df = pd.read_excel(caminho_planilha, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]

    col_sku = _resolver_coluna(df, COL_SKU_SAIDA)
    col_codigo = _resolver_coluna(df, COL_CODIGO_SISCOMEX_SAIDA)

    if not col_sku or not col_codigo:
        raise ValueError(
            f"A planilha {NOME_PLANILHA_VINCULOS} precisa ter as colunas "
            f"'{COL_SKU_SAIDA}' e '{COL_CODIGO_SISCOMEX_SAIDA}'. "
            f"Colunas encontradas: {', '.join(map(str, df.columns))}"
        )

    if col_sku != COL_SKU_SAIDA:
        df = df.rename(columns={col_sku: COL_SKU_SAIDA})
    if col_codigo != COL_CODIGO_SISCOMEX_SAIDA:
        df = df.rename(columns={col_codigo: COL_CODIGO_SISCOMEX_SAIDA})

    df[COL_SKU_SAIDA] = df[COL_SKU_SAIDA].apply(normalizar_sku_king)
    df[COL_CODIGO_SISCOMEX_SAIDA] = df[COL_CODIGO_SISCOMEX_SAIDA].apply(normalizar_codigo_siscomex)

    return df


def _primeiro_codigo_por_sku(df_vinculos: pd.DataFrame) -> tuple[dict[str, str], pd.DataFrame]:
    """
    Mantém um código por SKU para preenchimento e registra conflitos quando
    o mesmo SKU aparece com mais de um código Siscomex nos CSVs.
    """
    mapa = {}
    conflitos = []

    for _, row in df_vinculos.iterrows():
        sku = row.get(COL_SKU_SAIDA, "")
        codigo = row.get(COL_CODIGO_SISCOMEX_SAIDA, "")
        arquivo = row.get("arquivo_origem", "")

        if not sku or not codigo:
            continue

        if sku not in mapa:
            mapa[sku] = codigo
        elif mapa[sku] != codigo:
            conflitos.append({
                "arquivo": arquivo,
                "tipo": "conflito_csv",
                "mensagem": "Mesmo SKU encontrado com mais de um código Siscomex nos CSVs. Mantido o primeiro código encontrado.",
                "SKU": sku,
                "codigo_siscomex_csv": codigo,
                "codigo_siscomex_planilha": mapa[sku],
            })

    log_conflitos = pd.DataFrame(conflitos)
    if log_conflitos.empty:
        log_conflitos = pd.DataFrame(columns=[
            "arquivo", "tipo", "mensagem", "SKU", "codigo_siscomex_csv", "codigo_siscomex_planilha"
        ])
    return mapa, log_conflitos


def processar_pasta_siscomex(caminho_pasta: str):
    """
    Replica o fluxo original do vinculador:
    - lê a pasta inteira informada;
    - abre todos os CSVs exportados do Catálogo Siscomex;
    - abre/cria SKU_SISCOMEX_ATIVADOS_TODOS_ARQUIVOS.xlsx na mesma pasta;
    - preenche apenas os SKUs sem vínculo/códigos faltantes;
    - salva a planilha atualizada na própria pasta.
    """
    if not caminho_pasta or not str(caminho_pasta).strip():
        raise ValueError("Informe o caminho da pasta onde estão os CSVs do Siscomex.")

    pasta = Path(str(caminho_pasta).strip().strip('"'))
    if not pasta.exists() or not pasta.is_dir():
        raise ValueError(f"Pasta não encontrada: {pasta}")

    arquivos_csv = [p for p in pasta.iterdir() if p.is_file() and p.suffix.lower() == ".csv"]
    if not arquivos_csv:
        raise ValueError("Nenhum arquivo .csv encontrado na pasta informada.")

    caminho_planilha = pasta / NOME_PLANILHA_VINCULOS
    df_base = _ler_planilha_existente(caminho_planilha)
    total_existente_inicial = len(df_base)

    df_vinculos, log_csv, arquivos_processados = _extrair_vinculos_ativos_de_csvs(arquivos_csv)
    if df_vinculos.empty:
        raise ValueError(
            "Nenhum vínculo ativo foi encontrado nos CSVs. "
            "Verifique se os arquivos possuem registros com Situação = Ativado."
        )

    mapa_csv, log_conflitos_csv = _primeiro_codigo_por_sku(df_vinculos)

    # Garante colunas mínimas e preserva colunas extras que a planilha existente possa ter.
    if COL_SKU_SAIDA not in df_base.columns:
        df_base[COL_SKU_SAIDA] = ""
    if COL_CODIGO_SISCOMEX_SAIDA not in df_base.columns:
        df_base[COL_CODIGO_SISCOMEX_SAIDA] = ""

    skus_existentes = set(df_base[COL_SKU_SAIDA].astype(str).str.strip())
    atualizados = 0
    adicionados = 0
    ja_vinculados = 0
    conflitos_planilha = []

    # Preenche SKUs já existentes sem código.
    for idx, row in df_base.iterrows():
        sku = normalizar_sku_king(row.get(COL_SKU_SAIDA, ""))
        codigo_atual = normalizar_codigo_siscomex(row.get(COL_CODIGO_SISCOMEX_SAIDA, ""))
        codigo_csv = mapa_csv.get(sku, "")

        df_base.at[idx, COL_SKU_SAIDA] = sku
        df_base.at[idx, COL_CODIGO_SISCOMEX_SAIDA] = codigo_atual

        if not sku or not codigo_csv:
            continue

        if not codigo_atual:
            df_base.at[idx, COL_CODIGO_SISCOMEX_SAIDA] = codigo_csv
            atualizados += 1
        elif codigo_atual == codigo_csv:
            ja_vinculados += 1
        else:
            conflitos_planilha.append({
                "arquivo": "",
                "tipo": "conflito_planilha",
                "mensagem": "SKU já possui código Siscomex diferente na planilha. Código existente preservado.",
                "SKU": sku,
                "codigo_siscomex_csv": codigo_csv,
                "codigo_siscomex_planilha": codigo_atual,
            })

    # Adiciona SKUs novos que ainda não estavam na planilha.
    novas_linhas = []
    for sku, codigo in mapa_csv.items():
        if sku not in skus_existentes:
            novas_linhas.append({COL_SKU_SAIDA: sku, COL_CODIGO_SISCOMEX_SAIDA: codigo})
            skus_existentes.add(sku)
            adicionados += 1

    if novas_linhas:
        df_base = pd.concat([df_base, pd.DataFrame(novas_linhas)], ignore_index=True)

    # Remove linhas totalmente vazias e ordena pelo SKU, sem apagar colunas extras.
    df_base = df_base[df_base[COL_SKU_SAIDA].astype(str).str.strip().ne("")].copy()
    df_base = df_base.sort_values(by=COL_SKU_SAIDA, kind="stable").reset_index(drop=True)

    # Salva exatamente no arquivo operacional da pasta.
    df_base.to_excel(caminho_planilha, index=False, engine="openpyxl")

    buffer = BytesIO()
    df_base.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    logs = [log_csv, log_conflitos_csv]
    if conflitos_planilha:
        logs.append(pd.DataFrame(conflitos_planilha))

    log_df = pd.concat(logs, ignore_index=True) if logs else pd.DataFrame()
    if log_df.empty:
        log_df = pd.DataFrame(columns=[
            "arquivo", "tipo", "mensagem", "SKU", "codigo_siscomex_csv", "codigo_siscomex_planilha"
        ])

    estatisticas = {
        "caminho_planilha": str(caminho_planilha),
        "arquivos_csv_encontrados": len(arquivos_csv),
        "arquivos_csv_processados": arquivos_processados,
        "registros_ativos_lidos": len(df_vinculos),
        "skus_unicos_ativos": len(mapa_csv),
        "linhas_existentes_inicial": total_existente_inicial,
        "linhas_finais": len(df_base),
        "codigos_preenchidos_em_skus_existentes": atualizados,
        "skus_novos_adicionados": adicionados,
        "skus_ja_vinculados": ja_vinculados,
        "conflitos": len(log_df[log_df["tipo"].astype(str).str.contains("conflito", na=False)]) if "tipo" in log_df.columns else 0,
    }

    return buffer, df_base, log_df, estatisticas


def processar_csvs_siscomex(arquivos_csv):
    """
    Compatibilidade com a versão anterior da feature em Streamlit.
    Consolida uploads múltiplos em uma planilha nova, sem atualizar arquivo de pasta.
    """
    if not arquivos_csv:
        raise ValueError("Envie ao menos um arquivo CSV exportado do Siscomex.")

    df_vinculos, log_df, arquivos_processados = _extrair_vinculos_ativos_de_csvs(arquivos_csv)
    if df_vinculos.empty:
        raise ValueError(
            "Nenhum arquivo pôde ser processado com itens 'Ativado'. "
            "Verifique se os CSVs possuem registros ativos e as colunas corretas."
        )

    df_final = df_vinculos[[COL_SKU_SAIDA, COL_CODIGO_SISCOMEX_SAIDA]].copy()

    buffer = BytesIO()
    df_final.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    return buffer, df_final, log_df, arquivos_processados, len(arquivos_csv)

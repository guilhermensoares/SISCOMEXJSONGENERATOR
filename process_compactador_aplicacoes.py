import re
from io import BytesIO

import pandas as pd


# Correções ortográficas comuns mantidas a partir do script original.
correcoes = {
    r"\bERCEDES\b": "MERCEDES",
    r"\bBENZ\b": "MERCEDES",
    r"\bOLVO\b": "VOLVO",
    r"\bOLKSWAGEN\b": "VOLKSWAGEN",
    r"\bORSCHE\b": "PORSCHE",
}


_COLUNAS_CONTEXTO_LOG = [
    ("SKU", ["SKU", "COD. KING", "COD KING", "CÓD. KING", "CODIGO KING", "CÓDIGO KING", "COD. PRODUTO", "COD PRODUTO"]),
    ("COD FAB", ["COD FAB", "CÓD FAB", "COD. FAB", "CÓD. FAB", "COD FABRICANTE", "CÓD FABRICANTE", "COD. FABRICANTE", "CÓD. FABRICANTE"]),
    ("NCM", ["NCM"]),
    ("DESCRIÇÃO EM PORTUGUES", ["DESCRIÇÃO EM PORTUGUES", "DESCRIÇÃO EM PORTUGUÊS", "DESCRICAO EM PORTUGUES", "DESCRICAO EM PORTUGUÊS"]),
]


def compactar_anos(lista_anos):
    lista_anos = sorted(set(lista_anos))
    if not lista_anos:
        return []

    intervalos = []
    inicio = fim = lista_anos[0]

    for ano in lista_anos[1:]:
        if ano == fim + 1:
            fim = ano
        else:
            intervalos.append(f"{inicio}" if inicio == fim else f"{inicio} a {fim}")
            inicio = fim = ano

    intervalos.append(f"{inicio}" if inicio == fim else f"{inicio} a {fim}")
    return intervalos


def compactar_aplicacoes(trecho):
    trecho_original = trecho

    for errado, certo in correcoes.items():
        trecho = re.sub(errado, certo, trecho, flags=re.IGNORECASE)

    modelos = {}
    complexos = []

    entradas = re.split(r"\s*/\s*", trecho)
    for entrada in entradas:
        entrada = entrada.strip()
        match = re.match(r"(.+?)\s(\d{2,4})$", entrada)
        if match:
            modelo = match.group(1).strip().upper()
            ano = match.group(2)
            if len(ano) == 2:
                ano = "20" + ano if int(ano) < 30 else "19" + ano
            modelos.setdefault(modelo, []).append(int(ano))
        else:
            complexos.append(entrada)

    resultado = []
    for modelo, anos in modelos.items():
        anos_compactados = compactar_anos(anos)
        resultado.append(f"{modelo} {' / '.join(anos_compactados)}")

    return " / ".join(resultado + complexos) if (resultado or complexos) else trecho_original


def processar_descricao(descricao):
    descricao = str(descricao)

    for errado, certo in correcoes.items():
        descricao = re.sub(errado, certo, descricao, flags=re.IGNORECASE)

    padrao = re.compile(
        r"(?i)(com aplicação nos veículos automóveis:|com aplicação nos veiculos automoveis:|com aplicação:)(.*?)(\s*[-–\.]?\s*produto novo|\s*[-–\.]?\s*marca:)",
        re.IGNORECASE,
    )

    match = padrao.search(descricao)

    if match:
        prefixo, trecho_aplicacao, sufixo = match.groups()
        trecho_compactado = compactar_aplicacoes(trecho_aplicacao.strip())

        novo_trecho = f"{prefixo.strip()} {trecho_compactado.strip()} {sufixo.strip()}"
        novo_trecho = re.sub(r"\s*/\s*-\s*", " - ", novo_trecho)

        descricao = descricao.replace(match.group(0), novo_trecho)

    return descricao


def _resolver_coluna(df: pd.DataFrame, nome_coluna: str) -> str | None:
    if nome_coluna in df.columns:
        return nome_coluna

    alvo = str(nome_coluna).strip().upper()
    for coluna in df.columns:
        if str(coluna).strip().upper() == alvo:
            return coluna

    return None


def _resolver_primeira_coluna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    for candidato in candidatos:
        coluna = _resolver_coluna(df, candidato)
        if coluna:
            return coluna
    return None


def _montar_log_alteracoes(
    df_original: pd.DataFrame,
    coluna_descricao: str,
    descricoes_originais: pd.Series,
    descricoes_processadas: pd.Series,
) -> pd.DataFrame:
    mask = descricoes_originais != descricoes_processadas
    indices_alterados = list(df_original.index[mask])

    dados_log = {
        "linha_excel": [int(i) + 2 for i in indices_alterados],
    }

    for nome_saida, candidatos in _COLUNAS_CONTEXTO_LOG:
        coluna = _resolver_primeira_coluna(df_original, candidatos)
        if coluna:
            dados_log[nome_saida] = df_original.loc[mask, coluna].astype(str).tolist()

    originais = descricoes_originais.loc[mask].astype(str)
    compactadas = descricoes_processadas.loc[mask].astype(str)

    dados_log["descricao_original"] = originais.tolist()
    dados_log["descricao_compactada"] = compactadas.tolist()
    dados_log["caracteres_original"] = originais.str.len().astype(int).tolist()
    dados_log["caracteres_compactada"] = compactadas.str.len().astype(int).tolist()

    log_df = pd.DataFrame(dados_log)

    if not log_df.empty:
        log_df["reducao_caracteres"] = log_df["caracteres_original"] - log_df["caracteres_compactada"]
        log_df["reducao_%"] = (
            (log_df["reducao_caracteres"] / log_df["caracteres_original"].replace(0, pd.NA)) * 100
        ).round(2)
        log_df.insert(1, "coluna_alterada", coluna_descricao)

    return log_df


def processar_planilha_aplicacoes(planilha_file, coluna_descricao: str = "DESCRIÇÃO"):
    """
    Processa a planilha de itens compactando as aplicações dentro da coluna de descrição.

    Mantém a lógica do script Tkinter original, mas retorna um arquivo Excel em memória para
    download no Streamlit.
    """
    df = pd.read_excel(planilha_file, dtype=object)
    df.columns = [str(c).strip() for c in df.columns]

    coluna = _resolver_coluna(df, coluna_descricao)
    if not coluna:
        raise ValueError(
            f"Coluna '{coluna_descricao}' não encontrada. "
            f"Colunas disponíveis: {', '.join(map(str, df.columns))}"
        )

    df_original = df.copy()
    descricoes_originais = df[coluna].astype(str)
    descricoes_processadas = descricoes_originais.apply(processar_descricao)
    descricoes_processadas = descricoes_processadas.str.replace(r"\bBmw\b", "BMW", regex=True)

    df[coluna] = descricoes_processadas

    log_df = _montar_log_alteracoes(
        df_original=df_original,
        coluna_descricao=coluna,
        descricoes_originais=descricoes_originais,
        descricoes_processadas=descricoes_processadas,
    )

    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    return buffer, df, log_df, int(len(log_df))

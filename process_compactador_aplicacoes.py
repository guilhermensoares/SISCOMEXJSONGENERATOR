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

    descricoes_originais = df[coluna].astype(str)
    descricoes_processadas = descricoes_originais.apply(processar_descricao)
    descricoes_processadas = descricoes_processadas.str.replace(r"\bBmw\b", "BMW", regex=True)

    df[coluna] = descricoes_processadas

    alteradas = (descricoes_originais != descricoes_processadas).sum()

    log_df = pd.DataFrame({
        "linha_excel": [i + 2 for i, mudou in enumerate(descricoes_originais != descricoes_processadas) if mudou],
        "descricao_original": descricoes_originais[descricoes_originais != descricoes_processadas].tolist(),
        "descricao_compactada": descricoes_processadas[descricoes_originais != descricoes_processadas].tolist(),
    })

    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    return buffer, df, log_df, int(alteradas)

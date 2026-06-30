import json
import re
import zipfile
from io import BytesIO
from pathlib import Path

import pandas as pd


def _valor_vazio(valor) -> bool:
    return valor is None or pd.isna(valor)


def normalizar_sku_king(valor, tamanho: int = 5) -> str:
    """
    Normaliza códigos internos/SKUs para o padrão de 5 dígitos da King.

    Exemplos:
    - 12345.0  -> 12345
    - '12345.0' -> 12345
    - 1234 -> 01234
    - '00123.0' -> 00123
    """
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


def _resolver_coluna(df: pd.DataFrame, nome_desejado: str) -> str | None:
    """Resolve coluna por nome exato ou por comparação case-insensitive."""
    if nome_desejado in df.columns:
        return nome_desejado

    alvo = nome_desejado.strip().upper()
    for coluna in df.columns:
        if str(coluna).strip().upper() == alvo:
            return coluna
    return None


def carregar_de_para(arquivo_de_para, coluna_de: str, coluna_para: str) -> dict[str, str]:
    """
    Carrega uma planilha/CSV de de-para para edição em massa.

    A planilha deve conter duas colunas:
    - coluna_de: código atual/original;
    - coluna_para: código novo/final.
    """
    if arquivo_de_para is None:
        return {}

    nome = getattr(arquivo_de_para, "name", "").lower()
    if nome.endswith(".csv"):
        df = pd.read_csv(arquivo_de_para, dtype=str)
    else:
        df = pd.read_excel(arquivo_de_para, dtype=str)

    df.columns = [str(c).strip() for c in df.columns]
    col_de = _resolver_coluna(df, coluna_de)
    col_para = _resolver_coluna(df, coluna_para)

    if not col_de or not col_para:
        raise ValueError(
            f"Não encontrei as colunas de/para informadas. "
            f"Colunas disponíveis: {', '.join(map(str, df.columns))}"
        )

    mapa = {}
    for _, row in df.iterrows():
        origem = normalizar_sku_king(row.get(col_de, ""))
        destino = normalizar_sku_king(row.get(col_para, ""))
        if origem and destino:
            mapa[origem] = destino

    return mapa


def _deduplicar_preservando_ordem(valores: list[str]) -> list[str]:
    vistos = set()
    saida = []
    for valor in valores:
        if not valor or valor in vistos:
            continue
        vistos.add(valor)
        saida.append(valor)
    return saida


def _normalizar_codigos_interno_produto(produto: dict, mapa_de_para: dict[str, str], nome_arquivo: str) -> list[dict]:
    """Normaliza codigosInterno de um produto e retorna registros de log."""
    logs = []

    if "codigosInterno" not in produto:
        return logs

    codigos_originais = produto.get("codigosInterno")
    if codigos_originais is None:
        codigos_originais = []
    elif isinstance(codigos_originais, (str, int, float)):
        codigos_originais = [codigos_originais]
    elif not isinstance(codigos_originais, list):
        codigos_originais = [codigos_originais]

    codigos_finais = []
    for codigo_original in codigos_originais:
        codigo_normalizado = normalizar_sku_king(codigo_original)
        codigo_final = mapa_de_para.get(codigo_normalizado, codigo_normalizado)
        codigo_final = normalizar_sku_king(codigo_final)
        codigos_finais.append(codigo_final)

        mudou = str(codigo_original).strip() != codigo_final
        acao = "alterado" if mudou else "mantido"
        if mapa_de_para and codigo_normalizado in mapa_de_para:
            acao = "alterado por de/para"

        if mudou or acao == "alterado por de/para":
            logs.append({
                "arquivo": nome_arquivo,
                "seq": produto.get("seq", ""),
                "codigo_original": str(codigo_original).strip(),
                "codigo_normalizado": codigo_normalizado,
                "codigo_final": codigo_final,
                "acao": acao
            })

    produto["codigosInterno"] = _deduplicar_preservando_ordem(codigos_finais)
    return logs


def editar_json_catalogo(conteudo_bytes: bytes, nome_arquivo: str, mapa_de_para: dict[str, str] | None = None):
    """
    Edita um JSON de catálogo já gerado.

    Atualmente atua no campo `codigosInterno`, aceitando tanto JSON em lista
    quanto JSON em dicionário com produtos em chaves comuns.
    """
    mapa_de_para = mapa_de_para or {}
    texto = conteudo_bytes.decode("utf-8-sig")
    dados = json.loads(texto)

    logs = []

    if isinstance(dados, list):
        produtos = [item for item in dados if isinstance(item, dict)]
    elif isinstance(dados, dict):
        # Fallback para eventuais envelopes no futuro.
        produtos = []
        for chave in ("produtos", "catalogo", "itens", "data"):
            valor = dados.get(chave)
            if isinstance(valor, list):
                produtos = [item for item in valor if isinstance(item, dict)]
                break
        if not produtos and "codigosInterno" in dados:
            produtos = [dados]
    else:
        raise ValueError("Formato de JSON não suportado. Esperado lista ou dicionário.")

    for produto in produtos:
        logs.extend(_normalizar_codigos_interno_produto(produto, mapa_de_para, nome_arquivo))

    saida = BytesIO()
    saida.write(json.dumps(dados, ensure_ascii=False, indent=4).encode("utf-8"))
    saida.seek(0)
    return saida, logs


def editar_jsons_catalogo(arquivos_json, arquivo_de_para=None, coluna_de: str = "SKU_ORIGINAL", coluna_para: str = "SKU_NOVO"):
    """
    Processa um ou mais JSONs e devolve:
    - lista de arquivos JSON corrigidos;
    - DataFrame de log;
    - buffer ZIP com todos os arquivos corrigidos + log CSV.
    """
    if not arquivos_json:
        raise ValueError("Envie ao menos um arquivo JSON para editar.")

    mapa_de_para = carregar_de_para(arquivo_de_para, coluna_de, coluna_para) if arquivo_de_para else {}

    resultados = []
    todos_logs = []

    for arquivo in arquivos_json:
        nome_original = getattr(arquivo, "name", "catalogo.json")
        conteudo = arquivo.read()
        buffer_json, logs = editar_json_catalogo(conteudo, nome_original, mapa_de_para)

        nome_saida = f"{Path(nome_original).stem}_corrigido.json"
        resultados.append((nome_saida, buffer_json))
        todos_logs.extend(logs)

    log_df = pd.DataFrame(todos_logs)
    if log_df.empty:
        log_df = pd.DataFrame(columns=[
            "arquivo", "seq", "codigo_original", "codigo_normalizado", "codigo_final", "acao"
        ])

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for nome_saida, buffer in resultados:
            zf.writestr(nome_saida, buffer.getvalue())

        csv_log = log_df.to_csv(index=False, sep=";", encoding="utf-8-sig")
        zf.writestr("log_edicao_codigos_internos.csv", csv_log)

    zip_buffer.seek(0)
    return resultados, log_df, zip_buffer

import json
import re
import zipfile
from io import BytesIO
from pathlib import Path

import pandas as pd


CAMPOS_BODY_RETIFICACAO = [
    "descricao",
    "denominacao",
    "modalidade",
    "ncm",
    "atributos",
    "atributosMultivalorados",
    "atributosCompostos",
    "atributosCompostosMultivalorados",
    "codigosInterno",
]


CAMPOS_REMOVIDOS_DO_LOTE = [
    "seq",
    "cpfCnpjRaiz",
    "situacao",
    "fabricantesProdutores",
]


def _valor_vazio(valor) -> bool:
    try:
        return valor is None or pd.isna(valor)
    except Exception:
        return valor is None


def normalizar_sku_king(valor, tamanho: int = 5) -> str:
    """
    Normaliza códigos internos/SKUs para o padrão King de 5 dígitos.

    Exemplos:
    - 12345.0   -> 12345
    - 12345,0   -> 12345
    - 1234      -> 01234
    - 00123.0   -> 00123
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

    # Remove sufixos decimais zerados gerados por Excel/pandas: 12345.0, 12345.00, 12345,0
    if re.fullmatch(r"\d+[\.,]0+", texto):
        texto = re.split(r"[\.,]", texto, maxsplit=1)[0]

    # SKUs King numéricos devem preservar 5 dígitos
    if texto.isdigit() and len(texto) < tamanho:
        texto = texto.zfill(tamanho)

    return texto


def normalizar_ncm(valor) -> str:
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

    return re.sub(r"\D", "", texto)


def _resolver_coluna(df: pd.DataFrame, nome_desejado: str) -> str | None:
    """Resolve coluna por nome exato ou comparação case-insensitive."""
    if nome_desejado in df.columns:
        return nome_desejado

    alvo = str(nome_desejado).strip().upper()
    for coluna in df.columns:
        if str(coluna).strip().upper() == alvo:
            return coluna
    return None


def _ler_tabela(arquivo) -> pd.DataFrame:
    nome = getattr(arquivo, "name", "").lower()
    if nome.endswith(".csv"):
        return pd.read_csv(arquivo, dtype=str)
    return pd.read_excel(arquivo, dtype=str)


def carregar_de_para(
    arquivo_de_para,
    coluna_de: str = "SKU_ORIGINAL",
    coluna_para: str = "SKU_NOVO",
) -> dict[str, str]:
    """
    Carrega uma planilha/CSV de de-para.

    Colunas padrão:
    - SKU_ORIGINAL: código atual/original;
    - SKU_NOVO: código novo/final.
    """
    if arquivo_de_para is None:
        return {}

    df = _ler_tabela(arquivo_de_para)
    df.columns = [str(c).strip() for c in df.columns]

    col_de = _resolver_coluna(df, coluna_de)
    col_para = _resolver_coluna(df, coluna_para)

    if not col_de or not col_para:
        raise ValueError(
            "Não encontrei as colunas de/para informadas. "
            f"Colunas disponíveis: {', '.join(map(str, df.columns))}"
        )

    mapa = {}
    for _, row in df.iterrows():
        origem = normalizar_sku_king(row.get(col_de, ""))
        destino = normalizar_sku_king(row.get(col_para, ""))
        if origem and destino:
            mapa[origem] = destino

    return mapa


def carregar_path_siscomex(
    arquivo_path,
    coluna_sku: str = "SKU",
    coluna_codigo: str = "CODIGO_PRODUTO_SISCOMEX",
    coluna_versao: str = "VERSAO",
) -> dict[str, dict]:
    """
    Carrega uma planilha/CSV com o vínculo entre SKU King, código do produto Siscomex e versão.

    Essa planilha é opcional. Sem ela, o app gera apenas os bodies de retificação.
    Com ela, o app também gera um JSON com path + body para cada produto.
    """
    if arquivo_path is None:
        return {}

    df = _ler_tabela(arquivo_path)
    df.columns = [str(c).strip() for c in df.columns]

    col_sku = _resolver_coluna(df, coluna_sku)
    col_codigo = _resolver_coluna(df, coluna_codigo)
    col_versao = _resolver_coluna(df, coluna_versao)

    if not col_sku or not col_codigo or not col_versao:
        raise ValueError(
            "Não encontrei as colunas de SKU/código Siscomex/versão. "
            f"Colunas disponíveis: {', '.join(map(str, df.columns))}"
        )

    mapa = {}
    for _, row in df.iterrows():
        sku = normalizar_sku_king(row.get(col_sku, ""))
        codigo_bruto = str(row.get(col_codigo, "")).strip()
        versao = str(row.get(col_versao, "")).strip()

        if not sku or not codigo_bruto or not versao:
            continue

        # O código do produto Siscomex é inteiro int64 no path.
        codigo_limpo = re.sub(r"\D", "", codigo_bruto.split(".")[0])
        if not codigo_limpo:
            continue

        mapa[sku] = {
            "codigo": int(codigo_limpo),
            "versao": versao,
        }

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


def _extrair_produtos(dados) -> list[dict]:
    """Aceita JSON em lista ou envelopes simples como produtos/catalogo/itens/data."""
    if isinstance(dados, list):
        return [item for item in dados if isinstance(item, dict)]

    if isinstance(dados, dict):
        for chave in ("produtos", "catalogo", "itens", "data"):
            valor = dados.get(chave)
            if isinstance(valor, list):
                return [item for item in valor if isinstance(item, dict)]

        if "codigosInterno" in dados:
            return [dados]

    raise ValueError("Formato de JSON não suportado. Esperado lista ou dicionário.")


def _normalizar_codigos_produto(
    produto: dict,
    mapa_de_para: dict[str, str],
    nome_arquivo: str,
) -> tuple[list[str], list[dict]]:
    """Normaliza codigosInterno de um produto e retorna (codigos_finais, logs)."""
    logs = []

    codigos_originais = produto.get("codigosInterno", [])
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
                "acao": acao,
            })

    return _deduplicar_preservando_ordem(codigos_finais), logs


def editar_json_catalogo(
    conteudo_bytes: bytes,
    nome_arquivo: str,
    mapa_de_para: dict[str, str] | None = None,
):
    """
    Corrige o JSON de lote de catálogo, mantendo a mesma estrutura original.

    Use quando a intenção for apenas limpar o arquivo gerado localmente:
    - codigosInterno: ["53907.0"] -> ["53907"]
    """
    mapa_de_para = mapa_de_para or {}
    texto = conteudo_bytes.decode("utf-8-sig")
    dados = json.loads(texto)

    produtos = _extrair_produtos(dados)
    logs = []

    for produto in produtos:
        codigos_finais, logs_produto = _normalizar_codigos_produto(produto, mapa_de_para, nome_arquivo)
        produto["codigosInterno"] = codigos_finais
        logs.extend(logs_produto)

    saida = BytesIO()
    saida.write(json.dumps(dados, ensure_ascii=False, indent=4).encode("utf-8"))
    saida.seek(0)
    return saida, logs


def editar_jsons_catalogo(
    arquivos_json,
    arquivo_de_para=None,
    coluna_de: str = "SKU_ORIGINAL",
    coluna_para: str = "SKU_NOVO",
):
    """
    Processa um ou mais JSONs de lote e devolve:
    - lista de arquivos JSON corrigidos;
    - DataFrame de log;
    - ZIP com todos os arquivos corrigidos + log CSV.
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


def criar_body_retificacao(produto: dict, codigos_interno_corrigidos: list[str]) -> dict:
    """
    Converte um produto do JSON de lote para o body aceito na edição/retificação.

    Remove campos do modelo de lote:
    - seq
    - cpfCnpjRaiz
    - situacao
    - fabricantesProdutores
    """
    body = {
        "descricao": str(produto.get("descricao", "")).strip(),
        "denominacao": str(produto.get("denominacao", "")).strip(),
        "modalidade": str(produto.get("modalidade", "IMPORTACAO")).strip() or "IMPORTACAO",
        "ncm": normalizar_ncm(produto.get("ncm", "")),
        "atributos": produto.get("atributos", []) or [],
        "atributosMultivalorados": produto.get("atributosMultivalorados", []) or [],
        "atributosCompostos": produto.get("atributosCompostos", []) or [],
        "atributosCompostosMultivalorados": produto.get("atributosCompostosMultivalorados", []) or [],
        "codigosInterno": codigos_interno_corrigidos,
    }

    # Garante que o body fique apenas com os campos permitidos e na ordem esperada.
    return {campo: body.get(campo, [] if campo.startswith("atributos") else "") for campo in CAMPOS_BODY_RETIFICACAO}


def gerar_bodies_retificacao(
    arquivos_json,
    arquivo_de_para=None,
    coluna_de: str = "SKU_ORIGINAL",
    coluna_para: str = "SKU_NOVO",
    arquivo_path=None,
    coluna_sku_path: str = "SKU",
    coluna_codigo_path: str = "CODIGO_PRODUTO_SISCOMEX",
    coluna_versao_path: str = "VERSAO",
):
    """
    Gera bodies de retificação/edição a partir de JSONs de lote.

    Sem arquivo_path:
    - gera apenas os bodies, pois ainda faltam codigo e versao no path da API.

    Com arquivo_path:
    - gera também um JSON consolidado com path + body.
    """
    if not arquivos_json:
        raise ValueError("Envie ao menos um arquivo JSON para gerar body de retificação.")

    mapa_de_para = carregar_de_para(arquivo_de_para, coluna_de, coluna_para) if arquivo_de_para else {}
    mapa_path = carregar_path_siscomex(
        arquivo_path,
        coluna_sku=coluna_sku_path,
        coluna_codigo=coluna_codigo_path,
        coluna_versao=coluna_versao_path,
    ) if arquivo_path else {}

    bodies_individuais = []
    pacote_sem_path = []
    pacote_com_path = []
    logs_codigos = []
    manifest = []

    for arquivo in arquivos_json:
        nome_original = getattr(arquivo, "name", "catalogo.json")
        dados = json.loads(arquivo.read().decode("utf-8-sig"))
        produtos = _extrair_produtos(dados)

        for produto in produtos:
            codigos_finais, logs_produto = _normalizar_codigos_produto(produto, mapa_de_para, nome_original)
            logs_codigos.extend(logs_produto)

            body = criar_body_retificacao(produto, codigos_finais)
            sku_final = codigos_finais[0] if codigos_finais else "SEM_SKU"
            seq = produto.get("seq", "")
            cnpj_raiz = str(produto.get("cpfCnpjRaiz", "")).strip()

            nome_body = f"body_seq_{seq}_sku_{sku_final}.json" if seq != "" else f"body_sku_{sku_final}.json"
            nome_body = re.sub(r"[^A-Za-z0-9_\-.]", "_", nome_body)

            buffer_body = BytesIO()
            buffer_body.write(json.dumps(body, ensure_ascii=False, indent=4).encode("utf-8"))
            buffer_body.seek(0)
            bodies_individuais.append((nome_body, buffer_body))

            registro_sem_path = {
                "arquivo_origem": nome_original,
                "seq": seq,
                "cpfCnpjRaiz": cnpj_raiz,
                "sku_final": sku_final,
                "body": body,
            }
            pacote_sem_path.append(registro_sem_path)

            status_path = "sem codigo/versao"
            codigo_siscomex = ""
            versao = ""
            if sku_final in mapa_path:
                codigo_siscomex = mapa_path[sku_final]["codigo"]
                versao = mapa_path[sku_final]["versao"]
                pacote_com_path.append({
                    "path": {
                        "cpfCnpjRaiz": cnpj_raiz,
                        "codigo": codigo_siscomex,
                        "versao": versao,
                    },
                    "body": body,
                })
                status_path = "com path"
            elif mapa_path:
                status_path = "SKU nao encontrado na planilha de path"

            manifest.append({
                "arquivo_origem": nome_original,
                "arquivo_body": nome_body,
                "seq": seq,
                "cpfCnpjRaiz": cnpj_raiz,
                "sku_final": sku_final,
                "codigoProdutoSiscomex": codigo_siscomex,
                "versao": versao,
                "status_path": status_path,
                "ncm": body.get("ncm", ""),
                "denominacao": body.get("denominacao", ""),
                "descricao": body.get("descricao", ""),
            })

    log_df = pd.DataFrame(logs_codigos)
    if log_df.empty:
        log_df = pd.DataFrame(columns=[
            "arquivo", "seq", "codigo_original", "codigo_normalizado", "codigo_final", "acao"
        ])

    manifest_df = pd.DataFrame(manifest)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for nome_body, buffer in bodies_individuais:
            zf.writestr(f"bodies_individuais/{nome_body}", buffer.getvalue())

        zf.writestr(
            "pacote_retificacao_sem_path.json",
            json.dumps(pacote_sem_path, ensure_ascii=False, indent=4).encode("utf-8"),
        )

        if pacote_com_path:
            zf.writestr(
                "pacote_retificacao_com_path.json",
                json.dumps(pacote_com_path, ensure_ascii=False, indent=4).encode("utf-8"),
            )

        zf.writestr(
            "manifesto_retificacao.csv",
            manifest_df.to_csv(index=False, sep=";", encoding="utf-8-sig"),
        )
        zf.writestr(
            "log_normalizacao_codigos.csv",
            log_df.to_csv(index=False, sep=";", encoding="utf-8-sig"),
        )
        zf.writestr(
            "README_RETIFICACAO.txt",
            (
                "Este pacote foi gerado a partir do JSON de lote do catálogo.\n\n"
                "Arquivos principais:\n"
                "- bodies_individuais/: um body JSON por produto, no modelo de edição/retificação.\n"
                "- pacote_retificacao_sem_path.json: consolidação com metadados locais + body.\n"
                "- pacote_retificacao_com_path.json: gerado apenas quando enviada planilha com SKU, codigo Siscomex e versao.\n"
                "- manifesto_retificacao.csv: log para auditoria e cruzamento.\n"
                "- log_normalizacao_codigos.csv: alterações feitas em codigosInterno.\n\n"
                "Atenção: para chamar a API de retificação/edição, o Siscomex exige cpfCnpjRaiz, codigo do produto e versao no path.\n"
                "Sem o codigo do produto Siscomex e a versao, estes bodies NÃO devem ser interpretados como pacote pronto de envio via API.\n"
            ).encode("utf-8"),
        )

    zip_buffer.seek(0)
    return bodies_individuais, manifest_df, log_df, zip_buffer

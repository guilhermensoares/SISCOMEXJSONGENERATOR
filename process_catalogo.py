import json
import math
import re
from io import BytesIO

import pandas as pd

mapa_paises = {
    "CHINA": "CN", "CHINA, REPÚBLICA POPULAR": "CN",
    "ALEMANHA": "DE", "ESTADOS UNIDOS": "US", "EUA": "US",
    "BRASIL": "BR", "ITÁLIA": "IT", "JAPÃO": "JP", "COREIA DO SUL": "KR",
    "TAIWAN": "TW", "MÉXICO": "MX", "ÍNDIA": "IN", "REINO UNIDO": "GB",
    "FRANÇA": "FR", "POLÔNIA": "PL", "ESPANHA": "ES", "PORTUGAL": "PT",
    "TURQUIA": "TR", "ÁUSTRIA": "AT", "REPÚBLICA TCHECA": "CZ",
    "HUNGRIA": "HU", "PAÍSES BAIXOS": "NL", "SUÉCIA": "SE", "SUÍÇA": "CH",
    "TAILÂNDIA": "TH"
}


def _valor_vazio(valor) -> bool:
    """Retorna True para valores vazios/NaN vindos do Excel."""
    return valor is None or pd.isna(valor)


def normalizar_sku_king(valor, tamanho: int = 5) -> str:
    """
    Normaliza SKU King para evitar saídas como '12345.0'.

    Regras:
    - Remove espaços e espaços não quebráveis;
    - Converte números inteiros lidos como float pelo pandas: 12345.0 -> 12345;
    - Remove sufixos decimais zerados em texto: '12345.0', '12345.00', '12345,0';
    - Preenche com zero à esquerda quando o código numérico tiver menos de 5 dígitos.
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

    # Ex.: '12345.0', '12345.00', '12345,0'
    if re.fullmatch(r"\d+[\.,]0+", texto):
        texto = re.split(r"[\.,]", texto, maxsplit=1)[0]

    # Ex.: '12345,000' após exportações regionais
    if re.fullmatch(r"\d+", texto) and len(texto) < tamanho:
        texto = texto.zfill(tamanho)

    return texto


def normalizar_ncm(valor) -> str:
    """Normaliza NCM para 8 dígitos quando possível."""
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


def normalizar_texto(valor) -> str:
    if _valor_vazio(valor):
        return ""
    return str(valor).strip()


def processar_catalogo(planilha_file, cnpj_raiz: str, tamanho_lote: int = 5):
    # dtype=object mantém os tipos originais; a normalização é feita campo a campo
    # para impedir que códigos numéricos virem texto com '.0'.
    df = pd.read_excel(planilha_file, sheet_name="Planilha1", dtype=object)
    df.columns = df.columns.str.strip()

    pares_cols = [
        (f"Atributo {i}", f"Valor Atributo {i}")
        for i in range(1, 11)
        if f"Atributo {i}" in df.columns and f"Valor Atributo {i}" in df.columns
    ]

    if not pares_cols:
        raise ValueError("Nenhuma coluna de atributo encontrada na planilha.")

    produtos = []
    seq = 1

    for idx, linha in df.iterrows():
        try:
            cod_interno = normalizar_sku_king(linha.get("COD. KING", ""))
            ncm = normalizar_ncm(linha.get("NCM", ""))
            denominacao = normalizar_texto(linha.get("DESCRIÇÃO EM PORTUGUÊS", ""))
            descricao = normalizar_texto(linha.get("DESCRIÇÃO", ""))

            pais_nome = normalizar_texto(linha.get("PAIS", "")).upper()
            codigo_pais = mapa_paises.get(pais_nome, "XX") if pais_nome else "XX"
            cod_exportador = normalizar_texto(linha.get("Código Operador Estrangeiro Exportador", ""))
            cod_fabricante = normalizar_texto(linha.get("Código Operador Estrangeiro Fabricante", ""))

            fabricantes_produtores = []
            if cod_exportador:
                fabricantes_produtores.append({"codigoPais": codigo_pais, "codigo": cod_exportador})
            if cod_fabricante:
                fabricantes_produtores.append({"codigoPais": codigo_pais, "codigo": cod_fabricante})

            atributos = []
            for col_attr, col_val in pares_cols:
                attr = normalizar_texto(linha.get(col_attr, ""))
                val_bruto = linha.get(col_val, "")
                if _valor_vazio(val_bruto) or not attr:
                    continue

                val = normalizar_texto(val_bruto)
                if re.fullmatch(r"\d+[\.,]0+", val):
                    val = re.split(r"[\.,]", val, maxsplit=1)[0]
                if val.isdigit() and len(val) == 1:
                    val = val.zfill(2)

                atributos.append({"atributo": attr, "valor": val})

            produto = {
                "seq": seq,
                "modalidade": "IMPORTACAO",
                "cpfCnpjRaiz": cnpj_raiz,
                "situacao": "Ativado",
                "ncm": ncm,
                "denominacao": denominacao,
                "descricao": descricao,
                "atributos": atributos,
                "atributosMultivalorados": [],
                "atributosCompostos": [],
                "atributosCompostosMultivalorados": [],
                "codigosInterno": [cod_interno],
                "fabricantesProdutores": fabricantes_produtores
            }

            produtos.append(produto)
            seq += 1

        except Exception as e:
            print(f"Erro na linha {idx + 2}: {e}")

    total = len(produtos)
    num_arquivos = math.ceil(total / tamanho_lote)
    resultados = []

    for i in range(num_arquivos):
        inicio, fim = i * tamanho_lote, (i + 1) * tamanho_lote
        lote = produtos[inicio:fim]
        nome = f"{cnpj_raiz}_CATALOGO_Lote{i + 1}.json"
        buffer = BytesIO()
        json_str = json.dumps(lote, ensure_ascii=False, indent=4)
        buffer.write(json_str.encode("utf-8"))
        buffer.seek(0)
        resultados.append((nome, buffer))

    return resultados

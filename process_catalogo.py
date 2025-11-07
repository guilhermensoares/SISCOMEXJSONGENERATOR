import pandas as pd
import json
import math
from io import BytesIO

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

def processar_catalogo(planilha_file, cnpj_raiz: str, tamanho_lote: int = 5):
    df = pd.read_excel(planilha_file, sheet_name="Planilha1")

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
            cod_interno = str(linha.get("COD. KING", "")).strip()
            ncm = str(linha.get("NCM", "")).replace(".", "").replace("-", "").strip()
            denominacao = str(linha.get("DESCRIÇÃO EM PORTUGUÊS", "")).strip()
            descricao = str(linha.get("DESCRIÇÃO", "")).strip()

            pais_nome = str(linha.get("PAIS", "")).upper().strip()
            codigo_pais = mapa_paises.get(pais_nome, "XX") if pais_nome else "XX"
            cod_exportador = str(linha.get("Código Operador Estrangeiro Exportador", "")).strip()
            cod_fabricante = str(linha.get("Código Operador Estrangeiro Fabricante", "")).strip()

            fabricantes_produtores = []
            if cod_exportador:
                fabricantes_produtores.append({"codigoPais": codigo_pais, "codigo": cod_exportador})
            if cod_fabricante:
                fabricantes_produtores.append({"codigoPais": codigo_pais, "codigo": cod_fabricante})

            atributos = []
            for col_attr, col_val in pares_cols:
                attr = str(linha[col_attr]).strip() if pd.notna(linha.get(col_attr)) else ""
                val_bruto = linha.get(col_val, "")
                if pd.isna(val_bruto) or not attr:
                    continue

                val = str(val_bruto).strip()
                if val.endswith(".0"):
                    val = val[:-2]
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

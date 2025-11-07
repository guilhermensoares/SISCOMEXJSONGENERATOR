import pandas as pd
import json
from io import StringIO, BytesIO

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

def processar_vinculos(csv_file, planilha_file, cnpj_raiz, tamanho_lote):
    df_export = pd.read_csv(csv_file, sep=None, engine="python", encoding="utf-8-sig", dtype=str)
    df_base = pd.read_excel(planilha_file, sheet_name="Planilha1", dtype=str)

    df_export["Código interno do produto"] = df_export["Código interno do produto"].astype(str).str.strip().str.upper()
    df_base["COD. KING"] = df_base["COD. KING"].astype(str).str.strip().str.upper()

    df = df_export.merge(df_base, left_on="Código interno do produto", right_on="COD. KING", how="left", indicator=True)

    nao_casaram = df[df["_merge"] != "both"]
    if not nao_casaram.empty:
        debug_csv = nao_casaram[["Código do produto", "Código interno do produto"]]
        debug_buffer = StringIO()
        debug_csv.to_csv(debug_buffer, index=False, encoding="utf-8-sig")
        debug_csv_bytes = debug_buffer.getvalue().encode()
    else:
        debug_csv_bytes = None

    df_ok = df[df["_merge"] == "both"]
    lotes = [df_ok[i:i + tamanho_lote] for i in range(0, len(df_ok), tamanho_lote)]
    arquivos = []

    for i, lote in enumerate(lotes, start=1):
        saida = []
        seq = 1

        for _, row in lote.iterrows():
            pais_nome = str(row.get("País", "")).strip().upper()
            codigo_pais = mapa_paises.get(pais_nome, "XX")

            cod_exportador = str(row.get("Código Operador Estrangeiro Exportador", "")).strip()
            cod_fabricante = str(row.get("Código Operador Estrangeiro Fabricante", "")).strip()
            fabricante_conhecido = bool(cod_fabricante)

            try:
                codigo_produto = int(str(row.get("Código do produto", "")).strip())
            except Exception:
                continue

            if cod_fabricante:
                saida.append({
                    "seq": seq,
                    "cpfCnpjRaiz": cnpj_raiz,
                    "codigoOperadorEstrangeiro": cod_fabricante,
                    "cpfCnpjFabricante": "00000000",
                    "conhecido": fabricante_conhecido,
                    "codigoProduto": codigo_produto,
                    "codigoPais": codigo_pais
                })
                seq += 1

            if cod_exportador and cod_exportador != cod_fabricante:
                saida.append({
                    "seq": seq,
                    "cpfCnpjRaiz": cnpj_raiz,
                    "codigoOperadorEstrangeiro": cod_exportador,
                    "cpfCnpjFabricante": "00000000",
                    "conhecido": True,
                    "codigoProduto": codigo_produto,
                    "codigoPais": codigo_pais
                })
                seq += 1

        nome_arquivo = f"{cnpj_raiz}_VINCULOS_Lote{i}.json"
        buffer = BytesIO()
        buffer.write(json.dumps(saida, ensure_ascii=False, indent=4).encode("utf-8-sig"))
        buffer.seek(0)
        arquivos.append((nome_arquivo, buffer.read()))

    if debug_csv_bytes:
        arquivos.insert(0, ("ATENÇÃO_NAO_CASADOS.csv", debug_csv_bytes))

    return arquivos

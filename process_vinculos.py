import pandas as pd
import json
import math
from io import BytesIO

# Mapeamento de países
mapa_paises = {
    "CHINA": "CN", "ALEMANHA": "DE", "EUA": "US", "ESTADOS UNIDOS": "US",
    "ITÁLIA": "IT", "JAPÃO": "JP", "COREIA DO SUL": "KR", "TAIWAN": "TW",
    "MÉXICO": "MX", "ÍNDIA": "IN", "REINO UNIDO": "GB", "FRANÇA": "FR",
    "POLÔNIA": "PL", "ESPANHA": "ES", "PORTUGAL": "PT", "BRASIL": "BR"
}

def processar_vinculos(csv_file, excel_file, cnpj_raiz: str, tamanho_lote: int = 100):
    # ✅ Leitura correta do CSV exportado pelo Siscomex
    df_export = pd.read_csv(
        csv_file,
        sep=",",
        quotechar='"',
        encoding="utf-8-sig",
        engine="python",
        dtype=str
    )
    df_export.columns = df_export.columns.str.strip()

    if "Código interno do produto" not in df_export.columns:
        raise ValueError("A coluna 'Código interno do produto' não foi encontrada no CSV.")

    # ✅ Leitura da planilha base
    df_base = pd.read_excel(excel_file, sheet_name="Planilha1", dtype=str)
    df_base["COD. KING"] = df_base["COD. KING"].astype(str).str.strip().str.upper()
    df_export["Código interno do produto"] = df_export["Código interno do produto"].astype(str).str.strip().str.upper()

    # Merge entre o CSV e a base de itens
    df = df_export.merge(
        df_base,
        left_on="Código interno do produto",
        right_on="COD. KING",
        how="left",
        indicator=True
    )

    # Loteamento
    lotes_df = [df[i:i + tamanho_lote] for i in range(0, len(df), tamanho_lote)]
    resultados = []

    for i, lote in enumerate(lotes_df, start=1):
        saida = []
        seq = 1

        for _, row in lote.iterrows():
            pais_nome = str(row.get("PAIS", "")).strip().upper()
            codigo_pais = mapa_paises.get(pais_nome, "XX")

            cod_exportador = str(row.get("Código Operador Estrangeiro Exportador", "")).strip()
            cod_fabricante = str(row.get("Código Operador Estrangeiro Fabricante", "")).strip()
            fabricante_conhecido = bool(cod_fabricante)

            try:
                codigo_produto = int(str(row.get("Código do produto", "")).strip())
            except Exception:
                continue

            # Fabricante
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

            # Exportador (se diferente do fabricante)
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

        # Salva lote em memória
        nome = f"{cnpj_raiz}_VINCULOS_FABRICANTE_EXPORTADOR_Lote{i}.json"
        buffer = BytesIO()
        json_str = json.dumps(saida, ensure_ascii=False, indent=4)
        buffer.write(json_str.encode("utf-8"))
        buffer.seek(0)
        resultados.append((nome, buffer))

    return resultados

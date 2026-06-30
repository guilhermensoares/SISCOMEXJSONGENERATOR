import json
import re
import unicodedata
from io import BytesIO

import pandas as pd


LIMITE_REGISTROS_POR_ARQUIVO = 100

# Mapeamento de países
mapa_paises = {
    "CHINA": "CN", "CHINA, REPÚBLICA POPULAR": "CN",
    "ALEMANHA": "DE", "EUA": "US", "ESTADOS UNIDOS": "US",
    "ITÁLIA": "IT", "JAPÃO": "JP", "COREIA DO SUL": "KR", "TAIWAN": "TW",
    "MÉXICO": "MX", "ÍNDIA": "IN", "REINO UNIDO": "GB", "FRANÇA": "FR",
    "POLÔNIA": "PL", "ESPANHA": "ES", "PORTUGAL": "PT", "BRASIL": "BR",
    "TURQUIA": "TR", "ÁUSTRIA": "AT", "REPÚBLICA TCHECA": "CZ",
    "HUNGRIA": "HU", "PAÍSES BAIXOS": "NL", "SUÉCIA": "SE", "SUÍÇA": "CH",
    "TAILÂNDIA": "TH"
}


def _norm_txt(x) -> str:
    """Normaliza texto: strip + remove acentos + UPPER."""
    if x is None or pd.isna(x):
        return ""
    s = str(x).strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s.upper()


def _valor_vazio(valor) -> bool:
    return valor is None or pd.isna(valor)


def normalizar_sku_king(valor, tamanho: int = 5) -> str:
    """Normaliza SKU/código interno para evitar '12345.0' e falhas no merge."""
    if _valor_vazio(valor):
        return ""

    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if float(valor).is_integer():
            texto = str(int(valor))
        else:
            texto = str(valor)
    else:
        texto = str(valor)

    texto = texto.strip().replace("\u00a0", "").upper()
    if re.fullmatch(r"\d+[\.,]0+", texto):
        texto = re.split(r"[\.,]", texto, maxsplit=1)[0]
    if texto.isdigit() and len(texto) < tamanho:
        texto = texto.zfill(tamanho)
    return texto


def _resolver_col_pais(df: pd.DataFrame) -> str | None:
    """
    Resolve a coluna de país após o merge.
    Prioriza base (PAIS_Y) -> coluna exata PAIS -> export (PAIS_X).
    Funciona mesmo se a coluna original for 'País' (com acento).
    """
    norm_map = {_norm_txt(c): c for c in df.columns}

    for chave in ("PAIS_Y", "PAIS", "PAIS_X"):
        if chave in norm_map:
            return norm_map[chave]

    candidatos = [c for c in df.columns if "PAIS" in _norm_txt(c)]
    return candidatos[0] if candidatos else None


def _coluna_obrigatoria(df: pd.DataFrame, nome: str, origem: str):
    if nome not in df.columns:
        raise ValueError(f"A coluna '{nome}' não foi encontrada em {origem}.")


def _quebrar_em_lotes(registros: list, limite: int = LIMITE_REGISTROS_POR_ARQUIVO) -> list[list]:
    return [registros[i:i + limite] for i in range(0, len(registros), limite)]


def _resequenciar_lote(lote: list[dict]) -> list[dict]:
    """Garante seq de 1 a 100 dentro de cada arquivo gerado."""
    saida = []
    for seq, registro in enumerate(lote, start=1):
        novo = dict(registro)
        novo["seq"] = seq
        saida.append(novo)
    return saida


def processar_vinculos(csv_file, excel_file, cnpj_raiz: str, tamanho_lote: int = LIMITE_REGISTROS_POR_ARQUIVO):
    """
    Gera JSONs de Vínculo Fabricante–Exportador.

    Observação operacional: o limite é de 100 registros por arquivo. Aqui o controle é feito
    sobre a quantidade final de registros do JSON, não sobre as linhas do CSV, porque uma linha
    pode gerar dois vínculos: fabricante e exportador.
    """
    tamanho_lote = LIMITE_REGISTROS_POR_ARQUIVO

    # Leitura do CSV exportado pelo Siscomex
    df_export = pd.read_csv(
        csv_file,
        sep=",",
        quotechar='"',
        encoding="utf-8-sig",
        engine="python",
        dtype=str,
    )
    df_export.columns = df_export.columns.str.strip()

    _coluna_obrigatoria(df_export, "Código do produto", "CSV exportado do Siscomex")
    _coluna_obrigatoria(df_export, "Código interno do produto", "CSV exportado do Siscomex")

    # Leitura da planilha base
    df_base = pd.read_excel(excel_file, sheet_name="Planilha1", dtype=object)
    df_base.columns = df_base.columns.str.strip()
    _coluna_obrigatoria(df_base, "COD. KING", "planilha base")

    df_base["COD. KING"] = df_base["COD. KING"].apply(normalizar_sku_king)
    df_export["Código interno do produto"] = df_export["Código interno do produto"].apply(normalizar_sku_king)

    # Merge entre o CSV e a base de itens
    df = df_export.merge(
        df_base,
        left_on="Código interno do produto",
        right_on="COD. KING",
        how="left",
        indicator=True,
    )

    col_pais = _resolver_col_pais(df)

    registros = []

    for _, row in df.iterrows():
        pais_nome = _norm_txt(row.get(col_pais, "")) if col_pais else ""
        codigo_pais = mapa_paises.get(pais_nome, "XX")

        cod_exportador = str(row.get("Código Operador Estrangeiro Exportador", "") or "").strip()
        cod_fabricante = str(row.get("Código Operador Estrangeiro Fabricante", "") or "").strip()
        fabricante_conhecido = True

        try:
            codigo_produto = int(str(row.get("Código do produto", "")).strip())
        except Exception:
            continue

        registros.append({
            "seq": 0,
            "cpfCnpjRaiz": cnpj_raiz,
            "codigoOperadorEstrangeiro": cod_fabricante,
            "cpfCnpjFabricante": "00000000000000",
            "conhecido": fabricante_conhecido,
            "codigoProduto": codigo_produto,
            "codigoPais": codigo_pais,
        })

        # Exportador (se diferente do fabricante)
        if cod_exportador and cod_exportador != cod_fabricante:
            registros.append({
                "seq": 0,
                "cpfCnpjRaiz": cnpj_raiz,
                "codigoOperadorEstrangeiro": cod_exportador,
                "cpfCnpjFabricante": "00000000000000",
                "conhecido": fabricante_conhecido,
                "codigoProduto": codigo_produto,
                "codigoPais": codigo_pais,
            })

    resultados = []
    for i, lote in enumerate(_quebrar_em_lotes(registros, tamanho_lote), start=1):
        lote_seq = _resequenciar_lote(lote)
        nome = f"{cnpj_raiz}_VINCULOS_FABRICANTE_EXPORTADOR_Lote{i}.json"
        buffer = BytesIO()
        json_str = json.dumps(lote_seq, ensure_ascii=False, indent=4)
        buffer.write(json_str.encode("utf-8"))
        buffer.seek(0)
        resultados.append((nome, buffer))

    return resultados

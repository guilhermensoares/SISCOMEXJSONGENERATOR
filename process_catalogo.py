import json
import pandas as pd
import streamlit as st

def processar_catalogo(file, cnpj, lote):
    try:
        df = pd.read_excel(file)
        total_linhas = len(df)
        total_lotes = (total_linhas // lote) + int(total_linhas % lote != 0)

        for i in range(total_lotes):
            inicio = i * lote
            fim = min(inicio + lote, total_linhas)
            df_lote = df.iloc[inicio:fim]

            lista_produtos = []
            for _, row in df_lote.iterrows():
                produto = {
                    "cnpj": cnpj,
                    "codigo": str(row["codigo"]),
                    "descricao": row["descricao"],
                    "ncm": str(row["ncm"]),
                    "unidade_medida": row["unidade_medida"],
                    "preco": float(row["preco"])
                }
                lista_produtos.append(produto)

            json_data = {"produtos": lista_produtos}
            nome_arquivo = f"catalogo_lote_{i+1}.json"
            with open(nome_arquivo, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

            st.success(f"Catálogo gerado: {nome_arquivo}")
            st.download_button(
                label=f"📥 Baixar {nome_arquivo}",
                data=json.dumps(json_data, ensure_ascii=False, indent=4),
                file_name=nome_arquivo,
                mime="application/json"
            )

    except Exception as e:
        st.error(f"Ocorreu um erro: {str(e)}")

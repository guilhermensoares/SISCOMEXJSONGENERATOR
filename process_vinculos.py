import json
import pandas as pd
import streamlit as st

def processar_vinculos(csv_file, base_file, cnpj):
    try:
        df_siscomex = pd.read_csv(csv_file, sep=";")
        df_base = pd.read_excel(base_file)

        lista_vinculos = []

        for _, row in df_siscomex.iterrows():
            referencia = str(row["Referência"])
            base_row = df_base[df_base["Referência"] == referencia]

            if not base_row.empty:
                produto = base_row.iloc[0]
                vinculo = {
                    "cnpj": cnpj,
                    "codigo": str(produto["codigo"]),
                    "referencia": referencia
                }
                lista_vinculos.append(vinculo)

        json_data = {"vinculos": lista_vinculos}
        nome_arquivo = "vinculos.json"

        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        st.success("JSON de vínculos gerado com sucesso!")
        st.download_button(
            label="📥 Baixar vinculos.json",
            data=json.dumps(json_data, ensure_ascii=False, indent=4),
            file_name=nome_arquivo,
            mime="application/json"
        )

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar os vínculos: {str(e)}")

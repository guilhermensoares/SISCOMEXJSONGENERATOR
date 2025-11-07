import pandas as pd
import streamlit as st
import json

def processar_vinculos(file_siscomex, file_base, cnpj):
    if not file_siscomex or not file_base:
        st.warning("Por favor, envie os dois arquivos.")
        return

    df_siscomex = pd.read_csv(file_siscomex, sep=';', encoding='latin1')
    df_base = pd.read_excel(file_base)

    if df_siscomex.empty or df_base.empty:
        st.error("Algum dos arquivos está vazio.")
        return

    df_base = df_base.fillna("")

    resultados = []

    for _, row in df_base.iterrows():
        modelo = row.get("modelo", "").strip().lower()
        if not modelo:
            continue

        correspondencias = df_siscomex[df_siscomex['DESCRIÇÃO MERCADORIA'].str.lower().str.contains(modelo)]

        for _, match in correspondencias.iterrows():
            resultado = {
                "cnpj": str(cnpj),
                "modelo": modelo,
                "ncm": match.get("NCM"),
                "descricao_siscomex": match.get("DESCRIÇÃO MERCADORIA"),
                "chave_catalogo": row.get("chave_catalogo"),
            }
            resultados.append(resultado)

    if not resultados:
        st.info("Nenhuma correspondência encontrada.")
        return

    json_filename = "vinculos_gerados.json"
    st.download_button(
        label="📄 Baixar vinculos_gerados.json",
        file_name=json_filename,
        mime="application/json",
        data=json.dumps(resultados, indent=2, ensure_ascii=False),
    )

import streamlit as st
import pandas as pd
from utils.load_data import load_data

st.title("📊 Resumo")

df = load_data()

# Padronizar nomes das colunas
df.columns = df.columns.str.strip()

# Converter Dias com segurança
df["Dias"] = pd.to_numeric(df["Dias"], errors="coerce").fillna(0)

# Converter Valor com segurança
df["Valor"] = (
    df["Valor"]
    .astype(str)
    .str.replace("R$", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.strip()
)

df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

# Criar status
df["Status"] = df["Dias"].apply(
    lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")
)

# KPIs
total_notas = len(df)
valor_total = df["Valor"].sum()
atrasadas = (df["Status"] == "Atrasado").sum()
vence_hoje = (df["Status"] == "Vence hoje").sum()
no_prazo = (df["Status"] == "No prazo").sum()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total NFs", total_notas)
col2.metric("Valor Total", f"R$ {valor_total:,.2f}")
col3.metric("🔴 Atrasadas", atrasadas, delta=f"{atrasadas}")
col4.metric("🟡 Vence hoje", vence_hoje)
col5.metric("🟢 No prazo", no_prazo)
st.divider()

st.subheader("Dados carregados")
st.dataframe(df, use_container_width=True)

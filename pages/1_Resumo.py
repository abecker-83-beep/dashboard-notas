import streamlit as st
from utils.load_data import load_data

st.title("📊 Resumo")

df = load_data()

# =========================
# TRATAMENTOS
# =========================
df["Dias"] = df["Dias"].astype(float)
df["Valor"] = df["Valor"].replace("[R$ ]", "", regex=True).replace(",", ".", regex=True).astype(float)

# Status
df["Status"] = df["Dias"].apply(
    lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")
)

# =========================
# KPIs
# =========================
total_notas = len(df)
valor_total = df["Valor"].sum()
atrasadas = (df["Status"] == "Atrasado").sum()
no_prazo = (df["Status"] == "No prazo").sum()

col1, col2, col3, col4 = st.columns(4)

col1.metric("📦 Total NFs", total_notas)
col2.metric("💰 Valor Total", f"R$ {valor_total:,.2f}")
col3.metric("🔴 Atrasadas", atrasadas)
col4.metric("🟢 No Prazo", no_prazo)

st.divider()

st.subheader("📦 Dados carregados")
st.dataframe(df)

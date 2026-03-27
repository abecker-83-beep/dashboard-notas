import streamlit as st
import pandas as pd
import plotly.express as px
from utils.load_data import load_data

st.title("🚚 Transportadoras")

df = load_data()
df.columns = df.columns.str.strip()

# Tratamentos
df["Dias"] = pd.to_numeric(df["Dias"], errors="coerce").fillna(0)

df["Valor"] = (
    df["Valor"]
    .astype(str)
    .str.replace("R$", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.strip()
)
df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

df["Status"] = df["Dias"].apply(
    lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")
)

# Filtro
transportadoras = sorted(df["Transportadora"].dropna().unique())
selecionadas = st.multiselect(
    "Filtrar transportadora",
    transportadoras,
    default=transportadoras
)

df_filtrado = df[df["Transportadora"].isin(selecionadas)].copy()

# Agrupamentos
nf_por_transp = (
    df_filtrado.groupby("Transportadora")
    .size()
    .reset_index(name="Qtd NFs")
    .sort_values("Qtd NFs", ascending=False)
)

valor_por_transp = (
    df_filtrado.groupby("Transportadora")["Valor"]
    .sum()
    .reset_index()
    .sort_values("Valor", ascending=False)
)

atraso_por_transp = (
    df_filtrado[df_filtrado["Status"] == "Atrasado"]
    .groupby("Transportadora")
    .size()
    .reset_index(name="Qtd Atrasadas")
    .sort_values("Qtd Atrasadas", ascending=False)
)

col1, col2 = st.columns(2)

with col1:
    fig_nf = px.bar(
        nf_por_transp,
        x="Transportadora",
        y="Qtd NFs",
        title="Quantidade de NFs por Transportadora",
        text_auto=True
    )
    st.plotly_chart(fig_nf, use_container_width=True)

with col2:
    fig_valor = px.bar(
        valor_por_transp,
        x="Transportadora",
        y="Valor",
        title="Valor Total por Transportadora",
        text_auto=True
    )
    st.plotly_chart(fig_valor, use_container_width=True)

st.divider()

fig_atraso = px.bar(
    atraso_por_transp,
    x="Transportadora",
    y="Qtd Atrasadas",
    title="NFs Atrasadas por Transportadora",
    text_auto=True
)
st.plotly_chart(fig_atraso, use_container_width=True)

st.divider()
st.subheader("Tabela detalhada")
st.dataframe(df_filtrado, use_container_width=True)

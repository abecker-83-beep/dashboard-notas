import requests
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

from utils.load_data import load_data
from utils.ui import card_kpi, CORES, aplicar_estilo_global, cor_percentual, render_sidebar_brand
from utils.business import preparar_base_dashboard, formatar_moeda_br, percentual


# ============================================================
# CONFIG
# ============================================================
st.title("🗺️ Mapa V3")
st.caption("Mapa operacional com visão analítica por UF, cidade e NF.")

aplicar_estilo_global()
render_sidebar_brand()

STATUS_COLORS = {
    "No prazo": "#16A34A",
    "Vence hoje": "#D97706",
    "Atrasado": "#DC2626",
}


# ============================================================
# LOAD
# ============================================================
@st.cache_data
def carregar():
    df_raw = load_data()
    df, _, _ = preparar_base_dashboard(df_raw)
    cidades = pd.read_csv("data/cidades.csv")

    cidades["Cidade"] = cidades["Cidade"].str.upper().str.strip()
    cidades["UF"] = cidades["UF"].str.upper().str.strip()

    return df, cidades


df, cidades = carregar()


# ============================================================
# FILTROS
# ============================================================
st.subheader("Filtros")

col1, col2, col3, col4 = st.columns(4)

with col1:
    transp = st.multiselect("Transportadora", sorted(df["Transportadora"].dropna().unique()))

with col2:
    rep = st.multiselect("Representante", sorted(df["Representante"].dropna().unique()))

with col3:
    uf = st.multiselect("UF", sorted(df["UF"].dropna().unique()))

with col4:
    cidade = st.multiselect("Cidade", sorted(df["Cidade"].dropna().unique()))

df_f = df.copy()

if transp:
    df_f = df_f[df_f["Transportadora"].isin(transp)]
if rep:
    df_f = df_f[df_f["Representante"].isin(rep)]
if uf:
    df_f = df_f[df_f["UF"].isin(uf)]
if cidade:
    df_f = df_f[df_f["Cidade"].isin(cidade)]

if df_f.empty:
    st.warning("Sem dados")
    st.stop()


# ============================================================
# KPIs
# ============================================================
st.subheader("Indicadores")

col1, col2, col3, col4 = st.columns([1,1,1,2])

with col1:
    card_kpi("Total NFs", len(df_f), CORES["cinza"])

with col2:
    card_kpi("UFs", df_f["UF"].nunique(), CORES["cinza"])

with col3:
    card_kpi("Cidades", df_f[["Cidade","UF"]].drop_duplicates().shape[0], CORES["cinza"])

with col4:
    card_kpi("Valor total", formatar_moeda_br(df_f["Valor"].sum()), CORES["azul"])


# ============================================================
# AGREGAÇÕES
# ============================================================
base = df_f.merge(cidades, on=["Cidade","UF"], how="left").dropna(subset=["lat","lon"])

mapa_uf = df_f.groupby("UF").agg(
    qtd_nfs=("NF","count"),
    valor_total=("Valor","sum"),
    qtd_atrasadas=("Status", lambda x: (x=="Atrasado").sum())
).reset_index()

mapa_uf["perc_atraso"] = (mapa_uf["qtd_atrasadas"]/mapa_uf["qtd_nfs"]*100).round(1)

mapa_cidade = base.groupby(["Cidade","UF","lat","lon"]).agg(
    qtd_nfs=("NF","count"),
    valor_total=("Valor","sum"),
    qtd_atrasadas=("Status", lambda x: (x=="Atrasado").sum())
).reset_index()

mapa_cidade["perc_atraso"] = (mapa_cidade["qtd_atrasadas"]/mapa_cidade["qtd_nfs"]*100).round(1)


# ============================================================
# INTELIGÊNCIA
# ============================================================
st.subheader("🧠 Inteligência de negócio")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Top cidades com mais atraso**")
    tab = mapa_cidade.sort_values("qtd_atrasadas", ascending=False).head(5)

    tab = tab[["Cidade","UF","qtd_atrasadas","perc_atraso","valor_total"]]
    tab.columns = ["Cidade","UF","Qtd atrasadas","% atraso","Valor total"]

    tab["% atraso"] = tab["% atraso"].map(lambda x: f"{x:.1f}%")
    tab["Valor total"] = tab["Valor total"].apply(formatar_moeda_br)

    st.dataframe(tab, use_container_width=True, hide_index=True)

with col2:
    st.markdown("**Regiões críticas (UFs)**")
    tab = mapa_uf.sort_values("qtd_atrasadas", ascending=False).head(5)

    tab = tab[["UF","qtd_atrasadas","perc_atraso","valor_total"]]
    tab.columns = ["UF","Qtd atrasadas","% atraso","Valor total"]

    tab["% atraso"] = tab["% atraso"].map(lambda x: f"{x:.1f}%")
    tab["Valor total"] = tab["Valor total"].apply(formatar_moeda_br)

    st.dataframe(tab, use_container_width=True, hide_index=True)


# ============================================================
# MAPA UF
# ============================================================
st.subheader("Mapa do Brasil por UF")

geo = requests.get("https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson").json()

fig_uf = px.choropleth(
    mapa_uf,
    geojson=geo,
    locations="UF",
    featureidkey="properties.sigla",
    color="qtd_nfs",
    hover_data={"valor_total":":,.2f","perc_atraso":True}
)

fig_uf.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig_uf, use_container_width=True, config={"scrollZoom": True})


# ============================================================
# MAPA CIDADE
# ============================================================
st.subheader("Mapa Analítico")

fig_cidade = px.scatter_mapbox(
    mapa_cidade,
    lat="lat",
    lon="lon",
    size="qtd_nfs",
    color="perc_atraso",
    zoom=3.5,
    height=700,
    hover_data={"valor_total":":,.2f","perc_atraso":True}
)

fig_cidade.update_layout(mapbox_style="carto-positron")

st.plotly_chart(fig_cidade, use_container_width=True, config={"scrollZoom": True})

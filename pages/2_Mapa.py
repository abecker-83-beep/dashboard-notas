import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from utils.load_data import load_data

st.title("🗺️ Mapa")

# =========================
# CARREGAR DADOS
# =========================
df = load_data()
df.columns = df.columns.str.strip()

# =========================
# TRATAMENTOS
# =========================
df["Cidade"] = df["Cidade"].astype(str).str.upper().str.strip()
df["UF"] = df["UF"].astype(str).str.upper().str.strip()
df["Representante"] = df["Representante"].astype(str).str.upper().str.strip()
df["Transportadora"] = df["Transportadora"].astype(str).str.upper().str.strip()

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

df["Vol"] = pd.to_numeric(df["Vol"], errors="coerce").fillna(0)

df["Status"] = df["Dias"].apply(
    lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")
)

# =========================
# FILTROS
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    transportadoras = sorted(df["Transportadora"].dropna().unique())
    transp_sel = st.multiselect(
        "Transportadora",
        transportadoras,
        default=transportadoras
    )

with col2:
    representantes = sorted(df["Representante"].dropna().unique())
    rep_sel = st.multiselect(
        "Representante",
        representantes,
        default=representantes
    )

with col3:
    metricas = {
        "Quantidade de NFs": "qtd_nfs",
        "Valor Total": "valor_total",
        "Volume Total": "vol_total",
    }
    metrica_label = st.selectbox("Métrica do mapa", list(metricas.keys()))
    metrica = metricas[metrica_label]

# =========================
# BASE FILTRADA
# =========================
df_filtrado = df[
    df["Transportadora"].isin(transp_sel) &
    df["Representante"].isin(rep_sel)
].copy()

# =========================
# MAPA POR UF
# =========================
mapa_uf = (
    df_filtrado.groupby("UF", dropna=False)
    .agg(
        qtd_nfs=("NF", "count"),
        valor_total=("Valor", "sum"),
        vol_total=("Vol", "sum"),
    )
    .reset_index()
)

geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
brasil_geojson = requests.get(geojson_url).json()

fig_uf = px.choropleth(
    mapa_uf,
    geojson=brasil_geojson,
    locations="UF",
    featureidkey="properties.sigla",
    color=metrica,
    hover_name="UF",
    hover_data={
        "qtd_nfs": True,
        "valor_total": ":,.2f",
        "vol_total": True,
    },
    title=f"Mapa por UF - {metrica_label}"
)

fig_uf.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(fig_uf, use_container_width=True)

st.subheader("Ranking por UF")
ranking_uf = mapa_uf.sort_values(metrica, ascending=False)
st.dataframe(ranking_uf, use_container_width=True)

# =========================
# MAPA POR CIDADE
# =========================
st.divider()
st.subheader("📍 Mapa por Cidade")

# carregar coordenadas
cidades = pd.read_csv("data/cidades.csv")
cidades["Cidade"] = cidades["Cidade"].astype(str).str.upper().str.strip()
cidades["UF"] = cidades["UF"].astype(str).str.upper().str.strip()

# merge com coordenadas
mapa_cidade = df_filtrado.merge(
    cidades,
    on=["Cidade", "UF"],
    how="left"
)

# mostrar cidades sem coordenadas
st.write("🔍 Cidades sem coordenadas:")
faltando = mapa_cidade[mapa_cidade["lat"].isna()]
st.dataframe(
    faltando[["Cidade", "UF"]].drop_duplicates(),
    use_container_width=True
)

# manter só cidades com lat/lon
mapa_cidade = mapa_cidade.dropna(subset=["lat", "lon"])

# agrupar
mapa_cidade = (
    mapa_cidade.groupby(["Cidade", "UF", "lat", "lon"])
    .agg(
        qtd_nfs=("NF", "count"),
        valor_total=("Valor", "sum"),
        vol_total=("Vol", "sum"),
    )
    .reset_index()
)

if mapa_cidade.empty:
    st.warning("Nenhuma cidade com coordenadas encontrada no arquivo data/cidades.csv para os filtros selecionados.")
else:
    fig_cidade = px.scatter_mapbox(
        mapa_cidade,
        lat="lat",
        lon="lon",
        size=metrica,
        color=metrica,
        hover_name="Cidade",
        hover_data={
            "UF": True,
            "qtd_nfs": True,
            "valor_total": ":,.2f",
            "vol_total": True,
            "lat": False,
            "lon": False,
        },
        zoom=3,
        height=600,
        title=f"Mapa por Cidade - {metrica_label}"
    )

    fig_cidade.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_cidade, use_container_width=True)

    st.subheader("Ranking por Cidade")
    ranking_cidade = mapa_cidade.sort_values(metrica, ascending=False)
    st.dataframe(ranking_cidade, use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.load_data import load_data

st.title("🗺️ Mapa")

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

df["Vol"] = pd.to_numeric(df["Vol"], errors="coerce").fillna(0)

df["Status"] = df["Dias"].apply(
    lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")
)

# Filtros
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

df_filtrado = df[
    df["Transportadora"].isin(transp_sel) &
    df["Representante"].isin(rep_sel)
].copy()

# Agrupamento por UF
mapa_uf = (
    df_filtrado.groupby("UF", dropna=False)
    .agg(
        qtd_nfs=("NF", "count"),
        valor_total=("Valor", "sum"),
        vol_total=("Vol", "sum"),
    )
    .reset_index()
)

fig = px.choropleth(
    mapa_uf,
    locations="UF",
    locationmode="geojson-id",
    color=metrica,
    scope="south america",
    geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
    featureidkey="properties.sigla",
    hover_name="UF",
    hover_data={
        "qtd_nfs": True,
        "valor_total": ":,.2f",
        "vol_total": ":,.0f",
        "UF": False,
    },
    title=f"Mapa por UF - {metrica_label}"
)

fig.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Ranking complementar
ranking_uf = mapa_uf.sort_values(metrica, ascending=False)

st.subheader("Ranking por UF")
st.dataframe(ranking_uf, use_container_width=True)

st.divider()
st.subheader("📍 Mapa por Cidade")

# Agrupar por cidade
mapa_cidade = (
    df_filtrado.groupby(["Cidade", "UF"])
    .agg(
        qtd_nfs=("NF", "count"),
        valor_total=("Valor", "sum"),
        vol_total=("Vol", "sum"),
    )
    .reset_index()
)

# 🔥 Coordenadas básicas (vamos melhorar depois)
import requests

def get_lat_lon(cidade, uf):
    try:
        url = f"https://nominatim.openstreetmap.org/search?city={cidade}&state={uf}&country=Brazil&format=json"
        r = requests.get(url).json()
        if len(r) > 0:
            return float(r[0]["lat"]), float(r[0]["lon"])
    except:
        pass
    return None, None

# Criar colunas
mapa_cidade["lat"], mapa_cidade["lon"] = zip(
    *mapa_cidade.apply(lambda row: get_lat_lon(row["Cidade"], row["UF"]), axis=1)
)

mapa_cidade = mapa_cidade.dropna(subset=["lat", "lon"])

# Plotar mapa
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
    },
    zoom=3,
    height=600
)

st.divider()
st.subheader("📍 Mapa por Cidade")

# carregar base de cidades
cidades = pd.read_csv("data/cidades.csv")

# padronizar
df_filtrado["Cidade"] = df_filtrado["Cidade"].str.upper().str.strip()

# juntar com coordenadas
mapa_cidade = df_filtrado.merge(
    st.write("🔍 Cidades sem coordenadas:")

faltando = mapa_cidade[mapa_cidade["lat"].isna()]

st.dataframe(faltando[["Cidade", "UF"]].drop_duplicates())
    cidades,
    on=["Cidade", "UF"],
    how="left"
)

mapa_cidade = mapa_cidade.dropna(subset=["lat", "lon"])

# agregação
mapa_cidade = (
    mapa_cidade.groupby(["Cidade", "UF", "lat", "lon"])
    .agg(
        qtd_nfs=("NF", "count"),
        valor_total=("Valor", "sum"),
        vol_total=("Vol", "sum"),
    )
    .reset_index()
)

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
    },
    zoom=3,
    height=600
)

fig_cidade.update_layout(mapbox_style="open-street-map")

st.plotly_chart(fig_cidade, use_container_width=True)
fig_cidade.update_layout(mapbox_style="open-street-map")

st.plotly_chart(fig_cidade, use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import unicodedata
import re
from utils.load_data import load_data


def normalizar_texto(valor: str) -> str:
    if pd.isna(valor):
        return ""
    valor = str(valor).strip().upper()
    valor = unicodedata.normalize("NFKD", valor).encode("ASCII", "ignore").decode("ASCII")
    valor = re.sub(r"\s+", " ", valor)
    return valor


st.title("🗺️ Mapa")

# =========================
# CARREGAR DADOS
# =========================
df = load_data()
df.columns = df.columns.str.strip()

# =========================
# TRATAMENTOS
# =========================
for col in ["Cidade", "UF", "Representante", "Transportadora"]:
    df[col] = df[col].astype(str).apply(normalizar_texto)

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
    transportadoras = sorted([x for x in df["Transportadora"].dropna().unique() if x])
    transp_sel = st.multiselect(
        "Transportadora",
        transportadoras,
        default=transportadoras
    )

with col2:
    representantes = sorted([x for x in df["Representante"].dropna().unique() if x])
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
# KPIs
# =========================
colk1, colk2, colk3, colk4 = st.columns(4)
colk1.metric("Cidades no filtro", df_filtrado[["Cidade", "UF"]].drop_duplicates().shape[0])
colk2.metric("UFs no filtro", df_filtrado["UF"].nunique())
colk3.metric("Total NFs", len(df_filtrado))
colk4.metric("Valor Total", f"R$ {df_filtrado['Valor'].sum():,.2f}")

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
brasil_geojson = requests.get(geojson_url, timeout=30).json()

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

cidades = pd.read_csv("data/cidades.csv")
cidades.columns = cidades.columns.str.strip()

for col in ["Cidade", "UF"]:
    cidades[col] = cidades[col].astype(str).apply(normalizar_texto)

cidades["lat"] = pd.to_numeric(cidades["lat"], errors="coerce")
cidades["lon"] = pd.to_numeric(cidades["lon"], errors="coerce")

mapa_cidade = df_filtrado.merge(
    cidades[["Cidade", "UF", "lat", "lon"]],
    on=["Cidade", "UF"],
    how="left"
)

faltando = mapa_cidade[mapa_cidade["lat"].isna()][["Cidade", "UF"]].drop_duplicates()
encontradas = mapa_cidade[mapa_cidade["lat"].notna()][["Cidade", "UF"]].drop_duplicates()

colm1, colm2 = st.columns(2)
colm1.metric("Cidades com coordenadas", len(encontradas))
colm2.metric("Cidades sem coordenadas", len(faltando))

with st.expander("Ver cidades sem coordenadas"):
    st.dataframe(faltando.sort_values(["UF", "Cidade"]), use_container_width=True)

mapa_cidade = mapa_cidade.dropna(subset=["lat", "lon"])

mapa_cidade = (
    mapa_cidade.groupby(["Cidade", "UF", "lat", "lon"], as_index=False)
    .agg(
        qtd_nfs=("NF", "count"),
        valor_total=("Valor", "sum"),
        vol_total=("Vol", "sum"),
    )
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
        height=650,
        title=f"Mapa por Cidade - {metrica_label}"
    )
    fig_cidade.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_cidade, use_container_width=True)

    st.subheader("Ranking por Cidade")
    ranking_cidade = mapa_cidade.sort_values(metrica, ascending=False)
    st.dataframe(ranking_cidade, use_container_width=True)

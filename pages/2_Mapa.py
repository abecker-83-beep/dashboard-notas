import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import unicodedata
import re
from utils.load_data import load_data

def formatar_moeda_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
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
# FILTROS INTELIGENTES
# =========================

st.subheader("Filtros")

base_filtros = df.copy()

col1, col2, col3, col4 = st.columns(4)

# estado inicial
transportadoras_all = sorted([x for x in base_filtros["Transportadora"].dropna().unique() if x])
representantes_all = sorted([x for x in base_filtros["Representante"].dropna().unique() if x])
ufs_all = sorted([x for x in base_filtros["UF"].dropna().unique() if x])
cidades_all = sorted([x for x in base_filtros["Cidade"].dropna().unique() if x])

with col1:
    transp_sel = st.multiselect(
        "Transportadora",
        transportadoras_all,
        default=[]
    )

# restringe base conforme transportadora
base_rep = base_filtros.copy()
if transp_sel:
    base_rep = base_rep[base_rep["Transportadora"].isin(transp_sel)]

with col2:
    representantes_disp = sorted([x for x in base_rep["Representante"].dropna().unique() if x])
    rep_sel = st.multiselect(
        "Representante",
        representantes_disp,
        default=[]
    )

# restringe base conforme transportadora + representante
base_uf = base_filtros.copy()
if transp_sel:
    base_uf = base_uf[base_uf["Transportadora"].isin(transp_sel)]
if rep_sel:
    base_uf = base_uf[base_uf["Representante"].isin(rep_sel)]

with col3:
    ufs_disp = sorted([x for x in base_uf["UF"].dropna().unique() if x])
    uf_sel = st.multiselect(
        "UF",
        ufs_disp,
        default=[]
    )

# restringe base conforme transportadora + representante + uf
base_cidade = base_filtros.copy()
if transp_sel:
    base_cidade = base_cidade[base_cidade["Transportadora"].isin(transp_sel)]
if rep_sel:
    base_cidade = base_cidade[base_cidade["Representante"].isin(rep_sel)]
if uf_sel:
    base_cidade = base_cidade[base_cidade["UF"].isin(uf_sel)]

with col4:
    cidades_disp = sorted([x for x in base_cidade["Cidade"].dropna().unique() if x])
    cidade_sel = st.multiselect(
        "Cidade",
        cidades_disp,
        default=[]
    )

col5, col6 = st.columns(2)

with col5:
    metricas = {
        "Quantidade de NFs": "qtd_nfs",
        "Valor Total": "valor_total",
        "Volume Total": "vol_total",
    }
    metrica_label = st.selectbox("Métrica do mapa", list(metricas.keys()))
    metrica = metricas[metrica_label]

with col6:
    modo_mapa = st.radio(
        "Visualização",
        ["Agrupado por cidade", "Cada NF"],
        horizontal=True
    )

# aplica filtros finais
df_filtrado = base_filtros.copy()

if transp_sel:
    df_filtrado = df_filtrado[df_filtrado["Transportadora"].isin(transp_sel)]
if rep_sel:
    df_filtrado = df_filtrado[df_filtrado["Representante"].isin(rep_sel)]
if uf_sel:
    df_filtrado = df_filtrado[df_filtrado["UF"].isin(uf_sel)]
if cidade_sel:
    df_filtrado = df_filtrado[df_filtrado["Cidade"].isin(cidade_sel)]

# mensagem amigável se nada encontrado
if df_filtrado.empty:
    st.warning("Nenhum registro encontrado com os filtros selecionados. Ajuste Transportadora, Representante, UF ou Cidade.")
# =========================
# KPIs
# =========================
colk1, colk2, colk3, colk4 = st.columns(4)
colk1.metric("Cidades no filtro", df_filtrado[["Cidade", "UF"]].drop_duplicates().shape[0])
colk2.metric("UFs no filtro", df_filtrado["UF"].nunique())
colk3.metric("Total NFs", len(df_filtrado))
colk4.metric("Valor das Notas", formatar_moeda_br(df_filtrado["Valor"].sum()))

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
st.divider()
st.subheader("📍 Mapa por Cidade / NF")

import numpy as np

# carregar coordenadas
cidades = pd.read_csv("data/cidades.csv")
cidades.columns = cidades.columns.str.strip()

for col in ["Cidade", "UF"]:
    cidades[col] = cidades[col].astype(str).apply(normalizar_texto)

cidades["lat"] = pd.to_numeric(cidades["lat"], errors="coerce")
cidades["lon"] = pd.to_numeric(cidades["lon"], errors="coerce")

# filtro extra por UF no mapa
df_mapa = df_filtrado.copy()

# merge com base fixa
mapa_base = df_mapa.merge(
    cidades[["Cidade", "UF", "lat", "lon"]],
    on=["Cidade", "UF"],
    how="left"
)

faltando = mapa_base[mapa_base["lat"].isna()][["Cidade", "UF"]].drop_duplicates()
encontradas = mapa_base[mapa_base["lat"].notna()][["Cidade", "UF"]].drop_duplicates()

col_a, col_b, col_c = st.columns(3)
col_a.metric("Cidades com coordenadas", len(encontradas))
col_b.metric("Cidades sem coordenadas", len(faltando))
col_c.metric("Linhas no mapa", len(mapa_base.dropna(subset=["lat", "lon"])))

with st.expander("Ver cidades sem coordenadas"):
    st.dataframe(faltando.sort_values(["UF", "Cidade"]), use_container_width=True)

mapa_base = mapa_base.dropna(subset=["lat", "lon"]).copy()

if mapa_base.empty:
    st.warning("Nenhuma cidade com coordenadas encontrada para os filtros selecionados.")
else:
    # centro automático
    center_lat = float(mapa_base["lat"].mean())
    center_lon = float(mapa_base["lon"].mean())

    if modo_mapa == "Agrupado por cidade":
        mapa_cidade = (
            mapa_base.groupby(["Cidade", "UF", "lat", "lon"], as_index=False)
            .agg(
                qtd_nfs=("NF", "count"),
                valor_total=("Valor", "sum"),
                vol_total=("Vol", "sum"),
            )
        )

        fig_cidade = px.scatter_mapbox(
    mapa_cidade,
    lat="lat",
    lon="lon",
    size=metrica,
    color=metrica,
    color_continuous_scale="reds",  # 👈 AQUI
            size_max=40,
           zoom=5 if uf_sel and len(uf_sel) <= 2 else 3.8,
            center={"lat": center_lat, "lon": center_lon},
            height=650,
            hover_name="Cidade",
            hover_data={
                "UF": True,
                "qtd_nfs": True,
                "valor_total": ":,.2f",
                "vol_total": True,
                "lat": False,
                "lon": False,
            },
            title=f"Mapa por Cidade - {metrica_label}"
        )

        fig_cidade.update_layout(
            mapbox_style="carto-positron",
            margin=dict(l=0, r=0, t=50, b=0)
        )
        st.plotly_chart(fig_cidade, use_container_width=True)

        st.subheader("Ranking por Cidade")
        ranking_cidade = mapa_cidade.sort_values(metrica, ascending=False)
        st.dataframe(ranking_cidade, use_container_width=True)

    else:
        # Cada NF individualmente
        mapa_nf = mapa_base.copy()

        # garantir colunas para hover
        if "NF" not in mapa_nf.columns:
            mapa_nf["NF"] = ""
        if "Cliente" not in mapa_nf.columns:
            mapa_nf["Cliente"] = ""
        if "Transportadora" not in mapa_nf.columns:
            mapa_nf["Transportadora"] = ""
        if "Representante" not in mapa_nf.columns:
            mapa_nf["Representante"] = ""

        # jitter leve para separar NFs da mesma cidade
        mapa_nf["ordem"] = mapa_nf.groupby(["Cidade", "UF"]).cumcount()
        mapa_nf["lat_plot"] = mapa_nf["lat"] + (mapa_nf["ordem"] % 5) * 0.03
        mapa_nf["lon_plot"] = mapa_nf["lon"] + (mapa_nf["ordem"] // 5) * 0.03

        fig_nf = px.scatter_mapbox(
            mapa_nf,
            lat="lat_plot",
            lon="lon_plot",
            size=np.full(len(mapa_nf), 14),
            opacity=0.85,
            color="Status",
            zoom=3.8,
            center={"lat": center_lat, "lon": center_lon},
            height=700,
            hover_name="Cidade",
            hover_data={
                "UF": True,
                "NF": True,
                "Cliente": True,
                "Transportadora": True,
                "Representante": True,
                "Valor": ":,.2f",
                "Vol": True,
                "Dias": True,
                "Status": True,
                "lat_plot": False,
                "lon_plot": False,
            },
            title="Mapa por NF individual"
        )

        fig_nf.update_traces(marker=dict(opacity=0.75))
        fig_nf.update_layout(
            mapbox_style="carto-positron",
            margin=dict(l=0, r=0, t=50, b=0)
        )
        st.plotly_chart(fig_nf, use_container_width=True)

        st.subheader("Tabela das NFs no mapa")
        st.dataframe(
            mapa_nf[
                ["NF", "Cidade", "UF", "Cliente", "Transportadora", "Representante", "Valor", "Vol", "Dias", "Status"]
            ],
            use_container_width=True
        )


import pandas as pd
import streamlit as st
import plotly.express as px
import requests
from utils.load_data import load_data
from utils.ui import card_kpi, CORES, aplicar_estilo_global, cor_percentual, render_sidebar_brand
from utils.business import preparar_base_dashboard, formatar_moeda_br, percentual

st.title("🗺️ Mapa V3")
st.caption("Mapa operacional com visão analítica por UF, cidade e NF.")
aplicar_estilo_global()
render_sidebar_brand()

STATUS_COLORS = {"No prazo":"#16A34A","Vence hoje":"#D97706","Atrasado":"#DC2626"}

@st.cache_data(show_spinner=False)
def carregar_geojson_brasil():
    return requests.get("https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson", timeout=30).json()

@st.cache_data(show_spinner=False)
def carregar_cidades():
    cidades = pd.read_csv("data/cidades.csv")
    cidades.columns = cidades.columns.str.strip()
    for col in ["Cidade","UF"]:
        cidades[col] = cidades[col].astype(str).str.strip().str.upper()
    cidades["lat"] = pd.to_numeric(cidades["lat"], errors="coerce")
    cidades["lon"] = pd.to_numeric(cidades["lon"], errors="coerce")
    return cidades

df_raw = load_data()
df, _, _ = preparar_base_dashboard(df_raw)
cidades = carregar_cidades()

valor_total_mapa = formatar_moeda_br(df["Valor"].sum())
k1, k2, k3, k4 = st.columns([1,1,1,2.3])
with k1:
    card_kpi("Total NFs", f"{len(df):,}".replace(",", "."), CORES["cinza"])
with k2:
    card_kpi("UFs", str(df["UF"].nunique()), CORES["cinza"])
with k3:
    card_kpi("Cidades", str(df[["Cidade","UF"]].drop_duplicates().shape[0]), CORES["cinza"])
with k4:
    card_kpi("Valor total", valor_total_mapa, CORES["azul"])

mapa_base = df.merge(cidades[["Cidade","UF","lat","lon"]], on=["Cidade","UF"], how="left")
mapa_ok = mapa_base.dropna(subset=["lat","lon"]).copy()
if mapa_ok.empty:
    st.warning("Nenhuma cidade com coordenadas encontrada.")
    st.stop()

base_uf = df.copy()
base_uf["flag_atraso"] = (base_uf["Status"] == "Atrasado").astype(int)
mapa_uf = base_uf.groupby("UF", dropna=False).agg(qtd_nfs=("NF","count"), valor_total=("Valor","sum"), qtd_atrasadas=("flag_atraso","sum")).reset_index()
mapa_uf["perc_atraso"] = mapa_uf.apply(lambda r: percentual(r["qtd_atrasadas"], r["qtd_nfs"]), axis=1)

r1, r2, r3 = st.columns(3)
with r1:
    card_kpi("Atrasadas", str(int((df["Status"]=="Atrasado").sum())), CORES["vermelho"])
with r2:
    card_kpi("Vence hoje", str(int((df["Status"]=="Vence hoje").sum())), CORES["amarelo"])
with r3:
    card_kpi("% Atraso", f"{percentual(int((df['Status']=='Atrasado').sum()), len(df)):.1f}%", cor_percentual(percentual(int((df['Status']=='Atrasado').sum()), len(df))))

fig = px.choropleth(mapa_uf, geojson=carregar_geojson_brasil(), locations="UF", featureidkey="properties.sigla", color="qtd_nfs", hover_name="UF", title="Mapa do Brasil por UF")
fig.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(fig, use_container_width=True)

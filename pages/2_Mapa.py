import requests
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

from utils.load_data import load_data
from utils.ui import card_kpi, CORES, aplicar_estilo_global, cor_percentual, render_sidebar_brand
from utils.business import preparar_base_dashboard, formatar_moeda_br, percentual


# ============================================================
# CONFIGURAÇÃO
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

METRICAS = {
    "Quantidade de NFs": "qtd_nfs",
    "Valor total": "valor_total",
    "Volume total": "vol_total",
}

MAP_STYLES = {
    "Claro": "carto-positron",
    "Escuro": "carto-darkmatter",
    "OpenStreetMap": "open-street-map",
}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
@st.cache_data(show_spinner=False)
def carregar_dados():
    df_raw = load_data()
    df, _, _ = preparar_base_dashboard(df_raw)
    return df


@st.cache_data(show_spinner=False)
def carregar_cidades():
    cidades = pd.read_csv("data/cidades.csv")
    cidades.columns = cidades.columns.str.strip()

    for col in ["Cidade", "UF"]:
        cidades[col] = cidades[col].astype(str).str.strip().str.upper()

    cidades["lat"] = pd.to_numeric(cidades["lat"], errors="coerce")
    cidades["lon"] = pd.to_numeric(cidades["lon"], errors="coerce")
    return cidades


@st.cache_data(show_spinner=False, ttl=86400)
def carregar_geojson_brasil():
    geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return requests.get(geojson_url, timeout=30).json()


def classificar_status_cidade(row):
    if row["qtd_atrasadas"] > 0:
        return "Atrasado"
    if row["qtd_vence_hoje"] > 0:
        return "Vence hoje"
    return "No prazo"


def calcular_zoom(df_mapa, uf_sel, modo):
    if len(df_mapa) == 0:
        return 3.6

    qtd_ufs = df_mapa["UF"].nunique() if "UF" in df_mapa.columns else 0
    qtd_cidades = (
        df_mapa[["Cidade", "UF"]].drop_duplicates().shape[0]
        if {"Cidade", "UF"}.issubset(df_mapa.columns)
        else 0
    )

    if uf_sel:
        if len(uf_sel) == 1:
            return 5.6 if modo == "Agrupado por cidade" else 6.0
        if len(uf_sel) == 2:
            return 4.8 if modo == "Agrupado por cidade" else 5.0
        if len(uf_sel) <= 4:
            return 4.2
        return 3.8

    if qtd_ufs <= 3:
        return 4.5
    if qtd_ufs <= 8:
        return 4.0
    if qtd_cidades <= 30:
        return 4.2
    return 3.7


def calcular_center(df_mapa):
    if df_mapa.empty:
        return {"lat": -14.2350, "lon": -51.9253}
    return {
        "lat": float(df_mapa["lat"].mean()),
        "lon": float(df_mapa["lon"].mean()),
    }


def aplicar_filtros(df, transp_sel, rep_sel, uf_sel, cidade_sel):
    df_filtrado = df.copy()

    if transp_sel:
        df_filtrado = df_filtrado[df_filtrado["Transportadora"].isin(transp_sel)]
    if rep_sel:
        df_filtrado = df_filtrado[df_filtrado["Representante"].isin(rep_sel)]
    if uf_sel:
        df_filtrado = df_filtrado[df_filtrado["UF"].isin(uf_sel)]
    if cidade_sel:
        df_filtrado = df_filtrado[df_filtrado["Cidade"].isin(cidade_sel)]

    return df_filtrado


def gerar_base_mapa(df_filtrado, cidades):
    mapa_base = df_filtrado.merge(
        cidades[["Cidade", "UF", "lat", "lon"]],
        on=["Cidade", "UF"],
        how="left"
    )

    faltando = mapa_base[mapa_base["lat"].isna()][["Cidade", "UF"]].drop_duplicates()
    mapa_ok = mapa_base.dropna(subset=["lat", "lon"]).copy()

    return mapa_base, mapa_ok, faltando


def gerar_agregado_uf(df_filtrado):
    base = df_filtrado.copy()
    base["flag_atraso"] = (base["Status"] == "Atrasado").astype(int)

    mapa_uf = (
        base.groupby("UF", dropna=False)
        .agg(
            qtd_nfs=("NF", "count"),
            valor_total=("Valor", "sum"),
            vol_total=("Vol", "sum"),
            qtd_atrasadas=("flag_atraso", "sum"),
        )
        .reset_index()
    )

    mapa_uf["perc_atraso"] = np.where(
        mapa_uf["qtd_nfs"] > 0,
        (mapa_uf["qtd_atrasadas"] / mapa_uf["qtd_nfs"]) * 100,
        0,
    )
    return mapa_uf


def gerar_agregado_cidade(mapa_ok):
    base = mapa_ok.copy()
    base["flag_atraso"] = (base["Status"] == "Atrasado").astype(int)
    base["flag_vence_hoje"] = (base["Status"] == "Vence hoje").astype(int)
    base["flag_no_prazo"] = (base["Status"] == "No prazo").astype(int)

    mapa_cidade = (
        base.groupby(["Cidade", "UF", "lat", "lon"], as_index=False)
        .agg(
            qtd_nfs=("NF", "count"),
            valor_total=("Valor", "sum"),
            vol_total=("Vol", "sum"),
            qtd_atrasadas=("flag_atraso", "sum"),
            qtd_vence_hoje=("flag_vence_hoje", "sum"),
            qtd_no_prazo=("flag_no_prazo", "sum"),
        )
    )

    mapa_cidade["perc_atraso"] = np.where(
        mapa_cidade["qtd_nfs"] > 0,
        (mapa_cidade["qtd_atrasadas"] / mapa_cidade["qtd_nfs"]) * 100,
        0,
    ).round(1)

    mapa_cidade["status_mapa"] = mapa_cidade.apply(classificar_status_cidade, axis=1)

    return mapa_cidade


def gerar_mapa_uf(mapa_uf, metrica, metrica_label):
    brasil_geojson = carregar_geojson_brasil()

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
            "qtd_atrasadas": True,
            "perc_atraso": ":.1f",
        },
        title=f"Mapa do Brasil por UF • {metrica_label}",
        color_continuous_scale="Blues",
    )
    fig_uf.update_geos(fitbounds="locations", visible=False)
    fig_uf.update_layout(margin=dict(l=0, r=0, t=60, b=0), height=520)
    return fig_uf


def gerar_mapa_cidade_agrupado(
    mapa_cidade,
    metrica,
    metrica_label,
    map_style,
    zoom,
    center,
    destacar_so_atrasos,
):
    base = mapa_cidade.copy()

    if destacar_so_atrasos:
        base = base[base["qtd_atrasadas"] > 0].copy()

    if base.empty:
        return None

    fig = px.scatter_mapbox(
        base,
        lat="lat",
        lon="lon",
        size=metrica,
        color="status_mapa",
        color_discrete_map=STATUS_COLORS,
        hover_name="Cidade",
        hover_data={
            "UF": True,
            "qtd_nfs": True,
            "valor_total": ":,.2f",
            "vol_total": True,
            "qtd_atrasadas": True,
            "perc_atraso": ":.1f",
            "lat": False,
            "lon": False,
            "status_mapa": True,
        },
        size_max=34,
        zoom=zoom,
        center=center,
        height=760,
        title=f"Mapa por Cidade • {metrica_label}",
    )

    fig.update_traces(
        marker=dict(opacity=0.82),
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "UF: %{customdata[0]}<br>"
            "Qtd NFs: %{customdata[1]}<br>"
            "Valor total: R$ %{customdata[2]:,.2f}<br>"
            "Volume total: %{customdata[3]}<br>"
            "Qtd atrasadas: %{customdata[4]}<br>"
            "% atraso: %{customdata[5]:.1f}%<br>"
            "Status: %{customdata[6]}<extra></extra>"
        )
    )

    fig.update_layout(
        mapbox_style=map_style,
        legend_title="Status",
        margin=dict(l=0, r=0, t=55, b=0),
    )

    return fig


def gerar_mapa_nf_individual(
    mapa_ok,
    map_style,
    zoom,
    center,
    destacar_so_atrasos,
):
    base = mapa_ok.copy()

    if destacar_so_atrasos:
        base = base[base["Status"] == "Atrasado"].copy()

    if base.empty:
        return None, base

    for col in ["NF", "Cliente", "Transportadora", "Representante"]:
        if col not in base.columns:
            base[col] = ""

    base["ordem"] = base.groupby(["Cidade", "UF"]).cumcount()
    base["angulo"] = (base["ordem"] % 12) * (2 * np.pi / 12)
    base["anel"] = (base["ordem"] // 12) + 1
    base["lat_plot"] = base["lat"] + np.sin(base["angulo"]) * (0.035 * base["anel"])
    base["lon_plot"] = base["lon"] + np.cos(base["angulo"]) * (0.035 * base["anel"])

    fig = px.scatter_mapbox(
        base,
        lat="lat_plot",
        lon="lon_plot",
        color="Status",
        color_discrete_map=STATUS_COLORS,
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
        zoom=zoom,
        center=center,
        height=760,
        title="Mapa por NF Individual",
    )

    fig.update_traces(
        marker=dict(
            size=8,
            opacity=0.50,
        ),
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "UF: %{customdata[0]}<br>"
            "NF: %{customdata[1]}<br>"
            "Cliente: %{customdata[2]}<br>"
            "Transportadora: %{customdata[3]}<br>"
            "Representante: %{customdata[4]}<br>"
            "Valor: R$ %{customdata[5]:,.2f}<br>"
            "Volume: %{customdata[6]}<br>"
            "Dias: %{customdata[7]}<br>"
            "Status: %{customdata[8]}<extra></extra>"
        )
    )

    fig.update_layout(
        mapbox_style=map_style,
        legend_title="Status",
        margin=dict(l=0, r=0, t=55, b=0),
    )

    return fig, base


def exibir_kpis(df_filtrado):
    st.subheader("Indicadores principais")
    col1, col2, col3, col4 = st.columns([1.0, 1.0, 1.0, 2.2])

    valor_total_mapa = formatar_moeda_br(df_filtrado["Valor"].sum())

    with col1:
        card_kpi("Total NFs", f"{len(df_filtrado):,}".replace(",", "."), CORES["cinza"])
    with col2:
        card_kpi("UFs", str(df_filtrado["UF"].nunique()), CORES["cinza"])
    with col3:
        card_kpi("Cidades", str(df_filtrado[["Cidade", "UF"]].drop_duplicates().shape[0]), CORES["cinza"])
    with col4:
        card_kpi("Valor total", valor_total_mapa, CORES["azul"])

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    col5, col6, col7 = st.columns([1.2, 1.2, 1.2])

    total_atrasadas = int((df_filtrado["Status"] == "Atrasado").sum())
    total_vence_hoje = int((df_filtrado["Status"] == "Vence hoje").sum())
    perc_atraso_total = percentual(total_atrasadas, len(df_filtrado))

    with col5:
        card_kpi("Atrasadas", f"{total_atrasadas:,}".replace(",", "."), CORES["vermelho"])
    with col6:
        card_kpi("Vence hoje", f"{total_vence_hoje:,}".replace(",", "."), CORES["amarelo"])
    with col7:
        card_kpi("% Atraso", f"{perc_atraso_total:.1f}%", cor_percentual(perc_atraso_total))


def exibir_resumo_operacional(df_filtrado, mapa_base, mapa_ok, faltando):
    st.subheader("Resumo operacional")
    col1, col2, col3, col4 = st.columns(4)

    total_atrasadas = int((df_filtrado["Status"] == "Atrasado").sum())
    total_vence_hoje = int((df_filtrado["Status"] == "Vence hoje").sum())
    perc_atraso_total = percentual(total_atrasadas, len(df_filtrado))
    perc_coord = percentual(
        mapa_ok[["Cidade", "UF"]].drop_duplicates().shape[0],
        mapa_base[["Cidade", "UF"]].drop_duplicates().shape[0],
    )

    with col1:
        card_kpi("NFs atrasadas", f"{total_atrasadas:,}".replace(",", "."), CORES["vermelho"])
    with col2:
        card_kpi("Vence hoje", f"{total_vence_hoje:,}".replace(",", "."), CORES["amarelo"])
    with col3:
        card_kpi("% atraso", f"{perc_atraso_total:.1f}%", cor_percentual(perc_atraso_total))
    with col4:
        card_kpi("Cobertura geográfica", f"{perc_coord:.1f}%", CORES["verde"])

    with st.expander("Qualidade geográfica / cidades sem coordenadas"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Cidades com coordenadas", mapa_ok[["Cidade", "UF"]].drop_duplicates().shape[0])
        c2.metric("Cidades sem coordenadas", faltando.shape[0])
        c3.metric("Linhas aptas ao mapa", len(mapa_ok))

        if not faltando.empty:
            st.dataframe(
                faltando.sort_values(["UF", "Cidade"]),
                use_container_width=True,
                hide_index=True
            )


def exibir_insights(mapa_cidade, mapa_uf):
    st.subheader("🧠 Inteligência de negócio")

    col1, col2 = st.columns(2)

    cidades_criticas = mapa_cidade[mapa_cidade["qtd_atrasadas"] > 0].copy()
    cidades_criticas = cidades_criticas.sort_values(
        ["qtd_atrasadas", "perc_atraso", "valor_total"],
        ascending=[False, False, False]
    ).head(5)

    ufs_criticas = mapa_uf[mapa_uf["qtd_atrasadas"] > 0].copy()
    ufs_criticas = ufs_criticas.sort_values(
        ["qtd_atrasadas", "perc_atraso", "valor_total"],
        ascending=[False, False, False]
    ).head(5)

    with col1:
        st.markdown("**Top cidades com mais atraso**")
        if cidades_criticas.empty:
            st.success("Nenhuma cidade com atraso no filtro atual.")
        else:
            tabela = cidades_criticas[["Cidade", "UF", "qtd_atrasadas", "perc_atraso", "valor_total"]].copy()
            tabela.columns = ["Cidade", "UF", "Qtd atrasadas", "% atraso", "Valor total"]
            tabela["Valor total"] = tabela["Valor total"].apply(formatar_moeda_br)
            st.dataframe(tabela, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**Regiões críticas (UFs)**")
        if ufs_criticas.empty:
            st.success("Nenhuma UF com atraso no filtro atual.")
        else:
            tabela = ufs_criticas[["UF", "qtd_atrasadas", "perc_atraso", "valor_total"]].copy()
            tabela.columns = ["UF", "Qtd atrasadas", "% atraso", "Valor total"]
            tabela["Valor total"] = tabela["Valor total"].apply(formatar_moeda_br)
            st.dataframe(tabela, use_container_width=True, hide_index=True)


# ============================================================
# CARGA E PREPARAÇÃO
# ============================================================
df = carregar_dados()
cidades = carregar_cidades()

# ============================================================
# FILTROS
# ============================================================
st.subheader("Filtros")

base_filtros = df.copy()
col1, col2, col3, col4 = st.columns(4)

transportadoras_all = sorted([x for x in base_filtros["Transportadora"].dropna().unique() if x])

with col1:
    transp_sel = st.multiselect("Transportadora", transportadoras_all, default=[])

base_rep = base_filtros.copy()
if transp_sel:
    base_rep = base_rep[base_rep["Transportadora"].isin(transp_sel)]

with col2:
    representantes_disp = sorted([x for x in base_rep["Representante"].dropna().unique() if x])
    rep_sel = st.multiselect("Representante", representantes_disp, default=[])

base_uf = base_filtros.copy()
if transp_sel:
    base_uf = base_uf[base_uf["Transportadora"].isin(transp_sel)]
if rep_sel:
    base_uf = base_uf[base_uf["Representante"].isin(rep_sel)]

with col3:
    ufs_disp = sorted([x for x in base_uf["UF"].dropna().unique() if x])
    uf_sel = st.multiselect("UF", ufs_disp, default=[])

base_cidade = base_filtros.copy()
if transp_sel:
    base_cidade = base_cidade[base_cidade["Transportadora"].isin(transp_sel)]
if rep_sel:
    base_cidade = base_cidade[base_cidade["Representante"].isin(rep_sel)]
if uf_sel:
    base_cidade = base_cidade[base_cidade["UF"].isin(uf_sel)]

with col4:
    cidades_disp = sorted([x for x in base_cidade["Cidade"].dropna().unique() if x])
    cidade_sel = st.multiselect("Cidade", cidades_disp, default=[])

col5, col6, col7, col8 = st.columns([1.1, 1.4, 1.2, 1.2])

with col5:
    metrica_label = st.selectbox("Métrica do mapa", list(METRICAS.keys()))
    metrica = METRICAS[metrica_label]

with col6:
    modo_mapa = st.radio(
        "Visualização",
        ["Agrupado por cidade", "Cada NF individual"],
        horizontal=True
    )

with col7:
    destacar_so_atrasos = st.toggle("Mostrar só atrasos", value=False)

with col8:
    estilo_mapa_label = st.selectbox("Estilo do mapa", list(MAP_STYLES.keys()))
    estilo_mapa = MAP_STYLES[estilo_mapa_label]


# ============================================================
# FILTRO FINAL
# ============================================================
df_filtrado = aplicar_filtros(df, transp_sel, rep_sel, uf_sel, cidade_sel)

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado com os filtros selecionados.")
    st.stop()


# ============================================================
# KPIs
# ============================================================
exibir_kpis(df_filtrado)

# ============================================================
# AGREGAÇÕES E BASES DE MAPA
# ============================================================
mapa_base, mapa_ok, faltando = gerar_base_mapa(df_filtrado, cidades)
mapa_uf = gerar_agregado_uf(df_filtrado)

if mapa_ok.empty:
    st.warning("Nenhuma cidade com coordenadas encontrada para os filtros selecionados.")
    with st.expander("Ver cidades sem coordenadas"):
        st.dataframe(
            faltando.sort_values(["UF", "Cidade"]),
            use_container_width=True,
            hide_index=True
        )
    st.stop()

mapa_cidade = gerar_agregado_cidade(mapa_ok)

center = calcular_center(mapa_ok)
zoom = calcular_zoom(mapa_ok, uf_sel, modo_mapa)

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
exibir_resumo_operacional(df_filtrado, mapa_base, mapa_ok, faltando)
st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
exibir_insights(mapa_cidade, mapa_uf)

# ============================================================
# MAPA POR UF
# ============================================================
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
st.subheader("Mapa do Brasil por UF")

fig_uf = gerar_mapa_uf(mapa_uf, metrica, metrica_label)
st.plotly_chart(fig_uf, use_container_width=True)

ranking_uf = mapa_uf.sort_values(metrica, ascending=False).copy()
ranking_uf["valor_total_fmt"] = ranking_uf["valor_total"].apply(formatar_moeda_br)

with st.expander("Ver ranking por UF"):
    st.dataframe(
        ranking_uf[["UF", "qtd_nfs", "valor_total_fmt", "vol_total", "qtd_atrasadas", "perc_atraso"]],
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# MAPA ANALÍTICO POR CIDADE / NF
# ============================================================
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
st.subheader("Mapa Analítico")

if modo_mapa == "Agrupado por cidade":
    fig_cidade = gerar_mapa_cidade_agrupado(
        mapa_cidade=mapa_cidade,
        metrica=metrica,
        metrica_label=metrica_label,
        map_style=estilo_mapa,
        zoom=zoom,
        center=center,
        destacar_so_atrasos=destacar_so_atrasos,
    )

    if fig_cidade is None:
        st.warning("Nenhum ponto encontrado para exibir no modo agrupado com o filtro atual.")
    else:
        st.plotly_chart(fig_cidade, use_container_width=True)

    ranking_cidade = mapa_cidade.copy()
    if destacar_so_atrasos:
        ranking_cidade = ranking_cidade[ranking_cidade["qtd_atrasadas"] > 0]

    ranking_cidade = ranking_cidade.sort_values(
        [metrica, "qtd_atrasadas", "perc_atraso"],
        ascending=[False, False, False]
    )

    ranking_cidade["valor_total_fmt"] = ranking_cidade["valor_total"].apply(formatar_moeda_br)

    with st.expander("Ver ranking por cidade"):
        st.dataframe(
            ranking_cidade[
                ["Cidade", "UF", "qtd_nfs", "valor_total_fmt", "vol_total", "qtd_atrasadas", "perc_atraso", "status_mapa"]
            ],
            use_container_width=True,
            hide_index=True,
        )

else:
    fig_nf, mapa_nf = gerar_mapa_nf_individual(
        mapa_ok=mapa_ok,
        map_style=estilo_mapa,
        zoom=zoom,
        center=center,
        destacar_so_atrasos=destacar_so_atrasos,
    )

    if fig_nf is None:
        st.warning("Nenhuma NF encontrada para exibir no modo individual com o filtro atual.")
    else:
        st.plotly_chart(fig_nf, use_container_width=True)

    with st.expander("Ver tabela detalhada das NFs no mapa"):
        tabela_nf = mapa_nf[
            ["NF", "Cidade", "UF", "Cliente", "Transportadora", "Representante", "Valor", "Vol", "Dias", "Status"]
        ].copy()

        tabela_nf["Valor"] = tabela_nf["Valor"].apply(formatar_moeda_br)

        st.dataframe(
            tabela_nf.sort_values(["UF", "Cidade", "Status"]),
            use_container_width=True,
            hide_index=True,
        )

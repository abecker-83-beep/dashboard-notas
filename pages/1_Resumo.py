import re
import unicodedata
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

from utils.load_data import load_data
from utils.ui import card_kpi, CORES, aplicar_estilo_global, cor_percentual

st.title("📊 Resumo")
st.caption("Visão executiva dos indicadores operacionais, financeiros e logísticos.")
aplicar_estilo_global()


def formatar_moeda_br(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def normalizar_texto(valor: str) -> str:
    if pd.isna(valor):
        return ""
    valor = str(valor).strip().upper()
    valor = unicodedata.normalize("NFKD", valor).encode("ASCII", "ignore").decode("ASCII")
    valor = re.sub(r"\s+", " ", valor)
    return valor


def garantir_coluna(df, coluna, valor_padrao=""):
    if coluna not in df.columns:
        df[coluna] = valor_padrao
    return df


def detectar_coluna_data(df):
    candidatos = ["Data", "DATA", "Dt Emissao", "DT EMISSAO", "Dt_Emissao", "Data Emissao", "Emissao", "Data NF", "Data Faturamento"]
    for col in candidatos:
        if col in df.columns:
            return col
    return None


def detectar_coluna_frete(df):
    candidatos = ["Frete", "FRETE", "Valor Frete", "VALOR FRETE", "Vlr Frete", "VLR FRETE", "Frete Total", "Custo Frete", "Valor do Frete"]
    for col in candidatos:
        if col in df.columns:
            return col
    return None


def converter_moeda_ou_numero(serie):
    serie = (
        serie.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    return pd.to_numeric(serie, errors="coerce").fillna(0)


@st.cache_data(show_spinner=False)
def carregar_dados():
    df = load_data().copy()
    df.columns = df.columns.str.strip()

    for col in ["NF", "Cliente", "Cidade", "UF", "Representante", "Transportadora", "Status"]:
        df = garantir_coluna(df, col, "")

    df = garantir_coluna(df, "Dias", 0)
    df = garantir_coluna(df, "Valor", 0)
    df = garantir_coluna(df, "Vol", 0)

    col_frete = detectar_coluna_frete(df)
    if col_frete:
        df["Frete_calc"] = converter_moeda_ou_numero(df[col_frete])
    else:
        df["Frete_calc"] = 0

    for col in ["Cliente", "Cidade", "UF", "Representante", "Transportadora"]:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("").apply(normalizar_texto)

    df["NF"] = df["NF"].astype(str).fillna("").str.strip()
    df["Dias"] = pd.to_numeric(df["Dias"], errors="coerce").fillna(0)
    df["Valor"] = converter_moeda_ou_numero(df["Valor"])
    df["Vol"] = pd.to_numeric(df["Vol"], errors="coerce").fillna(0)

    status_vazio = df["Status"].astype(str).str.strip().replace("", np.nan).isna()
    df["Status"] = np.where(
        status_vazio,
        df["Dias"].apply(lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")),
        df["Status"].astype(str).str.strip(),
    )

    col_data = detectar_coluna_data(df)
    if col_data:
        df[col_data] = pd.to_datetime(df[col_data], errors="coerce")

    return df, col_data, col_frete


def aplicar_filtros(df, col_data, periodo, transportadoras_sel, reps_sel, ufs_sel, status_sel):
    base = df.copy()

    if col_data and periodo and len(periodo) == 2:
        dt_ini = pd.to_datetime(periodo[0], errors="coerce")
        dt_fim = pd.to_datetime(periodo[1], errors="coerce")
        if pd.notna(dt_ini) and pd.notna(dt_fim):
            base = base[(base[col_data] >= dt_ini) & (base[col_data] <= dt_fim)]

    if transportadoras_sel:
        base = base[base["Transportadora"].isin(transportadoras_sel)]
    if reps_sel:
        base = base[base["Representante"].isin(reps_sel)]
    if ufs_sel:
        base = base[base["UF"].isin(ufs_sel)]
    if status_sel:
        base = base[base["Status"].isin(status_sel)]

    return base


df, col_data, col_frete_original = carregar_dados()

if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

st.subheader("Filtros")

if col_data and df[col_data].notna().any():
    data_min = df[col_data].min().date()
    data_max = df[col_data].max().date()
    periodo = st.date_input("Período", value=(data_min, data_max), min_value=data_min, max_value=data_max)
else:
    periodo = None

base_filtros = df.copy()
col1, col2, col3, col4 = st.columns(4)

with col1:
    transportadoras_opcoes = sorted([x for x in base_filtros["Transportadora"].dropna().unique() if x])
    transportadoras_sel = st.multiselect("Transportadora", transportadoras_opcoes, default=[])

base_rep = base_filtros.copy()
if transportadoras_sel:
    base_rep = base_rep[base_rep["Transportadora"].isin(transportadoras_sel)]

with col2:
    reps_opcoes = sorted([x for x in base_rep["Representante"].dropna().unique() if x])
    reps_sel = st.multiselect("Representante", reps_opcoes, default=[])

base_uf = base_filtros.copy()
if transportadoras_sel:
    base_uf = base_uf[base_uf["Transportadora"].isin(transportadoras_sel)]
if reps_sel:
    base_uf = base_uf[base_uf["Representante"].isin(reps_sel)]

with col3:
    ufs_opcoes = sorted([x for x in base_uf["UF"].dropna().unique() if x])
    ufs_sel = st.multiselect("UF", ufs_opcoes, default=[])

with col4:
    status_opcoes = ["Atrasado", "Vence hoje", "No prazo"]
    status_sel = st.multiselect("Status", status_opcoes, default=[])

df_filtrado = aplicar_filtros(df, col_data, periodo, transportadoras_sel, reps_sel, ufs_sel, status_sel)

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado com os filtros selecionados.")
    st.stop()

st.subheader("Indicadores principais")

total_notas = len(df_filtrado)
valor_total = df_filtrado["Valor"].sum()
valor_frete = df_filtrado["Frete_calc"].sum()
perc_frete = (valor_frete / valor_total * 100) if valor_total > 0 else 0

atrasadas = int((df_filtrado["Status"] == "Atrasado").sum())
vence_hoje = int((df_filtrado["Status"] == "Vence hoje").sum())
no_prazo = int((df_filtrado["Status"] == "No prazo").sum())
perc_atraso = (atrasadas / total_notas * 100) if total_notas > 0 else 0

valor_atrasado = df_filtrado[df_filtrado["Status"] == "Atrasado"]["Valor"].sum()
valor_vence_hoje = df_filtrado[df_filtrado["Status"] == "Vence hoje"]["Valor"].sum()
perc_valor_atrasado = (valor_atrasado / valor_total * 100) if valor_total > 0 else 0

tamanho_padrao = "18px"

c1, c2, c3, c4 = st.columns([1, 1.8, 1.6, 1])
with c1:
    card_kpi("Notas", f"{total_notas:,}".replace(",", "."), CORES["cinza"], tamanho_padrao)
with c2:
    card_kpi("Valor das Notas", formatar_moeda_br(valor_total), CORES["azul"], tamanho_padrao)
with c3:
    card_kpi("Valor de Frete", formatar_moeda_br(valor_frete), CORES["ciano"], tamanho_padrao)
with c4:
    cor_frete = CORES["verde"] if perc_frete <= 5 else CORES["amarelo"] if perc_frete <= 8 else CORES["vermelho"]
    card_kpi("% Frete", f"{perc_frete:.2f}%", cor_frete, tamanho_padrao)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

c5, c6, c7, c8 = st.columns(4)
with c5:
    card_kpi("🔴 Atrasadas", str(atrasadas), CORES["vermelho"], tamanho_padrao)
with c6:
    card_kpi("🟡 Vence hoje", str(vence_hoje), CORES["amarelo"], tamanho_padrao)
with c7:
    card_kpi("🟢 No prazo", str(no_prazo), CORES["verde"], tamanho_padrao)
with c8:
    card_kpi("% Atraso", f"{perc_atraso:.1f}%", cor_percentual(perc_atraso), tamanho_padrao)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

r1, r2, r3 = st.columns([1.6, 1.6, 1])
with r1:
    card_kpi("🚨 Valor em atraso", formatar_moeda_br(valor_atrasado), CORES["vermelho"], tamanho_padrao)
with r2:
    card_kpi("🟡 Valor vence hoje", formatar_moeda_br(valor_vence_hoje), CORES["amarelo"], tamanho_padrao)
with r3:
    card_kpi("% valor em risco", f"{perc_valor_atrasado:.1f}%", cor_percentual(perc_valor_atrasado), tamanho_padrao)

st.subheader("🚨 Alertas automáticos")
alertas = []
if perc_frete > 8:
    alertas.append(f"⚠️ Frete elevado: {perc_frete:.2f}% do faturamento")
if perc_atraso > 20:
    alertas.append(f"🔴 Alto índice de atraso: {perc_atraso:.1f}%")
if perc_valor_atrasado > 15:
    alertas.append(f"💰 Alto valor em risco: {perc_valor_atrasado:.1f}% do total")

if not alertas:
    st.success("✅ Operação dentro dos padrões")
else:
    for alerta in alertas:
        st.warning(alerta)

st.subheader("🏆 Onde agir agora")

ranking_problemas = (
    df_filtrado[df_filtrado["Status"] == "Atrasado"]
    .groupby("Transportadora", dropna=False)
    .agg(qtd_atrasos=("NF", "count"), valor_atrasado=("Valor", "sum"), valor_frete=("Frete_calc", "sum"))
    .reset_index()
)

if ranking_problemas.empty:
    st.success("✅ Nenhuma transportadora com atraso no filtro atual")
else:
    ranking_problemas = ranking_problemas.sort_values(["valor_atrasado", "qtd_atrasos"], ascending=False).head(5)
    ranking_problemas["qtd_atrasos"] = ranking_problemas["qtd_atrasos"].map(lambda x: f"{int(x):,}".replace(",", "."))
    ranking_problemas["valor_atrasado"] = ranking_problemas["valor_atrasado"].apply(formatar_moeda_br)
    ranking_problemas["valor_frete"] = ranking_problemas["valor_frete"].apply(formatar_moeda_br)
    ranking_problemas.columns = ["Transportadora", "Qtd. atrasos", "Valor atrasado", "Valor frete"]
    st.dataframe(ranking_problemas, use_container_width=True, hide_index=True)

st.subheader("Resumo executivo")
res1, res2 = st.columns(2)
with res1:
    st.markdown("**Financeiro**")
    resumo_fin = pd.DataFrame({
        "Indicador": ["Valor das Notas", "Valor de Frete", "% Frete sobre Notas", "Valor em atraso", "% Valor em risco"],
        "Valor": [formatar_moeda_br(valor_total), formatar_moeda_br(valor_frete), f"{perc_frete:.2f}%", formatar_moeda_br(valor_atrasado), f"{perc_valor_atrasado:.1f}%"],
    })
    st.dataframe(resumo_fin, use_container_width=True, hide_index=True)

with res2:
    st.markdown("**Operacional**")
    resumo_op = pd.DataFrame({
        "Indicador": ["Notas", "Atrasadas", "Vence hoje", "No prazo", "% Atraso"],
        "Valor": [f"{total_notas:,}".replace(",", "."), f"{atrasadas:,}".replace(",", "."), f"{vence_hoje:,}".replace(",", "."), f"{no_prazo:,}".replace(",", "."), f"{perc_atraso:.1f}%"],
    })
    st.dataframe(resumo_op, use_container_width=True, hide_index=True)

st.subheader("Visões gráficas")
g1, g2 = st.columns(2)
with g1:
    status_df = pd.DataFrame({"Status": ["Atrasado", "Vence hoje", "No prazo"], "Quantidade": [atrasadas, vence_hoje, no_prazo]})
    fig_status = px.bar(status_df, x="Status", y="Quantidade", title="Distribuição por Status")
    fig_status.update_layout(margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_status, use_container_width=True)

with g2:
    financeiro_df = pd.DataFrame({"Indicador": ["Valor das Notas", "Valor de Frete", "Valor em atraso"], "Valor": [valor_total, valor_frete, valor_atrasado]})
    fig_fin = px.bar(financeiro_df, x="Indicador", y="Valor", title="Notas vs Frete vs Risco")
    fig_fin.update_layout(margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_fin, use_container_width=True)

st.subheader("Ranking por transportadora")
ranking_transp = (
    df_filtrado.groupby("Transportadora", dropna=False)
    .agg(qtd_nfs=("NF", "count"), valor_notas=("Valor", "sum"), valor_frete=("Frete_calc", "sum"))
    .reset_index()
)
ranking_transp["perc_frete"] = np.where(ranking_transp["valor_notas"] > 0, (ranking_transp["valor_frete"] / ranking_transp["valor_notas"]) * 100, 0)
ranking_transp["valor_notas"] = ranking_transp["valor_notas"].apply(formatar_moeda_br)
ranking_transp["valor_frete"] = ranking_transp["valor_frete"].apply(formatar_moeda_br)
ranking_transp["perc_frete"] = ranking_transp["perc_frete"].map(lambda x: f"{x:.2f}%")
st.dataframe(ranking_transp.sort_values("qtd_nfs", ascending=False), use_container_width=True, hide_index=True)

with st.expander("Informações técnicas da base"):
    info_frete = col_frete_original if col_frete_original else "Nenhuma coluna de frete detectada"
    st.write(f"**Coluna de frete detectada:** {info_frete}")
    st.write(f"**Coluna de data detectada:** {col_data if col_data else 'Nenhuma'}")

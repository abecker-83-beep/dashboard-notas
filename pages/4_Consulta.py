import re
import unicodedata
import numpy as np
import pandas as pd
import streamlit as st

from utils.load_data import load_data
from utils.ui import card_kpi, CORES, aplicar_estilo_global, cor_percentual

st.title("🔎 Consulta")
st.caption("Consulta detalhada de notas com filtros, busca e resumo operacional.")
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


def detectar_coluna_data(df):
    candidatos = ["Data", "DATA", "Dt Emissao", "DT EMISSAO", "Dt_Emissao", "Data Emissao", "Emissao", "Data NF", "Data Faturamento"]
    for col in candidatos:
        if col in df.columns:
            return col
    return None


def garantir_coluna(df, coluna, valor_padrao=""):
    if coluna not in df.columns:
        df[coluna] = valor_padrao
    return df


@st.cache_data(show_spinner=False)
def carregar_dados():
    df = load_data().copy()
    df.columns = df.columns.str.strip()

    for col in ["NF", "Cliente", "Cidade", "UF", "Representante", "Transportadora", "Status"]:
        df = garantir_coluna(df, col, "")

    df = garantir_coluna(df, "Dias", 0)
    df = garantir_coluna(df, "Valor", 0)
    df = garantir_coluna(df, "Vol", 0)

    for col in ["Cidade", "UF", "Representante", "Transportadora", "Cliente"]:
        df[col] = df[col].astype(str).fillna("").apply(normalizar_texto)

    df["NF"] = df["NF"].astype(str).fillna("").str.strip()
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

    status_vazio = df["Status"].astype(str).str.strip().replace("", np.nan).isna()
    df["Status"] = np.where(
        status_vazio,
        df["Dias"].apply(lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")),
        df["Status"].astype(str).str.strip(),
    )

    col_data = detectar_coluna_data(df)
    if col_data:
        df[col_data] = pd.to_datetime(df[col_data], errors="coerce")

    return df, col_data


def aplicar_filtros(df, col_data, periodo, transportadoras_sel, reps_sel, ufs_sel, cidades_sel, status_sel, busca_texto):
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
    if cidades_sel:
        base = base[base["Cidade"].isin(cidades_sel)]
    if status_sel:
        base = base[base["Status"].isin(status_sel)]

    if busca_texto:
        busca = normalizar_texto(busca_texto)
        mask = (
            base["NF"].astype(str).str.contains(busca, na=False)
            | base["Cliente"].astype(str).str.contains(busca, na=False)
            | base["Cidade"].astype(str).str.contains(busca, na=False)
            | base["Transportadora"].astype(str).str.contains(busca, na=False)
            | base["Representante"].astype(str).str.contains(busca, na=False)
        )
        base = base[mask]

    return base


def colorir_status_linha(row):
    status = str(row.get("Status", "")).strip()
    if "Atrasado" in status:
        return ["background-color: #FEF2F2; color: #991B1B;"] * len(row)
    elif "Vence hoje" in status:
        return ["background-color: #FFFBEB; color: #92400E;"] * len(row)
    elif "No prazo" in status:
        return ["background-color: #F0FDF4; color: #166534;"] * len(row)
    return [""] * len(row)


def formatar_status(valor):
    valor = str(valor).strip()
    if valor == "Atrasado":
        return "🔴 Atrasado"
    elif valor == "Vence hoje":
        return "🟡 Vence hoje"
    elif valor == "No prazo":
        return "🟢 No prazo"
    return valor


df, col_data = carregar_dados()

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

c1, c2, c3, c4 = st.columns(4)
with c1:
    transportadoras_opcoes = sorted([x for x in base_filtros["Transportadora"].dropna().unique() if x])
    transportadoras_sel = st.multiselect("Transportadora", transportadoras_opcoes, default=[])

base_rep = base_filtros.copy()
if transportadoras_sel:
    base_rep = base_rep[base_rep["Transportadora"].isin(transportadoras_sel)]

with c2:
    reps_opcoes = sorted([x for x in base_rep["Representante"].dropna().unique() if x])
    reps_sel = st.multiselect("Representante", reps_opcoes, default=[])

base_uf = base_filtros.copy()
if transportadoras_sel:
    base_uf = base_uf[base_uf["Transportadora"].isin(transportadoras_sel)]
if reps_sel:
    base_uf = base_uf[base_uf["Representante"].isin(reps_sel)]

with c3:
    ufs_opcoes = sorted([x for x in base_uf["UF"].dropna().unique() if x])
    ufs_sel = st.multiselect("UF", ufs_opcoes, default=[])

base_cidade = base_filtros.copy()
if transportadoras_sel:
    base_cidade = base_cidade[base_cidade["Transportadora"].isin(transportadoras_sel)]
if reps_sel:
    base_cidade = base_cidade[base_cidade["Representante"].isin(reps_sel)]
if ufs_sel:
    base_cidade = base_cidade[base_cidade["UF"].isin(ufs_sel)]

with c4:
    cidades_opcoes = sorted([x for x in base_cidade["Cidade"].dropna().unique() if x])
    cidades_sel = st.multiselect("Cidade", cidades_opcoes, default=[])

c5, c6 = st.columns([1, 2])
with c5:
    status_opcoes = ["Atrasado", "Vence hoje", "No prazo"]
    status_sel = st.multiselect("Status", status_opcoes, default=[])

with c6:
    busca_texto = st.text_input(
        "Buscar por NF, Cliente, Cidade, Transportadora ou Representante",
        value="",
        placeholder="Ex.: 12345, CLIENTE XPTO, SAO PAULO..."
    )

df_filtrado = aplicar_filtros(df, col_data, periodo, transportadoras_sel, reps_sel, ufs_sel, cidades_sel, status_sel, busca_texto)

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado com os filtros selecionados.")
    st.stop()

st.subheader("Resumo da consulta")

total = len(df_filtrado)
atrasadas = int((df_filtrado["Status"] == "Atrasado").sum())
vence_hoje = int((df_filtrado["Status"] == "Vence hoje").sum())
no_prazo = int((df_filtrado["Status"] == "No prazo").sum())
valor_total = float(df_filtrado["Valor"].sum())
perc_atraso = (atrasadas / total * 100) if total > 0 else 0
tam = "18px"

r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns([1.0, 1.15, 1.15, 1.15, 2.1])
with r1c1:
    card_kpi("Notas", f"{total:,}".replace(",", "."), CORES["cinza"], tam)
with r1c2:
    card_kpi("🔴 Atrasadas", f"{atrasadas:,}".replace(",", "."), CORES["vermelho"], tam)
with r1c3:
    card_kpi("🟡 Vence hoje", f"{vence_hoje:,}".replace(",", "."), CORES["amarelo"], tam)
with r1c4:
    card_kpi("🟢 No prazo", f"{no_prazo:,}".replace(",", "."), CORES["verde"], tam)
with r1c5:
    card_kpi("Valor das Notas", formatar_moeda_br(valor_total), CORES["azul"], tam)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

r2c1, r2c2, r2c3 = st.columns([1.0, 1.1, 4.0])
with r2c1:
    card_kpi("% atraso", f"{perc_atraso:.1f}%", cor_percentual(perc_atraso), tam)
with r2c2:
    card_kpi("UFs no filtro", str(df_filtrado["UF"].nunique()), CORES["cinza"], tam)
with r2c3:
    st.markdown("")

st.subheader("📋 Tabela detalhada")

colunas_preferidas = ["NF", "Cliente", "Cidade", "UF", "Transportadora", "Representante", "Valor", "Vol", "Dias", "Status"]
if col_data:
    colunas_preferidas = [col_data] + colunas_preferidas

colunas_exibir = [c for c in colunas_preferidas if c in df_filtrado.columns]
tabela = df_filtrado[colunas_exibir].copy()

if col_data and col_data in tabela.columns:
    tabela[col_data] = pd.to_datetime(tabela[col_data], errors="coerce").dt.strftime("%d/%m/%Y")
if "Valor" in tabela.columns:
    tabela["Valor"] = tabela["Valor"].apply(formatar_moeda_br)
if "Vol" in tabela.columns:
    tabela["Vol"] = pd.to_numeric(tabela["Vol"], errors="coerce").fillna(0)
if "Dias" in tabela.columns:
    tabela["Dias"] = pd.to_numeric(tabela["Dias"], errors="coerce").fillna(0)

ordem_status = {"Atrasado": 0, "Vence hoje": 1, "No prazo": 2}
if "Status" in tabela.columns:
    tabela["_ordem_status"] = tabela["Status"].map(ordem_status).fillna(9)
else:
    tabela["_ordem_status"] = 9

colunas_sort = ["_ordem_status"]
ascending = [True]

if col_data and col_data in df_filtrado.columns:
    tabela["_data_sort"] = pd.to_datetime(df_filtrado[col_data], errors="coerce")
    colunas_sort.append("_data_sort")
    ascending.append(False)

tabela = tabela.sort_values(colunas_sort, ascending=ascending)
tabela = tabela.drop(columns=[c for c in ["_ordem_status", "_data_sort"] if c in tabela.columns])

if "Status" in tabela.columns:
    tabela["Status"] = tabela["Status"].apply(formatar_status)

tabela_estilizada = tabela.style.apply(colorir_status_linha, axis=1)

st.dataframe(tabela_estilizada, use_container_width=True, hide_index=True)

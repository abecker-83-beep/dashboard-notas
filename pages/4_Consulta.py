
import pandas as pd
import streamlit as st
from utils.load_data import load_data
from utils.ui import (
    card_kpi,
    CORES,
    aplicar_estilo_global,
    cor_percentual,
    render_sidebar_brand,
    setup_page,
    render_page_header,
    render_section_header,
    render_spacer,
)

from utils.business import preparar_base_dashboard, formatar_moeda_br

import pandas as pd
import streamlit as st
from utils.load_data import load_data
from utils.ui import card_kpi, CORES, aplicar_estilo_global, cor_percentual, render_sidebar_brand
from utils.business import preparar_base_dashboard, formatar_moeda_br

setup_page("Consulta")

render_page_header(
    "🔎 Consulta",
    "Consulta detalhada de notas com filtros, busca e resumo operacional."
)
aplicar_estilo_global()
render_sidebar_brand()

df_raw = load_data()
df, col_data, _ = preparar_base_dashboard(df_raw)
if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

render_section_header("🎛️ Filtros da consulta")

f1, f2, f3 = st.columns(3)
with f1:
    filtro_nf = st.text_input("NF", placeholder="Digite o número da NF")
with f2:
    opcoes_uf = sorted([uf for uf in df["UF"].dropna().unique().tolist() if str(uf).strip() != ""])
    filtro_uf = st.multiselect("UF", opcoes_uf)
with f3:
    opcoes_cidade = sorted([cidade for cidade in df["Cidade"].dropna().unique().tolist() if str(cidade).strip() != ""])
    filtro_cidade = st.multiselect("Cidade", opcoes_cidade)

f4, f5 = st.columns(2)
with f4:
    opcoes_cliente = sorted([cliente for cliente in df["Cliente"].dropna().unique().tolist() if str(cliente).strip() != ""])
    filtro_cliente = st.multiselect("Cliente", opcoes_cliente)
with f5:
    opcoes_transportadora = sorted([t for t in df["Transportadora"].dropna().unique().tolist() if str(t).strip() != ""])
    filtro_transportadora = st.multiselect("Transportadora", opcoes_transportadora)

df_filtrado = df.copy()

if filtro_nf:
    df_filtrado = df_filtrado[
        df_filtrado["NF"].astype(str).str.contains(filtro_nf.strip(), case=False, na=False)
    ]

if filtro_uf:
    df_filtrado = df_filtrado[df_filtrado["UF"].isin(filtro_uf)]

if filtro_cidade:
    df_filtrado = df_filtrado[df_filtrado["Cidade"].isin(filtro_cidade)]

if filtro_cliente:
    df_filtrado = df_filtrado[df_filtrado["Cliente"].isin(filtro_cliente)]

if filtro_transportadora:
    df_filtrado = df_filtrado[df_filtrado["Transportadora"].isin(filtro_transportadora)]

total = len(df_filtrado)
atrasadas = int((df_filtrado["Status"] == "Atrasado").sum())
vence_hoje = int((df_filtrado["Status"] == "Vence hoje").sum())
no_prazo = int((df_filtrado["Status"] == "No prazo").sum())
valor_total = float(df_filtrado["Valor"].sum())
perc_atraso = (atrasadas / total * 100) if total > 0 else 0

r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns([1.0, 1.15, 1.15, 1.15, 2.1])
with r1c1:
    card_kpi("Notas", f"{total:,}".replace(",", "."), CORES["cinza"])
with r1c2:
    card_kpi("🔴 Atrasadas", f"{atrasadas:,}".replace(",", "."), CORES["vermelho"])
with r1c3:
    card_kpi("🟡 Vence hoje", f"{vence_hoje:,}".replace(",", "."), CORES["amarelo"])
with r1c4:
    card_kpi("🟢 No prazo", f"{no_prazo:,}".replace(",", "."), CORES["verde"])
with r1c5:
    card_kpi("Valor das Notas", formatar_moeda_br(valor_total), CORES["azul"])

render_spacer()
r2c1, r2c2 = st.columns([1.0, 1.1])
with r2c1:
    card_kpi("% atraso", f"{perc_atraso:.1f}%", cor_percentual(perc_atraso))
with r2c2:
    card_kpi("UFs no filtro", str(df_filtrado["UF"].nunique()), CORES["cinza"])

df_raw = load_data()
df, col_data, _ = preparar_base_dashboard(df_raw)
if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

render_section_header("📋 Tabela detalhada")
tabela = df_filtrado[["NF","Cliente","Cidade","UF","Transportadora","Representante","Valor","Vol","Dias","Status"]].copy()
tabela["Valor"] = tabela["Valor"].apply(formatar_moeda_br)
st.dataframe(tabela, use_container_width=True, hide_index=True)

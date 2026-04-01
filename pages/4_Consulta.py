
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

total = len(df)
atrasadas = int((df["Status"] == "Atrasado").sum())
vence_hoje = int((df["Status"] == "Vence hoje").sum())
no_prazo = int((df["Status"] == "No prazo").sum())
valor_total = float(df["Valor"].sum())
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
    card_kpi("UFs no filtro", str(df["UF"].nunique()), CORES["cinza"])

render_section_header("📋 Tabela detalhada")
tabela = df[["NF","Cliente","Cidade","UF","Transportadora","Representante","Valor","Vol","Dias","Status"]].copy()
tabela["Valor"] = tabela["Valor"].apply(formatar_moeda_br)
st.dataframe(tabela, use_container_width=True, hide_index=True)
aplicar_estilo_global()
render_sidebar_brand()

df_raw = load_data()
df, col_data, _ = preparar_base_dashboard(df_raw)
if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

total = len(df)
atrasadas = int((df["Status"] == "Atrasado").sum())
vence_hoje = int((df["Status"] == "Vence hoje").sum())
no_prazo = int((df["Status"] == "No prazo").sum())
valor_total = float(df["Valor"].sum())
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

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
r2c1, r2c2 = st.columns([1.0, 1.1])
with r2c1:
    card_kpi("% atraso", f"{perc_atraso:.1f}%", cor_percentual(perc_atraso))
with r2c2:
    card_kpi("UFs no filtro", str(df["UF"].nunique()), CORES["cinza"])

render_section_header("📋 Tabela detalhada")
tabela = df[["NF","Cliente","Cidade","UF","Transportadora","Representante","Valor","Vol","Dias","Status"]].copy()
tabela["Valor"] = tabela["Valor"].apply(formatar_moeda_br)
st.dataframe(tabela, use_container_width=True, hide_index=True)

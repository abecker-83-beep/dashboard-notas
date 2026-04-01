
from utils.ui import card_kpi, CORES, aplicar_estilo_global, cor_percentual, render_sidebar_brand, cor_score
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.load_data import load_data
from utils.business import preparar_base_dashboard, formatar_moeda_br, calcular_score_transportadoras

st.title("🚚 Transportadoras")
st.caption("Análise operacional, financeira e executiva por transportadora.")
aplicar_estilo_global()
render_sidebar_brand()

df_raw = load_data()
df, _, col_frete = preparar_base_dashboard(df_raw)

render_section_header("🎛️ Filtro de transportadora")

opcoes_transportadora = sorted(
    [t for t in df["Transportadora"].dropna().unique().tolist() if str(t).strip() != ""]
)

transportadora_selecionada = st.selectbox(
    "Selecione uma transportadora",
    options=["Todas"] + opcoes_transportadora
)

if transportadora_selecionada != "Todas":
    df_filtrado = df[df["Transportadora"] == transportadora_selecionada].copy()
else:
    df_filtrado = df.copy()

# ===== INDICADORES BASEADOS NO FILTRO =====

total_transportadoras = df_filtrado["Transportadora"].nunique()
total_notas = len(df_filtrado)

atrasadas = int((df_filtrado["Status"] == "Atrasado").sum())
vence_hoje = int((df_filtrado["Status"] == "Vence hoje").sum())
no_prazo = int((df_filtrado["Status"] == "No prazo").sum())

valor_total = float(df_filtrado["Valor"].sum())
valor_frete = float(df_filtrado["Frete_calc"].sum())

perc_frete = (valor_frete / valor_total * 100) if valor_total > 0 else 0
perc_atraso = (atrasadas / total_notas * 100) if total_notas > 0 else 0

# score recalculado com base no filtro
ranking_score = calcular_score_transportadoras(df_filtrado)
score_medio = ranking_score["score"].mean() if not ranking_score.empty else 0

ranking_score = calcular_score_transportadoras(df_filtrado)
score_medio = ranking_score["score"].mean() if not ranking_score.empty else 0

tam = "18px"
k1, k2, k3, k4, k5 = st.columns([1, 1, 1, 1, 1])
with k1:
    card_kpi("Transportadoras", str(total_transportadoras), CORES["cinza"], tam)
with k2:
    card_kpi("Notas", f"{total_nfs:,}".replace(",", "."), CORES["cinza"], tam)
with k3:
    card_kpi("🔴 Atrasadas", str(atrasadas), CORES["vermelho"], tam)
with k4:
    card_kpi("% Atraso", f"{perc_atraso:.1f}%", cor_percentual(perc_atraso), tam)
with k5:
    card_kpi("Score médio", f"{score_medio:.1f}", cor_score(score_medio), tam)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
k6, k7, k8 = st.columns([2.0, 1.6, 1.0])
with k6:
    card_kpi("Valor Total das Notas", formatar_moeda_br(valor_total), CORES["azul"], tam)
with k7:
    card_kpi("Valor de Frete", formatar_moeda_br(valor_frete), CORES["ciano"], tam)
with k8:
    card_kpi("% Frete", f"{perc_frete:.2f}%", cor_percentual(perc_frete, 5, 8), tam)

st.subheader("Tabela executiva por transportadora")
ranking_tabela = ranking_score.sort_values(["score", "valor_risco"], ascending=[True, False]).copy()
ranking_tabela["valor_notas"] = ranking_tabela["valor_notas"].apply(formatar_moeda_br)
ranking_tabela["valor_frete"] = ranking_tabela["valor_frete"].apply(formatar_moeda_br)
ranking_tabela["valor_risco"] = ranking_tabela["valor_risco"].apply(formatar_moeda_br)
ranking_tabela["perc_atraso"] = ranking_tabela["perc_atraso"].map(lambda x: f"{x:.1f}%")
ranking_tabela["perc_frete"] = ranking_tabela["perc_frete"].map(lambda x: f"{x:.2f}%")
ranking_tabela["score"] = ranking_tabela["score"].map(lambda x: f"{x:.1f}")
st.dataframe(ranking_tabela[["Transportadora","qtd_notas","valor_notas","valor_frete","valor_risco","perc_atraso","perc_frete","score","classificacao"]], use_container_width=True, hide_index=True)

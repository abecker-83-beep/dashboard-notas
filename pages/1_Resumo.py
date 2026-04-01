
import pandas as pd
import streamlit as st
import plotly.express as px

from utils.ui import (
    setup_page,
    render_page_header,
    render_section_header,
    render_spacer,
    get_standard_kpi_columns,
    get_standard_two_columns,
    get_kpi_columns_custom,
)

from utils.load_data import load_data
from utils.ui import card_kpi, CORES, aplicar_estilo_global, cor_percentual, render_sidebar_brand, cor_score, METAS
from utils.business import preparar_base_dashboard, formatar_moeda_br, percentual, calcular_score_transportadoras, gerar_alertas_executivos, gerar_insights_transportadoras

setup_page("Resumo")

render_page_header(
    "📊 Resumo",
    "Visão executiva dos indicadores operacionais, financeiros e logísticos."
)

aplicar_estilo_global()
render_sidebar_brand()

df_raw = load_data()
df, _, col_frete_original = preparar_base_dashboard(df_raw)
if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

total_notas = len(df)
valor_total = df["Valor"].sum()
valor_frete = df["Frete_calc"].sum()
perc_frete = percentual(valor_frete, valor_total)
atrasadas = int((df["Status"] == "Atrasado").sum())
vence_hoje = int((df["Status"] == "Vence hoje").sum())
no_prazo = int((df["Status"] == "No prazo").sum())
perc_atraso = percentual(atrasadas, total_notas)
valor_atrasado = df[df["Status"] == "Atrasado"]["Valor"].sum()
valor_vence_hoje = df[df["Status"] == "Vence hoje"]["Valor"].sum()
perc_valor_atrasado = percentual(valor_atrasado, valor_total)
ranking_score = calcular_score_transportadoras(df)
score_medio = ranking_score["score"].mean() if not ranking_score.empty else 0

tam = "18px"
c1, c2, c3, c4 = get_kpi_columns_custom()
with c1:
    card_kpi("Notas", f"{total_notas:,}".replace(",", "."), CORES["cinza"], tam)
with c2:
    card_kpi("Valor das Notas", formatar_moeda_br(valor_total), CORES["azul"], tam)
with c3:
    card_kpi("Valor de Frete", formatar_moeda_br(valor_frete), CORES["ciano"], tam)
with c4:
    card_kpi("% Frete", f"{perc_frete:.2f}%", cor_percentual(perc_frete, 5, 8), tam)

render_spacer()
c5, c6, c7, c8 = st.columns(4)
with c5:
    card_kpi("🔴 Atrasadas", str(atrasadas), CORES["vermelho"], tam)
with c6:
    card_kpi("🟡 Vence hoje", str(vence_hoje), CORES["amarelo"], tam)
with c7:
    card_kpi("🟢 No prazo", str(no_prazo), CORES["verde"], tam)
with c8:
    card_kpi("% Atraso", f"{perc_atraso:.1f}%", cor_percentual(perc_atraso), tam)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
r1, r2, r3 = st.columns([1.6, 1.6, 1])
with r1:
    card_kpi("🚨 Valor em atraso", formatar_moeda_br(valor_atrasado), CORES["vermelho"], tam)
with r2:
    card_kpi("🟡 Valor vence hoje", formatar_moeda_br(valor_vence_hoje), CORES["amarelo"], tam)
with r3:
    card_kpi("% valor em risco", f"{perc_valor_atrasado:.1f}%", cor_percentual(perc_valor_atrasado), tam)

render_section_header("🎯 Metas e SLA")
m1, m2, m3 = st.columns(3)
with m1:
    card_kpi("Meta % Atraso", f"≤ {METAS['perc_atraso']:.1f}%", cor_percentual(perc_atraso), tam)
with m2:
    card_kpi("Meta % Frete", f"≤ {METAS['perc_frete']:.1f}%", cor_percentual(perc_frete, 5, 8), tam)
with m3:
    perc_dentro_prazo = (no_prazo / total_notas * 100) if total_notas > 0 else 0
    cor_sla = CORES["verde"] if perc_dentro_prazo >= 94 else CORES["amarelo"] if perc_dentro_prazo >= 90 else CORES["vermelho"]
    card_kpi("% NFs dentro do prazo", f"{perc_dentro_prazo:.1f}%", cor_sla, tam)

render_section_header("🚨 Alertas automáticos")

if perc_atraso <= 6:
    st.success("✅ Operação dentro do esperado")

elif perc_atraso <= 10:
    st.warning("⚠️ Atenção: atrasos recorrentes")

else:
    st.error("🚨 Atrasos graves — atuar urgente")

render_section_header("🏆 Onde agir agora")
st.caption(
    "Score de eficiência das transportadoras: 🟢 Excelente (>=95), "
    "🟡 Atenção (89 a 94,9), 🔴 Crítica (<89)."
)

ranking_problemas = ranking_score.sort_values(["score", "valor_risco"], ascending=[True, False]).head(5).copy()
ranking_problemas["valor_risco"] = ranking_problemas["valor_risco"].apply(formatar_moeda_br)
ranking_problemas["perc_frete"] = ranking_problemas["perc_frete"].map(lambda x: f"{x:.2f}%")
ranking_problemas["score"] = ranking_problemas["score"].map(lambda x: f"{x:.1f}%")

ranking_problemas["classificacao"] = ranking_problemas["classificacao"].map(
    lambda x: "🟢 Excelente" if x == "Excelente" else ("🟡 Atenção" if x == "Atenção" else "🔴 Crítica")
)

st.dataframe(
    ranking_problemas[["Transportadora", "qtd_notas", "valor_risco", "perc_frete", "score", "classificacao"]], 
    use_container_width=True, 
    hide_index=True)

render_section_header("🧠 Insights automáticos")
for insight in gerar_insights_transportadoras(ranking_score):
    st.info(insight)
)

render_section_header("Visões gráficas")
g1, g2 = st.columns(2)
with g1:
    status_df = pd.DataFrame({"Status": ["Atrasado", "Vence hoje", "No prazo"], "Quantidade": [atrasadas, vence_hoje, no_prazo]})
    fig_status = px.bar(status_df, x="Status", y="Quantidade", title="Distribuição por Status")
    st.plotly_chart(fig_status, use_container_width=True)
with g2:
    financeiro_df = pd.DataFrame({"Indicador": ["Valor das Notas", "Valor de Frete", "Valor em atraso"], "Valor": [valor_total, valor_frete, valor_atrasado]})
    fig_fin = px.bar(financeiro_df, x="Indicador", y="Valor", title="Notas vs Frete vs Risco")
    st.plotly_chart(fig_fin, use_container_width=True)

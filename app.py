
import streamlit as st
from utils.load_data import load_data
from utils.ui import card_kpi, CORES, aplicar_estilo_global, cor_percentual, render_sidebar_brand
from utils.business import preparar_base_dashboard, formatar_moeda_br, percentual, calcular_score_transportadoras, gerar_alertas_executivos, gerar_insights_transportadoras

st.set_page_config(page_title="Dashboard de Notas Fiscais", layout="wide")
aplicar_estilo_global()
render_sidebar_brand()

st.markdown(
    """
    <div style='text-align: center; margin-top: 10px; margin-bottom: 5px;'>
        <img src='https://raw.githubusercontent.com/abecker-83-beep/dashboard-notas/main/logo.png' width='180'>
    </div>
    <hr style='margin-top: 5px; margin-bottom: 15px;'>
    """,
    unsafe_allow_html=True
)

st.title("📊 Dashboard de Notas Fiscais | SUMMIT")
st.caption("Visão inicial do painel com navegação executiva e desempenho por transportadora.")

df_raw = load_data()
df, _, _ = preparar_base_dashboard(df_raw)

total = len(df)
valor_total = df["Valor"].sum()
valor_frete = df["Frete_calc"].sum()
atrasadas = int((df["Status"] == "Atrasado").sum())
perc_atraso = percentual(atrasadas, total)
perc_frete = percentual(valor_frete, valor_total)
valor_atrasado = df.loc[df["Status"] == "Atrasado", "Valor"].sum()
perc_valor_risco = percentual(valor_atrasado, valor_total)

k1, k2, k3, k4 = st.columns([1, 1.8, 1, 1])
with k1:
    card_kpi("Notas", f"{total:,}".replace(",", "."), CORES["cinza"])
with k2:
    card_kpi("Valor das Notas", formatar_moeda_br(valor_total), CORES["azul"])
with k3:
    card_kpi("% Atraso", f"{perc_atraso:.1f}%", cor_percentual(perc_atraso))
with k4:
    card_kpi("% Frete", f"{perc_frete:.2f}%", cor_percentual(perc_frete, 5, 8))

st.divider()

st.subheader("📌 Navegação")
n1, n2, n3, n4 = st.columns(4)
with n1:
    st.page_link("pages/1_Resumo.py", label="📊 Resumo")
with n2:
    st.page_link("pages/2_Mapa.py", label="🗺️ Mapa")
with n3:
    st.page_link("pages/3_Transportadoras.py", label="🚚 Transportadoras")
with n4:
    st.page_link("pages/4_Consulta.py", label="🔎 Consulta")

st.divider()

st.subheader("🚨 Alertas")
alertas = gerar_alertas_executivos(valor_total, valor_frete, total, atrasadas, perc_frete, perc_atraso, perc_valor_risco)
if not alertas:
    st.success("✅ Operação dentro do esperado")
else:
    for alerta in alertas:
        st.warning(alerta)

st.divider()

st.subheader("🚚 Visão por transportadora")
ranking = calcular_score_transportadoras(df).sort_values(["score", "valor_risco"], ascending=[True, False]).copy()
ranking["valor_notas_fmt"] = ranking["valor_notas"].apply(formatar_moeda_br)
ranking["valor_frete_fmt"] = ranking["valor_frete"].apply(formatar_moeda_br)
ranking["valor_risco_fmt"] = ranking["valor_risco"].apply(formatar_moeda_br)
ranking["perc_frete_fmt"] = ranking["perc_frete"].map(lambda x: f"{x:.2f}%")
ranking["performance_fmt"] = ((ranking["no_prazo"] / ranking["qtd_notas"]) * 100).fillna(0).map(lambda x: f"{x:.0f}%")
ranking["score_fmt"] = ranking["score"].map(lambda x: f"{x:.1f}")

tabela_app = ranking[["Transportadora", "qtd_notas", "valor_notas_fmt", "valor_frete_fmt", "perc_frete_fmt", "valor_risco_fmt", "performance_fmt", "score_fmt", "classificacao"]].copy()
tabela_app.columns = ["Transportadora", "Qtd. notas", "Valor notas", "Valor frete", "% Frete", "Valor risco", "Performance %", "Score", "Status executivo"]
st.dataframe(tabela_app, use_container_width=True, hide_index=True)

st.divider()

st.subheader("🧠 Insights automáticos")
for insight in gerar_insights_transportadoras(ranking):
    st.info(insight)

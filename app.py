import streamlit as st
import pandas as pd
from utils.load_data import load_data
from utils.ui import card_kpi, CORES, aplicar_estilo_global, cor_percentual

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Dashboard de Notas", layout="wide")

aplicar_estilo_global()

# =========================
# FUNÇÕES
# =========================
def formatar_moeda_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# =========================
# DADOS
# =========================
df = load_data()
df.columns = df.columns.str.strip()

# tratamento básico
df["Dias"] = pd.to_numeric(df.get("Dias", 0), errors="coerce").fillna(0)

df["Valor"] = (
    df.get("Valor", 0)
    .astype(str)
    .str.replace("R$", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)
df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

# frete (se existir)
col_frete = None
for col in ["Frete", "Valor Frete", "Frete Total"]:
    if col in df.columns:
        col_frete = col
        break

if col_frete:
    df["Frete_calc"] = (
        df[col_frete]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["Frete_calc"] = pd.to_numeric(df["Frete_calc"], errors="coerce").fillna(0)
else:
    df["Frete_calc"] = 0

# status
df["Status"] = df["Dias"].apply(
    lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")
)

# =========================
# HEADER
# =========================
st.title("📊 Dashboard de Notas Fiscais")
st.caption("Visão geral operacional, financeira e logística")

# =========================
# KPIs PRINCIPAIS
# =========================
total = len(df)
valor_total = df["Valor"].sum()
valor_frete = df["Frete_calc"].sum()

atrasadas = int((df["Status"] == "Atrasado").sum())
perc_atraso = (atrasadas / total * 100) if total > 0 else 0

perc_frete = (valor_frete / valor_total * 100) if valor_total > 0 else 0

k1, k2, k3, k4 = st.columns(4)

with k1:
    card_kpi("Notas", f"{total:,}".replace(",", "."), CORES["cinza"])

with k2:
    card_kpi("Valor das Notas", formatar_moeda_br(valor_total), CORES["azul"])

with k3:
    card_kpi("% Atraso", f"{perc_atraso:.1f}%", cor_percentual(perc_atraso))

with k4:
    card_kpi("% Frete", f"{perc_frete:.2f}%", cor_percentual(perc_frete, 5, 8))

st.divider()

# =========================
# NAVEGAÇÃO (cards clicáveis)
# =========================
st.subheader("📌 Navegação")

nav1, nav2, nav3, nav4 = st.columns(4)

def botao_nav(titulo, descricao):
    st.markdown(
        f"""
        <div style="
            border:1px solid #e5e7eb;
            border-radius:12px;
            padding:16px;
            background:#ffffff;
            cursor:pointer;
        ">
            <b>{titulo}</b><br>
            <span style='color:#6b7280'>{descricao}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

with nav1:
    botao_nav("📊 Resumo", "Indicadores completos")

with nav2:
    botao_nav("🗺️ Mapa", "Análise geográfica")

with nav3:
    botao_nav("🚚 Transportadoras", "Performance logística")

with nav4:
    botao_nav("🔎 Consulta", "Busca detalhada")

st.divider()

# =========================
# ALERTAS
# =========================
st.subheader("🚨 Alertas")

if perc_atraso > 20:
    st.error(f"Alto índice de atraso: {perc_atraso:.1f}%")

if perc_frete > 8:
    st.warning(f"Frete elevado: {perc_frete:.2f}%")

if perc_atraso <= 20 and perc_frete <= 8:
    st.success("Operação dentro do esperado")

# =========================
# ONDE AGIR (TOP)
# =========================
st.subheader("🎯 Onde agir agora")

top = (
    df[df["Status"] == "Atrasado"]
    .groupby("Transportadora")
    .agg(qtd=("NF", "count"), valor=("Valor", "sum"))
    .reset_index()
    .sort_values("valor", ascending=False)
    .head(5)
)

if top.empty:
    st.success("Sem atrasos relevantes")
else:
    top["valor"] = top["valor"].apply(formatar_moeda_br)
    st.dataframe(top, use_container_width=True, hide_index=True)

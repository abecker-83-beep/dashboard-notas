import pandas as pd
import streamlit as st

from utils.load_data import load_data
from utils.ui import card_kpi, CORES, aplicar_estilo_global, cor_percentual


# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Dashboard de Notas Fiscais", layout="wide")
aplicar_estilo_global()

st.title("📊 Dashboard de Notas Fiscais")
st.caption("Visão inicial do painel com navegação executiva e desempenho por transportadora.")


# =========================
# FUNÇÕES
# =========================
def formatar_moeda_br(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def detectar_coluna_frete(df):
    candidatos = [
        "Frete",
        "FRETE",
        "Valor Frete",
        "VALOR FRETE",
        "Vlr Frete",
        "VLR FRETE",
        "Frete Total",
        "Custo Frete",
        "Valor do Frete",
    ]
    for col in candidatos:
        if col in df.columns:
            return col
    return None


def converter_moeda_ou_numero(serie):
    return pd.to_numeric(
        serie.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip(),
        errors="coerce",
    ).fillna(0)


def metricas_transportadora(df_base):
    base = df_base.copy()

    agrupado = (
        base.groupby("Transportadora", dropna=False)
        .agg(
            qtd_notas=("NF", "count"),
            valor_notas=("Valor", "sum"),
            valor_frete=("Frete_calc", "sum"),
            atrasadas=("Status", lambda x: (x == "Atrasado").sum()),
            vence_hoje=("Status", lambda x: (x == "Vence hoje").sum()),
            no_prazo=("Status", lambda x: (x == "No prazo").sum()),
        )
        .reset_index()
    )

    agrupado["performance"] = (
        (agrupado["no_prazo"] / agrupado["qtd_notas"]) * 100
    ).fillna(0)

    return agrupado


# =========================
# DADOS
# =========================
df = load_data().copy()
df.columns = df.columns.str.strip()

if "NF" not in df.columns:
    df["NF"] = ""

if "Transportadora" not in df.columns:
    df["Transportadora"] = "NÃO INFORMADA"

if "Dias" not in df.columns:
    df["Dias"] = 0
df["Dias"] = pd.to_numeric(df["Dias"], errors="coerce").fillna(0)

if "Valor" not in df.columns:
    df["Valor"] = 0
df["Valor"] = converter_moeda_ou_numero(df["Valor"])

col_frete = detectar_coluna_frete(df)
if col_frete:
    df["Frete_calc"] = converter_moeda_ou_numero(df[col_frete])
else:
    df["Frete_calc"] = 0

df["Transportadora"] = df["Transportadora"].astype(str).fillna("").str.strip().str.upper()

df["Status"] = df["Dias"].apply(
    lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")
)


# =========================
# KPIs
# =========================
total = len(df)
valor_total = df["Valor"].sum()
valor_frete = df["Frete_calc"].sum()
atrasadas = int((df["Status"] == "Atrasado").sum())
perc_atraso = (atrasadas / total * 100) if total > 0 else 0
perc_frete = (valor_frete / valor_total * 100) if valor_total > 0 else 0

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


# =========================
# NAVEGAÇÃO
# =========================
st.subheader("📌 Navegação")

n1, n2, n3, n4 = st.columns(4)

with n1:
    st.page_link("pages/1_Resumo.py", label="📊 Resumo", help="Indicadores executivos completos")

with n2:
    st.page_link("pages/2_Mapa.py", label="🗺️ Mapa", help="Análise geográfica das NFs")

with n3:
    st.page_link("pages/3_Transportadoras.py", label="🚚 Transportadoras", help="Performance logística por transportadora")

with n4:
    st.page_link("pages/4_Consulta.py", label="🔎 Consulta", help="Busca detalhada de notas")

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

st.divider()


# =========================
# TABELA DE TRANSPORTADORAS
# =========================
st.subheader("🚚 Visão por transportadora")

resumo_transp = metricas_transportadora(df)

if resumo_transp.empty:
    st.info("Sem dados para exibir.")
else:
    resumo_transp = resumo_transp.sort_values(
        ["performance", "valor_notas"],
        ascending=[False, False]
    ).copy()

    resumo_transp["valor_notas_fmt"] = resumo_transp["valor_notas"].apply(formatar_moeda_br)
    resumo_transp["valor_frete_fmt"] = resumo_transp["valor_frete"].apply(formatar_moeda_br)
    resumo_transp["performance_fmt"] = resumo_transp["performance"].map(lambda x: f"{x:.0f} %")

    tabela_app = resumo_transp[
        [
            "Transportadora",
            "qtd_notas",
            "valor_notas_fmt",
            "valor_frete_fmt",
            "atrasadas",
            "vence_hoje",
            "no_prazo",
            "performance_fmt",
        ]
    ].copy()

    tabela_app.columns = [
        "Transportadora",
        "Qtd. notas",
        "Valor notas",
        "Valor frete",
        "Atrasadas",
        "Vence hoje",
        "No prazo",
        "Performance %",
    ]

    st.dataframe(
        tabela_app,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Transportadora": st.column_config.TextColumn("Transportadora", width="medium"),
            "Qtd. notas": st.column_config.NumberColumn("Qtd. notas", format="%d"),
            "Valor notas": st.column_config.TextColumn("Valor notas", width="medium"),
            "Valor frete": st.column_config.TextColumn("Valor frete", width="medium"),
            "Atrasadas": st.column_config.NumberColumn("Atrasadas", format="%d"),
            "Vence hoje": st.column_config.NumberColumn("Vence hoje", format="%d"),
            "No prazo": st.column_config.NumberColumn("No prazo", format="%d"),
            "Performance %": st.column_config.TextColumn("Performance %", width="small"),
        },
    )

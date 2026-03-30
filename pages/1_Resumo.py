import streamlit as st
import pandas as pd
from utils.load_data import load_data


# =========================
# FUNCOES
# =========================
def formatar_moeda_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def card_kpi(titulo, valor, cor_fundo="#f8f9fa", cor_texto="#1f2937", tamanho="24px"):
    st.markdown(
        f"""
        <div style="
            background-color: {cor_fundo};
            padding: 14px 16px;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            min-height: 95px;
        ">
            <div style="
                font-size: 13px;
                color: #6b7280;
                margin-bottom: 6px;
                font-weight: 600;
                white-space: nowrap;
            ">
                {titulo}
            </div>
            <div style="
                font-size: {tamanho};
                font-weight: 700;
                color: {cor_texto};
                line-height: 1.1;
                white-space: nowrap;
            ">
                {valor}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# PAGINA
# =========================
st.title("📊 Resumo")

df = load_data()
df.columns = df.columns.str.strip()

# =========================
# TRATAMENTOS
# =========================
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

df["Status"] = df["Dias"].apply(
    lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")
)

# =========================
# KPIS
# =========================
total_notas = len(df)
valor_total = df["Valor"].sum()
atrasadas = int((df["Status"] == "Atrasado").sum())
vence_hoje = int((df["Status"] == "Vence hoje").sum())
no_prazo = int((df["Status"] == "No prazo").sum())

col1, col2, col3, col4, col5 = st.columns([1, 1.6, 1, 1, 1])

with col1:
    card_kpi("📦 Total NFs", f"{total_notas:,}".replace(",", "."), tamanho="22px")

with col2:
    card_kpi(
        "💰 Valor Total",
        formatar_moeda_br(valor_total),
        cor_fundo="#eef6ff",
        cor_texto="#0f172a",
        tamanho="18px"
    )

with col3:
    card_kpi(
        "🔴 Atrasadas",
        str(atrasadas),
        cor_fundo="#fff1f2",
        cor_texto="#b91c1c",
        tamanho="22px"
    )

with col4:
    card_kpi(
        "🟡 Vence hoje",
        str(vence_hoje),
        cor_fundo="#fffbeb",
        cor_texto="#b45309",
        tamanho="22px"
    )

with col5:
    card_kpi(
        "🟢 No prazo",
        str(no_prazo),
        cor_fundo="#f0fdf4",
        cor_texto="#166534",
        tamanho="22px"
    )

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# =========================
# DADOS
# =========================
st.subheader("📦 Dados carregados")
st.dataframe(df, use_container_width=True, hide_index=True)

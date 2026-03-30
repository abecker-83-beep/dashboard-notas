import streamlit as st
import pandas as pd
from utils.load_data import load_data


# =========================
# FUNCOES
# =========================
def formatar_moeda_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def card_kpi(titulo, valor, cor_fundo="#f8f9fa", cor_texto="#1f2937", tamanho="34px"):
    st.markdown(
        f"""
        <div style="
            background-color: {cor_fundo};
            padding: 16px 18px;
            border-radius: 14px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            min-height: 110px;
        ">
            <div style="
                font-size: 14px;
                color: #6b7280;
                margin-bottom: 8px;
                font-weight: 600;
            ">
                {titulo}
            </div>
            <div style="
                font-size: {tamanho};
                font-weight: 700;
                color: {cor_texto};
                line-height: 1.1;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
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

col1, col2, col3, col4, col5 = st.columns([1, 1.4, 1, 1, 1])

def card_kpi(titulo, valor, cor_fundo="#f8f9fa", cor_texto="#1f2937", tamanho="26px"):
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
                white-space: nowrap;   /* 🔥 impede quebra (Vence hoje) */
            ">
                {titulo}
            </div>
            <div style="
                font-size: {tamanho};
                font-weight: 700;
                color: {cor_texto};
                line-height: 1.1;
                white-space: nowrap;   /* 🔥 mantém valor inteiro */
            ">
                {valor}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# =========================
# DADOS
# =========================
st.subheader("📦 Dados carregados")
st.dataframe(df, use_container_width=True, hide_index=True)

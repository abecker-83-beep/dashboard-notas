import streamlit as st
import pandas as pd
import plotly.express as px
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
st.title("🚚 Transportadoras")

df = load_data()
df.columns = df.columns.str.strip()

# =========================
# TRATAMENTOS
# =========================
for col in ["Transportadora", "Cidade", "UF", "Representante", "Ocorrência", "Cliente"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.upper()

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

df["Status"] = df["Dias"].apply(
    lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")
)

# =========================
# FILTROS
# =========================
st.subheader("Filtros")

transportadoras = sorted([x for x in df["Transportadora"].dropna().unique() if x])

selecionadas = st.multiselect(
    "Transportadora",
    transportadoras,
    default=[],
    placeholder="Selecione uma ou mais transportadoras"
)

if selecionadas:
    df_filtrado = df[df["Transportadora"].isin(selecionadas)].copy()
else:
    df_filtrado = df.copy()
# =========================
# KPIS
# =========================
total_transportadoras = df_filtrado["Transportadora"].nunique()
total_nfs = len(df_filtrado)
valor_total = df_filtrado["Valor"].sum()
atrasadas = int((df_filtrado["Status"] == "Atrasado").sum())
clientes = df_filtrado["Cliente"].nunique() if "Cliente" in df_filtrado.columns else 0

col1, col2, col3, col4, col5 = st.columns([1, 1, 1.5, 1, 1])

with col1:
    card_kpi("🚚 Transp.", str(total_transportadoras), tamanho="22px")

with col2:
    card_kpi("📦 Total NFs", f"{total_nfs:,}".replace(",", "."), tamanho="22px")

with col3:
    card_kpi(
        "💰 Valor Total",
        formatar_moeda_br(valor_total),
        cor_fundo="#eef6ff",
        cor_texto="#0f172a",
        tamanho="18px"
    )

with col4:
    card_kpi(
        "🔴 Atrasadas",
        str(atrasadas),
        cor_fundo="#fff1f2",
        cor_texto="#b91c1c",
        tamanho="22px"
    )

with col5:
    card_kpi(
        "🏢 Clientes",
        str(clientes),
        cor_fundo="#f0fdf4",
        cor_texto="#166534",
        tamanho="22px"
    )

with col6:
    card_kpi(
        "⚠️ % Atraso",
        f"{perc_atraso:.1f}%",
        cor_fundo="#fff7ed",
        cor_texto="#c2410c",
        tamanho="22px"
    )

top_transp = nf_por_transp.iloc[0]["Transportadora"] if not nf_por_transp.empty else "-"
top_qtd = nf_por_transp.iloc[0]["Qtd NFs"] if not nf_por_transp.empty else 0

st.info(f"🏆 Top transportadora: **{top_transp}** ({top_qtd} NFs)")

st.markdown("<br>", unsafe_allow_html=True)

# =========================
# AGRUPAMENTOS
# =========================
nf_por_transp = (
    df_filtrado.groupby("Transportadora")
    .size()
    .reset_index(name="Qtd NFs")
    .sort_values("Qtd NFs", ascending=False)
)

valor_por_transp = (
    df_filtrado.groupby("Transportadora")["Valor"]
    .sum()
    .reset_index()
    .sort_values("Valor", ascending=False)
)

atraso_por_transp = (
    df_filtrado[df_filtrado["Status"] == "Atrasado"]
    .groupby("Transportadora")
    .size()
    .reset_index(name="Qtd Atrasadas")
    .sort_values("Qtd Atrasadas", ascending=False)
)

# =========================
# GRAFICOS
# =========================
colg1, colg2 = st.columns(2)

with colg1:
    fig_nf = px.bar(
        nf_por_transp,
        x="Transportadora",
        y="Qtd NFs",
        title="Quantidade de NFs por Transportadora",
        text_auto=True
    )
    fig_nf.update_layout(xaxis_title="", yaxis_title="Qtd NFs")
    st.plotly_chart(fig_nf, use_container_width=True)

with colg2:
    fig_valor = px.bar(
        valor_por_transp,
        x="Transportadora",
        y="Valor",
        title="Valor Total por Transportadora",
        text_auto=True
    )
    fig_valor.update_layout(xaxis_title="", yaxis_title="Valor")
    st.plotly_chart(fig_valor, use_container_width=True)

st.divider()

fig_atraso = px.bar(
    atraso_por_transp,
    x="Transportadora",
    y="Qtd Atrasadas",
    title="NFs Atrasadas por Transportadora",
    text_auto=True,
    color="Qtd Atrasadas",
    color_continuous_scale="reds"
)
fig_atraso.update_layout(xaxis_title="", yaxis_title="Qtd Atrasadas")
st.plotly_chart(fig_atraso, use_container_width=True)

# =========================
# RANKINGS AUXILIARES
# =========================
st.subheader("Rankings auxiliares")

colr1, colr2 = st.columns(2)

with colr1:
    top_cidades = (
        df_filtrado.groupby("Cidade")
        .size()
        .reset_index(name="Qtd NFs")
        .sort_values("Qtd NFs", ascending=False)
        .head(10)
    )
    st.markdown("**Top 10 cidades**")
    st.dataframe(top_cidades, use_container_width=True, hide_index=True)

with colr2:
    top_ocorrencias = (
        df_filtrado.groupby("Ocorrência")
        .size()
        .reset_index(name="Qtd NFs")
        .sort_values("Qtd NFs", ascending=False)
        .head(10)
    )
    st.markdown("**Top 10 ocorrências**")
    st.dataframe(top_ocorrencias, use_container_width=True, hide_index=True)

# =========================
# TABELA DETALHADA
# =========================
st.subheader("Tabela detalhada")

colunas_exibir = [
    "NF", "Cliente", "Cidade", "UF", "Transportadora",
    "Representante", "Ocorrência", "Dias", "Status",
    "Valor", "Vol", "Emissão", "Prev. Entrega"
]

colunas_exibir = [c for c in colunas_exibir if c in df_filtrado.columns]

tabela = df_filtrado[colunas_exibir].copy()

if "Dias" in tabela.columns:
    tabela = tabela.sort_values(by="Dias", ascending=False)

for col in ["Emissão", "Prev. Entrega"]:
    if col in tabela.columns:
        tabela[col] = pd.to_datetime(tabela[col], errors="coerce", dayfirst=True).dt.strftime("%d/%m/%Y")

if "Valor" in tabela.columns:
    tabela["Valor"] = tabela["Valor"].apply(formatar_moeda_br)

st.dataframe(tabela, use_container_width=True, hide_index=True)

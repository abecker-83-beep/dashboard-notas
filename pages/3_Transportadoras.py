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


def cor_status(val):
    if val == "Atrasado":
        return "background-color: #fff1f2; color: #b91c1c;"
    elif val == "Vence hoje":
        return "background-color: #fffbeb; color: #b45309;"
    elif val == "No prazo":
        return "background-color: #f0fdf4; color: #166534;"
    return ""


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

if "Dias" in df.columns:
    df["Dias"] = pd.to_numeric(df["Dias"], errors="coerce").fillna(0)

if "Valor" in df.columns:
    df["Valor"] = (
        df["Valor"]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

if "Vol" in df.columns:
    df["Vol"] = pd.to_numeric(df["Vol"], errors="coerce").fillna(0)

df["Status"] = df["Dias"].apply(
    lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")
)

# =========================
# FILTROS
# =========================
st.subheader("Filtros")

colf1, colf2, colf3, colf4 = st.columns(4)

with colf1:
    transportadoras = sorted([x for x in df["Transportadora"].dropna().unique() if x])
    selecionadas = st.multiselect(
        "Transportadora",
        transportadoras,
        default=[],
        placeholder="Selecione uma ou mais transportadoras"
    )

with colf2:
    status_sel = st.multiselect(
        "Status",
        ["Atrasado", "Vence hoje", "No prazo"],
        default=[],
        placeholder="Selecione um ou mais status"
    )

base_rep = df.copy()
if selecionadas:
    base_rep = base_rep[base_rep["Transportadora"].isin(selecionadas)]
if status_sel:
    base_rep = base_rep[base_rep["Status"].isin(status_sel)]

with colf3:
    representantes = sorted([x for x in base_rep["Representante"].dropna().unique() if x])
    representante_sel = st.multiselect(
        "Representante",
        representantes,
        default=[],
        placeholder="Selecione um ou mais representantes"
    )

base_uf = base_rep.copy()
if representante_sel:
    base_uf = base_uf[base_uf["Representante"].isin(representante_sel)]

with colf4:
    ufs = sorted([x for x in base_uf["UF"].dropna().unique() if x])
    uf_sel = st.multiselect(
        "UF",
        ufs,
        default=[],
        placeholder="Selecione uma ou mais UFs"
    )

# aplica filtros finais
df_filtrado = df.copy()

if selecionadas:
    df_filtrado = df_filtrado[df_filtrado["Transportadora"].isin(selecionadas)]

if status_sel:
    df_filtrado = df_filtrado[df_filtrado["Status"].isin(status_sel)]

if representante_sel:
    df_filtrado = df_filtrado[df_filtrado["Representante"].isin(representante_sel)]

if uf_sel:
    df_filtrado = df_filtrado[df_filtrado["UF"].isin(uf_sel)]

# =========================
# KPIS
# =========================
total_transportadoras = df_filtrado["Transportadora"].nunique() if "Transportadora" in df_filtrado.columns else 0
total_nfs = len(df_filtrado)
valor_total = df_filtrado["Valor"].sum() if "Valor" in df_filtrado.columns else 0
atrasadas = int((df_filtrado["Status"] == "Atrasado").sum())
vence_hoje = int((df_filtrado["Status"] == "Vence hoje").sum())
clientes = df_filtrado["Cliente"].nunique() if "Cliente" in df_filtrado.columns else 0
perc_atraso = (atrasadas / total_nfs * 100) if total_nfs > 0 else 0

col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

with col1:
    card_kpi("🚚 Transp.", str(total_transportadoras), tamanho="22px")

with col2:
    card_kpi("📦 Total NFs", f"{total_nfs:,}".replace(",", "."), tamanho="22px")

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
        "⚠️ % Atraso",
        f"{perc_atraso:.1f}%",
        cor_fundo="#fff7ed",
        cor_texto="#c2410c",
        tamanho="22px"
    )

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("**💰 Valor Total das Notas**")
st.markdown(
    f"""
    <div style="
        font-size: 34px;
        font-weight: 700;
        color: #0f172a;
        background-color: #eef6ff;
        border: 1px solid #dbeafe;
        border-radius: 12px;
        padding: 16px 18px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        width: fit-content;
        min-width: 320px;
    ">
        {formatar_moeda_br(valor_total)}
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# =========================
# DESTAQUE PERFORMANCE
# =========================
performance = (
    df_filtrado
    .groupby("Transportadora")
    .agg(
        total_nfs=("NF", "count"),
        atrasadas=("Status", lambda x: (x == "Atrasado").sum())
    )
    .reset_index()
)

performance["perc_atraso"] = (
    performance["atrasadas"] / performance["total_nfs"] * 100
)

# evita distorção (mínimo de volume)
performance = performance[performance["total_nfs"] >= 10]

if not performance.empty:

    melhor = performance.sort_values("perc_atraso").iloc[0]
    pior = performance.sort_values("perc_atraso", ascending=False).iloc[0]

    col_perf1, col_perf2 = st.columns(2)

    with col_perf1:
        st.success(
            f"🏆 Melhor performance\n\n"
            f"**{melhor['Transportadora']}**\n\n"
            f"{melhor['perc_atraso']:.1f}% atraso • {melhor['total_nfs']} NFs"
        )

    with col_perf2:
        st.error(
            f"⚠️ Pior performance\n\n"
            f"**{pior['Transportadora']}**\n\n"
            f"{pior['perc_atraso']:.1f}% atraso • {pior['total_nfs']} NFs"
        )

else:
    st.info("Sem dados suficientes para análise de performance")

# =========================
# AGRUPAMENTOS
# =========================
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

if "Dias" in tabela.columns and "Valor" in tabela.columns:
    tabela = tabela.sort_values(by=["Dias", "Valor"], ascending=[False, False])
elif "Dias" in tabela.columns:
    tabela = tabela.sort_values(by="Dias", ascending=False)

for col in ["Emissão", "Prev. Entrega"]:
    if col in tabela.columns:
        tabela[col] = pd.to_datetime(tabela[col], errors="coerce", dayfirst=True).dt.strftime("%d/%m/%Y")

if "Valor" in tabela.columns:
    tabela["Valor"] = tabela["Valor"].apply(formatar_moeda_br)

st.dataframe(
    tabela.style.applymap(cor_status, subset=["Status"]),
    use_container_width=True,
    hide_index=True
)

# =========================
# EXPORTACAO
# =========================
csv = tabela.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="📥 Baixar análise em CSV",
    data=csv,
    file_name="transportadoras.csv",
    mime="text/csv"
)

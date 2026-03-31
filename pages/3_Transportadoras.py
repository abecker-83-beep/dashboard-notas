from utils.ui import card_kpi, CORES, aplicar_estilo_global, cor_percentual
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.load_data import load_data


def formatar_moeda_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def detectar_coluna_frete(df):
    candidatos = [
        "Frete", "FRETE", "Valor Frete", "VALOR FRETE", "Vlr Frete",
        "VLR FRETE", "Frete Total", "Custo Frete", "Valor do Frete",
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
        errors="coerce"
    ).fillna(0)


def cor_status(val):
    if val == "Atrasado":
        return "background-color: #FEF2F2; color: #991B1B;"
    elif val == "Vence hoje":
        return "background-color: #FFFBEB; color: #92400E;"
    elif val == "No prazo":
        return "background-color: #F0FDF4; color: #166534;"
    return ""


st.title("🚚 Transportadoras")
st.caption("Análise operacional e financeira por transportadora.")
aplicar_estilo_global()

df = load_data()
df.columns = df.columns.str.strip()

for col in ["Transportadora", "Cidade", "UF", "Representante", "Ocorrência", "Cliente"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.upper()

if "Dias" in df.columns:
    df["Dias"] = pd.to_numeric(df["Dias"], errors="coerce").fillna(0)
else:
    df["Dias"] = 0

if "Valor" in df.columns:
    df["Valor"] = converter_moeda_ou_numero(df["Valor"])
else:
    df["Valor"] = 0

if "Vol" in df.columns:
    df["Vol"] = pd.to_numeric(df["Vol"], errors="coerce").fillna(0)
else:
    df["Vol"] = 0

col_frete = detectar_coluna_frete(df)
if col_frete:
    df["Frete_calc"] = converter_moeda_ou_numero(df[col_frete])
else:
    df["Frete_calc"] = 0

df["Status"] = df["Dias"].apply(
    lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")
)

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

df_filtrado = df.copy()
if selecionadas:
    df_filtrado = df_filtrado[df_filtrado["Transportadora"].isin(selecionadas)]
if status_sel:
    df_filtrado = df_filtrado[df_filtrado["Status"].isin(status_sel)]
if representante_sel:
    df_filtrado = df_filtrado[df_filtrado["Representante"].isin(representante_sel)]
if uf_sel:
    df_filtrado = df_filtrado[df_filtrado["UF"].isin(uf_sel)]

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado com os filtros selecionados.")
    st.stop()

total_transportadoras = df_filtrado["Transportadora"].nunique() if "Transportadora" in df_filtrado.columns else 0
total_nfs = len(df_filtrado)
valor_total = df_filtrado["Valor"].sum() if "Valor" in df_filtrado.columns else 0
valor_frete = df_filtrado["Frete_calc"].sum() if "Frete_calc" in df_filtrado.columns else 0
atrasadas = int((df_filtrado["Status"] == "Atrasado").sum())
vence_hoje = int((df_filtrado["Status"] == "Vence hoje").sum())
no_prazo = int((df_filtrado["Status"] == "No prazo").sum())
perc_atraso = (atrasadas / total_nfs * 100) if total_nfs > 0 else 0
perc_frete = (valor_frete / valor_total * 100) if valor_total > 0 else 0

tam = "18px"

k1, k2, k3, k4, k5 = st.columns([1, 1, 1, 1, 1])
with k1:
    card_kpi("Transportadoras", str(total_transportadoras), CORES["cinza"], tam)
with k2:
    card_kpi("Notas", f"{total_nfs:,}".replace(",", "."), CORES["cinza"], tam)
with k3:
    card_kpi("🔴 Atrasadas", str(atrasadas), CORES["vermelho"], tam)
with k4:
    card_kpi("🟡 Vence hoje", str(vence_hoje), CORES["amarelo"], tam)
with k5:
    card_kpi("% Atraso", f"{perc_atraso:.1f}%", cor_percentual(perc_atraso), tam)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

k6, k7, k8 = st.columns([2.0, 1.6, 1.0])
with k6:
    card_kpi("Valor Total das Notas", formatar_moeda_br(valor_total), CORES["azul"], tam)
with k7:
    card_kpi("Valor de Frete", formatar_moeda_br(valor_frete), CORES["ciano"], tam)
with k8:
    card_kpi("% Frete", f"{perc_frete:.2f}%", cor_percentual(perc_frete, 5, 8), tam)

st.markdown("<br>", unsafe_allow_html=True)

performance = (
    df_filtrado
    .groupby("Transportadora")
    .agg(
        total_nfs=("NF", "count"),
        atrasadas=("Status", lambda x: (x == "Atrasado").sum())
    )
    .reset_index()
)

performance["perc_atraso"] = performance["atrasadas"] / performance["total_nfs"] * 100
performance = performance[performance["total_nfs"] >= 10]

if not performance.empty:
    melhor = performance.sort_values("perc_atraso").iloc[0]
    pior = performance.sort_values("perc_atraso", ascending=False).iloc[0]

    col_perf1, col_perf2 = st.columns(2)

    with col_perf1:
        st.success(
            f"🏆 Melhor performance\n\n"
            f"**{melhor['Transportadora']}**\n\n"
            f"{melhor['perc_atraso']:.1f}% atraso • {int(melhor['total_nfs'])} NFs"
        )

    with col_perf2:
        st.error(
            f"⚠️ Pior performance\n\n"
            f"**{pior['Transportadora']}**\n\n"
            f"{pior['perc_atraso']:.1f}% atraso • {int(pior['total_nfs'])} NFs"
        )
else:
    st.info("Sem dados suficientes para análise de performance")

st.markdown("<br>", unsafe_allow_html=True)

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

if atraso_por_transp.empty:
    st.info("Nenhuma NF atrasada no filtro atual.")
else:
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
    if "Ocorrência" in df_filtrado.columns:
        top_ocorrencias = (
            df_filtrado.groupby("Ocorrência")
            .size()
            .reset_index(name="Qtd NFs")
            .sort_values("Qtd NFs", ascending=False)
            .head(10)
        )
        st.markdown("**Top 10 ocorrências**")
        st.dataframe(top_ocorrencias, use_container_width=True, hide_index=True)

st.subheader("Tabela detalhada")

colunas_exibir = [
    "NF", "Cliente", "Cidade", "UF", "Transportadora",
    "Representante", "Ocorrência", "Dias", "Status",
    "Valor", "Vol", "Emissão", "Prev. Entrega"
]
if col_frete:
    colunas_exibir.append(col_frete)

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

if col_frete and col_frete in tabela.columns:
    tabela[col_frete] = converter_moeda_ou_numero(tabela[col_frete]).apply(formatar_moeda_br)

st.dataframe(
    tabela.style.applymap(cor_status, subset=["Status"]),
    use_container_width=True,
    hide_index=True
)

csv = tabela.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="📥 Baixar análise em CSV",
    data=csv,
    file_name="transportadoras.csv",
    mime="text/csv"
)

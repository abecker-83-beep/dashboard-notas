import re
import unicodedata
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

from utils.load_data import load_data


st.title("📊 Resumo")
st.caption("Visão executiva dos indicadores operacionais, financeiros e logísticos.")

st.markdown(
    '''
    <style>
    div[data-testid="metric-container"] {
        overflow: visible !important;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 14px 16px;
        border-radius: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        min-height: 96px;
    }
    div[data-testid="stMetricValue"] {
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: unset !important;
        font-size: 20px !important;
    }
    div[data-testid="stMetricLabel"] {
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: unset !important;
    }
    .metric-red div[data-testid="metric-container"] {
        background: #FEF2F2;
        border: 1px solid #FECACA;
    }
    .metric-yellow div[data-testid="metric-container"] {
        background: #FFFBEB;
        border: 1px solid #FDE68A;
    }
    .metric-green div[data-testid="metric-container"] {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
    }
    .metric-blue div[data-testid="metric-container"] {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
    }
    .metric-gray div[data-testid="metric-container"] {
        background: #F8FAFC;
        border: 1px solid #E5E7EB;
    }
    </style>
    ''',
    unsafe_allow_html=True,
)


def formatar_moeda_br(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def normalizar_texto(valor: str) -> str:
    if pd.isna(valor):
        return ""
    valor = str(valor).strip().upper()
    valor = unicodedata.normalize("NFKD", valor).encode("ASCII", "ignore").decode("ASCII")
    valor = re.sub(r"\s+", " ", valor)
    return valor


def garantir_coluna(df, coluna, valor_padrao=""):
    if coluna not in df.columns:
        df[coluna] = valor_padrao
    return df


def detectar_coluna_data(df):
    candidatos = ["Data", "DATA", "Dt Emissao", "DT EMISSAO", "Dt_Emissao", "Data Emissao", "Emissao", "Data NF", "Data Faturamento"]
    for col in candidatos:
        if col in df.columns:
            return col
    return None


def detectar_coluna_frete(df):
    candidatos = ["Frete", "FRETE", "Valor Frete", "VALOR FRETE", "Vlr Frete", "VLR FRETE", "Frete Total", "Custo Frete", "Valor do Frete"]
    for col in candidatos:
        if col in df.columns:
            return col
    return None


def converter_moeda_ou_numero(serie):
    serie = (
        serie.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    return pd.to_numeric(serie, errors="coerce").fillna(0)


def card_kpi(titulo, valor, cor_fundo="#f8f9fa", cor_texto="#1f2937", tamanho="24px", borda="#e5e7eb"):
    st.markdown(
        f'''
        <div style="
            background: {cor_fundo};
            border: 1px solid {borda};
            border-radius: 16px;
            padding: 16px 18px;
            min-height: 105px;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div style="
                font-size: 13px;
                color: #6b7280;
                font-weight: 600;
                white-space: nowrap;
                overflow: visible;
                text-overflow: unset;
            ">
                {titulo}
            </div>
            <div style="
                font-size: {tamanho};
                font-weight: 700;
                color: {cor_texto};
                line-height: 1.1;
                white-space: nowrap;
                overflow: visible;
                text-overflow: unset;
            ">
                {valor}
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )


@st.cache_data(show_spinner=False)
def carregar_dados():
    df = load_data().copy()
    df.columns = df.columns.str.strip()

    for col in ["NF", "Cliente", "Cidade", "UF", "Representante", "Transportadora", "Status"]:
        df = garantir_coluna(df, col, "")

    df = garantir_coluna(df, "Dias", 0)
    df = garantir_coluna(df, "Valor", 0)
    df = garantir_coluna(df, "Vol", 0)

    col_frete = detectar_coluna_frete(df)
    if col_frete:
        df["Frete_calc"] = converter_moeda_ou_numero(df[col_frete])
    else:
        df["Frete_calc"] = 0

    for col in ["Cliente", "Cidade", "UF", "Representante", "Transportadora"]:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("").apply(normalizar_texto)

    df["NF"] = df["NF"].astype(str).fillna("").str.strip()
    df["Dias"] = pd.to_numeric(df["Dias"], errors="coerce").fillna(0)
    df["Valor"] = converter_moeda_ou_numero(df["Valor"])
    df["Vol"] = pd.to_numeric(df["Vol"], errors="coerce").fillna(0)

    status_vazio = df["Status"].astype(str).str.strip().replace("", np.nan).isna()
    df["Status"] = np.where(
        status_vazio,
        df["Dias"].apply(lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")),
        df["Status"].astype(str).str.strip(),
    )

    col_data = detectar_coluna_data(df)
    if col_data:
        df[col_data] = pd.to_datetime(df[col_data], errors="coerce")

    return df, col_data, col_frete


def aplicar_filtros(df, col_data, periodo, transportadoras_sel, reps_sel, ufs_sel, status_sel):
    base = df.copy()

    if col_data and periodo and len(periodo) == 2:
        dt_ini = pd.to_datetime(periodo[0], errors="coerce")
        dt_fim = pd.to_datetime(periodo[1], errors="coerce")
        if pd.notna(dt_ini) and pd.notna(dt_fim):
            base = base[(base[col_data] >= dt_ini) & (base[col_data] <= dt_fim)]

    if transportadoras_sel:
        base = base[base["Transportadora"].isin(transportadoras_sel)]
    if reps_sel:
        base = base[base["Representante"].isin(reps_sel)]
    if ufs_sel:
        base = base[base["UF"].isin(ufs_sel)]
    if status_sel:
        base = base[base["Status"].isin(status_sel)]

    return base


df, col_data, col_frete_original = carregar_dados()

if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

st.subheader("Filtros")

if col_data and df[col_data].notna().any():
    data_min = df[col_data].min().date()
    data_max = df[col_data].max().date()
    periodo = st.date_input("Período", value=(data_min, data_max), min_value=data_min, max_value=data_max)
else:
    periodo = None

base_filtros = df.copy()
col1, col2, col3, col4 = st.columns(4)

with col1:
    transportadoras_opcoes = sorted([x for x in base_filtros["Transportadora"].dropna().unique() if x])
    transportadoras_sel = st.multiselect("Transportadora", transportadoras_opcoes, default=[])

base_rep = base_filtros.copy()
if transportadoras_sel:
    base_rep = base_rep[base_rep["Transportadora"].isin(transportadoras_sel)]

with col2:
    reps_opcoes = sorted([x for x in base_rep["Representante"].dropna().unique() if x])
    reps_sel = st.multiselect("Representante", reps_opcoes, default=[])

base_uf = base_filtros.copy()
if transportadoras_sel:
    base_uf = base_uf[base_uf["Transportadora"].isin(transportadoras_sel)]
if reps_sel:
    base_uf = base_uf[base_uf["Representante"].isin(reps_sel)]

with col3:
    ufs_opcoes = sorted([x for x in base_uf["UF"].dropna().unique() if x])
    ufs_sel = st.multiselect("UF", ufs_opcoes, default=[])

with col4:
    status_opcoes = ["Atrasado", "Vence hoje", "No prazo"]
    status_sel = st.multiselect("Status", status_opcoes, default=[])

df_filtrado = aplicar_filtros(df, col_data, periodo, transportadoras_sel, reps_sel, ufs_sel, status_sel)

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado com os filtros selecionados.")
    st.stop()

st.subheader("Indicadores principais")

total_notas = len(df_filtrado)
valor_total = df_filtrado["Valor"].sum()
valor_frete = df_filtrado["Frete_calc"].sum()
perc_frete = (valor_frete / valor_total * 100) if valor_total > 0 else 0

atrasadas = int((df_filtrado["Status"] == "Atrasado").sum())
vence_hoje = int((df_filtrado["Status"] == "Vence hoje").sum())
no_prazo = int((df_filtrado["Status"] == "No prazo").sum())
perc_atraso = (atrasadas / total_notas * 100) if total_notas > 0 else 0

valor_atrasado = df_filtrado[df_filtrado["Status"] == "Atrasado"]["Valor"].sum()
valor_vence_hoje = df_filtrado[df_filtrado["Status"] == "Vence hoje"]["Valor"].sum()
perc_valor_atrasado = (valor_atrasado / valor_total * 100) if valor_total > 0 else 0

col1, col2, col3, col4 = st.columns([1, 1.8, 1.6, 1])

with col1:
    card_kpi("Notas", f"{total_notas:,}".replace(",", "."), cor_fundo="#f8fafc", cor_texto="#0f172a", borda="#e2e8f0", tamanho="22px")
with col2:
    card_kpi("Valor das Notas", formatar_moeda_br(valor_total), cor_fundo="#eff6ff", cor_texto="#1d4ed8", borda="#bfdbfe", tamanho="18px")
with col3:
    card_kpi("Valor de Frete", formatar_moeda_br(valor_frete), cor_fundo="#ecfeff", cor_texto="#0f766e", borda="#a5f3fc", tamanho="18px")
with col4:
    fundo_frete = "#f0fdf4" if perc_frete <= 5 else "#fffbeb" if perc_frete <= 8 else "#fff1f2"
    texto_frete = "#166534" if perc_frete <= 5 else "#b45309" if perc_frete <= 8 else "#b91c1c"
    borda_frete = "#bbf7d0" if perc_frete <= 5 else "#fde68a" if perc_frete <= 8 else "#fecaca"
    card_kpi("% Frete", f"{perc_frete:.2f}%", cor_fundo=fundo_frete, cor_texto=texto_frete, borda=borda_frete, tamanho="22px")

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

col5, col6, col7, col8 = st.columns(4)
with col5:
    card_kpi("🔴 Atrasadas", str(atrasadas), cor_fundo="#fff1f2", cor_texto="#b91c1c", borda="#fecdd3", tamanho="22px")
with col6:
    card_kpi("🟡 Vence hoje", str(vence_hoje), cor_fundo="#fffbeb", cor_texto="#b45309", borda="#fde68a", tamanho="22px")
with col7:
    card_kpi("🟢 No prazo", str(no_prazo), cor_fundo="#f0fdf4", cor_texto="#166534", borda="#bbf7d0", tamanho="22px")
with col8:
    fundo_atraso = "#f0fdf4" if perc_atraso < 10 else "#fffbeb" if perc_atraso < 20 else "#fff1f2"
    texto_atraso = "#166534" if perc_atraso < 10 else "#b45309" if perc_atraso < 20 else "#b91c1c"
    borda_atraso = "#bbf7d0" if perc_atraso < 10 else "#fde68a" if perc_atraso < 20 else "#fecaca"
    card_kpi("% Atraso", f"{perc_atraso:.1f}%", cor_fundo=fundo_atraso, cor_texto=texto_atraso, borda=borda_atraso, tamanho="22px")

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

colr1, colr2, colr3 = st.columns([1.6, 1.6, 1])
with colr1:
    card_kpi("🚨 Valor em atraso", formatar_moeda_br(valor_atrasado), cor_fundo="#fff1f2", cor_texto="#b91c1c", borda="#fecaca", tamanho="18px")
with colr2:
    card_kpi("🟡 Valor vence hoje", formatar_moeda_br(valor_vence_hoje), cor_fundo="#fffbeb", cor_texto="#b45309", borda="#fde68a", tamanho="18px")
with colr3:
    cor = "#166534" if perc_valor_atrasado < 10 else "#b45309" if perc_valor_atrasado < 20 else "#b91c1c"
    fundo = "#f0fdf4" if perc_valor_atrasado < 10 else "#fffbeb" if perc_valor_atrasado < 20 else "#fff1f2"
    borda = "#bbf7d0" if perc_valor_atrasado < 10 else "#fde68a" if perc_valor_atrasado < 20 else "#fecaca"
    card_kpi("% valor em risco", f"{perc_valor_atrasado:.1f}%", cor_fundo=fundo, cor_texto=cor, borda=borda, tamanho="20px")

st.subheader("🚨 Alertas automáticos")
alertas = []
if perc_frete > 8:
    alertas.append(f"⚠️ Frete elevado: {perc_frete:.2f}% do faturamento")
if perc_atraso > 20:
    alertas.append(f"🔴 Alto índice de atraso: {perc_atraso:.1f}%")
if perc_valor_atrasado > 15:
    alertas.append(f"💰 Alto valor em risco: {perc_valor_atrasado:.1f}% do total")

if not alertas:
    st.success("✅ Operação dentro dos padrões")
else:
    for alerta in alertas:
        st.warning(alerta)

st.subheader("🏆 Onde agir agora")

ranking_problemas = (
    df_filtrado[df_filtrado["Status"] == "Atrasado"]
    .groupby("Transportadora", dropna=False)
    .agg(qtd_atrasos=("NF", "count"), valor_atrasado=("Valor", "sum"))
    .reset_index()
)

if ranking_problemas.empty:
    st.success("✅ Nenhuma transportadora com atraso no filtro atual")
else:
    ranking_problemas = ranking_problemas.sort_values(["valor_atrasado", "qtd_atrasos"], ascending=False).head(5)
    ranking_problemas["valor_atrasado"] = ranking_problemas["valor_atrasado"].apply(formatar_moeda_br)
    st.dataframe(ranking_problemas, use_container_width=True, hide_index=True)

st.subheader("Resumo executivo")

col_res1, col_res2 = st.columns(2)
with col_res1:
    st.markdown("**Financeiro**")
    resumo_fin = pd.DataFrame({
        "Indicador": ["Valor das Notas", "Valor de Frete", "% Frete sobre Notas", "Valor em atraso", "% Valor em risco"],
        "Valor": [formatar_moeda_br(valor_total), formatar_moeda_br(valor_frete), f"{perc_frete:.2f}%", formatar_moeda_br(valor_atrasado), f"{perc_valor_atrasado:.1f}%"],
    })
    st.dataframe(resumo_fin, use_container_width=True, hide_index=True)

with col_res2:
    st.markdown("**Operacional**")
    resumo_op = pd.DataFrame({
        "Indicador": ["Notas", "Atrasadas", "Vence hoje", "No prazo", "% Atraso"],
        "Valor": [f"{total_notas:,}".replace(",", "."), f"{atrasadas:,}".replace(",", "."), f"{vence_hoje:,}".replace(",", "."), f"{no_prazo:,}".replace(",", "."), f"{perc_atraso:.1f}%"],
    })
    st.dataframe(resumo_op, use_container_width=True, hide_index=True)

st.subheader("Visões gráficas")

g1, g2 = st.columns(2)
with g1:
    status_df = pd.DataFrame({"Status": ["Atrasado", "Vence hoje", "No prazo"], "Quantidade": [atrasadas, vence_hoje, no_prazo]})
    fig_status = px.bar(status_df, x="Status", y="Quantidade", title="Distribuição por Status")
    fig_status.update_layout(margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_status, use_container_width=True)

with g2:
    financeiro_df = pd.DataFrame({"Indicador": ["Valor das Notas", "Valor de Frete", "Valor em atraso"], "Valor": [valor_total, valor_frete, valor_atrasado]})
    fig_fin = px.bar(financeiro_df, x="Indicador", y="Valor", title="Notas vs Frete vs Risco")
    fig_fin.update_layout(margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_fin, use_container_width=True)

st.subheader("Ranking por transportadora")

ranking_transp = (
    df_filtrado.groupby("Transportadora", dropna=False)
    .agg(qtd_nfs=("NF", "count"), valor_notas=("Valor", "sum"), valor_frete=("Frete_calc", "sum"))
    .reset_index()
)

ranking_transp["perc_frete"] = np.where(
    ranking_transp["valor_notas"] > 0,
    (ranking_transp["valor_frete"] / ranking_transp["valor_notas"]) * 100,
    0,
)

ranking_transp["valor_notas"] = ranking_transp["valor_notas"].apply(formatar_moeda_br)
ranking_transp["valor_frete"] = ranking_transp["valor_frete"].apply(formatar_moeda_br)
ranking_transp["perc_frete"] = ranking_transp["perc_frete"].map(lambda x: f"{x:.2f}%")

st.dataframe(ranking_transp.sort_values("qtd_nfs", ascending=False), use_container_width=True, hide_index=True)

with st.expander("Informações técnicas da base"):
    info_frete = col_frete_original if col_frete_original else "Nenhuma coluna de frete detectada"
    st.write(f"**Coluna de frete detectada:** {info_frete}")
    st.write(f"**Coluna de data detectada:** {col_data if col_data else 'Nenhuma'}")

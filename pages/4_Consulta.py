import streamlit as st
import pandas as pd
import unicodedata
import re
from utils.load_data import load_data


# =========================
# FUNCOES
# =========================
def normalizar_texto(valor):
    if pd.isna(valor):
        return ""
    valor = str(valor).strip().upper()
    valor = unicodedata.normalize("NFKD", valor).encode("ASCII", "ignore").decode("ASCII")
    valor = re.sub(r"\s+", " ", valor)
    return valor


def formatar_moeda_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cor_status(val):
    if val == "Atrasado":
        return "background-color: #ffcccc; color: #b00020;"
    elif val == "Vence hoje":
        return "background-color: #fff3cd; color: #856404;"
    elif val == "No prazo":
        return "background-color: #d4edda; color: #155724;"
    return ""


# =========================
# PAGINA
# =========================
st.title("🔎 Consulta")
st.caption("Consulta detalhada das notas fiscais")

# =========================
# CARREGAR DADOS
# =========================
df = load_data()
df.columns = df.columns.str.strip()

# =========================
# TRATAMENTOS
# =========================
colunas_texto = [
    "NF", "CNPJ", "BP", "Cliente", "Cidade", "UF",
    "Transportadora", "Ocorrência", "Representante", "Analista"
]

for col in colunas_texto:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

# colunas normalizadas para filtro
for col in ["Cliente", "Cidade", "UF", "Transportadora", "Ocorrência", "Representante"]:
    if col in df.columns:
        df[f"{col}_norm"] = df[col].apply(normalizar_texto)

# numericos
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

# datas
for col in ["Emissão", "Prev. Entrega", "Coleta", "Emissão CTE"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

# status
df["Status"] = df["Dias"].apply(
    lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")
)

# =========================
# FILTROS
# =========================
st.subheader("Filtros")

col1, col2, col3 = st.columns(3)

with col1:
    busca_nf = st.text_input("Buscar NF", placeholder="Ex: 185361")

with col2:
    busca_cliente = st.text_input("Buscar Cliente", placeholder="Nome do cliente")

with col3:
    busca_cnpj = st.text_input("Buscar CNPJ", placeholder="CNPJ")

base = df.copy()

col4, col5, col6, col7 = st.columns(4)

with col4:
    transportadoras = sorted([x for x in base["Transportadora_norm"].dropna().unique() if x])
    transportadora_sel = st.multiselect("Transportadora", transportadoras, default=[])

if transportadora_sel:
    base = base[base["Transportadora_norm"].isin(transportadora_sel)]

with col5:
    representantes = sorted([x for x in base["Representante_norm"].dropna().unique() if x])
    representante_sel = st.multiselect("Representante", representantes, default=[])

if representante_sel:
    base = base[base["Representante_norm"].isin(representante_sel)]

with col6:
    ufs = sorted([x for x in base["UF_norm"].dropna().unique() if x])
    uf_sel = st.multiselect("UF", ufs, default=[])

if uf_sel:
    base = base[base["UF_norm"].isin(uf_sel)]

with col7:
    cidades = sorted([x for x in base["Cidade_norm"].dropna().unique() if x])
    cidade_sel = st.multiselect("Cidade", cidades, default=[])

if cidade_sel:
    base = base[base["Cidade_norm"].isin(cidade_sel)]

col8, col9, col10 = st.columns(3)

with col8:
    ocorrencias = sorted([x for x in base["Ocorrência_norm"].dropna().unique() if x])
    ocorrencia_sel = st.multiselect("Ocorrência", ocorrencias, default=[])

if ocorrencia_sel:
    base = base[base["Ocorrência_norm"].isin(ocorrencia_sel)]

with col9:
    status_sel = st.multiselect(
        "Status",
        ["Atrasado", "Vence hoje", "No prazo"],
        default=[]
    )

if status_sel:
    base = base[base["Status"].isin(status_sel)]

with col10:
    campo_data = st.selectbox(
        "Filtrar por data",
        ["Emissão", "Prev. Entrega", "Coleta", "Emissão CTE"]
    )

# filtro por período
if campo_data in base.columns:
    data_min = base[campo_data].min()
    data_max = base[campo_data].max()

    if pd.notna(data_min) and pd.notna(data_max):
        periodo = st.date_input(
            f"Período - {campo_data}",
            value=(data_min.date(), data_max.date())
        )

        if isinstance(periodo, tuple) and len(periodo) == 2:
            dt_ini, dt_fim = periodo
            base = base[
                (base[campo_data].dt.date >= dt_ini) &
                (base[campo_data].dt.date <= dt_fim)
            ]

# =========================
# BUSCAS
# =========================
if busca_nf:
    base = base[base["NF"].astype(str).str.contains(busca_nf.strip(), case=False, na=False)]

if busca_cliente:
    cliente_norm = normalizar_texto(busca_cliente)
    base = base[base["Cliente_norm"].str.contains(cliente_norm, na=False)]

if busca_cnpj:
    base = base[base["CNPJ"].astype(str).str.contains(busca_cnpj.strip(), case=False, na=False)]

df_filtrado = base.copy()

# =========================
# KPIS
# =========================
st.subheader("Resumo da consulta")

col1, col2, col3, col4 = st.columns(4)

with col1:
    card_indicador(
        "NFs encontradas",
        f"{total:,}".replace(",", "."),
        cor="#1f2937",
        fundo="#f9fafb",
        borda="#e5e7eb"
    )

with col2:
    card_indicador(
        "🔴 Atrasadas",
        f"{atrasadas:,}".replace(",", "."),
        cor="#DC2626",
        fundo="#FEF2F2",
        borda="#FECACA"
    )

with col3:
    card_indicador(
        "🟢 No prazo",
        f"{no_prazo:,}".replace(",", "."),
        cor="#16A34A",
        fundo="#F0FDF4",
        borda="#BBF7D0"
    )

with col4:
    card_indicador(
        "Valor das Notas",
        formatar_moeda_br(valor_total),
        cor="#1d4ed8",
        fundo="#eff6ff",
        borda="#bfdbfe"
    )

with col5:
    card_indicador(
        "% atraso",
        f"{perc_atraso:.1f}%",
        cor="#DC2626" if perc_atraso > 20 else "#D97706" if perc_atraso > 10 else "#16A34A",
        fundo="#FEF2F2" if perc_atraso > 20 else "#FFFBEB" if perc_atraso > 10 else "#F0FDF4",
        borda="#FECACA" if perc_atraso > 20 else "#FDE68A" if perc_atraso > 10 else "#BBF7D0"
    )

# =========================
# TABELA
# =========================
st.subheader("Tabela detalhada")

colunas_exibir = [
    "NF", "Emissão", "Prev. Entrega", "Dias", "Status",
    "Cliente", "Cidade", "UF", "Transportadora", "Ocorrência",
    "Representante", "Valor", "Vol", "Coleta", "Emissão CTE"
]

colunas_exibir = [c for c in colunas_exibir if c in df_filtrado.columns]

tabela = df_filtrado[colunas_exibir].copy()

# ordenacao pelos maiores atrasos
if "Dias" in tabela.columns:
    tabela = tabela.sort_values(by="Dias", ascending=False)

# formatacoes
for col in ["Emissão", "Prev. Entrega", "Coleta", "Emissão CTE"]:
    if col in tabela.columns:
        tabela[col] = tabela[col].dt.strftime("%d/%m/%Y")

if "Valor" in tabela.columns:
    tabela["Valor"] = tabela["Valor"].apply(formatar_moeda_br)

if "Vol" in tabela.columns:
    tabela["Vol"] = tabela["Vol"].fillna(0)

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
    label="📥 Baixar consulta em CSV",
    data=csv,
    file_name="consulta_notas.csv",
    mime="text/csv"
)
  


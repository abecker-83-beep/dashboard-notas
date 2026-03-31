
import re
import unicodedata
import numpy as np
import pandas as pd

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
    serie = (serie.astype(str).str.replace("R$", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip())
    return pd.to_numeric(serie, errors="coerce").fillna(0)

def percentual(parte, total):
    return (parte / total) * 100 if total and total > 0 else 0.0

def preparar_base_dashboard(df):
    df = df.copy()
    df.columns = df.columns.str.strip()
    for col in ["NF", "Cliente", "Cidade", "UF", "Representante", "Transportadora", "Status", "Ocorrência"]:
        df = garantir_coluna(df, col, "")
    df = garantir_coluna(df, "Dias", 0)
    df = garantir_coluna(df, "Valor", 0)
    df = garantir_coluna(df, "Vol", 0)
    col_frete = detectar_coluna_frete(df)
    df["Frete_calc"] = converter_moeda_ou_numero(df[col_frete]) if col_frete else 0
    for col in ["Cliente", "Cidade", "UF", "Representante", "Transportadora", "Ocorrência", "Status"]:
        df[col] = df[col].astype(str).fillna("").apply(normalizar_texto)
    df["NF"] = df["NF"].astype(str).fillna("").str.strip()
    df["Dias"] = pd.to_numeric(df["Dias"], errors="coerce").fillna(0)
    df["Valor"] = converter_moeda_ou_numero(df["Valor"])
    df["Vol"] = pd.to_numeric(df["Vol"], errors="coerce").fillna(0)
    status_vazio = df["Status"].astype(str).str.strip().replace("", np.nan).isna()
    df["Status"] = np.where(status_vazio, df["Dias"].apply(lambda x: "Atrasado" if x > 0 else ("Vence hoje" if x == 0 else "No prazo")), df["Status"].astype(str).str.strip())
    col_data = detectar_coluna_data(df)
    if col_data:
        df[col_data] = pd.to_datetime(df[col_data], errors="coerce")
    return df, col_data, col_frete

def classificar_score(score):
    if score >= 95:
        return "Excelente"
    if score >= 85:
        return "Boa"
    if score >= 70:
        return "Atenção"
    return "Crítica"

def calcular_score_transportadoras(df):
    base = df.copy()
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
    agrupado["perc_atraso"] = np.where(agrupado["qtd_notas"] > 0, (agrupado["atrasadas"] / agrupado["qtd_notas"]) * 100, 0)
    agrupado["perc_frete"] = np.where(agrupado["valor_notas"] > 0, (agrupado["valor_frete"] / agrupado["valor_notas"]) * 100, 0)
    agrupado["valor_risco"] = np.where(agrupado["qtd_notas"] > 0, (agrupado["atrasadas"] / agrupado["qtd_notas"]) * agrupado["valor_notas"], 0)
    agrupado["perc_valor_risco"] = np.where(agrupado["valor_notas"] > 0, (agrupado["valor_risco"] / agrupado["valor_notas"]) * 100, 0)
    penalidade_atraso = np.minimum(agrupado["perc_atraso"] * 1.5, 60)
    penalidade_frete = np.minimum(np.clip(agrupado["perc_frete"] - 5, 0, None) * 5, 20)
    penalidade_risco = np.minimum(agrupado["perc_valor_risco"] * 0.8, 20)
    agrupado["score"] = (100 - penalidade_atraso - penalidade_frete - penalidade_risco).clip(lower=0).round(1)
    agrupado["classificacao"] = agrupado["score"].apply(classificar_score)
    return agrupado

def gerar_alertas_executivos(valor_total, valor_frete, total_notas, atrasadas, perc_frete, perc_atraso, perc_valor_risco):
    alertas = []
    if perc_frete > 8:
        alertas.append(f"⚠️ Frete elevado: {perc_frete:.2f}% do faturamento.")
    if perc_atraso > 20:
        alertas.append(f"🔴 Alto índice de atraso: {perc_atraso:.1f}% das notas.")
    if perc_valor_risco > 15:
        alertas.append(f"💰 Valor em risco elevado: {perc_valor_risco:.1f}% do total das notas.")
    if valor_total <= 0:
        alertas.append("ℹ️ Valor total das notas zerado ou não disponível.")
    if total_notas <= 0:
        alertas.append("ℹ️ Não há notas no filtro selecionado.")
    return alertas

def gerar_insights_transportadoras(ranking):
    if ranking.empty:
        return []
    top_risco = ranking.sort_values("valor_risco", ascending=False).iloc[0]
    top_frete = ranking.sort_values("perc_frete", ascending=False).iloc[0]
    pior_score = ranking.sort_values("score", ascending=True).iloc[0]
    return [
        f"{top_risco['Transportadora']} concentra o maior valor em risco: {formatar_moeda_br(top_risco['valor_risco'])}.",
        f"{top_frete['Transportadora']} tem o maior % de frete: {top_frete['perc_frete']:.2f}%.",
        f"{pior_score['Transportadora']} é a transportadora mais crítica no score executivo: {pior_score['score']:.1f}.",
    ]

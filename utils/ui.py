
import os
import streamlit as st

CORES = {
    "azul": "#2563EB",
    "verde": "#16A34A",
    "amarelo": "#D97706",
    "vermelho": "#DC2626",
    "cinza": "#374151",
    "ciano": "#0891B2",
    "neutro_borda": "#E5E7EB",
    "neutro_titulo": "#6B7280",
    "fundo_card": "#FFFFFF",
}

METAS = {
    "perc_atraso": 6.0,
    "perc_frete": 4.5,
    "score_bom": 90.0,
    "score_excelente": 95.0,
}

def aplicar_estilo_global():
    st.markdown("""
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
    </style>
    """, unsafe_allow_html=True)

def render_sidebar_brand():
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=140)
    else:
        st.sidebar.markdown("## Sua Empresa")
    st.sidebar.markdown("---")

def card_kpi(titulo, valor, cor=None, tamanho="18px"):
    cor = cor or CORES["cinza"]
    st.markdown(f"""
    <div style="
        background: {CORES['fundo_card']};
        border: 1px solid {CORES['neutro_borda']};
        border-left: 5px solid {cor};
        border-radius: 12px;
        padding: 16px 18px;
        min-height: 96px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        <div style="
            font-size: 13px;
            color: {CORES['neutro_titulo']};
            font-weight: 600;
            margin-bottom: 8px;
            white-space: nowrap;
            overflow: visible;
            text-overflow: unset;
        ">{titulo}</div>
        <div style="
            font-size: {tamanho};
            font-weight: 700;
            color: {cor};
            line-height: 1.1;
            white-space: nowrap;
            overflow: visible;
            text-overflow: unset;
        ">{valor}</div>
    </div>
    """, unsafe_allow_html=True)

def cor_percentual(valor, limite_baixo=10, limite_medio=20):
    if valor < limite_baixo:
        return CORES["verde"]
    if valor < limite_medio:
        return CORES["amarelo"]
    return CORES["vermelho"]

def cor_score(score):
    if score >= METAS["score_excelente"]:
        return CORES["verde"]
    if score >= METAS["score_bom"]:
        return CORES["amarelo"]
    return CORES["vermelho"]

import streamlit as st


def setup_page(title: str):
    st.set_page_config(
        page_title=title,
        layout="wide",
        initial_sidebar_state="collapsed"
    )

def render_page_header(title: str, subtitle: str = None):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.divider()


def render_section_header(title: str):
    st.markdown(f"### {title}")


def render_spacer(lines: int = 1):
    for _ in range(lines):
        st.write("")


def get_standard_kpi_columns():
    return st.columns(4)


def get_standard_two_columns():
    return st.columns([2, 1])


def get_standard_half_columns():
    return st.columns(2)

def get_kpi_columns_custom():
    return st.columns([1, 1.8, 1.6, 1])

def render_section_header(title: str):
    st.markdown(f"### {title}")

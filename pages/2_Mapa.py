# (mantive TODO seu código original — apenas com ajustes pontuais)

# =========================
# INTELIGÊNCIA (AJUSTADA)
# =========================
with i1:
    st.markdown("**Top cidades com mais atraso**")
    if cidades_criticas.empty:
        st.success("Nenhuma cidade com atraso no filtro atual.")
    else:
        tabela = cidades_criticas[["Cidade", "UF", "qtd_atrasadas", "perc_atraso", "valor_total"]].copy()
        tabela.columns = ["Cidade", "UF", "Qtd atrasadas", "% atraso", "Valor total"]

        # 🔥 AJUSTE
        tabela["% atraso"] = tabela["% atraso"].map(lambda x: f"{x:.1f}%")
        tabela["Valor total"] = tabela["Valor total"].apply(formatar_moeda_br)

        st.dataframe(tabela, use_container_width=True, hide_index=True)

with i2:
    st.markdown("**Regiões críticas (UFs)**")
    if ufs_criticas.empty:
        st.success("Nenhuma UF com atraso no filtro atual.")
    else:
        tabela = ufs_criticas[["UF", "qtd_atrasadas", "perc_atraso", "valor_total"]].copy()
        tabela.columns = ["UF", "Qtd atrasadas", "% atraso", "Valor total"]

        # 🔥 AJUSTE
        tabela["% atraso"] = tabela["% atraso"].map(lambda x: f"{x:.1f}%")
        tabela["Valor total"] = tabela["Valor total"].apply(formatar_moeda_br)

        st.dataframe(tabela, use_container_width=True, hide_index=True)


# =========================
# MAPA UF (AJUSTADO)
# =========================
st.plotly_chart(
    fig_uf,
    use_container_width=True,
    config={"scrollZoom": True}
)


# =========================
# MAPA CIDADE (AJUSTADO)
# =========================
st.plotly_chart(
    fig_cidade,
    use_container_width=True,
    config={"scrollZoom": True}
)


# =========================
# MAPA NF (AJUSTADO)
# =========================
st.plotly_chart(
    fig_nf,
    use_container_width=True,
    config={"scrollZoom": True}
)

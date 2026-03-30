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

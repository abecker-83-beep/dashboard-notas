def card_kpi(titulo, valor, cor="#1f2937", tamanho="18px"):
    import streamlit as st

    st.markdown(
        f"""
        <div style="
            background: #ffffff;
            border: 1px solid #e5e7eb;
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
                color: #6b7280;
                font-weight: 600;
                margin-bottom: 8px;
            ">
                {titulo}
            </div>
            <div style="
                font-size: {tamanho};
                font-weight: 700;
                color: {cor};
            ">
                {valor}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

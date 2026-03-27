import streamlit as st
from utils.load_data import load_data

st.title("📊 Resumo")

df = load_data()

st.write("Prévia dos dados:")
st.dataframe(df.head())

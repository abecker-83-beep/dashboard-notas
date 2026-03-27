import pandas as pd
from utils.config import SHEET_URL

def load_data():
    df = pd.read_csv(SHEET_URL)

    # limpar nomes das colunas
    df.columns = df.columns.str.strip()

    return df

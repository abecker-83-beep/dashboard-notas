import pandas as pd
from utils.config import SHEET_URL

def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
    except:
        df = pd.read_excel("TRACKING CLIENTES.xlsx")

    return df

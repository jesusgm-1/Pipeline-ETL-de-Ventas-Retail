import pandas as pd
import os

RAW_PATH = "data/raw/online_retail_II.xlsx"

def extract():
    print("Leyendo archivo Excel...")
    
    df_1 = pd.read_excel(RAW_PATH, sheet_name="Year 2009-2010")
    df_2 = pd.read_excel(RAW_PATH, sheet_name="Year 2010-2011")
    
    df = pd.concat([df_1, df_2], ignore_index=True)
    
    print(f"Total de filas cargadas: {len(df)}")
    print(f"Columnas: {list(df.columns)}")
    print(f"\nPrimeras filas:")
    print(df.head())
    print(f"\nValores nulos por columna:")
    print(df.isnull().sum())
    
    return df

if __name__ == "__main__":
    df = extract()
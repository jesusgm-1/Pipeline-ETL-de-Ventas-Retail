import pandas as pd

def transform(df):
    print("Iniciando limpieza...")
    filas_inicial = len(df)

    # Eliminar filas sin Customer ID
    df = df.dropna(subset=["Customer ID"])
    print(f"Filas eliminadas por Customer ID nulo: {filas_inicial - len(df)}")

    # Eliminar devoluciones (Quantity negativa) y precios en cero
    df = df[df["Quantity"] > 0]
    df = df[df["Price"] > 0]
    print(f"Filas después de eliminar devoluciones y precios cero: {len(df)}")

    # Eliminar duplicados
    df = df.drop_duplicates()
    print(f"Filas después de eliminar duplicados: {len(df)}")

    # Limpiar nombres de columnas
    df.columns = ["invoice_no", "stock_code", "description", 
                  "quantity", "invoice_date", "unit_price", 
                  "customer_id", "country"]

    # Convertir tipos
    df["customer_id"] = df["customer_id"].astype(int).astype(str)
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    df["stock_code"] = df["stock_code"].astype(str).str.strip()
    df["description"] = df["description"].fillna("Sin descripción").str.strip()

    # Calcular total por fila
    df["total_amount"] = df["quantity"] * df["unit_price"]

    # Agregar columnas de fecha para dim_date
    df["full_date"] = df["invoice_date"].dt.date
    df["year"] = df["invoice_date"].dt.year
    df["month"] = df["invoice_date"].dt.month
    df["day"] = df["invoice_date"].dt.day
    df["quarter"] = df["invoice_date"].dt.quarter
    df["day_of_week"] = df["invoice_date"].dt.day_name()

    print(f"\nTotal filas limpias: {len(df)}")
    print(f"Rango de fechas: {df['invoice_date'].min()} → {df['invoice_date'].max()}")
    print(f"Países únicos: {df['country'].nunique()}")
    print(f"Productos únicos: {df['stock_code'].nunique()}")
    print(f"Clientes únicos: {df['customer_id'].nunique()}")

    return df

if __name__ == "__main__":
    from extract import extract
    df_raw = extract()
    df_clean = transform(df_raw)
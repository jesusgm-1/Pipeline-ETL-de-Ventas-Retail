import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = "postgresql+psycopg2://retail_user:retail_pass@localhost:5433/retail_db"

def get_engine():
    return create_engine(DB_URL)

def load(df):
    engine = get_engine()
    print("Conectando a PostgreSQL...")

    with engine.connect() as conn:
        # Limpiar tablas antes de cargar (para re-ejecuciones)
        conn.execute(text("TRUNCATE fact_sales, dim_date, dim_customer, dim_product RESTART IDENTITY CASCADE"))
        conn.commit()

    # --- dim_customer ---
    print("Cargando dim_customer...")
    dim_customer = df[["customer_id", "country"]].drop_duplicates(subset=["customer_id"])
    dim_customer.to_sql("dim_customer", engine, if_exists="append", index=False)
    print(f"  {len(dim_customer)} clientes cargados")

    # --- dim_product ---
    print("Cargando dim_product...")
    dim_product = df[["stock_code", "description"]].drop_duplicates(subset=["stock_code"])
    dim_product.to_sql("dim_product", engine, if_exists="append", index=False)
    print(f"  {len(dim_product)} productos cargados")

    # --- dim_date ---
    print("Cargando dim_date...")
    dim_date = df[["full_date", "year", "month", "day", "quarter", "day_of_week"]].drop_duplicates(subset=["full_date"])
    dim_date = dim_date.sort_values("full_date").reset_index(drop=True)
    dim_date["date_id"] = dim_date.index + 1
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    print(f"  {len(dim_date)} fechas cargadas")

    # --- fact_sales ---
    print("Cargando fact_sales (puede tardar unos minutos)...")
    date_map = dim_date.set_index("full_date")["date_id"]
    df["date_id"] = df["full_date"].map(date_map)

    fact = df[["invoice_no", "customer_id", "stock_code", "date_id", "quantity", "unit_price", "total_amount"]]
    fact.to_sql("fact_sales", engine, if_exists="append", index=False, chunksize=10000)
    print(f"  {len(fact)} filas cargadas en fact_sales")

    print("\nCarga completada exitosamente.")

if __name__ == "__main__":
    from extract import extract
    from transform import transform
    df_raw = extract()
    df_clean = transform(df_raw)
    load(df_clean)
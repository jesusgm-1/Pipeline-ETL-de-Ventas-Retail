from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text

# Dentro de Docker, la conexión usa el nombre del servicio, no localhost
DB_URL = "postgresql+psycopg2://retail_user:retail_pass@postgres:5432/retail_db"
RAW_PATH = "/opt/airflow/data/online_retail_II.xlsx"

def extract(**context):
    print("Leyendo archivo Excel...")
    df1 = pd.read_excel(RAW_PATH, sheet_name="Year 2009-2010")
    df2 = pd.read_excel(RAW_PATH, sheet_name="Year 2010-2011")
    df = pd.concat([df1, df2], ignore_index=True)
    print(f"Filas cargadas: {len(df)}")
    # Convertir todas las columnas object a string para compatibilidad con pyarrow
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str)
    df.to_parquet("/tmp/raw_data.parquet", index=False)

def transform(**context):
    print("Transformando datos...")
    df = pd.read_parquet("/tmp/raw_data.parquet")
    
    df = df.dropna(subset=["Customer ID"])
    df = df[df["Quantity"] > 0]
    df = df[df["Price"] > 0]
    df = df.drop_duplicates()
    
    df.columns = ["invoice_no", "stock_code", "description",
                  "quantity", "invoice_date", "unit_price",
                  "customer_id", "country"]
    
    df["customer_id"] = df["customer_id"].astype(int).astype(str)
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    df["stock_code"] = df["stock_code"].astype(str).str.strip()
    df["description"] = df["description"].fillna("Sin descripción").str.strip()
    df["total_amount"] = df["quantity"] * df["unit_price"]
    df["full_date"] = df["invoice_date"].dt.date
    df["year"] = df["invoice_date"].dt.year
    df["month"] = df["invoice_date"].dt.month
    df["day"] = df["invoice_date"].dt.day
    df["quarter"] = df["invoice_date"].dt.quarter
    df["day_of_week"] = df["invoice_date"].dt.day_name()
    
    print(f"Filas limpias: {len(df)}")
    df.to_parquet("/tmp/clean_data.parquet", index=False)

def load(**context):
    print("Cargando a PostgreSQL...")
    df = pd.read_parquet("/tmp/clean_data.parquet")
    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE fact_sales, dim_date, dim_customer, dim_product RESTART IDENTITY CASCADE"))

    dim_customer = df[["customer_id", "country"]].drop_duplicates(subset=["customer_id"])
    dim_customer.to_sql("dim_customer", engine, if_exists="append", index=False)
    print(f"Clientes cargados: {len(dim_customer)}")

    dim_product = df[["stock_code", "description"]].drop_duplicates(subset=["stock_code"])
    dim_product.to_sql("dim_product", engine, if_exists="append", index=False)
    print(f"Productos cargados: {len(dim_product)}")

    dim_date = df[["full_date", "year", "month", "day", "quarter", "day_of_week"]].drop_duplicates(subset=["full_date"])
    dim_date = dim_date.sort_values("full_date").reset_index(drop=True)
    dim_date["date_id"] = dim_date.index + 1
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    print(f"Fechas cargadas: {len(dim_date)}")

    date_map = dim_date.set_index("full_date")["date_id"]
    df["date_id"] = df["full_date"].map(date_map)
    fact = df[["invoice_no", "customer_id", "stock_code", "date_id", "quantity", "unit_price", "total_amount"]]
    fact.to_sql("fact_sales", engine, if_exists="append", index=False, chunksize=10000)
    print(f"Ventas cargadas: {len(fact)}")
    print("Carga completada exitosamente.")

with DAG(
    dag_id="retail_etl_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    description="Pipeline ETL completo de ventas retail"
) as dag:

    t1 = PythonOperator(task_id="extract", python_callable=extract)
    t2 = PythonOperator(task_id="transform", python_callable=transform)
    t3 = PythonOperator(task_id="load", python_callable=load)

    t1 >> t2 >> t3
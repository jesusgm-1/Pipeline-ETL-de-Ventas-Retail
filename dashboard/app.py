import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

DB_URL = "postgresql+psycopg2://retail_user:retail_pass@localhost:5433/retail_db"

engine = create_engine(DB_URL)

@st.cache_data
def load_ventas_por_mes():
    query = """
        SELECT d.year, d.month, SUM(f.total_amount) as total
        FROM fact_sales f
        JOIN dim_date d ON f.date_id = d.date_id
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month
    """
    df = pd.read_sql(query, engine)
    df["periodo"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
    return df

@st.cache_data
def load_ventas_por_pais():
    query = """
        SELECT c.country, SUM(f.total_amount) as total
        FROM fact_sales f
        JOIN dim_customer c ON f.customer_id = c.customer_id
        GROUP BY c.country
        ORDER BY total DESC
        LIMIT 10
    """
    return pd.read_sql(query, engine)

@st.cache_data
def load_top_productos():
    query = """
        SELECT p.description, SUM(f.quantity) as unidades, SUM(f.total_amount) as total
        FROM fact_sales f
        JOIN dim_product p ON f.stock_code = p.stock_code
        GROUP BY p.description
        ORDER BY total DESC
        LIMIT 10
    """
    return pd.read_sql(query, engine)

@st.cache_data
def load_kpis():
    query = """
        SELECT 
            COUNT(DISTINCT invoice_no) as total_ordenes,
            COUNT(DISTINCT customer_id) as total_clientes,
            SUM(total_amount) as revenue_total,
            ROUND(AVG(total_amount)::numeric, 2) as ticket_promedio
        FROM fact_sales
    """
    return pd.read_sql(query, engine)
# --- LAYOUT ---
st.set_page_config(page_title="Retail Dashboard", layout="wide")
st.title("Dashboard de Ventas Retail")
st.markdown("Análisis de ventas 2009-2011 | Pipeline ETL con Python, Airflow y PostgreSQL")

# KPIs
kpis = load_kpis().iloc[0]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Órdenes", f"{int(kpis['total_ordenes']):,}")
col2.metric("Clientes Únicos", f"{int(kpis['total_clientes']):,}")
col3.metric("Revenue Total", f"£{float(kpis['revenue_total']):,.0f}")
col4.metric("Ticket Promedio", f"£{float(kpis['ticket_promedio']):,.2f}")

st.divider()

# Ventas por mes
st.subheader("Revenue por Mes")
df_mes = load_ventas_por_mes()
st.line_chart(df_mes.set_index("periodo")["total"])

st.divider()

col_left, col_right = st.columns(2)

# Top países
with col_left:
    st.subheader("Top 10 Países por Revenue")
    df_pais = load_ventas_por_pais()
    st.bar_chart(df_pais.set_index("country")["total"])

# Top productos
with col_right:
    st.subheader("Top 10 Productos por Revenue")
    df_prod = load_top_productos()
    st.bar_chart(df_prod.set_index("description")["total"])
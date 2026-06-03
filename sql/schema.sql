-- Dimensión de clientes
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id VARCHAR(20) PRIMARY KEY,
    country VARCHAR(100)
);

-- Dimensión de productos
CREATE TABLE IF NOT EXISTS dim_product (
    stock_code VARCHAR(20) PRIMARY KEY,
    description VARCHAR(255)
);

-- Dimensión de tiempo
CREATE TABLE IF NOT EXISTS dim_date (
    date_id SERIAL PRIMARY KEY,
    full_date DATE,
    year INT,
    month INT,
    day INT,
    quarter INT,
    day_of_week VARCHAR(20)
);

-- Tabla de hechos
CREATE TABLE IF NOT EXISTS fact_sales (
    id SERIAL PRIMARY KEY,
    invoice_no VARCHAR(20),
    customer_id VARCHAR(20) REFERENCES dim_customer(customer_id),
    stock_code VARCHAR(20) REFERENCES dim_product(stock_code),
    date_id INT REFERENCES dim_date(date_id),
    quantity INT,
    unit_price NUMERIC(10,2),
    total_amount NUMERIC(10,2)
);
# Retail Data Warehouse using Apache Airflow & dbt

An end-to-end Data Engineering project that builds a production-style Retail Data Warehouse using **Apache Airflow**, **dbt**, **PostgreSQL**, and **Docker**. The project implements the **Bronze → Silver → Gold Medallion Architecture** to ingest, transform, validate, and model retail data into an analytics-ready warehouse.

---

## Project Overview

This project demonstrates a modern data engineering workflow commonly used in enterprise data platforms.

The pipeline:

- Extracts retail data from the Olist Brazilian E-Commerce Dataset
- Loads raw data into the Bronze layer
- Cleans and transforms data into the Silver layer using dbt
- Builds analytics-ready fact and dimension tables in the Gold layer
- Orchestrates the complete workflow using Apache Airflow
- Performs automated data quality validation using dbt tests

---

## Architecture

```text
                 Olist Retail Dataset
                          │
                          ▼
              Apache Airflow Orchestration
                          │
                          ▼
             Bronze Layer (Raw Data)
                          │
                          ▼
      Silver Layer (Cleaned & Transformed)
                          │
                          ▼
       Gold Layer (Star Schema)
                          │
                          ▼
          Data Quality Validation (dbt)
```

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | ETL scripting |
| Apache Airflow | Workflow orchestration |
| dbt | Data transformation & modeling |
| PostgreSQL | Data warehouse |
| Docker | Containerization |
| SQL | Data modeling & analytics |

---

## Dataset

This project uses the **Olist Brazilian E-Commerce Dataset** as the primary data source.

Expected files inside the `datasets/` directory:

```text
datasets/
├── olist_customers_dataset.csv
├── olist_orders_dataset.csv
├── olist_order_items_dataset.csv
├── olist_order_payments_dataset.csv
└── olist_products_dataset.csv
```

The dataset is **not included** in this repository.

---

## Project Structure

```text
.
├── config/
├── dags/
├── dbt/
├── output_screenshots/
├── scripts/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile.airflow
├── requirements.txt
├── sample_queries.sql
├── verify_pipeline.sql
└── README.md
```

---

## Key Features

- Bronze → Silver → Gold Medallion Architecture
- Apache Airflow DAG orchestration
- dbt-based SQL transformations
- Star Schema dimensional modeling
- Automated data quality testing
- Dockerized development environment
- Modular and scalable project structure

---

## Pipeline Workflow

```text
Olist Dataset
      │
      ▼
Extract
      │
      ▼
Bronze
      │
      ▼
Transform
      │
      ▼
Silver
      │
      ▼
Load
      │
      ▼
Gold
      │
      ▼
Data Quality Tests
```

---

## Project Screenshots

### Apache Airflow

- Airflow Home
- Airflow DAG Overview
- Master Pipeline Execution

### PostgreSQL

- Medallion Architecture Schemas
- Bronze Tables
- Silver Tables
- Gold Tables

### SQL Query Results

- Bronze Layer Query
- Silver Layer Query
- Gold Layer Query

Screenshots are available in the `output_screenshots/` folder.

---

## Future Improvements

- Real-time data ingestion using Apache Kafka
- CI/CD using GitHub Actions
- Pipeline monitoring and alerting
- Dashboard integration using Power BI

---

## Repository Contents

- Apache Airflow DAGs
- dbt Models
- SQL Scripts
- Docker Configuration
- Sample SQL Queries
- Project Screenshots

---

## Author

**Tanvi Dedhia**

GitHub: https://github.com/thetanvi18

LinkedIn: https://www.linkedin.com/in/tanvi-dedhia-8a0787251/
# AWS Serverless YouTube Trending ETL Pipeline

An end-to-end serverless ETL pipeline built on AWS that ingests YouTube Trending video metadata, stores raw JSON data in Amazon S3 (Bronze layer), transforms it into analytics-ready Parquet files using AWS Glue (PySpark), and enables SQL analytics through Amazon Athena.

---

## Tech Stack

* Python
* AWS Lambda
* Amazon S3
* AWS Glue
* AWS Glue Crawlers
* AWS Glue Data Catalog
* PySpark
* Amazon Athena
* AWS IAM
* Amazon CloudWatch
* YouTube Data API v3

---

## Project Flow

1. AWS Lambda fetches trending video metadata from the YouTube Data API.
2. Raw JSON responses are stored in the Amazon S3 **Bronze** layer.
3. AWS Glue Crawler catalogs the Bronze dataset in the Glue Data Catalog.
4. AWS Glue ETL (PySpark) extracts the required fields, flattens the nested JSON structure, and converts it into Parquet format.
5. The transformed dataset is stored in the Amazon S3 **Silver** layer.
6. A second AWS Glue Crawler catalogs the Silver dataset.
7. Amazon Athena queries the transformed Parquet files using SQL for analytics.

---

## Repository Structure

```text
AWS_LAKEHOUSE/
│
├── api_test/
├── data/
├── glue_jobs/
├── lambda/
│   └── ingestion/
├── output_screenshots/
├── scripts/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## SQL Queries

Sample Athena SQL queries used in this project are available in:

```text
scripts/athena_queries.sql
```

---

## Screenshots

The `output_screenshots/` folder contains screenshots of:

* AWS Lambda deployment and execution
* Amazon S3 Bronze & Silver layers
* AWS Glue Crawlers
* AWS Glue ETL Job
* Amazon Athena query results

---

## Future Improvements

* Add a Gold layer for business-level aggregations.
* Automate scheduled ingestion using Amazon EventBridge.
* Build dashboards using Amazon QuickSight or Power BI.
* Implement automated data quality validation.
* Process larger datasets using incremental ETL.

---

## Author

**Tanvi Dedhia**

GitHub: https://github.com/thetanvi18

LinkedIn: https://linkedin.com/in/thetanvi18

# Rearc Data Quest

This repository contains my solution to the Rearc Data Quest.  
The project demonstrates data ingestion, data processing, analytics, and a fully deployed AWS serverless architecture using Infrastructure as Code (Terraform).

The implementation supports both:

- A clean local-first execution model
- A fully automated AWS deployment

---

## Overview

The quest consists of four parts:

1. **Part 1 – BLS Dataset Ingestion**
2. **Part 2 – Population API Ingestion**
3. **Part 3 – Data Analytics**
4. **Part 4 – Infrastructure Deployment (Terraform)**

The solution emphasizes:

- Incremental data ingestion
- Idempotent processing
- Clean data transformations
- Event-driven architecture
- Infrastructure as Code
- Clear documentation and structure

---

# AWS Deployment (Terraform Implementation)

In addition to the local implementation, the complete pipeline is deployed on AWS using Terraform.

All infrastructure is defined under:

```
infra/terraform/
```

### Services Provisioned

- Amazon S3 (raw data storage)
- AWS Lambda (Ingestion)
- AWS Lambda (Analytics)
- Amazon SQS (decoupled event processing)
- Amazon EventBridge (scheduled trigger)
- IAM Roles & Policies
- S3 → SQS notification configuration
- SQS → Lambda event source mapping
- CloudWatch Logs

### Deployment

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

This provisions the entire event-driven data pipeline.

### Destroy Infrastructure

```bash
terraform destroy
```

---

## Production Data Flow (AWS)

```
EventBridge (Daily Schedule)
        ↓
Lambda – Ingestion
        ↓
S3 (raw/bls/, raw/api/)
        ↓
S3 ObjectCreated Event
        ↓
SQS Queue
        ↓
Lambda – Analytics
        ↓
CloudWatch Logs
```

This architecture ensures:

- Loose coupling
- Retry capability via SQS
- Event-driven execution
- Scalable serverless processing
- Clean separation of ingestion and analytics layers

---

# Part 1 – BLS Dataset Ingestion

File: `src/bls_sync.py`

This script incrementally synchronizes the BLS productivity time-series dataset.

### Key Features

- Fetches remote directory listing dynamically
- Handles HTTP access constraints (403 behavior)
- Detects new files without hardcoded names
- Downloads only missing files
- Ensures idempotent execution
- Stores raw files under:

```
data/raw/bls/
```

In AWS deployment, files are written to:

```
s3://<bucket>/raw/bls/
```

---

# Part 2 – Population API Ingestion

File: `src/population.py`

This script fetches U.S. population data from the DataUSA API.

### Key Features

- Parameterized API request
- Raw JSON storage (no transformation during ingestion)
- Timestamped output files
- Idempotent upload (skips if file already exists for the day)

Local storage:

```
data/raw/api/
```

AWS deployment writes to:

```
s3://<bucket>/raw/api/
```

---

# Part 3 – Data Analytics

Local notebook: `notebooks/part3_analysis.ipynb`  
AWS implementation: `analytics_lambda_package/analytics.py`

The analytics layer performs the required tasks.

---

## 1. Population Statistics (2013–2018)

- Filters population data for years 2013–2018 (inclusive)
- Computes:
  - Mean population
  - Standard deviation

---

## 2. Best Year per `series_id`

For each `series_id`:

- Aggregates quarterly values into yearly totals
- Identifies the year with the maximum summed value

Produces:

```
series_id | year | value
```

---

## 3. Target Series Join

For:

- `series_id = PRS30006032`
- `period = Q01`

The logic:

- Filters relevant rows
- Performs left join with population on `year`
- Returns:

```
series_id | year | period | value | Population
```

The left join ensures:

> "Population for that given year (if available)."

---

# Lambda Packaging

Lambda artifacts are prebuilt and included:

```
lambda_package/lambda_ingestion.zip
analytics_lambda_package/analytics_lambda.zip
```

Terraform references these zip files directly.

This ensures the project can be deployed without rebuilding dependencies.

---

# Architectural Pattern

The design loosely follows a medallion-style architecture:

- **Bronze** – Raw ingested data (S3)
- **Silver** – Cleaned and aggregated datasets
- **Gold** – Final analytical outputs

Additional design principles:

- Event-driven architecture
- Idempotent ingestion
- Decoupled compute layers
- Infrastructure as Code
- Reproducible deployment

---

# Project Structure

```
rearc-data-quest/
│
├── src/
│   ├── bls_sync.py
│   ├── population.py
│   ├── lambda_ingestion.py
│   └── analytics.py
│
├── lambda_package/
│   └── lambda_ingestion.zip
│
├── analytics_lambda_package/
│   └── analytics_lambda.zip
│
├── infra/
│   └── terraform/
│       ├── main.tf
│       └── provider.tf
│
├── notebooks/
│   └── part3_analysis.ipynb
│
├── docs/
│   └── architecture.md
│
├── requirements.txt
└── README.md
```

---

# Running the Project Locally

### 1. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### 2. Run Ingestion Scripts

```bash
python src/bls_sync.py
python src/population.py
```

---

### 3. Run Analytics Notebook

```bash
jupyter notebook
```

Open:

```
notebooks/part3_analysis.ipynb
```

Run all cells.

---
### Future Improvements

The current ingestion logic detects new files by comparing filenames between the
remote BLS directory and objects already present in S3. This ensures idempotent
execution and avoids unnecessary writes.

However, if the source system were to modify the contents of an existing file
without changing the filename, the current implementation would not detect the
update.

In a production system, this could be addressed by:

- Comparing file checksums (e.g., MD5 hash) between the source and stored object
- Using HTTP `Last-Modified` headers to detect upstream updates
- Storing file metadata (hash or timestamp) in DynamoDB to track historical versions

This enhancement would allow the ingestion pipeline to detect content updates
while still preserving idempotent behavior.

---


## AI Usage Disclosure

AI tools were used as development aids during this project for:

- Troubleshooting HTTP behavior
- Reviewing pandas transformation patterns
- Verifying Terraform syntax
- Clarifying AWS service configurations

All architectural decisions, implementation logic, debugging steps, and final code were fully reviewed, tested, and understood independently before submission.

---

# Summary

This solution demonstrates:

- Incremental ingestion design
- Idempotent API ingestion
- Data cleaning and transformation practices
- Aggregation and join logic
- Fully deployed AWS serverless pipeline
- Infrastructure as Code using Terraform
- Event-driven architecture with SQS decoupling
- Clean repository organization and documentation

The implementation prioritizes correctness, clarity, reproducibility, and production-aligned engineering practices.
# Rearc Data Quest

This repository contains my solution to the Rearc Data Quest.  
The project demonstrates data ingestion, data processing, analytics, and infrastructure design using a clean, local-first implementation that maps directly to AWS services.

---

## Overview

The quest consists of four parts:

1. **Part 1 – BLS Dataset Ingestion**
2. **Part 2 – Population API Ingestion**
3. **Part 3 – Data Analytics**
4. **Part 4 – Infrastructure Design**

The solution emphasizes:

- Incremental data ingestion
- Idempotent processing
- Clean data transformations
- Event-driven architecture design
- Clear documentation and structure

---

## Part 1 – BLS Dataset Ingestion

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

This mirrors how ingestion would write to an S3 bucket in production.

---

## Part 2 – Population API Ingestion

File: `src/population.py`

This script fetches U.S. population data from the DataUSA API.

### Key Features

- Parameterized API request
- Raw JSON storage (no transformation during ingestion)
- Timestamped output files
- Stored under:

```
data/raw/api/
```

Raw responses are preserved to maintain ingestion integrity and separation of concerns.

---

## Part 3 – Data Analytics

File: `notebooks/part3_analysis.ipynb`

The notebook performs the required analytics tasks using pandas.

### 1. Population Statistics

- Filters population data for years 2013–2018 (inclusive)
- Computes:
  - Mean population
  - Standard deviation

---

### 2. Best Year per `series_id`

For each `series_id`:

- Aggregates quarterly values into yearly totals
- Identifies the year with the maximum summed value

Produces:

```
series_id | year | value
```

This matches the specification provided in the Quest example.

---

### 3. Target Series Join

For:

- `series_id = PRS30006032`
- `period = Q01`

The notebook:

- Filters relevant rows
- Joins with population data on `year`
- Returns:

```
series_id | year | period | value | Population
```

The join uses a left join to respect the requirement:

> "Population for that given year (if available)."

---

### Data Cleaning Considerations

- Trimmed whitespace in column names and string fields
- Enforced correct data types (`year`, `value`, `Population`)
- Ensured consistent join keys
- Validated grouping logic

---

## Part 4 – Infrastructure Design

File: [`docs/architecture.md`](docs/architecture.md)

The infrastructure is designed using AWS services in an event-driven pattern.

### Components

- **EventBridge** – Daily scheduling trigger
- **Lambda (Ingestion Layer)** – Executes Part 1 & Part 2
- **S3 Bucket** – Stores raw data (Bronze layer)
- **SQS Queue** – Triggered by S3 event notifications
- **Lambda (Analytics Layer)** – Executes aggregation logic
- **CloudWatch Logs** – Logs final outputs

---

### Data Flow

```
EventBridge
    ↓
Lambda (Ingestion)
    ↓
S3 (Raw Storage)
    ↓
S3 Event Notification
    ↓
SQS
    ↓
Lambda (Analytics)
    ↓
CloudWatch Logs
```

---

### Architectural Pattern

The design loosely follows a medallion-style architecture:

- **Bronze** – Raw ingested data in S3
- **Silver** – Cleaned and aggregated data
- **Gold** – Final analytical outputs

Infrastructure can be provisioned using:

- AWS CDK
- CloudFormation
- Terraform

---

## Project Structure

```
rearc-data-quest/
│
├── src/
│   ├── bls_sync.py
│   └── population.py
│
├── notebooks/
│   └── part3_analysis.ipynb
│
├── docs/
│   └── architecture.md
│
├── data/
│   └── raw/
│          └── api/
│          └── bls/
│
├── requirements.txt
└── README.md
```

---

## Running the Project Locally

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

## AI Usage Disclosure

AI tools were used as a reference during development for:

- Debugging HTTP behavior
- Structuring pandas transformations
- Refining architecture explanation

All logic, implementation, and architectural decisions were verified and understood independently.

---

## Summary

This solution demonstrates:

- Incremental ingestion design
- Data cleaning and transformation practices
- Aggregation and join logic
- Event-driven AWS pipeline architecture
- Clean repository organization and documentation

The implementation prioritizes correctness, clarity, and production-aligned design decisions.
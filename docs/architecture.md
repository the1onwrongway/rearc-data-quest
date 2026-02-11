# Part 4 – Infrastructure Design

## Overview

This data pipeline automates the ingestion and analytics steps using AWS services. The architecture follows a simple event-driven design.

---

## Components

### 1. EventBridge (Scheduler)
- Triggers ingestion Lambda daily.

### 2. Lambda – Ingestion Layer
- Executes Part 1 (BLS sync).
- Executes Part 2 (Population API ingestion).
- Writes raw files to S3 (Bronze layer).

### 3. S3 Bucket
- Stores:
  - Raw BLS files
  - Raw population JSON
- Configured with S3 Event Notification to send message to SQS when JSON file is created.

### 4. SQS Queue
- Receives event when new population JSON is written.
- Decouples ingestion from analytics.

### 5. Lambda – Analytics Layer
- Triggered by SQS.
- Executes Part 3 aggregation logic.
- Logs results to CloudWatch Logs (no file output required).

---

## Data Flow

EventBridge → Lambda (Ingestion) → S3  
S3 → SQS → Lambda (Analytics) → CloudWatch Logs

---

## Architectural Pattern

The pipeline loosely follows a medallion architecture:

- Bronze: Raw data stored in S3.
- Silver: Cleaned and aggregated data in processing layer.
- Gold: Final analytical outputs logged.

---

## Infrastructure as Code

The infrastructure can be provisioned using:
- AWS CDK
- CloudFormation
- Terraform

Resources required:
- 2 Lambda functions
- 1 S3 bucket
- 1 SQS queue
- 1 EventBridge rule
- IAM roles with appropriate permissions
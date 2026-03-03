resource "aws_s3_bucket" "rearc_bucket" {
  bucket = "rearc-data-quest-milan-tf"
  force_destroy = true
  tags = {
    Project   = "rearc-data-quest"
    ManagedBy = "terraform"
  }
}

resource "aws_sqs_queue" "analytics_queue" {
  name                       = "rearc-analytics-queue-tf"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 86400

  tags = {
    Project   = "rearc-data-quest"
    ManagedBy = "terraform"
  }
}


resource "aws_iam_role" "ingestion_lambda_role" {
  name = "rearc-ingestion-lambda-role-tf"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ingestion_basic_logs" {
  role       = aws_iam_role.ingestion_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "ingestion_s3_access" {
  role       = aws_iam_role.ingestion_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_lambda_function" "ingestion_lambda" {
  function_name = "rearc-ingestion-lambda-tf"
  role          = aws_iam_role.ingestion_lambda_role.arn
  handler       = "lambda_ingestion.lambda_handler"
  runtime       = "python3.11"

  filename         = "../../lambda_package/lambda_ingestion.zip"
  source_code_hash = filebase64sha256("../../lambda_package/lambda_ingestion.zip")
  timeout          = 60
  memory_size      = 256

  environment {
    variables = {
      USE_S3    = "true"
      S3_BUCKET = aws_s3_bucket.rearc_bucket.bucket
    }
  }

  tags = {
    Project   = "rearc-data-quest"
    ManagedBy = "terraform"
  }
}


resource "aws_cloudwatch_event_rule" "daily_ingestion" {
  name                = "rearc-daily_ingestion-tf"
  schedule_expression = "rate(1 day)"
}

resource "aws_cloudwatch_event_target" "ingestion_target" {
  rule      = aws_cloudwatch_event_rule.daily_ingestion.name
  target_id = "IngestionLambda"
  arn       = aws_lambda_function.ingestion_lambda.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_ingestion.arn
}


resource "aws_iam_role" "analytics_lambda_role" {
  name = "rearc-analytics-lambda-role-tf"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "analytics_basic_logs" {
  role       = aws_iam_role.analytics_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "analytics_s3_access" {
  role       = aws_iam_role.analytics_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "analytics_sqs_access" {
  role       = aws_iam_role.analytics_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
}


resource "aws_lambda_function" "analytics_lambda" {
  function_name = "rearc-analytics-lambda-tf"
  role          = aws_iam_role.analytics_lambda_role.arn
  handler       = "analytics.lambda_handler"
  runtime       = "python3.11"

  filename         = "../../analytics_lambda_package/analytics_lambda.zip"
  source_code_hash = filebase64sha256("../../analytics_lambda_package/analytics_lambda.zip")

  timeout     = 60
  memory_size = 256

  tags = {
    Project   = "rearc-data-quest"
    ManagedBy = "terraform"
  }
}

resource "aws_lambda_event_source_mapping" "sqs_to_analytics" {
  event_source_arn = aws_sqs_queue.analytics_queue.arn
  function_name    = aws_lambda_function.analytics_lambda.arn
  batch_size       = 1
}

resource "aws_sqs_queue_policy" "allow_s3_publish" {
  queue_url = aws_sqs_queue.analytics_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowS3SendMessage"
        Effect    = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action    = "SQS:SendMessage"
        Resource  = aws_sqs_queue.analytics_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_s3_bucket.rearc_bucket.arn
          }
        }
      }
    ]
  })
}


resource "aws_s3_bucket_notification" "s3_to_sqs" {
  bucket = aws_s3_bucket.rearc_bucket.id

  queue {
    queue_arn     = aws_sqs_queue.analytics_queue.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "raw/api/"
    filter_suffix = ".json"
  }

  depends_on = [
    aws_sqs_queue_policy.allow_s3_publish
  ]
}
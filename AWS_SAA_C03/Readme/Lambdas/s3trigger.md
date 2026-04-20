# AWS Lambda + S3 CSV to JSON Lab

## Goal
Build an event-driven AWS lab where uploading a `.csv` file to a source S3 bucket triggers a Lambda function written in Python. The Lambda function reads the CSV, validates it, converts it to JSON, and writes the output to a processed bucket. If the CSV is invalid, the function writes an error artifact to a rejected bucket.

This lab is intentionally small but realistic. It teaches core Lambda patterns without mixing in unrelated complexity like VPCs, Batch, or Step Functions.

---

## What we will learn
- How S3 event notifications trigger Lambda
- Why Lambda needs an execution role
- How to read and write S3 objects from Python
- How to validate uploaded files before processing them
- How to separate raw, processed, and rejected data
- How to observe Lambda with CloudWatch Logs
- Why multiple buckets are safer than a same-bucket design for this use case

---

## Final architecture

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/2279bceb-1763-4ec3-9c8b-fc98082ce32d" />

---

## Services used
- Amazon S3
- AWS Lambda
- IAM
- Amazon CloudWatch Logs

---

## Recommended region
Use one AWS region for the entire lab, for example:
- `eu-north-1`
- `eu-west-1`
- `us-east-1`

Do not spread resources across multiple regions.

---

## Naming convention
Replace `<unique-id>` with something unique such as your initials and a date.

Suggested names:
- Source bucket: `lambda-csv-source-<unique-id>`
- Processed bucket: `lambda-csv-processed-<unique-id>`
- Rejected bucket: `lambda-csv-rejected-<unique-id>`
- Lambda function: `csv-to-json-transformer`
- IAM role: `lambda-csv-to-json-role`

---

## Prerequisites
Before you start, make sure you have:
- An AWS account
- Permission to create S3 buckets, Lambda functions, IAM roles, and view CloudWatch logs
- Basic familiarity with the AWS Console
- A small CSV file for testing

Optional:
- VS Code or another editor

---

## High-level flow
1. Create 3 S3 buckets
2. Create an IAM role for Lambda
3. Create the Lambda function in Python
4. Attach the S3 trigger from the source bucket
5. Configure suffix filtering so only `.csv` files trigger the Lambda
6. Upload a valid CSV to test the success path
7. Upload an invalid CSV to test the rejection path
8. Review CloudWatch logs and the output objects

---

# Part 1: Create the S3 buckets

Create these 3 buckets in the same region:
  <img width="1262" height="488" alt="image" src="https://github.com/user-attachments/assets/35c68eb2-846a-47fc-8680-9683bc87f2ac" />

1. Source bucket
   - Purpose: raw uploads
   - Example folder structure: `incoming/`
     <img width="1296" height="495" alt="image" src="https://github.com/user-attachments/assets/3df7dfb0-bd26-4ba1-abbd-e1e63252d00c" />


2. Processed bucket
   - Purpose: valid transformed JSON output
   - Example folder structure: `json/`
     <img width="1042" height="487" alt="image" src="https://github.com/user-attachments/assets/a5ac8322-445e-4a4a-a9c4-c6cd5772e7ff" />


3. Rejected bucket
   - Purpose: invalid file details and error artifacts
   - Example folder structure: `errors/`
     <img width="1041" height="463" alt="image" src="https://github.com/user-attachments/assets/aaedbeb8-f54b-4c19-ac61-e716f42fad8e" />

---

# Part 3: Create the IAM role for Lambda

The Lambda function needs permissions to:
- Write logs to CloudWatch
- Read objects from the source bucket
- Write objects to the processed bucket
- Write objects to the rejected bucket

## Console steps
1. Open **IAM**
2. Go to **Roles**
3. Click **Create role**
4. Trusted entity type: **AWS service**
5. Use case: **Lambda**
6. Click **Next**
7. Attach the managed policy:
   - `AWSLambdaBasicExecutionRole`
8. Create the role with the name:
   - `lambda-csv-to-json-role`
  <img width="1778" height="814" alt="image" src="https://github.com/user-attachments/assets/612301cc-0a75-4fd0-965c-e0e7474a6b59" />
  <img width="1731" height="821" alt="image" src="https://github.com/user-attachments/assets/28282952-1368-4702-bad8-94baff1641c0" />
  <img width="1087" height="442" alt="image" src="https://github.com/user-attachments/assets/9fd7c2ba-d2fc-4cd4-be4d-a30857723236" />




## Add custom inline policy for S3 access
After the role is created:
1. Open the role
2. Click **Add permissions**
3. Click **Create inline policy**
4. Choose the JSON editor
5. Paste the policy below
6. Replace the bucket names with your actual bucket names

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadSourceCsvFiles",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::lambda-csv-source-<unique-id>/*"
    },
    {
      "Sid": "WriteProcessedJsonFiles",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::lambda-csv-processed-<unique-id>/*"
    },
    {
      "Sid": "WriteRejectedErrorFiles",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::lambda-csv-rejected-<unique-id>/*"
    }
  ]
}

```

  <img width="1277" height="662" alt="image" src="https://github.com/user-attachments/assets/63ee6d9a-2a76-42a6-a080-84c2af05db46" />
  
### Optional stricter version
If you want to make it a bit more realistic later, you can scope permissions down further to:
- source bucket `incoming/*`
- processed bucket `json/*`
- rejected bucket `errors/*`

---

# Part 4: Create the Lambda function

## Runtime choice
Use:
- **Python 3.12** if available in your region and account
- otherwise the latest supported Python 3.x runtime in Lambda

## Basic settings
Create the function:
- Function name: `csv-to-json-transformer`
- Runtime: Python 3.x
- Execution role: use existing role
- Existing role: `lambda-csv-to-json-role`

## Suggested Lambda configuration
For this lab:
- Memory: `256 MB`
- Timeout: `30 seconds`

Why:
- CSV parsing is lightweight
- This is enough for small test files
- You can increase later if needed

---

# Part 5: Add environment variables

In the Lambda function configuration, add these environment variables:

- `PROCESSED_BUCKET` = your processed bucket name
- `REJECTED_BUCKET` = your rejected bucket name
- `PROCESSED_PREFIX` = `json/`
- `REJECTED_PREFIX` = `errors/`

These make the code cleaner and avoid hardcoding resource names.

---

# Part 6: Lambda Python code

Replace the default Lambda code with the following.

```python
import boto3
import csv
import io
import json
import logging
import os
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")

PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
REJECTED_BUCKET = os.environ["REJECTED_BUCKET"]
PROCESSED_PREFIX = os.environ.get("PROCESSED_PREFIX", "json/")
REJECTED_PREFIX = os.environ.get("REJECTED_PREFIX", "errors/")

REQUIRED_COLUMNS = ["id", "name", "email"]


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    for record in event.get("Records", []):
        source_bucket = record["s3"]["bucket"]["name"]
        source_key = unquote_plus(record["s3"]["object"]["key"])

        logger.info("Processing file s3://%s/%s", source_bucket, source_key)

        try:
            response = s3.get_object(Bucket=source_bucket, Key=source_key)
            file_content = response["Body"].read().decode("utf-8")

            rows = parse_and_validate_csv(file_content)

            output_key = build_output_key(source_key)
            output_body = json.dumps(rows, indent=2)

            s3.put_object(
                Bucket=PROCESSED_BUCKET,
                Key=output_key,
                Body=output_body.encode("utf-8"),
                ContentType="application/json"
            )

            logger.info(
                "Successfully processed %s rows from %s and wrote to s3://%s/%s",
                len(rows), source_key, PROCESSED_BUCKET, output_key
            )

        except Exception as ex:
            logger.exception("Failed to process file %s", source_key)
            error_key = build_error_key(source_key)
            error_body = {
                "source_bucket": source_bucket,
                "source_key": source_key,
                "error": str(ex)
            }
            s3.put_object(
                Bucket=REJECTED_BUCKET,
                Key=error_key,
                Body=json.dumps(error_body, indent=2).encode("utf-8"),
                ContentType="application/json"
            )

    return {
        "statusCode": 200,
        "body": "Processing complete"
    }


def parse_and_validate_csv(file_content: str):
    if not file_content.strip():
        raise ValueError("The CSV file is empty")

    reader = csv.DictReader(io.StringIO(file_content))

    if reader.fieldnames is None:
        raise ValueError("CSV header row is missing")

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    rows = []
    for index, row in enumerate(reader, start=1):
        normalized_row = {
            "id": row.get("id", "").strip(),
            "name": row.get("name", "").strip(),
            "email": row.get("email", "").strip()
        }

        if not normalized_row["id"]:
            raise ValueError(f"Row {index} is missing required value for 'id'")
        if not normalized_row["name"]:
            raise ValueError(f"Row {index} is missing required value for 'name'")
        if not normalized_row["email"]:
            raise ValueError(f"Row {index} is missing required value for 'email'")

        rows.append(normalized_row)

    if not rows:
        raise ValueError("The CSV file contains a header but no data rows")

    return rows


def build_output_key(source_key: str) -> str:
    filename = source_key.split("/")[-1]
    base_name = filename.rsplit(".", 1)[0]
    return f"{PROCESSED_PREFIX}{base_name}.json"


def build_error_key(source_key: str) -> str:
    filename = source_key.split("/")[-1]
    base_name = filename.rsplit(".", 1)[0]
    return f"{REJECTED_PREFIX}{base_name}.error.json"
```

---

# Part 7: Understand what the code does

## Main flow
For each S3 event record, the Lambda function:
1. Reads the bucket name and object key
2. Downloads the CSV file from the source bucket
3. Decodes it as UTF-8 text
4. Parses it using `csv.DictReader`
5. Validates the required header columns
6. Validates required values in each row
7. Converts rows into JSON objects
8. Writes the JSON file to the processed bucket
9. If anything fails, writes an error JSON to the rejected bucket

## Why the function loops over records
S3 events can contain more than one record. Even if you only upload one file in most tests, writing the handler to process all records is the correct pattern.

## Why the error is written to a bucket
This creates a visible artifact of failure. That is useful because in real systems you often need to keep a trace of bad inputs instead of silently failing.

---

# Part 8: Add the S3 trigger

Now configure the source bucket to trigger the Lambda function.

## Console steps
1. Open **Lambda**
2. Open your function `csv-to-json-transformer`
3. Go to **Configuration** or use the **Add trigger** action depending on the console version
4. Add trigger: **S3**
5. Choose your source bucket
6. Event type: **PUT** or **All object create events**
7. Prefix: `incoming/`
8. Suffix: `.csv`
9. Enable trigger
10. Save

## Why use both prefix and suffix
Use both so the trigger only fires for:
- files in `incoming/`
- whose names end with `.csv`

This is cleaner than relying only on suffix matching.

Example files that should trigger:
- `incoming/customers.csv`
- `incoming/file-01.csv`

Example files that should not trigger:
- `notes.txt`
- `incoming/customers.json`
- `archive/customers.csv`

---

# Part 9: Create a valid CSV test file

Create a file locally called `customers-valid.csv` with this content:

```csv
id,name,email
1,Alice,alice@example.com
2,Bob,bob@example.com
3,Charlie,charlie@example.com
```

## Upload test
Upload it to the source bucket under:
- `incoming/customers-valid.csv`

---

# Part 10: Verify the success path

After upload, check the following:

## In the processed bucket
You should see:
- `json/customers-valid.json`

Expected content:

```json
[
  {
    "id": "1",
    "name": "Alice",
    "email": "alice@example.com"
  },
  {
    "id": "2",
    "name": "Bob",
    "email": "bob@example.com"
  },
  {
    "id": "3",
    "name": "Charlie",
    "email": "charlie@example.com"
  }
]
```

## In CloudWatch Logs
You should see messages similar to:
- event received
- processing file path
- rows processed
- output bucket and key

---

# Part 11: Create an invalid CSV test file

Create a file called `customers-invalid.csv`:

```csv
id,name
1,Alice
2,Bob
```

This file is invalid because the required `email` column is missing.

Upload it to:
- `incoming/customers-invalid.csv`

---

# Part 12: Verify the rejection path

## In the rejected bucket
You should see:
- `errors/customers-invalid.error.json`

Expected content will look like this:

```json
{
  "source_bucket": "your-source-bucket-name",
  "source_key": "incoming/customers-invalid.csv",
  "error": "Missing required columns: ['email']"
}
```

## In CloudWatch Logs
You should see the exception details and stack trace.

---

# Part 13: CloudWatch log verification

## Steps
1. Open **CloudWatch**
2. Go to **Logs**
3. Open the log group for your Lambda function
4. Open the newest log stream

## What to look for
- the S3 event payload
- the source bucket and key
- row count for successful processing
- the exception for failed processing

This is important. Do not treat logs like optional garnish. They are part of the lab.

---

# Part 14: Why 3 buckets are a good design here

You chose the correct design for a first Lambda lab.

## Source bucket
Stores raw incoming data.

## Processed bucket
Stores successful transformed output.

## Rejected bucket
Stores failure artifacts.

This separation helps because:
- raw inputs are not mixed with outputs
- failure artifacts are easy to inspect
- there is no risk of same-bucket recursion from transformed files
- the system is easier to explain in an interview

Could one bucket work with prefix and suffix filtering? Yes.
Should you do that for your first version? No. Three buckets are clearer and safer.

---


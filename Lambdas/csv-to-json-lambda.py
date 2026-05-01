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
# API Gateway + Lambda + DynamoDB Order Intake Lab

## Overview

This lab builds a realistic serverless order intake microservice on AWS.

A client sends HTTP requests to API Gateway. API Gateway authorizes the request, validates the request body, and invokes Lambda. The create Lambda stores the order in DynamoDB, enforces idempotency, publishes an `OrderCreated` event to EventBridge, and returns a response. The get Lambda retrieves an order by ID.

- separate create and get Lambdas
- custom authorization with a Lambda authorizer
- idempotency using a dedicated DynamoDB table
- API Gateway request validation
- EventBridge event publishing after successful order creation
- structured logging

---

## Architecture

Client
- API Gateway REST API
- Lambda Authorizer
- CreateOrderLambda or GetOrderLambda
- DynamoDB Orders table
- EventBridge custom bus after successful create

Supporting components:

- CloudWatch Logs
- lambda triggered by event bridge event

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/bc700d16-3ac6-4f6f-91ce-6d0eff809210" />

---

## Learning goals

By the end of this lab, you should be able to explain and demonstrate:

- how API Gateway invokes Lambda
- why auth should sit before business logic
- how request validation reduces garbage traffic reaching Lambda
- how to emit domain events after persistence
- how structured logs and traces help debugging

---

## Final design

### API routes

- `POST /orders` -> `CreateOrderLambda`
- `GET /orders/{orderId}` -> `GetOrderLambda`

### Lambda functions

- `CreateOrderLambda`
- `GetOrderLambda`
- `OrderApiAuthorizerLambda`
- `OrderCreatedConsumerLambda`

### DynamoDB tables

- `Orders`
- `OrderIdempotency`

### EventBridge

- custom bus: `order-bus`
- event type: `OrderCreated`

---

## Business scenario

A partner portal sends order requests to your backend.

You do not allow the partner to write directly to DynamoDB. Instead, the partner calls an API. The API enforces authorization, validates the contract, protects against duplicate submissions, stores the order, and emits a business event that downstream services can react to later.

This is a realistic first step in a larger event-driven system.

---

## Project structure

```text
api-gateway-order-intake-advanced-lab/
├── README.md
├── src/
│   ├── create_order/
│   │   └── lambda_function.py
│   ├── get_order/
│   │   └── lambda_function.py
│   ├── authorizer/
│   │   └── lambda_function.py
│   └── order_created_consumer/
│       └── lambda_function.py
├── events/
│   ├── valid-create-order.json
│   ├── invalid-create-order.json
│   └── get-order-event.json
├── schemas/
│   └── create-order-model.json
└── docs/
    └── architecture.png
```

---

## AWS resources to create

Create these resources in this order:

1. DynamoDB table `Orders`
2. DynamoDB table `OrderIdempotency`
3. EventBridge custom bus `order-bus`
4. Lambda `GetOrderLambda`
5. Lambda `CreateOrderLambda`
6. Lambda `OrderApiAuthorizerLambda`
7. Lambda `OrderCreatedConsumerLambda`
8. API Gateway REST API
9. API resources and methods
10. Request model and validator
11. Authorizer attachments
12. EventBridge rule and target
13. Stage deployment
14. Tracing enablement

---

## Resource configuration details

## 1. Create the Orders table

Create a DynamoDB table:

- Table name: `Orders`
- Partition key: `orderId` (String)

This table stores the full order record.

### Example item

```json
{
  "orderId": "ord-7f3c9a12",
  "customerId": "cust-1001",
  "source": "partner-portal",
  "status": "RECEIVED",
  "currency": "USD",
  "totalAmount": 1250,
  "createdAt": "2026-04-26T14:00:00Z",
  "items": [
    {
      "sku": "LAPTOP-15",
      "quantity": 1,
      "unitPrice": 1200
    },
    {
      "sku": "MOUSE-01",
      "quantity": 2,
      "unitPrice": 25
    }
  ]
}
```

---

## 2. Create the OrderIdempotency table

Create another DynamoDB table:

- Table name: `OrderIdempotency`
- Partition key: `id` (String)

Enable TTL on this table:

- TTL attribute: `expiration`

### Why this exists

This table stores idempotency records so that repeated POST requests with the same idempotency key do not create duplicate orders.

---

## 3. Create the EventBridge bus

Create a custom EventBridge bus:

- Name: `order-bus`

This will receive business events after order creation.

Optional:

Create a test rule that matches:

- source: `order.api`
- detail-type: `OrderCreated`

and send it to a small logging Lambda or CloudWatch target for verification.

---

## 4. Create the Lambda functions

Use Python 3.x runtime.

Create four Lambda functions:

### A. CreateOrderLambda

Purpose:

- accept valid POST request payload
- enforce business validation
- enforce idempotency
- generate `orderId`
- calculate `totalAmount`
- store order in DynamoDB
- publish `OrderCreated` event to EventBridge
- return `201 Created`

### B. GetOrderLambda

Purpose:

- accept `GET /orders/{orderId}`
- read order from DynamoDB
- return `200` or `404`

### C. OrderApiAuthorizerLambda

Purpose:

- check the `Authorization` header
- allow or deny request before business Lambda is called

### D. OrderCreatedConsumerLambda

Purpose:

- receive the `OrderCreated` event from EventBridge
- log a clear message to CloudWatch Logs saying the order was received
- prove that the event was actually consumed by a downstream target

---

## 5. Environment variables

Set the following environment variables.

### CreateOrderLambda

- `ORDERS_TABLE=Orders`
- `IDEMPOTENCY_TABLE=OrderIdempotency`
- `EVENT_BUS_NAME=order-bus`
- `POWERTOOLS_SERVICE_NAME=create-order-service`
- `LOG_LEVEL=INFO`

### GetOrderLambda

- `ORDERS_TABLE=Orders`
- `POWERTOOLS_SERVICE_NAME=get-order-service`
- `LOG_LEVEL=INFO`

### OrderApiAuthorizerLambda

- `EXPECTED_BEARER_TOKEN=lab-secret-token`
- `POWERTOOLS_SERVICE_NAME=order-api-authorizer`
- `LOG_LEVEL=INFO`

### OrderCreatedConsumerLambda

- `POWERTOOLS_SERVICE_NAME=order-created-consumer`
- `LOG_LEVEL=INFO`

---

## 6. IAM permissions

Do not use wildcard admin permissions.

### CreateOrderLambda role

Allow:

- `dynamodb:PutItem` on `Orders`
- `events:PutEvents` on `order-bus`
- read/write access needed for `OrderIdempotency`
- CloudWatch Logs permissions
- X-Ray write permissions

### GetOrderLambda role

Allow:

- `dynamodb:GetItem` on `Orders`
- CloudWatch Logs permissions
- X-Ray write permissions

### OrderApiAuthorizerLambda role

Allow:

- CloudWatch Logs permissions
- X-Ray write permissions

### OrderCreatedConsumerLambda role

Allow:

- CloudWatch Logs permissions
- X-Ray write permissions

---

## 7. Enable tracing on all Lambdas

For each Lambda:

- open the Lambda configuration
- enable **Active tracing**

This allows X-Ray to show service flow and downstream calls.

---

## 8. Lambda code

## `src/create_order/lambda_function.py`

```python
import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()

dynamodb = boto3.resource("dynamodb")
events = boto3.client("events")

orders_table = dynamodb.Table(os.environ["ORDERS_TABLE"])
idempotency_table_name = os.environ["IDEMPOTENCY_TABLE"]
event_bus_name = os.environ["EVENT_BUS_NAME"]

persistence_layer = DynamoDBPersistenceLayer(table_name=idempotency_table_name)
config = IdempotencyConfig(event_key_jmespath="headers.idempotency-key")


def response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def parse_body(event: dict) -> dict:
    body = event.get("body") or "{}"
    return json.loads(body)


def validate_business_rules(payload: dict) -> list[str]:
    errors = []

    if not payload.get("customerId"):
        errors.append("customerId is required")

    if not payload.get("source"):
        errors.append("source is required")

    if not payload.get("currency"):
        errors.append("currency is required")

    items = payload.get("items") or []
    if not items:
        errors.append("items must contain at least one item")
    else:
        for index, item in enumerate(items):
            if not item.get("sku"):
                errors.append(f"items[{index}].sku is required")
            if item.get("quantity", 0) <= 0:
                errors.append(f"items[{index}].quantity must be greater than 0")
            if item.get("unitPrice", -1) < 0:
                errors.append(f"items[{index}].unitPrice must be greater than or equal to 0")

    return errors


def calculate_total(items: list[dict]) -> Decimal:
    total = Decimal("0")
    for item in items:
        qty = Decimal(str(item["quantity"]))
        price = Decimal(str(item["unitPrice"]))
        total += qty * price
    return total


@idempotent(persistence_store=persistence_layer, config=config)
@tracer.capture_method

def process_order(event: dict) -> dict:
    payload = parse_body(event)
    errors = validate_business_rules(payload)

    if errors:
        return response(400, {"message": "Validation failed", "errors": errors})

    order_id = f"ord-{uuid.uuid4().hex[:8]}"
    created_at = datetime.now(timezone.utc).isoformat()
    total_amount = calculate_total(payload["items"])

    order = {
        "orderId": order_id,
        "customerId": payload["customerId"],
        "source": payload["source"],
        "currency": payload["currency"],
        "status": "RECEIVED",
        "createdAt": created_at,
        "totalAmount": float(total_amount),
        "items": payload["items"],
    }

    logger.append_keys(orderId=order_id, customerId=payload["customerId"], source=payload["source"])
    logger.info("Persisting order")

    orders_table.put_item(Item=order)

    logger.info("Publishing OrderCreated event")
    events.put_events(
        Entries=[
            {
                "Source": "order.api",
                "DetailType": "OrderCreated",
                "EventBusName": event_bus_name,
                "Detail": json.dumps(
                    {
                        "orderId": order_id,
                        "customerId": payload["customerId"],
                        "status": "RECEIVED",
                        "createdAt": created_at,
                        "totalAmount": float(total_amount),
                    }
                ),
            }
        ]
    )

    return response(
        201,
        {
            "orderId": order_id,
            "status": "RECEIVED",
            "createdAt": created_at,
        },
    )


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler

def lambda_handler(event: dict, context: LambdaContext) -> dict:
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}

    if not headers.get("idempotency-key"):
        return response(400, {"message": "Missing required header: Idempotency-Key"})

    event["headers"] = headers
    return process_order(event)
```

### Notes

- This uses Powertools Logger and Tracer.
- Idempotency is based on the `Idempotency-Key` header.
- API Gateway request validation should still be enabled even though Lambda performs business validation.

---

## `src/get_order/lambda_function.py`

```python
import json
import os

import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()

dynamodb = boto3.resource("dynamodb")
orders_table = dynamodb.Table(os.environ["ORDERS_TABLE"])


def response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler

def lambda_handler(event: dict, context: LambdaContext) -> dict:
    path_params = event.get("pathParameters") or {}
    order_id = path_params.get("orderId")

    if not order_id:
        return response(400, {"message": "orderId path parameter is required"})

    logger.append_keys(orderId=order_id)
    logger.info("Fetching order")

    result = orders_table.get_item(Key={"orderId": order_id})
    item = result.get("Item")

    if not item:
        logger.info("Order not found")
        return response(404, {"message": "Order not found"})

    logger.info("Order found")
    return response(200, item)
```

---

## `src/authorizer/lambda_function.py`

```python
import os

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()


def build_policy(principal_id: str, effect: str, resource: str) -> dict:
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource,
                }
            ],
        },
    }


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler

def lambda_handler(event: dict, context: LambdaContext) -> dict:
    expected = os.environ["EXPECTED_BEARER_TOKEN"]
    auth_header = (event.get("authorizationToken") or "").strip()
    method_arn = event["methodArn"]

    logger.info("Authorizing request")

    if auth_header == f"Bearer {expected}":
        return build_policy("partner-client", "Allow", method_arn)

    return build_policy("partner-client", "Deny", method_arn)
```

---
## `src/order_created_consumer/lambda_function.py`

```python
import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    entries = event.get("detail", {})
    order_id = entries.get("orderId", "unknown")
    customer_id = entries.get("customerId", "unknown")
    status = entries.get("status", "unknown")

    logger.append_keys(orderId=order_id, customerId=customer_id, status=status)
    logger.info(f"OrderCreatedConsumerLambda received order {order_id}")

    print(json.dumps({
        "message": "Order event consumed",
        "orderId": order_id,
        "customerId": customer_id,
        "status": status
    }))

    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"Received order {order_id}"})
    }
```

### Notes

- This Lambda is the downstream consumer of the `OrderCreated` event.
- It is triggered by EventBridge, not by API Gateway.
- You will see its output in CloudWatch Logs, which proves the event was routed and consumed successfully.

---

## 9. Package dependencies

If you deploy manually, either include dependencies in the deployment package or use a Lambda layer.

Required packages:

```text
boto3
aws-lambda-powertools
```

Create a `requirements.txt`:

```text
aws-lambda-powertools
```

Note:

- `boto3` is available in the Lambda runtime, but many teams still pin and package dependencies consistently.
- For a simple lab, using runtime-provided `boto3` is fine.

---

## 10. Create the EventBridge consumer rule

Create an EventBridge rule on the `order-bus` custom bus.

### Rule pattern

Match:

- source: `order.api`
- detail-type: `OrderCreated`

### Target

Set the target to:

- `OrderCreatedConsumerLambda`

### What this does

When `CreateOrderLambda` publishes an `OrderCreated` event, EventBridge evaluates the rule. If the event matches, EventBridge invokes `OrderCreatedConsumerLambda`. That Lambda writes a message to CloudWatch Logs saying it received the order.

This is the consumer in your lab.

---

## 11. Create the REST API in API Gateway

Create a **REST API**, not an HTTP API.

Why:

- request validation is easier and more mature here
- API keys and usage plans are available if you want them later
- this version of the lab is intentionally closer to a real partner API

### Resources

Create these resources:

- `/orders`
- `/orders/{orderId}`

### Methods

- `POST /orders`
- `GET /orders/{orderId}`

### Integrations

- `POST /orders` -> `CreateOrderLambda`
- `GET /orders/{orderId}` -> `GetOrderLambda`

Use Lambda proxy integration.

---

## 12. Add request validation for POST /orders

Create an API Gateway model named `CreateOrderModel` using JSON schema.

## `schemas/create-order-model.json`

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "CreateOrderModel",
  "type": "object",
  "required": ["customerId", "source", "currency", "items"],
  "properties": {
    "customerId": {
      "type": "string",
      "minLength": 1
    },
    "source": {
      "type": "string",
      "minLength": 1
    },
    "currency": {
      "type": "string",
      "minLength": 1
    },
    "items": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["sku", "quantity", "unitPrice"],
        "properties": {
          "sku": {
            "type": "string",
            "minLength": 1
          },
          "quantity": {
            "type": "integer",
            "minimum": 1
          },
          "unitPrice": {
            "type": "number",
            "minimum": 0
          }
        }
      }
    }
  }
}
```

Create a request validator that validates:

- request body
- request headers if you choose to mark headers as required at the method request level

Attach this model and validator to `POST /orders`.

### Important

API Gateway validation handles structure and basic contract checks.

Lambda should still enforce business rules.

---

## 13. Add required headers and parameters

### For POST /orders

Require these headers in your lab documentation and method request configuration:

- `Authorization`
- `Idempotency-Key`

### For GET /orders/{orderId}`

Require:

- path parameter `orderId`
- `Authorization` header

---

## 14. Create the Lambda authorizer in API Gateway

Create a Lambda authorizer that points to `OrderApiAuthorizerLambda`.

Attach it to:

- `POST /orders`
- `GET /orders/{orderId}`

### Test auth behavior

#### Allowed

```http
Authorization: Bearer lab-secret-token
```

#### Denied

- missing header
- wrong token

---

## 15. Deploy the API

Create a stage, for example:

- `dev`

After deployment, note the invoke URL.

Example:

```text
https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev
```

---

## 16. Enable API Gateway tracing

Enable X-Ray tracing for the deployed stage.

This lets you see:

- request entry at API Gateway
- Lambda invocation
- downstream service calls

---

## 17. Test payloads

## `events/valid-create-order.json`

```json
{
  "customerId": "cust-1001",
  "source": "partner-portal",
  "currency": "USD",
  "items": [
    {
      "sku": "LAPTOP-15",
      "quantity": 1,
      "unitPrice": 1200
    },
    {
      "sku": "MOUSE-01",
      "quantity": 2,
      "unitPrice": 25
    }
  ]
}
```

## `events/invalid-create-order.json`

```json
{
  "source": "partner-portal",
  "currency": "USD",
  "items": []
}
```

---

## 18. Example curl commands

Replace the API URL with your deployed invoke URL.

### Unauthorized request

```bash
curl -X POST "https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/dev/orders" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-001" \
  -d @events/valid-create-order.json
```

Expected:

- request denied by authorizer

### Invalid schema request

```bash
curl -X POST "https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/dev/orders" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lab-secret-token" \
  -H "Idempotency-Key: test-002" \
  -d @events/invalid-create-order.json
```

Expected:

- API Gateway validation failure or Lambda `400` depending on what fails first

### Valid create request

```bash
curl -X POST "https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/dev/orders" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lab-secret-token" \
  -H "Idempotency-Key: test-003" \
  -d @events/valid-create-order.json
```

Expected response:

```json
{
  "orderId": "ord-xxxxxxxx",
  "status": "RECEIVED",
  "createdAt": "2026-04-26T14:00:00+00:00"
}
```

### Duplicate create request with same idempotency key

Run the same command again using the same `Idempotency-Key`.

Expected:

- no duplicate order is created
- same logical result is returned

### Get existing order

```bash
curl -X GET "https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/dev/orders/ord-xxxxxxxx" \
  -H "Authorization: Bearer lab-secret-token"
```

Expected:

- `200 OK`

### Get non-existent order

```bash
curl -X GET "https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/dev/orders/ord-does-not-exist" \
  -H "Authorization: Bearer lab-secret-token"
```

Expected:

- `404 Not Found`

---

## 19. Expected behaviors

### POST /orders

#### Success

- HTTP 201
- order stored in DynamoDB
- event published to EventBridge
- `OrderCreatedConsumerLambda` is invoked
- consumer log visible in CloudWatch
- logs visible in CloudWatch
- trace visible in X-Ray

#### Failure cases

- unauthorized -> denied before business Lambda
- invalid schema -> rejected at API Gateway or Lambda
- missing `Idempotency-Key` -> `400`
- EventBridge permission removed -> failure during create flow

### GET /orders/{orderId}

#### Success

- HTTP 200
- full order returned

#### Failure cases

- unauthorized -> denied before business Lambda
- missing order -> `404`

---

## 20. Structured logging guidance

Use structured JSON logs, not random print statements.

Recommended keys:

- `service`
- `level`
- `timestamp`
- `correlation_id`
- `orderId`
- `customerId`
- `source`
- `message`

### Why this matters

When a request fails, you want logs you can filter and reason about.

Good logs are one of the biggest differences between a real backend and a tutorial project.

---

## 21. Tracing guidance

With X-Ray enabled on API Gateway and Lambda, inspect:

- end-to-end request flow
- Lambda latency
- DynamoDB call timing
- EventBridge publish call timing

Use traces to understand where latency or failure occurs.

---

## 22. Break/fix exercises

These are mandatory if you want this lab to teach anything useful.

### Exercise 1: Break auth

Set the wrong token in the request.

Observe:

- request denied before business Lambda

### Exercise 2: Break request schema

Send payload missing `customerId`.

Observe:

- validation failure

### Exercise 3: Break DynamoDB permissions for CreateOrderLambda

Remove `dynamodb:PutItem`.

Observe:

- create request fails
- CloudWatch logs show permission issue
- trace shows failed downstream call

### Exercise 4: Break EventBridge publish permission

Remove `events:PutEvents`.

Observe:

- order write may succeed but event publish fails
- `OrderCreatedConsumerLambda` is not triggered
- study logs and decide whether this should fail the whole request in your lab design

### Exercise 5: Break the EventBridge rule target

Disable the EventBridge rule or remove the Lambda target permission.

Observe:

- create request may still succeed
- event may be published
- consumer Lambda does not run
- this teaches the difference between publishing an event and actually consuming it

### Exercise 6: Retry same create with same idempotency key

Observe:

- no duplicate order

### Exercise 7: Retry same create with different idempotency key

Observe:

- duplicate logical submission is possible
- understand why client behavior matters

---

## 23. Suggested design decisions to discuss in README

### Why split create and get into separate Lambdas?

Because responsibilities stay cleaner:

- create path is write-heavy and more complex
- get path is read-only and simpler
- permissions differ
- logs and failures are easier to isolate

### Why authorizer before business Lambda?

Because unauthorized requests should be rejected before business logic runs.

### Why idempotency?

Because clients retry.
Without idempotency, one flaky network path can create duplicate orders.

### Why EventBridge after persistence?

Because you should not emit `OrderCreated` if the order did not actually get stored.

### Why API Gateway validation and Lambda validation both?

Because API Gateway catches malformed requests early, while Lambda enforces deeper business rules.

---

## 24. Cost notes

This lab will likely be cheap, but not free if you leave things running and keep testing.

Cost contributors:

- API Gateway requests
- Lambda invocations and duration
- DynamoDB read/write capacity or on-demand requests
- EventBridge event ingestion
- CloudWatch Logs storage
- X-Ray traces

Clean up after the lab.

---

## 25. Cleanup steps

Delete in this order:

1. API Gateway REST API
2. Lambda functions
3. EventBridge rules and custom bus
4. DynamoDB tables
5. CloudWatch log groups if you want full cleanup

---

## 26. Future improvements

Once this lab works, improve it with one of these extensions:

- add API keys and usage plans
- move to infrastructure as code with AWS CDK
- add contract versioning
- add schema registry for events
- add dead-letter or outbox-style handling for event publication failures
- replace simple bearer-token authorizer with Cognito or JWT authorizer

---

## 27. What you should be able to explain after finishing

You should be able to explain all of this in simple terms:

- what API Gateway does in this lab
- what the authorizer does
- why create and get use separate Lambdas
- why POST uses idempotency
- why validation exists at multiple layers
- why EventBridge is emitted after create
- how logs and traces help debugging
- what breaks when IAM permissions are wrong

If you cannot explain those clearly, you built it but you do not understand it yet.

---

## 28. Definition of done

This lab is done only if all of these are true:

- unauthorized request is blocked
- invalid request is rejected
- valid order is stored
- duplicate request with same idempotency key does not create a second order
- `OrderCreated` event is published
- existing order can be fetched
- missing order returns `404`
- structured logs are visible
- traces are visible
- you have broken at least two things and fixed them


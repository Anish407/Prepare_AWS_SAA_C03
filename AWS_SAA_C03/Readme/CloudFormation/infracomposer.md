# AWS Infrastructure Composer Lab: Design and Deploy a Serverless Order API

## Goal

This lab teaches you how to use **AWS Infrastructure Composer** to visually design AWS infrastructure and generate a deployable CloudFormation/SAM template.

You will build a small serverless order-processing architecture:

```text
Client
  |
  v
API Gateway HTTP API
  |
  v
Lambda Function
  |
  v
DynamoDB Orders Table
```

By the end of this lab, you should understand:

- What AWS Infrastructure Composer is used for
- How visual design becomes Infrastructure as Code
- How Composer relates to CloudFormation and SAM
- How to export a generated template
- How to deploy the generated template
- How to verify the deployed resources
- How to clean up the stack
- Where Composer is useful and where it is not enough

---

## Important Idea

AWS Infrastructure Composer is not a separate deployment engine.

It is a visual tool that helps you create or edit infrastructure templates.

The actual deployment still happens through:

- AWS CloudFormation
- AWS SAM CLI
- AWS CLI
- CI/CD pipeline
- CDK workflow, if you later migrate or rebuild the design in CDK

Think of it like this:

```text
Infrastructure Composer = visual designer
CloudFormation/SAM template = generated IaC output
CloudFormation/SAM CLI = deployment mechanism
```

---

## Architecture

```text
+----------------+
|    Client      |
+--------+-------+
         |
         | HTTPS request
         v
+------------------------+
| API Gateway HTTP API   |
+--------+---------------+
         |
         | invokes
         v
+------------------------+
| Lambda Function        |
| CreateOrderFunction    |
+--------+---------------+
         |
         | PutItem
         v
+------------------------+
| DynamoDB Table         |
| OrdersTable            |
+------------------------+
```

This is a realistic beginner architecture because many production serverless backends start with the same pattern:

```text
API -> Lambda -> DynamoDB
```

---

## Services Used

| Service | Purpose |
|---|---|
| AWS Infrastructure Composer | Visual design tool for creating the template |
| AWS CloudFormation | Deploys the infrastructure as a stack |
| AWS SAM | Simplifies serverless resources and deployment |
| API Gateway HTTP API | Public API endpoint |
| AWS Lambda | Runs backend business logic |
| DynamoDB | Stores order data |
| IAM | Grants Lambda permission to write to DynamoDB |
| CloudWatch Logs | Stores Lambda logs |

---

## Prerequisites

You need:

- AWS account
- IAM permissions to create CloudFormation stacks, Lambda, API Gateway, DynamoDB, IAM roles, and CloudWatch Logs
- AWS CLI configured
- SAM CLI installed if you deploy using SAM
- Basic understanding of CloudFormation templates

Check AWS CLI:

```bash
aws --version
aws sts get-caller-identity
```

Check SAM CLI:

```bash
sam --version
```

---

## Lab Flow

```text
Step 1: Open Infrastructure Composer
Step 2: Create a new project
Step 3: Add API Gateway
Step 4: Add Lambda
Step 5: Add DynamoDB
Step 6: Connect resources visually
Step 7: Review generated template
Step 8: Export template
Step 9: Add Lambda code
Step 10: Build and deploy
Step 11: Test API
Step 12: Inspect stack and resources
Step 13: Clean up
```

---

# Step 1: Open AWS Infrastructure Composer

You can access Infrastructure Composer in different ways:

1. AWS Infrastructure Composer console
2. CloudFormation console mode
3. AWS Toolkit for Visual Studio Code

For this lab, use the **AWS Console**.

Go to:

```text
AWS Console -> Infrastructure Composer
```

Or from CloudFormation:

```text
AWS Console -> CloudFormation -> Infrastructure Composer
```
<img width="834" height="428" alt="image" src="https://github.com/user-attachments/assets/b5b2eba1-99ca-455b-ba80-7464f1ea5820" />

---

# Step 2: Create a New Project

Choose:

```text
Create project
```
<img width="826" height="328" alt="image" src="https://github.com/user-attachments/assets/833d6235-2d1d-4ced-9dc3-e172f98901ad" />

Select a blank canvas.

Use YAML as the template format if asked.

Recommended project name:

```text
composer-order-api-lab
```

---

# Step 3: Add API Gateway

From the resource palette, search for:

```text
API Gateway
```

Choose an HTTP API or Serverless API card, depending on what the Composer UI shows.

Drag it onto the canvas.

Rename it to:

```text
OrderApi
```
<img width="836" height="561" alt="image" src="https://github.com/user-attachments/assets/3f2d4121-9ed0-4880-8e91-c802fa58cad2" />

Conceptually, this resource represents the public entry point into your backend.

---

# Step 4: Add Lambda Function

Search for:

```text
Lambda Function
```

Drag it onto the canvas.

Rename it to:

```text
CreateOrderFunction
```

Suggested configuration:

```text
Runtime: Python 3.12
Handler: app.lambda_handler
Memory: 128 MB
Timeout: 10 seconds
```

This Lambda function will receive an HTTP request and write an order item to DynamoDB.
<img width="970" height="562" alt="image" src="https://github.com/user-attachments/assets/b0cb2c12-3eb0-4bf4-9568-31c5603f7719" />

---

# Step 5: Add DynamoDB Table

Search for:

```text
DynamoDB Table
```

Drag it onto the canvas.

Rename it to:

```text
OrdersTable
```

Suggested table configuration:

```text
Partition key: orderId
Partition key type: String
Billing mode: PAY_PER_REQUEST
```
<img width="1141" height="569" alt="image" src="https://github.com/user-attachments/assets/ca160aa7-ec33-4c27-9620-acc44370c576" />

For a lab, on-demand billing is easier because you do not need to configure read/write capacity.

---

# Step 6: Connect the Resources

Now connect the resources visually:

```text
API Gateway -> Lambda Function -> DynamoDB Table
```

<img width="954" height="458" alt="image" src="https://github.com/user-attachments/assets/93a45960-6ddb-4d32-9e13-c117725e6ddb" />

The exact drag/connect behavior depends on the Composer mode and resource card.

The important result is:

1. API Gateway can invoke Lambda
2. Lambda has permission to write to DynamoDB
3. Lambda receives the table name as an environment variable

After connecting resources, inspect the generated template to see what Composer created.

---

# Step 7: Review the Generated Template

Switch from visual/canvas view to template view.

You should see a CloudFormation or SAM template.

A serverless SAM-style template may look similar to this:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Order API created using AWS Infrastructure Composer

Resources:
  OrdersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: orderId
          AttributeType: S
      KeySchema:
        - AttributeName: orderId
          KeyType: HASH

  CreateOrderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: python3.12
      Handler: app.lambda_handler
      CodeUri: src/create-order/
      MemorySize: 128
      Timeout: 10
      Environment:
        Variables:
          ORDERS_TABLE_NAME: !Ref OrdersTable
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref OrdersTable
      Events:
        CreateOrderApi:
          Type: HttpApi
          Properties:
            Path: /orders
            Method: POST

Outputs:
  ApiEndpoint:
    Description: API Gateway endpoint URL
    Value: !Sub "https://${ServerlessHttpApi}.execute-api.${AWS::Region}.amazonaws.com/orders"
```
<img width="881" height="555" alt="image" src="https://github.com/user-attachments/assets/94238f62-13f4-4f99-9ded-ac6b80ce639b" />

Your generated template may not look exactly the same. That is fine.

The key things to check are:

- Does the template contain an API resource?
- Does the template contain a Lambda function?
- Does the template contain a DynamoDB table?
- Does Lambda have permission to write to the table?
- Does Lambda know the table name?
- Is there an API route that invokes the function?

---

# Step 8: Export the Template

Export the generated template to your local machine.

Recommended folder structure:

```text
composer-order-api-lab/
  template.yaml
  src/
    create-order/
      app.py
  README.md
```

If you use local sync, Composer can keep the local template synchronized while you edit visually.
<img width="1138" height="428" alt="image" src="https://github.com/user-attachments/assets/6ce30531-e06b-4270-9fdf-eb5839ccdf5c" />


If you export manually, download the template and place it in the project folder as:

```text
template.yaml
```

---

# Step 9: Add Lambda Code

Create this folder:

```bash
mkdir -p src/create-order
```

Create file:

```text
src/create-order/app.py
```

Add this code:

```python
import json
import os
import uuid
from datetime import datetime, timezone

import boto3


dynamodb = boto3.resource("dynamodb")
orders_table = dynamodb.Table(os.environ["ORDERS_TABLE_NAME"])


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")

        customer_id = body.get("customerId")
        product_id = body.get("productId")
        quantity = body.get("quantity", 1)

        if not customer_id or not product_id:
            return response(400, {
                "message": "customerId and productId are required"
            })

        order = {
            "orderId": str(uuid.uuid4()),
            "customerId": customer_id,
            "productId": product_id,
            "quantity": int(quantity),
            "status": "CREATED",
            "createdAt": datetime.now(timezone.utc).isoformat()
        }

        orders_table.put_item(Item=order)

        return response(201, order)

    except Exception as ex:
        print(f"Error creating order: {ex}")
        return response(500, {
            "message": "Internal server error"
        })


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }
```

---

# Step 10: Build the Application

From the project root:

```bash
sam build
```

Expected result:

```text
Build Succeeded
```

If SAM complains about `CodeUri`, check that your template points to:

```yaml
CodeUri: src/create-order/
```

---

# Step 11: Deploy the Stack

Run:

```bash
sam deploy --guided
```

Suggested answers:

```text
Stack Name: composer-order-api-lab
AWS Region: eu-north-1
Confirm changes before deploy: Y
Allow SAM CLI IAM role creation: Y
Disable rollback: N
Save arguments to samconfig.toml: Y
```

SAM will package and deploy the CloudFormation stack.

After deployment, copy the API endpoint from the stack outputs.

---

# Step 12: Test the API

Use curl:

```bash
curl -X POST "https://YOUR_API_ID.execute-api.eu-north-1.amazonaws.com/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "customer-123",
    "productId": "product-456",
    "quantity": 2
  }'
```

Expected response:

```json
{
  "orderId": "generated-guid",
  "customerId": "customer-123",
  "productId": "product-456",
  "quantity": 2,
  "status": "CREATED",
  "createdAt": "2026-05-17T...Z"
}
```

---

# Step 13: Verify DynamoDB

Go to:

```text
AWS Console -> DynamoDB -> Tables -> OrdersTable
```

Open table items.

You should see the order inserted by the Lambda function.

You can also use AWS CLI:

```bash
aws dynamodb scan \
  --table-name YOUR_TABLE_NAME \
  --region eu-north-1
```

The physical table name may be different from `OrdersTable` because CloudFormation may generate a unique name.

You can find the table name in:

```text
CloudFormation -> Stack -> Resources
```

---

# Step 14: Check Lambda Logs

Go to:

```text
CloudWatch -> Log groups
```

Find the log group for the Lambda function.

It will look similar to:

```text
/aws/lambda/composer-order-api-lab-CreateOrderFunction-xxxx
```

Invoke the API again and confirm logs are created.

---

# Step 15: Inspect the CloudFormation Stack

Go to:

```text
CloudFormation -> Stacks -> composer-order-api-lab
```

Inspect these tabs:

| Tab | What to check |
|---|---|
| Events | Resource creation order and errors |
| Resources | Physical resources created by the stack |
| Outputs | API endpoint |
| Template | Final deployed template |
| Parameters | Input values if any |

This is important because Composer creates the template, but CloudFormation manages the actual deployed stack.

---

# Step 16: Clean Up

To delete the stack:

```bash
sam delete --stack-name composer-order-api-lab --region eu-north-1
```

Or use CloudFormation:

```bash
aws cloudformation delete-stack \
  --stack-name composer-order-api-lab \
  --region eu-north-1
```

Check that the stack is deleted:

```bash
aws cloudformation describe-stacks \
  --stack-name composer-order-api-lab \
  --region eu-north-1
```

If the stack no longer exists, cleanup is complete.

---

## What You Learned

You used AWS Infrastructure Composer to:

- Visually design a serverless architecture
- Generate an IaC template
- Understand the generated CloudFormation/SAM resources
- Export the template
- Add Lambda code
- Deploy using SAM/CloudFormation
- Test an API Gateway endpoint
- Verify DynamoDB data
- Inspect CloudWatch logs
- Delete the stack

---

## Exam-Relevant Lessons

For SAA-C03, remember:

1. Infrastructure Composer is a visual IaC design tool.
2. It creates CloudFormation or SAM templates.
3. It does not replace CloudFormation.
4. CloudFormation still deploys and manages the stack.
5. SAM is useful for serverless applications.
6. Composer can help visualize resource relationships.
7. Templates can be exported and used in CI/CD.
8. Composer is useful for learning, prototyping, and visual editing.
9. For complex production systems, CDK or hand-written CloudFormation may be cleaner.
10. Lambda-related resources may still need packaging/build steps outside Composer.

---

## Common Mistakes

### Mistake 1: Thinking Composer deploys everything by itself

Composer creates or edits the template.

Deployment still happens through CloudFormation, SAM, or another deployment workflow.

---

### Mistake 2: Ignoring the generated template

Do not only look at the visual diagram.

Always inspect the generated template because that is the real infrastructure definition.

---

### Mistake 3: Forgetting Lambda code packaging

Composer can define Lambda resources, but your Lambda code still needs to exist, be packaged, and be deployed correctly.

For SAM, this is usually handled by:

```bash
sam build
sam deploy
```

---

### Mistake 4: Not checking IAM permissions

Your Lambda needs permission to write to DynamoDB.

In SAM, this can be simplified using:

```yaml
Policies:
  - DynamoDBCrudPolicy:
      TableName: !Ref OrdersTable
```

In raw CloudFormation, you may need to explicitly define IAM roles and policies.

---

### Mistake 5: Treating Composer as a replacement for CDK

Composer is good for visualization and template generation.

CDK is better when you want reusable code, constructs, environment-specific configuration, and serious application infrastructure structure.

---

## Composer vs CloudFormation vs SAM vs CDK

| Tool | Best For |
|---|---|
| Infrastructure Composer | Visual design and learning resource relationships |
| CloudFormation | Native AWS IaC deployment engine |
| SAM | Serverless applications built on CloudFormation |
| CDK | Writing infrastructure using programming languages |

Simple rule:

```text
Use Composer to understand and draft.
Use CloudFormation/SAM to deploy.
Use CDK for serious reusable infrastructure code.
```

---

## Optional Extension Ideas

After the basic lab works, extend it with:

1. Add a GET /orders/{orderId} Lambda
2. Add request validation
3. Add structured JSON logging
4. Add CloudWatch alarms
5. Add X-Ray tracing
6. Add SQS after order creation
7. Add EventBridge order-created event
8. Add Cognito authorizer
9. Add WAF in front of API Gateway
10. Rebuild the same architecture manually in CDK

---

## Final Takeaway

Infrastructure Composer is excellent for seeing how AWS services connect and for generating a starting CloudFormation or SAM template.

But the real skill is not just dragging boxes on a canvas.

The real skill is understanding what template was generated, what IAM permissions were created, how the stack is deployed, how the resources behave, and how to troubleshoot when CloudFormation fails.

For your learning path, the best use of Composer is:

```text
Visualize -> Generate template -> Read template -> Deploy -> Break/fix -> Rebuild manually in CDK
```

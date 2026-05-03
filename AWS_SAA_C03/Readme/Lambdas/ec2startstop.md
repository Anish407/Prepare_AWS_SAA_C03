
# Lab Architecture
<img width="1672" height="941" alt="image" src="https://github.com/user-attachments/assets/f51bae02-41a6-47f3-8ba0-e4feca6a8346" />

# AWS Lab: Start and Stop EC2 using Manual EventBridge Events and EventBridge Scheduler

## 1. What this lab is about

This lab shows how to automatically **stop and start an EC2 instance** using AWS EventBridge, Lambda, and EC2 APIs.

The lab has two flows:

1. **Manual event-driven test**  
   You manually send a custom event to EventBridge using `PutEvents`. EventBridge matches the event using a rule and invokes a Lambda function. The Lambda function starts or stops the EC2 instance.

2. **Scheduled automation**  
   EventBridge Scheduler sends the same type of event on a schedule. The event goes through the same EventBridge rule and invokes the same Lambda function.

This is useful for learning:

- EventBridge custom events
- EventBridge event buses
- EventBridge rules
- EventBridge Scheduler
- Lambda as an automation worker
- IAM least privilege
- EC2 start/stop automation
- CloudWatch Logs troubleshooting
- Cost optimization for dev/test EC2 instances

---

## 2. Architecture

### Manual event test flow

```text
AWS CLI / Console / App
        |
        | PutEvents
        v
EventBridge Event Bus
        |
        | EventBridge Rule
        v
Lambda: ec2-power-manager
        |
        | StartInstances / StopInstances
        v
EC2 Instance
```

### Scheduled automation flow

```text
EventBridge Scheduler
        |
        | Sends event payload
        v
EventBridge Event Bus
        |
        | EventBridge Rule
        v
Lambda: ec2-power-manager
        |
        | StartInstances / StopInstances
        v
EC2 Instance
```

### Diagram

If you generated the architecture image, place it in your repository under:

```text
/images/eventbridge-ec2-start-stop-lab.png
```

Then reference it like this:

```md
![EventBridge EC2 Start Stop Lab](images/eventbridge-ec2-start-stop-lab.png)
```

---

## 3. Why this lab uses manual EventBridge events first

A common beginner mistake is to create a daily schedule immediately and then wait for the schedule to run.

That is slow and painful for testing.

Instead, this lab uses this pattern:

```text
Manual PutEvents test first -> one-time Scheduler test -> daily Scheduler automation
```

This gives you fast feedback.

You can prove each layer separately:

| Test | What it proves |
|---|---|
| Manual `PutEvents` | EventBridge bus, rule, Lambda target, Lambda code, IAM, and EC2 API work |
| One-time Scheduler | Scheduler can send the correct event payload |
| Daily cron schedule | Real automation works for morning start and evening stop |

---

## 4. Important concept: EventBridge Bus vs EventBridge Scheduler

EventBridge has different features that are easy to confuse.

| Feature | Purpose |
|---|---|
| EventBridge Event Bus | Receives events from applications, AWS services, or custom producers |
| EventBridge Rule | Matches events and sends them to targets |
| EventBridge Scheduler | Runs something at a specific time or on a recurring schedule |

In this lab:

- Manual testing uses `PutEvents` to send a custom event to the event bus.
- EventBridge rule matches the event.
- Lambda receives the event and starts/stops EC2.
- Later, EventBridge Scheduler sends the same kind of event automatically.

---

## 5. Lab resources

You will create:

| Resource | Purpose |
|---|---|
| EC2 instance | Test instance to start and stop |
| IAM role for Lambda | Allows Lambda to write logs and start/stop EC2 |
| Lambda function | Reads event payload and calls EC2 API |
| EventBridge rule | Matches EC2 power action events |
| Lambda target permission | Allows EventBridge to invoke Lambda |
| EventBridge Scheduler schedules | Sends start/stop events automatically |

---

## 6. Prerequisites

You need:

- AWS account or sandbox account
- AWS CLI configured
- IAM permissions to create EC2, Lambda, IAM roles, EventBridge rules, and Scheduler schedules
- Basic knowledge of AWS Lambda and IAM

Check your AWS identity:

```bash
aws sts get-caller-identity
```

Set environment variables to avoid repeating values:

```bash
export AWS_REGION=eu-north-1
export AWS_PROFILE=your-profile-name
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile $AWS_PROFILE)
```

If you are not using named profiles, remove `--profile $AWS_PROFILE` from the commands.

---

## 7. Step 1: Create or choose a test EC2 instance

Use a small EC2 instance, for example:

```text
Instance type: t3.micro or t2.micro
AMI: Amazon Linux 2023
Root volume: EBS-backed
```

Add this tag to the instance:

```text
Key: AutoSchedule
Value: true
```

For the first version of the lab, you can use a single hardcoded instance ID.

Store the instance ID:

```bash
export INSTANCE_ID=i-xxxxxxxxxxxxxxxxx
```

Verify the instance:

```bash
aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region $AWS_REGION \
  --profile $AWS_PROFILE \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags]' \
  --output table
```

---

## 8. Step 2: Create the Lambda execution role

Create a trust policy file:

```bash
cat > lambda-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
```

Create the role:

```bash
aws iam create-role \
  --role-name ec2-power-manager-lambda-role \
  --assume-role-policy-document file://lambda-trust-policy.json \
  --profile $AWS_PROFILE
```

Attach the basic Lambda logging policy:

```bash
aws iam attach-role-policy \
  --role-name ec2-power-manager-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  --profile $AWS_PROFILE
```

Create a least-privilege EC2 policy for this lab.

Replace the region, account ID, and instance ID automatically using environment variables:

```bash
cat > ec2-start-stop-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:StartInstances",
        "ec2:StopInstances"
      ],
      "Resource": "arn:aws:ec2:${AWS_REGION}:${ACCOUNT_ID}:instance/${INSTANCE_ID}"
    }
  ]
}
EOF
```

Create the policy:

```bash
aws iam create-policy \
  --policy-name ec2-start-stop-single-instance-policy \
  --policy-document file://ec2-start-stop-policy.json \
  --profile $AWS_PROFILE
```

Attach it to the Lambda role:

```bash
aws iam attach-role-policy \
  --role-name ec2-power-manager-lambda-role \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/ec2-start-stop-single-instance-policy \
  --profile $AWS_PROFILE
```

Store the Lambda role ARN:

```bash
export LAMBDA_ROLE_ARN=arn:aws:iam::${ACCOUNT_ID}:role/ec2-power-manager-lambda-role
```

Wait a few seconds for IAM propagation before creating the Lambda function.

---

## 9. Step 3: Create the Lambda function

Create a file named `lambda_function.py`:

```python
import json
import os
import boto3

REGION = os.environ.get("AWS_REGION", "eu-north-1")
ec2 = boto3.client("ec2", region_name=REGION)

VALID_ACTIONS = {"start", "stop"}


def lambda_handler(event, context):
    print("Received event:")
    print(json.dumps(event, default=str))

    detail = event.get("detail", event)

    action = detail.get("action")
    instance_ids = detail.get("instanceIds", [])

    if action not in VALID_ACTIONS:
        raise ValueError(f"Invalid action: {action}. Expected one of: {VALID_ACTIONS}")

    if not instance_ids:
        raise ValueError("instanceIds is required and cannot be empty")

    if action == "stop":
        response = ec2.stop_instances(InstanceIds=instance_ids)
        print(f"StopInstances response: {json.dumps(response, default=str)}")
        return {
            "statusCode": 200,
            "action": action,
            "instanceIds": instance_ids,
            "message": "Stop request submitted"
        }

    if action == "start":
        response = ec2.start_instances(InstanceIds=instance_ids)
        print(f"StartInstances response: {json.dumps(response, default=str)}")
        return {
            "statusCode": 200,
            "action": action,
            "instanceIds": instance_ids,
            "message": "Start request submitted"
        }
```

Package the function:

```bash
zip function.zip lambda_function.py
```

Create the Lambda function:

```bash
aws lambda create-function \
  --function-name ec2-power-manager \
  --runtime python3.12 \
  --role $LAMBDA_ROLE_ARN \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

---

## 10. Step 4: Create the EventBridge rule

Create an EventBridge rule that matches custom EC2 power action events.

```bash
aws events put-rule \
  --name ec2-power-action-rule \
  --event-pattern '{
    "source": ["lab.ec2.scheduler"],
    "detail-type": ["EC2 Power Action Requested"]
  }' \
  --state ENABLED \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

Get the Lambda ARN:

```bash
export LAMBDA_ARN=$(aws lambda get-function \
  --function-name ec2-power-manager \
  --region $AWS_REGION \
  --profile $AWS_PROFILE \
  --query 'Configuration.FunctionArn' \
  --output text)
```

Add the Lambda as a target for the rule:

```bash
aws events put-targets \
  --rule ec2-power-action-rule \
  --targets "Id"="1","Arn"="$LAMBDA_ARN" \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

Allow EventBridge to invoke the Lambda function:

```bash
aws lambda add-permission \
  --function-name ec2-power-manager \
  --statement-id allow-eventbridge-rule-invoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:${AWS_REGION}:${ACCOUNT_ID}:rule/ec2-power-action-rule \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

---

## 11. Step 5: Send a manual stop event using PutEvents

Create a stop event file:

```bash
cat > stop-instance-event.json <<EOF
[
  {
    "Source": "lab.ec2.scheduler",
    "DetailType": "EC2 Power Action Requested",
    "Detail": "{\"action\":\"stop\",\"instanceIds\":[\"${INSTANCE_ID}\"]}",
    "EventBusName": "default"
  }
]
EOF
```

Send the event:

```bash
aws events put-events \
  --entries file://stop-instance-event.json \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

Check the EC2 state:

```bash
aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region $AWS_REGION \
  --profile $AWS_PROFILE \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' \
  --output table
```

Expected state transition:

```text
running -> stopping -> stopped
```

Check Lambda logs:

```bash
aws logs tail /aws/lambda/ec2-power-manager \
  --follow \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

---

## 12. Step 6: Send a manual start event using PutEvents

Create a start event file:

```bash
cat > start-instance-event.json <<EOF
[
  {
    "Source": "lab.ec2.scheduler",
    "DetailType": "EC2 Power Action Requested",
    "Detail": "{\"action\":\"start\",\"instanceIds\":[\"${INSTANCE_ID}\"]}",
    "EventBusName": "default"
  }
]
EOF
```

Send the event:

```bash
aws events put-events \
  --entries file://start-instance-event.json \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

Check the EC2 state:

```bash
aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region $AWS_REGION \
  --profile $AWS_PROFILE \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' \
  --output table
```

Expected state transition:

```text
stopped -> pending -> running
```

---

## 13. Step 7: Create an EventBridge Scheduler execution role

EventBridge Scheduler needs permission to send events to the EventBridge event bus.

Create a trust policy:

```bash
cat > scheduler-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "scheduler.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
```

Create the role:

```bash
aws iam create-role \
  --role-name ec2-power-scheduler-role \
  --assume-role-policy-document file://scheduler-trust-policy.json \
  --profile $AWS_PROFILE
```

Create a policy that allows Scheduler to put events on the default event bus:

```bash
cat > scheduler-put-events-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "events:PutEvents",
      "Resource": "arn:aws:events:${AWS_REGION}:${ACCOUNT_ID}:event-bus/default"
    }
  ]
}
EOF
```

Create and attach the policy:

```bash
aws iam create-policy \
  --policy-name ec2-power-scheduler-put-events-policy \
  --policy-document file://scheduler-put-events-policy.json \
  --profile $AWS_PROFILE

aws iam attach-role-policy \
  --role-name ec2-power-scheduler-role \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/ec2-power-scheduler-put-events-policy \
  --profile $AWS_PROFILE
```

Store the role ARN:

```bash
export SCHEDULER_ROLE_ARN=arn:aws:iam::${ACCOUNT_ID}:role/ec2-power-scheduler-role
```

---

## 14. Step 8: Create one-time test schedules

Before creating daily schedules, create one-time schedules for testing.

Example:

```text
Stop instance: 5 minutes from now
Start instance: 10 minutes from now
```

EventBridge Scheduler uses schedule expressions. For one-time schedules, use the `at()` expression.

Example format:

```text
at(2026-05-03T15:30:00)
```

Use your local desired time or UTC carefully.

Create a one-time stop schedule:

```bash
aws scheduler create-schedule \
  --name ec2-one-time-stop-test \
  --schedule-expression "at(2026-05-03T15:30:00)" \
  --schedule-expression-timezone "Europe/Stockholm" \
  --flexible-time-window '{"Mode":"OFF"}' \
  --target "Arn=arn:aws:scheduler:::aws-sdk:eventbridge:putEvents,RoleArn=${SCHEDULER_ROLE_ARN},Input={\"Entries\":[{\"Source\":\"lab.ec2.scheduler\",\"DetailType\":\"EC2 Power Action Requested\",\"Detail\":\"{\\\"action\\\":\\\"stop\\\",\\\"instanceIds\\\":[\\\"${INSTANCE_ID}\\\"]}\",\"EventBusName\":\"default\"}]}" \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

Create a one-time start schedule:

```bash
aws scheduler create-schedule \
  --name ec2-one-time-start-test \
  --schedule-expression "at(2026-05-03T15:35:00)" \
  --schedule-expression-timezone "Europe/Stockholm" \
  --flexible-time-window '{"Mode":"OFF"}' \
  --target "Arn=arn:aws:scheduler:::aws-sdk:eventbridge:putEvents,RoleArn=${SCHEDULER_ROLE_ARN},Input={\"Entries\":[{\"Source\":\"lab.ec2.scheduler\",\"DetailType\":\"EC2 Power Action Requested\",\"Detail\":\"{\\\"action\\\":\\\"start\\\",\\\"instanceIds\\\":[\\\"${INSTANCE_ID}\\\"]}\",\"EventBusName\":\"default\"}]}" \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

> Note: The inline JSON escaping for Scheduler targets can be annoying. If this command becomes painful, create the schedule from the AWS Console first, then convert it to IaC later.

---

## 15. Step 9: Create daily schedules

After the one-time schedules work, replace them with daily cron schedules.

Example requirement:

```text
Start EC2 every weekday morning at 08:00 Europe/Stockholm
Stop EC2 every weekday evening at 19:00 Europe/Stockholm
```

### Daily morning start schedule

```bash
aws scheduler create-schedule \
  --name ec2-daily-start \
  --schedule-expression "cron(0 8 ? * MON-FRI *)" \
  --schedule-expression-timezone "Europe/Stockholm" \
  --flexible-time-window '{"Mode":"OFF"}' \
  --target "Arn=arn:aws:scheduler:::aws-sdk:eventbridge:putEvents,RoleArn=${SCHEDULER_ROLE_ARN},Input={\"Entries\":[{\"Source\":\"lab.ec2.scheduler\",\"DetailType\":\"EC2 Power Action Requested\",\"Detail\":\"{\\\"action\\\":\\\"start\\\",\\\"instanceIds\\\":[\\\"${INSTANCE_ID}\\\"]}\",\"EventBusName\":\"default\"}]}" \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

### Daily evening stop schedule

```bash
aws scheduler create-schedule \
  --name ec2-daily-stop \
  --schedule-expression "cron(0 19 ? * MON-FRI *)" \
  --schedule-expression-timezone "Europe/Stockholm" \
  --flexible-time-window '{"Mode":"OFF"}' \
  --target "Arn=arn:aws:scheduler:::aws-sdk:eventbridge:putEvents,RoleArn=${SCHEDULER_ROLE_ARN},Input={\"Entries\":[{\"Source\":\"lab.ec2.scheduler\",\"DetailType\":\"EC2 Power Action Requested\",\"Detail\":\"{\\\"action\\\":\\\"stop\\\",\\\"instanceIds\\\":[\\\"${INSTANCE_ID}\\\"]}\",\"EventBusName\":\"default\"}]}" \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

---

## 16. Recommended simpler Scheduler target option

The previous Scheduler commands publish events to the EventBridge event bus.

That is good for learning EventBridge properly.

But for a simpler production setup, Scheduler can invoke Lambda directly.

Direct flow:

```text
EventBridge Scheduler -> Lambda -> EC2 API
```

Event bus flow:

```text
EventBridge Scheduler -> EventBridge Bus -> EventBridge Rule -> Lambda -> EC2 API
```

For this lab, the event bus flow is intentionally used because it teaches custom events and rules.

---

## 17. Production-style improvement: use tags instead of hardcoded instance IDs

Hardcoding instance IDs is fine for version 1 of the lab.

But in real projects, tag-based automation is better.

Example tag:

```text
AutoSchedule = true
Environment = dev
```

Then the event can be:

```json
{
  "action": "stop",
  "filters": {
    "AutoSchedule": "true",
    "Environment": "dev"
  }
}
```

The Lambda can call `DescribeInstances`, find matching instances, and stop only the running ones.

Advantages:

- No hardcoded instance IDs
- Easier to add/remove instances
- Safer automation boundary
- Better for dev/test environments

IAM can also be restricted using resource tags.

Example concept:

```json
{
  "Effect": "Allow",
  "Action": [
    "ec2:StartInstances",
    "ec2:StopInstances"
  ],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "ec2:ResourceTag/AutoSchedule": "true"
    }
  }
}
```

---

## 18. Verification checklist

After sending a manual event or waiting for a schedule, verify these things:

### EventBridge `PutEvents` result

The command should return something like:

```json
{
  "FailedEntryCount": 0,
  "Entries": [
    {
      "EventId": "example-event-id"
    }
  ]
}
```

If `FailedEntryCount` is not `0`, the event was not accepted properly.

### Lambda logs

Check CloudWatch Logs:

```bash
aws logs tail /aws/lambda/ec2-power-manager \
  --follow \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

You should see:

```text
Received event
StopInstances response
```

or:

```text
Received event
StartInstances response
```

### EC2 instance state

```bash
aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region $AWS_REGION \
  --profile $AWS_PROFILE \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' \
  --output table
```

---

## 19. Troubleshooting

### Problem: `PutEvents` succeeds but Lambda does not run

Check:

- Event pattern source matches exactly: `lab.ec2.scheduler`
- Detail type matches exactly: `EC2 Power Action Requested`
- Lambda is added as target to the rule
- Lambda permission allows `events.amazonaws.com` to invoke it
- You are using the correct region

---

### Problem: Lambda runs but EC2 does not stop/start

Check:

- Lambda execution role has `ec2:StartInstances` and `ec2:StopInstances`
- IAM policy resource ARN has the correct region, account ID, and instance ID
- EC2 instance is EBS-backed
- You are targeting the correct instance ID
- The instance is in a valid state for the requested action

---

### Problem: Scheduler does not trigger

Check:

- Schedule is enabled
- Schedule expression timezone is correct
- Scheduler execution role trusts `scheduler.amazonaws.com`
- Scheduler execution role has `events:PutEvents`
- Target ARN and input are correctly configured
- You are looking in the correct AWS region

---

### Problem: JSON escaping is painful

This is normal.

Nested JSON inside Scheduler target input becomes ugly because the EventBridge `Detail` field itself must be a JSON string.

For learning, it is acceptable to create the Scheduler target in the AWS Console first.

Later, move it to CDK or CloudFormation for cleaner management.

---

## 20. Cost notes

Stopping an EC2 instance saves compute cost, but not all cost.

You may still pay for:

- EBS volumes
- Elastic IP if allocated and not attached/running depending on usage
- Snapshots
- CloudWatch Logs storage
- NAT Gateway if your lab uses one

For this lab, use a very small EC2 instance and delete resources after testing.

---

## 21. Cleanup

Delete Scheduler schedules:

```bash
aws scheduler delete-schedule \
  --name ec2-one-time-stop-test \
  --region $AWS_REGION \
  --profile $AWS_PROFILE

aws scheduler delete-schedule \
  --name ec2-one-time-start-test \
  --region $AWS_REGION \
  --profile $AWS_PROFILE

aws scheduler delete-schedule \
  --name ec2-daily-start \
  --region $AWS_REGION \
  --profile $AWS_PROFILE

aws scheduler delete-schedule \
  --name ec2-daily-stop \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

Remove EventBridge target:

```bash
aws events remove-targets \
  --rule ec2-power-action-rule \
  --ids 1 \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

Delete EventBridge rule:

```bash
aws events delete-rule \
  --name ec2-power-action-rule \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

Delete Lambda:

```bash
aws lambda delete-function \
  --function-name ec2-power-manager \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

Detach and delete IAM policies/roles:

```bash
aws iam detach-role-policy \
  --role-name ec2-power-manager-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  --profile $AWS_PROFILE

aws iam detach-role-policy \
  --role-name ec2-power-manager-lambda-role \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/ec2-start-stop-single-instance-policy \
  --profile $AWS_PROFILE

aws iam delete-role \
  --role-name ec2-power-manager-lambda-role \
  --profile $AWS_PROFILE

aws iam delete-policy \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/ec2-start-stop-single-instance-policy \
  --profile $AWS_PROFILE

aws iam detach-role-policy \
  --role-name ec2-power-scheduler-role \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/ec2-power-scheduler-put-events-policy \
  --profile $AWS_PROFILE

aws iam delete-role \
  --role-name ec2-power-scheduler-role \
  --profile $AWS_PROFILE

aws iam delete-policy \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/ec2-power-scheduler-put-events-policy \
  --profile $AWS_PROFILE
```

Terminate the test EC2 instance if you no longer need it:

```bash
aws ec2 terminate-instances \
  --instance-ids $INSTANCE_ID \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

---

## 22. What you should be able to explain after this lab

After completing this lab, you should be able to explain:

1. The difference between EventBridge event bus, rule, and Scheduler.
2. How a custom application can send events using `PutEvents`.
3. How EventBridge rules match events using `source` and `detail-type`.
4. How Lambda receives EventBridge event payloads.
5. How Lambda calls EC2 `StartInstances` and `StopInstances`.
6. Why Lambda needs an execution role.
7. Why Scheduler needs its own execution role.
8. How to test scheduled automation without waiting for the final daily schedule.
9. Why tag-based automation is better than hardcoded instance IDs.
10. Which EC2 costs remain even after stopping an instance.

---

## 23. Interview-style explanation

A strong explanation would be:

> I built an automation lab where EC2 instances can be stopped and started using EventBridge events. First, I manually published custom events using `PutEvents` to an EventBridge event bus. A rule matched events with source `lab.ec2.scheduler` and detail type `EC2 Power Action Requested`, then invoked a Lambda function. The Lambda function read the requested action from the event detail and called either `StartInstances` or `StopInstances` on the target EC2 instance. After proving the event-driven flow manually, I added EventBridge Scheduler to publish the same event format on a cron schedule. This allowed me to reuse the same rule and Lambda function for both manual testing and scheduled automation. IAM was restricted so Lambda could only start or stop the target instance, and Scheduler only had permission to publish events to the event bus.

---

## 24. Possible next improvements

Good follow-up improvements:

- Convert this lab to AWS CDK
- Add GitLab CI/CD deployment
- Use tags instead of instance IDs
- Add SNS notification after start/stop
- Add CloudWatch alarm for failed Lambda invocations
- Add dead-letter queue for failed EventBridge target delivery
- Store configuration in SSM Parameter Store
- Add structured JSON logging
- Add unit tests for Lambda event parsing

---

## 25. Final takeaway

The clean learning pattern is:

```text
Manual custom event -> EventBridge rule -> Lambda -> EC2
```

Then extend it to:

```text
EventBridge Scheduler -> EventBridge event bus -> EventBridge rule -> Lambda -> EC2
```

This makes the lab testable, realistic, and closer to how event-driven automation is designed in real AWS environments.


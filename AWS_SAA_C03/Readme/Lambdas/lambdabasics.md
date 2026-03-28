# AWS Lambda Notes — Fundamentals, Invocation Models, Use Cases, and Misuse

## Purpose

These notes summarize:

- **Lambda function vs Lambda service**
- **push-based vs poll-based invocation**
- **what the Lambda service actually does**
- **whether Lambda is multi-AZ**
- **common patterns and anti-patterns**

---

## 1. Lambda Function vs Lambda Service

This distinction is critical.

### Lambda function
A **Lambda function** is:

- your code
- the handler entry point
- runtime choice
- memory, timeout, environment variables
- IAM execution role
- other configuration

By itself, the function is just a deployable unit. It does not run on its own.

### Lambda service
The **Lambda service** is the managed AWS platform that:

- receives invocations
- integrates with triggers
- creates or reuses execution environments
- runs your code
- scales concurrency
- handles retries for async workloads
- polls supported event sources
- routes responses or failures
- manages security boundaries and execution isolation

### Simple mental model

- **Function = your code package**
- **Service = the AWS system that runs and manages it**

Without the Lambda service, your function is just code sitting in a zip or container image.

---

## 2. How Lambda Works at a High Level

At a high level, the Lambda service does this:

1. Receives an event or request
2. Decides how to process it based on the invocation model
3. Creates or reuses an execution environment
4. Loads your runtime and code
5. Passes the event to your handler
6. Collects the result or error
7. Applies retry / async delivery / failure handling rules if relevant

You do **not** manage servers, operating systems, or process lifecycles directly.

---

## 3. Invocation Models

There are three important models to remember.

### A. Synchronous invocation

The caller waits for the result.

Examples:

- API Gateway
- Function URL
- Application Load Balancer
- SDK `Invoke` with synchronous mode

### Flow

1. Client sends request
2. Lambda service receives it
3. Lambda service runs the function
4. Caller waits
5. Response is returned

### Characteristics

- request/response style
- caller is blocked until result comes back
- good for APIs and direct user-facing operations

### Example

A frontend calls `/basket/add` through API Gateway, and the Lambda returns success or failure immediately.

---

### B. Asynchronous invocation

The caller hands over the event and does **not** wait for the function result.

Examples:

- SNS
- S3 event notifications
- EventBridge
- some service-to-Lambda integrations

### Flow

1. Source pushes an event to Lambda
2. Lambda service accepts it
3. Lambda service queues it internally
4. Caller/source continues
5. Lambda later executes the function
6. Success/failure handling is applied

### Characteristics

- decoupled
- producer does not wait
- better for event-driven designs
- retries and destinations can be configured

### Important clarification

For async push-based services like **SNS**, Lambda does **not** poll SNS.

Instead:

- **SNS pushes to Lambda**
- Lambda service internally queues and processes the event

---

### C. Event source mapping

This is different from push-based async invocation.

Examples:

- SQS
- Kinesis Data Streams
- DynamoDB Streams
- Amazon MQ
- MSK / Kafka
- DocumentDB change streams

### Flow

1. You configure an event source mapping
2. Lambda service polls or consumes from the source
3. Lambda batches records if configured
4. Lambda invokes your function with those records
5. Retry/batch failure behavior is applied

### Important clarification

Your function does **not** sit there polling.

The **Lambda service** polls on your behalf.

---

## 4. Push vs Poll — The Correct Mental Model

This is where many people get confused.

### Push-based integrations
The source sends the event to Lambda.

Examples:

- SNS
- S3
- EventBridge
- API Gateway
- Function URL
- ALB direct Lambda target

### Poll-based integrations
The Lambda service reads from the source.

Examples:

- SQS
- Kinesis
- DynamoDB Streams
- Kafka / MSK
- Amazon MQ
- DocumentDB change streams

### The rule

- **Push model** → event is sent to Lambda
- **Poll model** → Lambda service fetches the event from the source

---

## 5. Does Lambda Always Poll?

No.

That would be the wrong conclusion.

### Correct answer

Lambda only polls for **event source mappings** such as:

- SQS
- Kinesis
- DynamoDB Streams
- Kafka
- MQ
- DocumentDB change streams

For push-based integrations like SNS or HTTP calls, there is **no polling of the external source** by your function.

---

## 6. Does Lambda Always Run Across Multiple Availability Zones?

### High-level answer
Lambda is a **regional managed service** and AWS designs it for **multi-AZ resilience**.

That means AWS can place and scale execution environments across multiple Availability Zones within a region.

### What this does **not** mean

It does **not** mean:

- your single invocation runs in all AZs at once
- you manually pick the AZ like EC2
- every function instance is permanently pre-running in every AZ

### Better mental model

Lambda is region-level infrastructure managed by AWS. AWS handles placement and resilience.

### Important VPC note

If your function is attached to **your VPC**, you should select subnets in **multiple AZs**.  
Otherwise you reduce the practical availability of your setup.

---

## 7. What the Lambda Service Actually Provides

Even in push-based models, you still need the Lambda service.

### The Lambda service provides:

- invocation intake
- event integration
- execution environment creation
- warm environment reuse
- runtime loading
- concurrency scaling
- internal async queueing
- retries and destinations
- permission enforcement
- execution role support
- isolation and security boundaries
- event source polling where applicable

### Key takeaway

The event source does **not** call your code directly.

It calls or sends to the **Lambda service**, and the Lambda service runs your code.

---

## 8. Good Use Cases for Lambda

The Pluralsight module is broadly correct here.

### 1. Data transformation
Use Lambda to transform data as it passes through the system.

Examples:

- transforming Kinesis records
- normalizing event payloads
- converting one message format into another

### 2. File processing
Use Lambda when files arrive in S3.

Examples:

- image resizing
- thumbnail generation
- PDF processing
- CSV validation or import
- media metadata extraction

### 3. Website backend logic / lightweight APIs
Lambda works well for backend logic behind:

- API Gateway
- Function URLs
- ALB integrations

Examples:

- basket operations
- account actions
- small microservice endpoints

### 4. Reacting to DynamoDB item changes
Use DynamoDB Streams + Lambda for downstream processing.

Examples:

- reporting
- notifications
- audit trails
- denormalized read model updates

### 5. IoT data processing
Use Lambda for event-driven processing from IoT services.

Examples:

- validating incoming telemetry
- enrichment
- writing processed results to DynamoDB or S3

### 6. Automated remediation
Lambda is great for security or ops automation.

Examples:

- revert an overly permissive security group
- tag noncompliant resources
- notify on policy drift

### 7. Scheduled tasks
Use EventBridge schedules to run Lambda on a timer.

Examples:

- daily Slack summary
- cleanup jobs
- scheduled reports
- periodic checks

---

## 9. Where Lambda Is a Bad Fit

This is where people misuse it.

### 1. Long-running processes
Lambda has a maximum execution time of **15 minutes**.

If the process is long, continuous, or computationally heavy, Lambda may be the wrong tool.

Better alternatives might include:

- ECS / Fargate
- AWS Batch
- EC2
- Step Functions + tasks
- **s3 invokes lambda and then lambda writes to the same s3 bucket (infinite loop)**
- containerized workers

---

### 2. Constant high-throughput workloads
If traffic is constantly high and predictable, Lambda can become expensive compared to always-on compute.

Example:

- a backend receiving thousands of requests per second at a steady rate all day

In such cases, ECS/Fargate or EC2 may be more cost-effective.

### Nuance
This is not saying Lambda cannot scale high. It can.  
The real question is **cost efficiency and workload shape**.

Lambda shines when there is spiky, bursty, or intermittent traffic.

---

### 3. Extra-large codebases
Huge function packages increase:

- cold start load time
- deployment complexity
- maintenance complexity

A giant Lambda package is usually a sign of poor decomposition.

---

### 4. Long-term in-memory state
Lambda is stateless from an application design perspective.

You cannot rely on:

- memory contents surviving
- the same execution environment being reused
- local state remaining available across future invocations

If state matters, store it externally.

Examples:

- DynamoDB
- ElastiCache / Redis
- S3
- RDS

---

## 10. Common Good Patterns

### A. Web application backend pattern
Frontend calls API Gateway, which routes to Lambda functions.

Example:

- `POST /basket/add` → one Lambda
- `POST /basket/remove` → another Lambda

This keeps handlers focused and small.

---

### B. File processing pattern
A file lands in S3, which triggers Lambda.

Example flow:

1. User uploads image to S3
2. S3 event triggers Lambda
3. Lambda creates thumbnail
4. Thumbnail is saved to S3
5. Metadata is stored in a database

This is one of the most natural Lambda patterns.

---

### C. Fan-out pattern
One event triggers multiple independent actions.

Typical design:

1. Something publishes to SNS or EventBridge
2. Multiple consumers react independently

Example:

- one Lambda archives image to S3
- one Lambda stores metadata in a DB
- one Lambda calls AI analysis

Benefits:

- parallel processing
- loose coupling
- simpler functions
- better fault isolation

---

## 11. Anti-Patterns and Misuse

These are the parts that matter most in real projects.

### A. Monolithic function

One giant Lambda doing everything is a bad design.

#### Problems
- larger package size
- slower cold starts
- too many responsibilities
- harder testing
- harder maintenance
- harder deployments
- harder least-privilege IAM design

#### Better approach
Use smaller focused functions or a clearer service boundary.

---

### B. Recursion

A Lambda triggers itself indirectly and keeps looping.

#### Example 1: S3 recursion
1. File uploaded to bucket
2. Lambda runs
3. Lambda writes output back to same triggering location
4. Write triggers Lambda again

#### Example 2: DynamoDB recursion
1. Table write creates stream record
2. Lambda processes record
3. Lambda writes back to same table in a triggering way
4. Same function fires again

#### Result
- runaway invocations
- excessive cost
- instability

#### Prevention ideas
- separate input and output buckets/prefixes
- filter events
- tag self-generated events
- write to different resources when possible

---

### C. Orchestration inside Lambda

Do not stuff a large multi-step workflow into one Lambda.

#### Why it is bad
- complex code
- tangled retry logic
- hard error handling
- tightly coupled services
- poor maintainability

#### Better approach
Use **AWS Step Functions** for workflow orchestration.

Lambda should usually do a focused unit of work, not coordinate a huge saga by itself.

---

### D. Chaining synchronous Lambdas

One Lambda calls another Lambda synchronously, which calls another, and so on.

#### Why it is bad
- higher latency
- more points of failure
- harder tracing/debugging
- cost increases because each function waits on the next
- the whole chain fails if one link fails

#### Better alternatives
- EventBridge
- SNS
- SQS
- Step Functions
- direct shared library for truly local logic

### Important nuance
Calling another Lambda is not always wrong.  
But deep synchronous chains as a main architecture pattern are usually bad design.

---

### E. Waiting sequentially for independent work

A Lambda calls service A, waits, then calls service B, waits, even though both are independent.

#### Example
- fetch data from Aurora
- then fetch data from DynamoDB
- then combine

If the two calls are independent, do them concurrently.

#### Why this matters
Lambda billing is tied to execution duration.  
Longer waiting means more latency and more cost.

#### Better approach
Use concurrency / async programming where possible.

---

## 12. Brutally Honest Rules for Real Projects

### Lambda is a good fit when:
- the work is event-driven
- execution time is short
- traffic is bursty or unpredictable
- each unit of work is small and isolated
- you want minimal server management

### Lambda is a bad fit when:
- the process is long-running
- the system is stateful in-memory
- traffic is constantly high and predictable
- the codebase is huge and tightly coupled
- you are trying to force orchestration into a handler

---

## 13. Best Short Answers to Remember

### What is the difference between Lambda function and Lambda service?
A Lambda function is your code and config.  
The Lambda service is the managed AWS platform that receives events, runs the function, scales it, retries it, and integrates it with other services.

### Does Lambda always poll?
No.  
Lambda only polls for event source mappings such as SQS, Kinesis, DynamoDB Streams, Kafka, MQ, and DocumentDB change streams.

### Does SNS require polling?
No.  
SNS pushes events to Lambda asynchronously. Lambda may queue the event internally, but it does not poll SNS.

### Is Lambda multi-AZ?
Lambda is a regional multi-AZ managed service, but you do not manage AZ placement directly like EC2. If you attach Lambda to a VPC, use subnets in multiple AZs.

### What is the biggest Lambda misuse?
Trying to turn Lambda into:
- a monolith
- a workflow engine
- a long-running worker
- a tightly chained synchronous service mesh

---

## 14. Interview-Safe Summary

AWS Lambda is a regional serverless compute service where AWS manages execution environments, scaling, integrations, retries, and invocation handling. Invocation models include synchronous, asynchronous, and event source mappings. Push-based sources such as SNS and API Gateway send events directly to Lambda, while event source mappings such as SQS and streams are polled by the Lambda service. Lambda is strong for event-driven processing, file handling, lightweight APIs, remediation, and schedules, but it is a poor fit for long-running, constantly busy, heavily stateful, or monolithic workloads.

---

## 15. Personal Study Notes

When learning Lambda, do not just memorize triggers. Understand:

- who sends the event
- who polls
- who queues
- who retries
- whether the caller waits
- where state lives
- what happens if one part fails
- whether Step Functions or queues are a better fit

That is the difference between passing an exam and actually designing systems correctly.

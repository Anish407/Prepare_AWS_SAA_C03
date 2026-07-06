# Amazon Data Firehose and Amazon Kinesis for SAA-C03

Amazon Kinesis is a family of AWS services for collecting, buffering, processing, and analyzing streaming data.

For the Solutions Architect Associate exam, focus on choosing the right streaming service for the workload:

- Use **Amazon Kinesis Data Streams** when applications need to process streaming data in near real time with custom consumers.
- Use **Amazon Data Firehose** when you want a managed delivery pipeline that loads streaming data into destinations such as Amazon S3, Amazon Redshift, Amazon OpenSearch Service, Splunk, or HTTP endpoints.
- Use **Amazon Managed Service for Apache Flink** when you need real-time stream analytics with Apache Flink.
- Use **Amazon Kinesis Video Streams** for streaming video from connected devices.

Older exam material may refer to **Kinesis Data Firehose**. The current service name is **Amazon Data Firehose**.

---

## Big Picture

Streaming data is data generated continuously by many sources.

Common examples:

- Application logs
- Clickstream events
- IoT sensor data
- Financial transactions
- Metrics and telemetry
- Security events

The main architectural question is:

> Do you need to process events yourself, or only deliver them to a destination?

If you need custom applications to read, process, replay, and fan out records, choose Kinesis Data Streams.

If you only need to collect, optionally transform, and deliver data to a storage or analytics destination, choose Amazon Data Firehose.

---

## Amazon Kinesis Data Streams

Amazon Kinesis Data Streams is a managed real-time streaming service.

It stores streaming records temporarily so that one or more consumers can read and process them.

### Key Concepts

| Concept | Meaning |
| --- | --- |
| Data stream | A stream made of one or more shards |
| Producer | Application or service that writes records into the stream |
| Consumer | Application or service that reads records from the stream |
| Record | Unit of data stored in the stream |
| Partition key | Determines which shard receives the record |
| Shard | Unit of read and write capacity |
| Sequence number | Unique identifier assigned to each record in a shard |
| Retention period | How long records remain available for reading |

### Shards

A shard is the scaling unit of Kinesis Data Streams.

In provisioned mode, each shard supports:

- Up to 1 MB/second write throughput
- Up to 1,000 records/second writes
- Up to 2 MB/second read throughput

If the workload needs more throughput, increase the number of shards.

Exam tip:

- Hot shards happen when too many records use the same partition key.
- Use a high-cardinality partition key to distribute traffic evenly.

### Capacity Modes

Kinesis Data Streams supports two capacity modes.

| Mode | Use Case |
| --- | --- |
| Provisioned | Predictable workloads where you manage shard count |
| On-demand | Variable or unpredictable workloads where AWS manages capacity |

Choose on-demand when the exam describes unknown traffic patterns or wants reduced operational overhead.

Choose provisioned when the exam describes predictable throughput and cost optimization.

### Retention and Replay

Kinesis Data Streams stores records for a retention period.

Important exam points:

- Default retention is 24 hours.
- Retention can be increased up to 365 days.
- Consumers can replay records within the retention period.
- This makes Kinesis Data Streams useful when multiple applications need to process the same event data independently.

### Consumers

Consumers read data from a Kinesis data stream.

Common consumers:

- AWS Lambda
- Amazon Data Firehose
- Custom applications using the Kinesis Client Library
- Amazon Managed Service for Apache Flink
- Amazon EC2 or container-based workers

### Shared Throughput vs Enhanced Fan-Out

| Consumer Type | Behavior |
| --- | --- |
| Shared throughput | Consumers share the shard read throughput |
| Enhanced fan-out | Each registered consumer gets dedicated read throughput per shard |

Use enhanced fan-out when multiple consumers need low-latency reads without competing for the same shard read capacity.

### Ordering

Kinesis Data Streams preserves ordering only within a shard.

Records with the same partition key go to the same shard, so ordering is preserved for that partition key.

Exam tip:

- If strict order is needed for one customer, device, account, or order ID, use that value as the partition key.
- Global ordering across all records is not guaranteed.

### Durability and Availability

Kinesis Data Streams is a managed regional service.

Records are replicated across multiple Availability Zones in the Region.

Use IAM policies, resource policies, VPC endpoints, and KMS encryption when the exam asks about secure ingestion and access control.

---

## Amazon Data Firehose

Amazon Data Firehose is a fully managed service for delivering streaming data to destinations.

It does not require you to manage consumers, shards, or custom delivery applications.

### Common Destinations

Amazon Data Firehose can deliver data to:

- Amazon S3
- Amazon Redshift
- Amazon OpenSearch Service
- Amazon OpenSearch Serverless
- Splunk
- HTTP endpoints
- Supported third-party observability and analytics services

For Amazon Redshift, Firehose first delivers data to Amazon S3, then loads it into Redshift using the Redshift `COPY` command.

### Data Sources

Firehose can receive data from:

- Direct PUT from applications
- AWS SDKs
- AWS services such as CloudWatch Logs, CloudWatch Metrics, and AWS IoT
- Kinesis Data Streams
- Amazon MSK

### Buffering

Firehose buffers incoming records before delivery.

It delivers data based on:

- Buffer size
- Buffer interval

This means Firehose is near real time, not instant per-record delivery.

Exam tip:

- If the requirement says "load streaming logs into S3 with minimal management," choose Firehose.
- If the requirement says "process each event immediately with custom logic and replay capability," choose Kinesis Data Streams.

### Transformation

Firehose can transform records before delivery.

Common options:

- Invoke AWS Lambda for transformation
- Convert record format, such as JSON to Apache Parquet or Apache ORC
- Compress data before writing to S3
- Encrypt data at rest

This is useful for building a data lake ingestion pipeline with less custom code.

### Delivery Semantics

Firehose uses at-least-once delivery behavior.

This means duplicate records can happen in some failure or retry scenarios.

Exam tip:

- Design downstream processing to be idempotent when duplicates matter.
- Do not choose Firehose when the workload requires exactly-once delivery.

### Error Handling

If delivery or transformation fails, Firehose can write failed records to an S3 backup or error location.

This is important for:

- Troubleshooting
- Reprocessing failed records
- Avoiding data loss

---

## Kinesis Data Streams vs Amazon Data Firehose

| Requirement | Best Choice | Why |
| --- | --- | --- |
| Custom real-time processing | Kinesis Data Streams | Consumers control processing logic |
| Replay events | Kinesis Data Streams | Records are retained and can be reread |
| Multiple independent consumers | Kinesis Data Streams | Consumers can read the same stream independently |
| Minimal management delivery to S3 | Amazon Data Firehose | Fully managed delivery |
| Delivery to Redshift | Amazon Data Firehose | Loads through S3 and Redshift COPY |
| Delivery to OpenSearch or Splunk | Amazon Data Firehose | Built-in destination support |
| Low-latency fan-out to many consumers | Kinesis Data Streams with enhanced fan-out | Dedicated throughput for consumers |
| Unknown or spiky stream throughput | Kinesis Data Streams on-demand or Firehose | Reduces capacity planning |
| Need shard-level control | Kinesis Data Streams provisioned | Shards control throughput |
| Need simple log ingestion pipeline | Amazon Data Firehose | Less code and less operations |

---

## Common Architectures

### Logs to S3 Data Lake

Use Amazon Data Firehose.

Flow:

```text
Applications / CloudWatch Logs -> Amazon Data Firehose -> Amazon S3
```

Optional additions:

- Lambda transformation
- Compression
- Format conversion to Parquet
- S3 backup for failed records
- Athena for querying S3 data

### Real-Time Application Processing

Use Kinesis Data Streams.

Flow:

```text
Producers -> Kinesis Data Streams -> Lambda / KCL Consumers -> DynamoDB / S3 / OpenSearch
```

Use this when the application must react to events quickly.

### Streams Plus Managed Delivery

Use Kinesis Data Streams with Firehose as one consumer.

Flow:

```text
Producers -> Kinesis Data Streams -> Custom Consumers
                               -> Amazon Data Firehose -> Amazon S3
```

This is common when you need both:

- Real-time custom processing
- Long-term archival in S3

---

## Choosing Between Kinesis, SQS, SNS, and EventBridge

| Service | Best For |
| --- | --- |
| Kinesis Data Streams | High-throughput streaming, ordering per partition key, replay, analytics |
| Amazon Data Firehose | Managed streaming delivery to storage and analytics destinations |
| Amazon SQS | Decoupling application components with message queues |
| Amazon SNS | Pub/sub notifications and fan-out |
| Amazon EventBridge | Event routing between AWS services, SaaS apps, and custom apps |

Exam shortcuts:

- Need replayable streaming data: Kinesis Data Streams.
- Need message queue and decoupling: SQS.
- Need push fan-out notifications: SNS.
- Need event bus and filtering rules: EventBridge.
- Need simple delivery of logs to S3 or OpenSearch: Firehose.

---

## Security

For both Kinesis Data Streams and Amazon Data Firehose, remember:

- Use IAM policies to control producers and consumers.
- Use AWS KMS for server-side encryption.
- Use TLS for data in transit.
- Use VPC endpoints when private connectivity from a VPC is required.
- Use CloudWatch metrics and logs for monitoring.

For Firehose, make sure the Firehose delivery role has permissions to write to the destination, such as S3, Redshift, OpenSearch, or a Lambda transformation function.

---

## Monitoring

Important monitoring areas:

- Incoming records
- Incoming bytes
- Write throttling
- Read throttling
- Iterator age for Kinesis consumers
- Delivery success or failure for Firehose
- Lambda transformation errors
- S3 backup or error records

Exam tip:

- High iterator age means a Kinesis consumer is falling behind.
- Write throttling can mean not enough shards, a hot partition key, or insufficient capacity.
- Firehose delivery failures usually point to destination permissions, destination availability, transformation errors, or data format issues.

---

## SAA-C03 Exam Traps

### Trap 1: Firehose Is Not for Custom Replay Processing

Firehose is for delivery.

If the question requires replay, multiple custom consumers, or shard-level processing, choose Kinesis Data Streams.

### Trap 2: Kinesis Data Streams Is Not the Simplest S3 Delivery Option

If the question only asks for ingesting logs into S3, Firehose is usually the simpler and more managed answer.

### Trap 3: Ordering Is Per Shard

Kinesis Data Streams does not guarantee global ordering.

Ordering is maintained for records with the same partition key because they are routed to the same shard.

### Trap 4: Shards Can Become Hot

A poor partition key can overload one shard while other shards are underused.

Choose partition keys with enough variety.

### Trap 5: Firehose Buffers Data

Firehose delivers data based on buffer size or interval.

If the requirement demands immediate per-record processing, Firehose is usually not the right answer.

### Trap 6: Redshift Delivery Uses S3 First

Firehose delivery to Redshift stages data in S3 and then uses the Redshift `COPY` command.

---

## Quick Review Questions

1. A company wants to collect web clickstream events and process them with three independent applications. Which service should be used?
   - Kinesis Data Streams.

2. A company wants to send application logs to S3 with minimal operational overhead. Which service should be used?
   - Amazon Data Firehose.

3. A consumer is falling behind when reading from a Kinesis data stream. Which metric is important?
   - Iterator age.

4. A workload needs ordering for all events from the same customer. What should be used as the partition key?
   - Customer ID.

5. A company needs to deliver streaming data into Redshift. What does Firehose use before loading Redshift?
   - Amazon S3 staging and the Redshift `COPY` command.

6. A Kinesis stream has uneven traffic and one shard is overloaded. What is the likely cause?
   - A hot partition key.

7. A workload needs dedicated read throughput for multiple Kinesis consumers. What feature helps?
   - Enhanced fan-out.

---

## One-Line Memory Aid

Use **Kinesis Data Streams** when you need to build streaming applications.

Use **Amazon Data Firehose** when you need to deliver streaming data to a destination.


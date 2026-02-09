# Amazon Simple Storage Service (S3) Overview

Amazon Simple Storage Service, commonly known as Amazon S3, is a secure, durable, and highly scalable object storage service provided by AWS.

It allows you to store and retrieve any amount of data from anywhere in the world using the internet, while paying a relatively low cost compared to traditional storage systems.

---

- [Storage classes](./storageclasses.md)
- [S3 replication](./S3Replication.md)
- [S3 lifecycle and versioning](./s3versioningandlifecycle.md)
- [S3 select](./s3select.md)
- [S3 bucket policies](./s3bucketpolicies.md)
- [S3 Encryption at rest](./s3encryption.md)

---

## What Amazon S3 Is

Amazon S3 is an object storage service.  
This means it stores data as objects rather than files or blocks.

Each object consists of:
- The data itself
- Metadata
- A unique object key used to retrieve the data

Amazon S3 is designed for massive scale and reliability, not for low-latency file system access.

---

## Global Service with Regional Resources

Amazon S3 is a global service, but the resources you create are regional.

Important points:
- Buckets are created in a specific AWS Region
- Data is stored within that Region by default
- The S3 service itself is globally accessible

This distinction is important for:
- Data residency requirements
- Latency considerations
- Cost control

---

## Scalability

Amazon S3 is designed to scale automatically.

- Unlimited number of buckets
- Unlimited number of objects
- No need to provision storage in advance

You can start with a few kilobytes of data and scale to terabytes or petabytes without changing your architecture.

---

## Object Size Limits

Each individual object in Amazon S3 has a maximum size limit.

- Maximum object size: 5 terabytes

This limit applies to a single object or file.  
Large files are typically uploaded using multipart upload.

---

## Supported File Types

Amazon S3 supports virtually any file type.

Examples include:
- Images
- Videos
- Documents such as PDF or Word files
- Log files
- Compressed archives
- Application artifacts

If a file can exist on a local system, it can be uploaded to Amazon S3.

---

## Durability and Availability

Amazon S3 is known for its extremely high durability and availability.

### Durability
- Designed for 99.999999999 percent durability
- Often referred to as eleven nines of durability
- Data is redundantly stored across multiple facilities within a Region

Data loss in S3 is extremely unlikely.

### Availability
- Designed for 99.95 to 99.99 percent availability
- Availability depends on the selected S3 storage class

Durability and availability are different concepts and should not be confused.

---

## What Amazon S3 Should Not Be Used For

Amazon S3 is not suitable for all use cases.

It should not be used for:
- Running an operating system
- Hosting a traditional database
- Low-latency transactional workloads

S3 is not a file system and does not support file locking or direct OS-level access.

---

## Common Use Cases

Amazon S3 is commonly used for:
- Data backups
- Archival storage
- Media hosting
- Data lakes
- Static website hosting
- Application artifacts and logs

It is often a foundational service in modern cloud architectures.

---

## Key Exam Points to Remember

- Amazon S3 is an object storage service
- It is a global service with regional resources
- Object size limit is 5 terabytes
- Designed for eleven nines of durability
- Provides up to 99.99 percent availability
- Not suitable for operating systems or databases

---

## Amazon S3 Buckets

Amazon S3 Buckets are containers used to store objects within the Amazon S3 service.  
Every object stored in Amazon S3 must belong to a bucket.

Buckets define:
- The AWS Region where data is stored
- The access control boundaries
- The namespace for stored objects

---

## Global Namespace and Regional Buckets

Amazon S3 uses a global namespace for bucket names.

Important points:
- All AWS accounts share the same S3 bucket namespace
- Bucket names must be globally unique
- Two AWS accounts cannot create buckets with the same name

Even though bucket names are global, buckets themselves are regional resources.
When you create a bucket, you must choose an AWS Region.

This distinction is critical for:
- Data residency
- Compliance
- Latency
- Cost management

---

## Bucket Durability and Data Storage

By default, objects stored in Amazon S3 Standard are redundantly stored across multiple facilities.

Key characteristics:
- Objects are stored across a minimum of three Availability Zones
- Each Availability Zone represents a physically separate data center
- Data is replicated automatically within the selected Region

This redundancy is what enables Amazon S3 to achieve extremely high durability.

---

## Handling Failures Automatically

Amazon S3 continuously monitors the health of stored objects.

If a storage device or Availability Zone failure occurs:
- S3 automatically detects the issue
- Lost redundancy is repaired by copying data to healthy locations
- This process happens automatically without user intervention

Users do not need to manage replication or recovery processes.

---

## Strong Read After Write Consistency

Amazon S3 provides strong read after write consistency for all operations.

This means:
- After creating or overwriting an object, all read requests immediately return the latest version
- Listing objects in a bucket immediately reflects all recent changes

There is no eventual consistency delay for:
- New object uploads
- Object overwrites
- Object deletes
- Object listings

This behavior simplifies application design and removes the need for retry logic due to stale reads.

---

## Bucket Naming Rules

Bucket names must follow specific naming rules.

Key rules to remember:
- Bucket names must be globally unique
- Bucket names must be between 3 and 63 characters
- Only lowercase letters, numbers, and hyphens are allowed
- Bucket names must start and end with a letter or number
- Bucket names cannot contain uppercase letters or underscores

These rules apply across all AWS accounts globally.

---

## Uploading Objects and HTTP Status Codes

Amazon S3 is accessed using REST APIs.

When an object is uploaded successfully:
- Amazon S3 returns an HTTP 200 status code

This confirms that the object upload operation completed successfully.

Understanding that S3 uses REST APIs is important for:
- Application integration
- Automation
- Debugging upload and download operations

---

## Summary

Amazon S3 Buckets act as the foundational containers for storing data in S3.
They use a globally shared namespace but exist as regional resources.

Buckets provide high durability through multi-AZ storage, strong read after write consistency, and automatic failure recovery.
Understanding bucket behavior is essential before working with S3 objects and permissions.

## Cross Account Replication and Encryption

This section explains how encryption works when S3 objects are replicated between AWS accounts.

### Scenario

- Source bucket in Account A
- Destination bucket in Account B
- Objects encrypted using AWS managed keys (SSE S3)
- S3 Replication enabled between the buckets

### How Replication Works with AWS Managed Keys

When an object encrypted with SSE S3 is replicated across accounts, the encrypted object is not copied byte for byte.

Instead, the following happens:

1. The object is stored encrypted in the source bucket in Account A
2. The S3 Replication service reads the object
3. AWS decrypts the object internally inside AWS infrastructure
4. The object is written to the destination bucket in Account B
5. The object is re encrypted using the destination account encryption configuration

No encryption keys are shared between accounts.

The destination account does not need access to the source account encryption keys.

### Important Mental Model

S3 replication copies data, not encryption keys.

Each account encrypts objects using its own keys.

### What the Destination Account Sees

From the destination account perspective:

- The object appears as a normal S3 object
- It is encrypted at rest using the destination account AWS managed key
- It can be accessed normally based on IAM permissions in the destination account

There is no dependency on the source account after replication is complete.

---

## Contrast with SSE KMS

When using SSE KMS instead of AWS managed keys, replication becomes more complex.

Additional requirements include:

- The source account KMS key policy must allow S3 Replication
- The replication role must be allowed to use the source KMS key
- A KMS key must exist in the destination account
- The replication configuration must specify the destination KMS key

If these permissions are not configured correctly, replication will fail.

### Why SSE KMS Is Different

With SSE KMS, encryption keys are customer controlled.

AWS does not automatically assume permission to decrypt data unless explicitly allowed by key policies.

---
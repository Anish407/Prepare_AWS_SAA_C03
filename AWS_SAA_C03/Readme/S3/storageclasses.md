# Amazon S3 Storage Classes – Complete Guide

## Overview

Amazon S3 (Simple Storage Service) provides multiple **storage classes** designed for different **access patterns, performance requirements, durability guarantees, and cost profiles**.

Every object stored in S3 **must belong to exactly one storage class**.
> So we dont assign storage classes to buckets, but to individual objects within those buckets.

Choosing the correct storage class is **one of the highest ROI cost-optimization decisions in AWS**, and it is heavily tested in AWS certification exams.

---

## Key Concepts (Must Know)

- **Storage class is set per object**, not per bucket
- **S3 is globally durable**, but most storage classes are **regionally resilient**
- **All storage classes provide high durability** (11 9s), unless explicitly stated otherwise
- Cost trade-offs involve:
  - Storage cost
  - Retrieval cost
  - Retrieval latency
  - Availability
  - Minimum storage duration

---

## Storage Classes for Frequently Accessed Data

### 1. S3 Standard (Default)

**Use Case**
- General-purpose workloads
- Frequently accessed data

**Examples**
- Websites
- Mobile applications
- Content distribution
- Gaming assets
- Big data analytics

**Characteristics**
- Availability: **99.99%**
- Durability: **99.999999999% (11 9s)**
- Data stored across **multiple AZs**
- No retrieval fees
- Highest cost among standard tiers

**When to use**
- If you are unsure, this is the safest default

---

### 2. S3 Express One Zone

**Use Case**
- Ultra-low latency workloads
- Data tightly coupled to compute in a specific AZ

**Examples**
- Machine learning training datasets
- High-performance computing
- Latency-sensitive analytics

**Characteristics**
- Stored in **single AZ**
- Single-digit millisecond access
- Higher performance than S3 Standard
- Less resilient than multi-AZ classes

**Trade-off**
- Higher performance
- Lower availability compared to multi-AZ storage

---

## Storage Classes for Infrequently Accessed Data

These classes reduce storage cost **at the expense of retrieval fees**.

### 3. S3 Standard-Infrequent Access (Standard-IA)

**Use Case**
- Long-lived but infrequently accessed data
- Immediate access required when needed

**Examples**
- Backups
- Disaster recovery data
- Older application data

**Characteristics**
- Multi-AZ redundancy
- Millisecond access
- Retrieval fee applies
- Lower storage cost than S3 Standard

---

### 4. S3 One Zone-Infrequent Access (One Zone-IA)

**Use Case**
- Infrequently accessed data where AZ failure is acceptable

**Examples**
- Secondary backups
- Easily reproducible data

**Characteristics**
- Stored in **single AZ**
- ~20% cheaper than Standard-IA
- Retrieval fee applies
- Lower resilience

**Important**
- Do NOT use for critical or irreplaceable data

---

## Storage Classes for Rarely Accessed / Archive Data

### 5. S3 Glacier Instant Retrieval

**Use Case**
- Long-term archive data
- Real-time access still required

**Examples**
- Compliance data
- Medical images
- Archived analytics data

**Characteristics**
- Millisecond retrieval
- Much cheaper than Standard
- Retrieval fee applies
- Minimum storage duration: **90 days**

---

### 6. S3 Glacier Flexible Retrieval

**Use Case**
- Archive data where retrieval time is flexible

**Examples**
- Historical logs
- Archived media
- Compliance audits

**Retrieval Options**
- Expedited (minutes)
- Standard (hours)
- Bulk (hours)

**Characteristics**
- Not real-time
- Cheaper than Instant Retrieval
- Minimum storage duration: **90 days**

---

### 7. S3 Glacier Deep Archive

**Use Case**
- Data that may never be accessed again

**Examples**
- Legal archives
- Long-term compliance storage
- Cold historical data

**Characteristics**
- Retrieval time: **up to 48 hours**
- Cheapest S3 storage option
- Minimum storage duration: **180 days**
- Never real-time access

---

## Cost Ordering (Most ? Least Expensive)

1. S3 Standard
2. S3 Express One Zone
3. S3 Standard-IA
4. S3 One Zone-IA
5. S3 Glacier Instant Retrieval
6. S3 Glacier Flexible Retrieval
7. S3 Glacier Deep Archive

---

## Storage Class for Unknown Access Patterns

### 8. S3 Intelligent-Tiering

**Problem it solves**
- You don’t know how frequently data will be accessed

**How it works**
- Automatically moves objects between tiers based on access patterns
- No performance impact
- No retrieval fees

**Tiers**
- Frequent Access (default)
- Infrequent Access (after 30 days of no access)
- Archive Instant Access (after 90 days of no access)

**Cost Trade-off**
- Small monthly monitoring fee
- Eliminates manual tuning errors

**Best For**
- New applications
- Unpredictable workloads
- Teams without strong cost governance

 Glacier = cheap but slow without nuance

---

## Practical Best Practices

- Use **Lifecycle Policies** to automate transitions
- Use **Intelligent-Tiering** for unknown workloads
- Always validate **retrieval time requirements**
- Monitor storage class distribution with **S3 Storage Lens**
- Treat One Zone classes as **cost optimizations with risk**

---

## Summary

S3 storage classes are not just about cost — they encode **availability, durability, and performance trade-offs**.

Choosing the correct storage class:
- Reduces cost
- Improves system reliability
- Prevents catastrophic recovery delays

This topic is foundational for **AWS Solutions Architect**, **Backend Architecture**, and **ML pipelines** (especially data lakes and training workflows).


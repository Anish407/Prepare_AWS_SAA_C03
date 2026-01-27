# AWS Savings Plans – EC2 Cost Optimization

Savings Plans are the modern and recommended way to reduce AWS compute costs.  
They are the successor to Reserved Instances and provide discounts in exchange for a time-based usage commitment.

Savings Plans apply automatically to eligible compute usage and are primarily used for long-running workloads.

---

## What Is a Savings Plan

A Savings Plan is a commitment to spend a fixed amount per hour on compute usage over a defined period.

Example:
You commit to spend $10 per hour for one year. AWS applies discounts automatically to matching compute usage.

Savings Plans are not tied to a specific instance by default. The level of flexibility depends on the plan type.

---

## Types of Savings Plans

There are three types of Savings Plans that are important for both exams and real-world architectures.

---

## Compute Savings Plan

### Characteristics
- Applies to any EC2 instance
- No restriction on:
  - Instance family
  - Instance size
  - AWS Region
  - Operating system
  - Tenancy
- Also applies to:
  - AWS Lambda
  - AWS Fargate

### Discount
- Up to approximately 66 percent compared to On-Demand pricing

### When to Use
- When workloads may change over time
- When flexibility is required
- When using a mix of EC2, Lambda, and Fargate

### Key Point
This plan offers the highest flexibility with slightly lower savings than EC2 Instance Savings Plans.

---

## EC2 Instance Savings Plan

### Characteristics
- Locked to:
  - A specific EC2 instance family
  - A specific AWS Region
- You can still change:
  - Instance size within the same family
  - Operating system
  - Tenancy

### Discount
- Up to approximately 72 percent compared to On-Demand pricing

### When to Use
- When EC2 workloads are predictable
- When instance family and region are stable
- When maximum cost savings are required

### Trade-Off
Less flexibility compared to Compute Savings Plans, but higher discounts.

---

## SageMaker Savings Plan

### Characteristics
- Applies only to Amazon SageMaker usage
- Covers:
  - Any instance family
  - Any instance size
  - Any AWS Region
  - Any operating system
  - Any tenancy

### Discount
- Up to approximately 64 percent compared to On-Demand pricing

### Important Limitation
- Compute Savings Plans do not apply to SageMaker
- SageMaker requires its own dedicated Savings Plan

### When to Use
- When running machine learning workloads using Amazon SageMaker
- When training or hosting ML models long term

---

## Commitment Periods

Savings Plans have only two valid commitment durations:
- One year
- Three years

Other durations such as two years or four years do not exist.

---

## Payment Options

Savings Plans offer the same payment options as Reserved Instances:
- No Upfront
- Partial Upfront
- All Upfront

The more you pay upfront, the greater the discount.

---

## Savings Plans vs Reserved Instances

Savings Plans are the modern replacement for Reserved Instances.

Reserved Instances:
- Are more rigid
- Are tied closely to specific instance attributes
- Still appear on exams but are being phased out

Savings Plans:
- Are more flexible
- Automatically apply to eligible usage
- Are recommended for new architectures

---

## Real-World Usage Guidance

Savings Plans are best suited for:
- Always-on workloads
- Long-running services
- Predictable baseline compute usage

Savings Plans are not ideal for:
- Short-lived workloads
- Infrequent or burst-only usage
- Highly unpredictable compute usage

---

## Exam-Oriented Summary

- Use Compute Savings Plans when flexibility is required
- Use EC2 Instance Savings Plans when workloads are stable and predictable
- Use SageMaker Savings Plans for machine learning workloads only
- Valid commitment periods are one year and three years
- Savings Plans are preferred over Reserved Instances for new workloads

---

## Final Notes

Savings Plans reduce cost by committing to usage over time, not by reserving specific instances.
They automatically apply discounts without requiring manual assignment.

Understanding the differences between the three plan types is critical for both certification exams and production architectures.

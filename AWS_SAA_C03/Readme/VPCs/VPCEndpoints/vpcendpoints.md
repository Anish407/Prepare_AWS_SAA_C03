# VPC Endpoints Deep Dive  
**Gateway Endpoints vs Interface Endpoints (AWS PrivateLink)**

---

## Introduction: Why VPC Endpoints Exist

By default, resources inside a VPC (EC2, ECS tasks, Lambda in VPC) access AWS services such as S3, SSM, or SQS using **public AWS service endpoints**.  
Even though these services belong to AWS, traffic still goes to **public IP addresses**, which means:

- Private subnets require a **NAT Gateway** for outbound access
- Traffic technically traverses the public internet (encrypted, but still public)
- Added cost, latency, and security exposure

**VPC Endpoints** allow private connectivity from a VPC to AWS services **without using the internet**, **without NAT**, and **without public IPs**.

---

## What Is AWS PrivateLink?

**AWS PrivateLink** is the technology that enables private connectivity to supported services using **Interface VPC Endpoints**.

Key characteristics:
- Traffic stays on the **AWS backbone**
- Uses **Elastic Network Interfaces (ENIs)** in your subnets
- Secured with **security groups**
- Uses **Private DNS** to override public AWS service hostnames

Not all AWS services use PrivateLink — which is why AWS provides **two types of VPC endpoints**.

---

## Types of VPC Endpoints

### 1. Gateway Endpoints

Gateway endpoints are **route-table based** endpoints.

Characteristics:
- No ENIs
- No security groups
- No PrivateLink
- Implemented using route table entries and AWS-managed prefix lists

Supported services:
- **Amazon S3**
- **Amazon DynamoDB**

Key properties:
- Free
- Highly scalable
- Simple
- Limited to S3 and DynamoDB

---

### 2. Interface Endpoints (PrivateLink)

Interface endpoints are **ENI-based** endpoints.

Characteristics:
- One or more ENIs per subnet
- Private IP addresses
- Secured with security groups
- Use Private DNS to rewrite service hostnames

Supported services include:
- SSM
- SQS
- SNS
- CloudWatch
- ECS, ECR, Secrets Manager, etc.

Key properties:
- Hourly + data processing cost
- Flexible
- Foundation for private production architectures

---

## Lab Goal

Build a **fully private VPC** where an EC2 instance:

- Has **no public IP**
- Has **no Internet Gateway**
- Has **no NAT Gateway**
- Can still:
  - Connect using **SSM Session Manager**
  - Access **Amazon S3** using a **Gateway VPC Endpoint**

---

## Architecture Overview

- **VPC**: `10.0.0.0/16`
- **Subnet**: 1 private subnet (`10.0.1.0/24`)
- **Routing**:
  - No IGW
  - No NAT
  - Local + endpoint routes only
- **Compute**: EC2 (private)
- **Endpoints**:
  - Interface: SSM
  - Gateway: S3

---

## Phase 0 — Base Network Setup

### Step 1: Create VPC
- CIDR: `10.0.0.0/16`
- Enable:
  - DNS resolution
  - DNS hostnames

### Step 2: Create Private Subnet
- CIDR: `10.0.1.0/24`
- Auto-assign public IP: Disabled

### Step 3: Route Table
- Associate with private subnet
- Routes:
  - `10.0.0.0/16 → local`
-  No Internet Gateway
- No NAT Gateway

---

## Phase 1 — EC2 + SSM (Interface Endpoints)

### Step 1: Create IAM Role
Attach policy:
- `AmazonSSMManagedInstanceCore`

Attach role as **instance profile**.

---

### Step 2: Launch EC2 Instance
- Subnet: private subnet
- Public IP: none
- Security Group:
  - Inbound: none
  - Outbound: allow TCP 443
- AMI: Amazon Linux 2 / AL2023

Expected at this stage:
- SSM (no endpoints yet)

---

### Step 3: Create SSM Interface Endpoints

Create the following interface endpoints:
- `com.amazonaws.<region>.ssm`
- `com.amazonaws.<region>.ec2messages`
- `com.amazonaws.<region>.ssmmessages`

Configuration:
- Subnet: private subnet
- **Private DNS enabled**
- Attach endpoint security group

---

### Step 4: Endpoint Security Group
Inbound rules:
- TCP 443
- Source: EC2 security group

Outbound:
- Allow all

---

### Step 5: Validate SSM
- Instance appears as **Managed** in Systems Manager
- Session Manager connection works

Key learning:
- SSM requires **outbound HTTPS**
- No inbound SSH
- No internet connectivity

---

## Phase 2 — S3 Access via Gateway Endpoint

### Step 1: Create S3 Gateway Endpoint
- create a gateway endpoint for S3
- Add s3 full access policy to the EC2 instance profile.

This adds S3 prefix-list routes automatically.

---



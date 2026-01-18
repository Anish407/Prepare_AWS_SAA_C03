# Lab 2: Connect to a Private EC2 from Your Laptop Using AWS CLI + SSM (and Download a File from S3)

## Goal

Use **AWS CLI on your local machine** to open an interactive shell to a **private EC2** using **SSM Session Manager** (no SSH, no port 22, no bastion), then download a file from **S3** from inside that session using the EC2 **instance role**.

### General flow
Private EC2
   ↓
NAT Gateway
   ↓
Internet Gateway
   ↓
Public AWS SSM endpoints
---

## How AWS Systems Manager (SSM) Works

AWS Systems Manager provides secure access to EC2 instances without inbound connectivity.

Key ideas:
- The **SSM Agent** runs on the EC2 instance.
- The agent establishes an **outbound HTTPS (443)** connection to AWS SSM endpoints.
- AWS acts as a **broker** between your client (CLI) and the instance.
- Access is controlled using **IAM**, not SSH keys.

Two IAM identities are involved:
1. **Your IAM identity** (local AWS CLI): must have `ssm:StartSession`
2. **EC2 instance role**: must have `AmazonSSMManagedInstanceCore`

---

## What we Build

- One **private EC2** (no public IP)
- EC2 instance role with:
  - `AmazonSSMManagedInstanceCore`
  - S3 read permissions
- Network connectivity for the instance to reach AWS services using:
  - NAT Gateway (simple), or
  - VPC Endpoints (production-style)

---

## Prerequisites

- AWS CLI installed and configured on your laptop
- Permissions to create EC2, IAM roles, and SSM sessions
- A test S3 bucket with a file to download

---

## Phase 0 — Local Machine Setup 

### Step 0.1: Verify AWS CLI
```bash
aws --version
aws sts get-caller-identity
```

### Step 0.2: Install Session Manager Plugin
```bash
session-manager-plugin --version
```
If not installed, install it for your OS and verify again.

---

## Phase 1 — Create IAM Role for EC2

1. IAM → Roles → Create role
2. Trusted entity: **EC2**
3. Attach policies:
   - `AmazonSSMManagedInstanceCore`
   - `AmazonS3ReadOnlyAccess` (or tighter custom policy)
4. Name the role: `EC2-SSM-S3Read-Role`

5. Create VPC 10.0.0.0.0/16
6. Create Subnets 10.0.1.0.0/24  and 10.0.2.0.0/24 
7. Create route tables
8. Create IGW and associate
9. Create NAT 
10. add routes in route tables for IGW and NAT

---

## Phase 2 — Launch Private EC2

- AMI: Amazon Linux 2023
- Subnet: Private subnet
- Public IP: Disabled
- Key pair: None
- Security Group: No inbound rules required
- Attach IAM role: `EC2-SSM-S3Read-Role`
- Tag Name: `private-ssm-ec2`

---

## Phase 3 — Network Connectivity

### Option A: NAT Gateway
- Private route table: `0.0.0.0/0 -> NAT Gateway`
- Public route table: `0.0.0.0/0 -> IGW`

### Option B: VPC Endpoints (No Internet)
1. Enable DNS hostnames and resolution on the VPC
2. Create Interface Endpoints:
   - `com.amazonaws.<region>.ssm`
   - `com.amazonaws.<region>.ssmmessages`
   - `com.amazonaws.<region>.ec2messages`
3. Create Gateway Endpoint for S3
4. Endpoint SG: allow inbound 443 from EC2 SG

---

## Phase 4 — Verify SSM Registration

Console:
Systems Manager => Fleet Manager => Managed nodes

Instance status should be **Online**.

---

## Phase 5 — Connect from Local AWS CLI

### Step 5.1: Get Instance ID
```bash
aws ec2 describe-instances   --filters "Name=tag:Name,Values=private-ssm-ec2"   --query "Reservations[].Instances[].InstanceId"   --output text
```

### Step 5.2: Start Session
```bash
aws ssm start-session --target i-xxxxxxxxxxxxxxxxx
```

---

## Phase 6 — Download File from S3 (Inside Session)

```bash
aws sts get-caller-identity
aws s3 ls s3://<bucket>/
aws s3 cp s3://<bucket>/<key> /tmp/<file>

```

---


## Key Takeaway

SSM allows you to manage private EC2 instances from your local machine using IAM and outbound-only connectivity, eliminating SSH keys, bastion hosts, and inbound access.

# AWS IAM Policy Types — Practical Guide (with Examples)

This document explains the main IAM “policy types” you’ll encounter in AWS, **where they apply**, **what they control**, and includes **copy-paste JSON examples** (mostly using S3) so you can test them in a lab.

> Core rule (memorize): **Explicit Deny wins. Always.**
> Access is granted only when an action is allowed and not blocked by any higher-level guardrails.

---

## Table of Contents

- [1) Identity-based policies](./IdentityBasedPolicies.md)
- [2) Resource-based policies TODO](#2-resource-based-policies)
- [3) Trust policies -TODO (role assume role policy)](#3-trust-policies-role-assume-role-policy)
- [4) Permissions boundaries TODO](#4-permissions-boundaries)
- [5) Service Control Policies (SCPs)  TODO](#5-service-control-policies-scps)
- [6) Session policies (STS)  TODO](#6-session-policies-sts)
- [7) ACLs (legacy)  TODO](#7-acls-legacy)
- [8) VPC Endpoint policies  TODO](#8-vpc-endpoint-policies)

---


## Summary of Policy Types
## IAM policy types — where they attach (quick cheat sheet)

- **Identity-based** = attached to **IAM identities**: **User**, **Group**, or **Role** (roles are what apps/services typically run as).
- **Resource-based** = attached to **resources**: e.g., **S3 bucket/object**, **SQS queue**, **SNS topic**, **KMS key**, etc.
- **Trust policy** = attached to an **IAM Role (trust relationship)**: defines **who/what can assume the role**.
- **Permissions boundary** = attached to an **IAM User or Role**: sets the **maximum** permissions that identity can ever have.
- **SCP (Organizations)** = attached to **Org Root / OU / Account**: sets the **maximum** permissions anyone in that account tree can have.
- **Session policy (STS)** = attached to an **assumed-role session** at runtime (not stored): further **restricts temporary credentials**.
- **Endpoint policy (VPC)** = attached to a **VPC Endpoint**: restricts what can be called **through that endpoint**.


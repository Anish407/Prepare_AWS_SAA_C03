# AWS IAM Policy Types — Practical Guide (with Examples)

This document explains the main IAM “policy types” you’ll encounter in AWS, **where they apply**, **what they control**, and includes **copy-paste JSON examples** (mostly using S3) so you can test them in a lab.

> Core rule (memorize): **Explicit Deny wins. Always.**
> Access is granted only when an action is allowed and not blocked by any higher-level guardrails.

---

## Table of Contents

- [1) Identity-based policies](./IdentityBasedPolicies.md)
- [2) Resource-based policies](./resourcebasedpolicy.md)
- [3) Trust policies -TODO (role assume role policy)](#3-trust-policies-role-assume-role-policy)

---


## Summary of Policy Types
## IAM policy types — where they attach (quick cheat sheet)

- **Identity-based** = attached to **IAM identities**: **User**, **Group**, or **Role** (roles are what apps/services typically run as). **Has no principal of its own**.
- **Resource-based** = attached to **resources**: e.g., **S3 bucket/object**, **SQS queue**, **SNS topic**, **KMS key**, etc. **Has a principal** (who can access it) defined inside the policy.**
- **Trust policy** = attached to an **IAM Role (trust relationship)**: defines **who/what can assume the role**. **"Action" is STS: sts:AssumeRole**



# AWS Outposts

## What problem does Outposts solve

AWS Outposts brings AWS managed infrastructure into an on premises data center.

It is designed for organizations that require:
- Very low latency access to on premises systems
- Data residency or regulatory compliance
- Consistent AWS APIs on premises

Outposts is not a cost optimization solution.

---

## High level architecture

Outposts uses a split control plane model.

## Control plane
- Runs in an AWS region
- Fully managed by AWS
- Includes service orchestration, IAM, monitoring, and management

## Data plane
- Runs on customer premises
- Includes EC2 instances, storage, and local networking

This separation is critical for exams and real world understanding.

---

## Supported services

Outposts supports a limited subset of AWS services such as:
- EC2
- EBS
- ECS with limitations
- RDS with limited engine support
- VPC networking

Not all AWS services are available on Outposts.

---

## When Outposts is the right choice

Outposts is the correct solution when:
- Workloads must run on premises
- Latency to local systems must be extremely low
- Data cannot leave the local environment
- AWS APIs and tooling are still required

Common industries:
- Finance
- Healthcare
- Government
- Manufacturing

---

## When Outposts is not the right choice

Do not use Outposts when:
- You only need private connectivity to AWS
- You want a cheaper hybrid solution
- You do not need AWS compute on premises

Better alternatives include VPN, Direct Connect, and Local Zones.

---

## Comparison with alternatives

Outposts versus Direct Connect:
- Direct Connect provides network connectivity only
- Outposts runs AWS compute on premises

Outposts versus Local Zones:
- Local Zones are AWS managed locations near metropolitan areas
- Outposts are installed in customer owned facilities

Outposts versus Snow family:
- Snow devices are temporary or mobile
- Outposts are permanent installations

---

## Limitations

- Requires physical installation and setup
- Long provisioning time
- High upfront and operational cost
- Limited service availability
- Requires network connectivity to an AWS region

---

## Cost considerations

Outposts pricing includes:
- Hardware
- Installation
- Ongoing maintenance

It is intended for large enterprises, not experimentation or learning labs.

---

## Exam strategy summary

- If the question mentions on premises workloads with AWS APIs, choose Outposts.
- If the question mentions strict data residency or regulatory requirements, choose Outposts.
- If the question mentions simple hybrid connectivity, Outposts is not the correct choice.

---

## Final takeaway

- Outposts exists to solve strict constraints, not convenience.

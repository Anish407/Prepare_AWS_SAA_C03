# AWS VPC Basics – What You *Must* Know 

This document covers the **core VPC fundamentals** you’re expected to know for:
- AWS certifications (SAA)

---

## What is a VPC?

A **VPC (Virtual Private Cloud)** is a **logically isolated private network** inside AWS where you run your resources (EC2, ECS, RDS, etc.).

Think of it as:
> “Your own data center network, but managed by AWS.”

---

## Private IP Ranges (RFC 1918)

A VPC **must** use one of the private IPv4 ranges below:

| Range | CIDR | Size | Common Usage |
|-----|------|------|-------------|
| `10.0.0.0 – 10.255.255.255` | `/8` | ~16M IPs | **Preferred for AWS** |
| `172.16.0.0 – 172.31.255.255` | `/12` | ~1M IPs | Legacy AWS default |
| `192.168.0.0 – 192.168.255.255` | `/16` | 65K IPs | Home / labs (avoid in AWS) |

---

## VPC CIDR Rules (Important)

When creating a VPC:

- CIDR **must be between `/16` and `/28`**
- CIDR **cannot be changed later** (you can only add secondary CIDRs)
- CIDR **must not overlap** with:
  - Other VPCs (if peering)
  - On-prem networks (VPN / Direct Connect)
- VPCs are **regional** (spans all AZs in the region)


## Creating a VPC
image

## Default VPC
- Every AWS account has a **default VPC** in each region
- Default VPC has:
    - A `/16` CIDR 
    - Public subnets in each AZ
    - An internet gateway attached
    - Default security group allowing all inbound traffic from within the VPC
    - Default NACL allowing all inbound and outbound traffic
    - Default route table with a route to the internet gateway
    - You can use the default VPC or create your own custom VPCs


   # Contents
- [Internet Gateways](./InternetGateway.md)

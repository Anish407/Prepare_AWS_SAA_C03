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
      <img width="1905" height="655" alt="image" src="https://github.com/user-attachments/assets/ef692b5c-a02a-486d-ad18-67a3cf44a3b9" />

    - Default route table with a route to the internet gateway
      <img width="1631" height="278" alt="image" src="https://github.com/user-attachments/assets/fa59939f-fbf3-4434-bc01-28d1d7ffa5c9" />

    - You can use the default VPC or create your own custom VPCs
<img width="808" height="467" alt="image" src="https://github.com/user-attachments/assets/b9a41fb9-22d6-4ae5-966c-234ee5bd6284" />


## Subnets
A subnet is just a slice of your VPC’s IP range (CIDR block) that you place inside exactly one Availability Zone (AZ).

- subnets are bound to a single AZ
- support ipv4 only , dual stack (both ipv4 and 6), ipv6 only
- subnets can communicate within the az or cross az but there is a cost involved when its cross az.

### Subnet types
Types

- public 
- private
- vpn only
- isolated

### AWS reserves 5 IP addresses for each subnets
VPC CIDR: 10.0.0.0/16
Subnet cidr: 10.0.0.0/24
- first one is for the network address 10.0.0.0
- 10.0.0.1 VPC router
- 10.0.0.1 VPC DNS server, also called the +2 address
- 10.0.0.3 Future use 
- 10.0.0.255 broadcast address

## CHATGPTs explanation
A subnet is just a slice of your VPC’s IP range (CIDR block) that you place inside exactly one Availability Zone (AZ). It’s the basic “network container” that AWS resources (ENIs → EC2/ECS/Lambda-in-VPC/RDS/ALB) actually attach to.

Think of it like:

- VPC = your private city
- Subnet = a neighborhood in one specific district (AZ)
- Route table = the roads leaving that neighborhood
- Security group = bouncer on each building
- NACL = checkpoint at the neighborhood entrance

## 1. Public subnet

Definition: subnet whose route table has a route like:

0.0.0.0/0 → Internet Gateway (igw-...)

## Key point: Resources in a public subnet are not automatically internet reachable. They need:

- a public IPv4 (or IPv6) and
- SG/NACL rules that allow it and
- the app listening on that port


## 2. Private subnet
Definition: subnet whose route table does not route to IGW. Commonly:
0.0.0.0/0 → NAT Gateway

Important: Private subnet instances can still reach the internet outbound via NAT (IPv4), or directly via egress-only IGW for IPv6.

## 3. Isolated subnet (a.k.a. “private isolated”)

Definition: no default route to IGW or NAT.
Route table has only VPC-local routes (and maybe VPC endpoints / TGW / VPN)

Typical workloads:
RDS (very common)
How they still talk to AWS services: VPC endpoints.

 - S3/Dynamo can use Gateway endpoints
 - Most others use Interface endpoints (PrivateLink)
 
## If you’re doing ECS Fargate / EKS:

- Don’t do /27 and then wonder why scaling dies.
- Common safe baseline per AZ for app subnets: /22 or /23 (depends on expected growth).
- For RDS isolated subnets: /26 or /27 is often fine.

## Subnets and high availability (AZ design)

- Because a subnet is single-AZ, “multi-AZ” always means:
- at least two subnets in different AZs for each tier

Example:

ALB: public subnet in A + public subnet in B
ECS service: private subnet in A + private subnet in B
RDS: isolated subnet group spanning A + B (RDS subnet group)

If you put everything in one AZ, you don’t have HA, no matter what your load balancer says.

### Common subnet gotchas

 - “My instance is in a public subnet but I can’t reach it”
   - No public IP, or SG blocked, or NACL blocked, or no route to IGW.
 - Private subnet with 0.0.0.0/0 → igw
   - You accidentally made it public.
 - NAT in a private subnet
   - Wrong. NAT must be in a public subnet with route to IGW.
 - One route table for all private subnets
   - Works, but if NAT is per-AZ (it should be), you want per-AZ route tables to keep traffic in-AZ and avoid cross-AZ data charges + failure coupling.
 - Subnet too small
   - Causes scaling failures, ENI attach failures, “insufficient free addresses”.
 - RDS in public subnets
   - Don’t. Just don’t. Even if it’s “locked by SG”, you’re increasing blast radius for no gain.

# Contents
- [Internet Gateways](./InternetGateways/InternetGateway.md)
- [Networking](./PrivateSubnets/networking.md)

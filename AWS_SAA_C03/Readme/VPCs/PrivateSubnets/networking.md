# VPC Networking Lab – Public & Private Subnets, IGW, NAT, SG vs ICMP

## Goal

Understand how:
- Public and private subnets work inside a VPC
- Internet Gateway (IGW) and NAT Gateway enable outbound internet access
- Security Groups control traffic **between EC2 instances**
- Routing alone is not enough for connectivity, we will not add the rules to allow ICMP or SSH in the security groups initially
- We will be able to see that ping from the public instance to the private instance will work and vice versa only after adding the appropriate security group rules


---
## Architecture Overview

- **VPC**: `10.0.0.0/16`
- **Public Subnet**: `10.0.1.0/24`
- **Private Subnet**: `10.0.2.0/24`

### Resources Created

- 1 Internet Gateway (IGW)
- 1 NAT Gateway (in public subnet)
- 2 Route Tables:
  - Public route table → IGW
  - Private route table → NAT Gateway
- 2 EC2 instances:
  - `ec2-public` (public subnet, public IP enabled)
  - `ec2-private` (private subnet, no public IP)
- 2 Security Groups:
  - `sg-public`: allows inbound SSH and ICMP from anywhere
  - `sg-private`: allows inbound SSH and ICMP only from `sg-public`
- SSM enabled for both instances for easy access by creating a role with SSM permissions.
- Both instances have outbound internet access via IGW and NAT Gateway respectively.

## Steps

### Create a role that allows us to connect to the instances using SSM
1. Go to IAM console
2. Create a new role and select AWS service EC2
<img width="789" height="546" alt="create_role1" src="https://github.com/user-attachments/assets/5d1e184c-c596-436e-9543-a4d608e2393a" />

3. Attach the AmazonSSMManagedInstanceCore policy, give it a name and save it.
   <img width="829" height="587" alt="create_role_ssm" src="https://github.com/user-attachments/assets/a8ce9302-64e1-4f75-b4d2-4b74ae24f9c7" />

---
### Create the VPC

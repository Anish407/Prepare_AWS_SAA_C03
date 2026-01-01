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

1. Go to the VPC console and create a new VPC with CIDR `
image

### Create Subnets
1. Create a public subnet with CIDR  10.0.1.0/24
image

2. Enable auto-assign public IPv4 address for the public subnet. This ensures that instances launched in this subnet automatically receive a public IP address.
image

3. Create a private subnet with CIDR  10.0.2.0/24
image
  - Note: No need to enable auto-assign public IP for the private subnet. Instances in this subnet will not have public IPs.

  ---
  ### Create and Attach Internet Gateway (IGW)
  1. Create an Internet Gateway
  image
  2. Attach the IGW to the VPC. This allows resources in the VPC to communicate with the internet.
  image

  ---
### Create NAT Gateway
1. Create the NAT Gateway in the public subnet. This allows instances in the private subnet to access the internet for updates, patches, etc.
 image
2. while creating the NAT gateway, we get 2 options 
   - Create a regional NAT gateway: This option creates a NAT gateway that is available in all Availability Zones within the selected region. It provides high availability and fault tolerance by automatically distributing traffic across multiple Availability Zones. In this case , we dont need to associate the
   NAT gateway with a specific subnet. Since it is regional, it can serve traffic from any subnet in the VPC.
   - Create a zonal NAT gateway: This option creates a NAT gateway that is available only in a specific Availability Zone. It is less expensive than a regional NAT gateway but does not provide the same level of availability and fault tolerance. In this option, we
    we need to associate the NAT gateway with a specific subnet within the selected Availability Zone.

    ---
### Create Route Tables

1. Create a public route table and associate it with the public subnet. 
image
   - Add a route to the Internet Gateway for internet-bound traffic. This allows instances in the public subnet to access the internet.
   image
2. Create a routetable for the private subnet and associate it with the private subnet. This allows instances in the private subnet to use this route table for routing decisions.
   image
  - Add a route to the NAT Gateway for internet-bound traffic. This allows instances in the private subnet to access the internet via the NAT Gateway.
   image

---

### Create Security Groups
1. Create 2 security groups
   - One for the public instance that we will create next
   - One for the private instance that we will create.

### Create EC2 Instances
1. Launch an EC2 instance in the public subnet with the following configurations:
   - AMI: Amazon Linux 2
   - Instance Type: t2.micro
   - Network: Select the VPC created earlier
   - Subnet: Select the public subnet
   - Auto-assign Public IP: Enable
   - Security Group: Attach the security group created for the public instance
   - IAM Role: Attach the IAM role created earlier for SSM access
   - Key Pair: NONE. since we are using SSM.

   image
2. Launch an EC2 instance in the private subnet with the following configurations:
   - AMI: Amazon Linux 2
   - Instance Type: t2.micro
   - Network: Select the VPC created earlier
   - Subnet: Select the private subnet
   - Auto-assign Public IP: Disable
   - Security Group: Attach the security group created for the private instance
   - IAM Role: Attach the IAM role created earlier for SSM access
   - Key Pair: NONE. since we are using SSM.
   image

   ---

### Testing Connectivity

1. Use SSM to connect to the public instance (`ec2-public`).
2. Run ping google.com to test internet connectivity from the public instance. It should succeed.
image
3. From the public instance, try to ping the private instance (`ec2-private`) using its private IP address. It should fail and timeout because we haven't added the necessary security group rules yet.
 image

 4. Now, use SSM to connect to the private instance (`ec2-private`).
    - Run ping google.com to test internet connectivity from the private instance. It should succeed via the NAT Gateway.
    - run ping to the public instance's private IP address. It should also fail and timeout because we haven't added the necessary security group rules yet.
   
### Update Security Groups to Allow ICMP Traffic
1. Update the security group of the public instance (`sg-public`) to allow inbound ICMP traffic from anywhere (
image
2. Update the security group of the private instance (`sg-private`) to allow inbound ICMP traffic only from the public instance's security group (`sg-public`).
3. Now , try pinging the private instance from the public instance again. It should succeed now.
 image
4. Try pinging the public instance from the private instance. It should also succeed now.
 image
5. Remove the private instance's security group ICMP rule and try pinging again from public to private. It should fail now.
 image
6. Add the ICMP rule back to the private instance's security group and try pinging again from public to private. It should succeed now.
 image


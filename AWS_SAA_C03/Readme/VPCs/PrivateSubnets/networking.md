# VPC Networking Lab – Public & Private Subnets, IGW, NAT, SG vs ICMP

## Diagram
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/7cd8e39c-eed4-4780-9a76-9bafe009cd8c" />

--- 
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
<img width="749" height="557" alt="create_vpc" src="https://github.com/user-attachments/assets/3f7ba646-0484-4fcc-a70d-d15e0ef5e08b" />

### Create Subnets
1. Create a public subnet with CIDR  10.0.1.0/24

<img width="802" height="553" alt="create_public_subnet" src="https://github.com/user-attachments/assets/1e03b982-83d2-47b5-8add-3e363ebcec9c" />

2. Enable auto-assign public IPv4 address for the public subnet. This ensures that instances launched in this subnet automatically receive a public IP address.

<img width="841" height="524" alt="enable_auto_assign_public_subnet" src="https://github.com/user-attachments/assets/051b4640-be4f-44b7-b26b-022df8d20694" />

3. Create a private subnet with CIDR  10.0.2.0/24

<img width="804" height="356" alt="Create_private_subnet" src="https://github.com/user-attachments/assets/558ddc41-c9f5-4c0c-a4c3-a0eae9a386e6" />

> [!TIP]
> No need to enable auto-assign public IP for the private subnet. Instances in this subnet will not have public IPs.

  ---
  ### Create and Attach Internet Gateway (IGW)
  1. Create an Internet Gateway
 <img width="833" height="415" alt="Create_igw" src="https://github.com/user-attachments/assets/a6af6318-b3fa-4d17-99af-adb0c60fb3fe" />

  2. Attach the IGW to the VPC. This allows resources in the VPC to communicate with the internet.
<img width="841" height="302" alt="8  Assign_igw_vpc" src="https://github.com/user-attachments/assets/b3336aa8-403c-4e4f-95e2-7925a542f2e3" />

  ---
### Create NAT Gateway
1. Create the NAT Gateway in the public subnet. This allows instances in the private subnet to access the internet for updates, patches, etc.
<img width="851" height="455" alt="11  create_nat" src="https://github.com/user-attachments/assets/6f0cd343-0c84-40a1-9775-b3a246292b4d" />

2. while creating the NAT gateway, we get 2 options 
   - Create a regional NAT gateway: This option creates a NAT gateway that is available in all Availability Zones within the selected region. It provides high availability and fault tolerance by automatically distributing traffic across multiple Availability Zones. In this case , we dont need to associate the
   NAT gateway with a specific subnet. Since it is regional, it can serve traffic from any subnet in the VPC.
   - Create a zonal NAT gateway: This option creates a NAT gateway that is available only in a specific Availability Zone. It is less expensive than a regional NAT gateway but does not provide the same level of availability and fault tolerance. In this option, we
    we need to associate the NAT gateway with a specific subnet within the selected Availability Zone.

    ---
### Create Route Tables

1. Create a public route table and associate it with the public subnet. 
<img width="848" height="441" alt="9  create_publicsubnet_rt" src="https://github.com/user-attachments/assets/8533b5bc-2c65-4b20-8744-996e02d24a99" />
<img width="844" height="389" alt="12  associate_privateRT_subnet" src="https://github.com/user-attachments/assets/8f4c3593-5279-484a-92cf-3ca82757d04d" />

   - Add a route to the Internet Gateway for internet-bound traffic. This allows instances in the public subnet to access the internet.
  <img width="869" height="353" alt="16  AssignRoute_igw_publicSubnet" src="https://github.com/user-attachments/assets/54e31678-a56e-4e2b-8381-c10677073bf6" />

2. Create a routetable for the private subnet and associate it with the private subnet. This allows instances in the private subnet to use this route table for routing decisions.
  <img width="849" height="401" alt="10  public_subnet_rt" src="https://github.com/user-attachments/assets/acaece7a-6ffd-45a7-a900-110955eac773" />

  - Add a route to the NAT Gateway for internet-bound traffic. This allows instances in the private subnet to access the internet via the NAT Gateway.
<img width="831" height="470" alt="15  AssignRoute_nat_privateSubnet" src="https://github.com/user-attachments/assets/dcb502f7-afb4-4ab9-a6cf-c10a5e78366b" />
<img width="843" height="371" alt="16  AssignRoute_nat_privateSubnet2" src="https://github.com/user-attachments/assets/a3bf4071-bc69-411e-842f-2603ef9e8f9b" />

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
<img width="605" height="477" alt="17  create_ec2" src="https://github.com/user-attachments/assets/97be6349-c530-4eb0-aca5-2a4a56fc434a" />
<img width="551" height="371" alt="18  create_ec2_ssm" src="https://github.com/user-attachments/assets/cf49610f-24fd-4874-a7da-aff296335fa4" />

2. Launch an EC2 instance in the private subnet with the following configurations:
   - AMI: Amazon Linux 2
   - Instance Type: t2.micro
   - Network: Select the VPC created earlier
   - Subnet: Select the private subnet
   - Auto-assign Public IP: Disable
   - Security Group: Attach the security group created for the private instance
   - IAM Role: Attach the IAM role created earlier for SSM access
   - Key Pair: NONE. since we are using SSM.
  <img width="559" height="449" alt="19  private_ec2" src="https://github.com/user-attachments/assets/7c3c3b3d-85b9-4503-a081-07c30da73952" />

3. So we should have 2 EC2 instances
<img width="668" height="269" alt="21  ec2" src="https://github.com/user-attachments/assets/3cb7ad75-44f9-4c7f-b0dd-df72edfecb1a" />


   ---

### Testing Connectivity

1. Use SSM to connect to the public instance (`ec2-public`).
   <img width="842" height="425" alt="22  public_ec2_test" src="https://github.com/user-attachments/assets/79712a47-6a64-4b15-9de9-609de0547c75" />

2. Run ping google.com to test internet connectivity from the public instance. It should succeed.
   <img width="554" height="241" alt="23  public_ec2_test" src="https://github.com/user-attachments/assets/9955972e-187d-487f-b30c-21a960bf1701" />

4. From the public instance, try to ping the private instance (`ec2-private`) using its private IP address. It should fail and timeout because we haven't added the necessary security group rules yet.
 <img width="425" height="81" alt="25  privateec2_ping_publicec2" src="https://github.com/user-attachments/assets/fa2a532d-f73e-4796-b61b-22ccce2c59d1" />


 5. Now, use SSM to connect to the private instance (`ec2-private`).
    - Run ping google.com to test internet connectivity from the private instance. It should succeed via the NAT Gateway.
      <img width="605" height="247" alt="28  ping_google_from_privateec2_working" src="https://github.com/user-attachments/assets/21be6f48-0f7a-4487-8cb4-720aea5aaa8d" />

    - run ping to the public instance's private IP address. It should also fail and timeout because we haven't added the necessary security group rules yet.
   
### Update Security Groups to Allow ICMP Traffic
1. Update the security group of the public instance (`sg-public`) to allow inbound ICMP traffic from anywhere
<img width="828" height="346" alt="31  ping_allowed_all" src="https://github.com/user-attachments/assets/ebe3bfc7-1c0c-4e50-b65a-595d634a8c7e" />

3. Update the security group of the private instance (`sg-private`) to allow inbound ICMP traffic only from the public instance's security group (`sg-public`).
   <img width="840" height="334" alt="32  ping_allowed_private_ec2_sg" src="https://github.com/user-attachments/assets/017763c7-7382-4fe7-9134-4d9b47bfef65" />

5. Now , try pinging the private instance from the public instance again. It should succeed now.
  <img width="416" height="200" alt="33  ping_working_from_private_sg" src="https://github.com/user-attachments/assets/6806f716-a4fe-4629-a1ff-258e4ffff40e" />

6. Try pinging the public instance from the private instance. It should also succeed now.
7. Remove the private instance's security group ICMP rule and try pinging again from public to private. It should fail now.
  <img width="691" height="433" alt="34  remove_privatesg_rule_public_sg" src="https://github.com/user-attachments/assets/bd1ab654-58cb-4aff-a189-08435025dc7e" />
  <img width="443" height="103" alt="35  ping stops working" src="https://github.com/user-attachments/assets/14959936-66be-490d-8876-fb6ba6b154d4" />

8. Add the ICMP rule back to the private instance's security group and try pinging again from public to private. It should succeed now.

## Key Takeaways

- Route tables control where traffic goes
- Security Groups control whether traffic is allowed



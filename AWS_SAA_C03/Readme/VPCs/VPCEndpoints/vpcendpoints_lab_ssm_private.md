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
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/56efc9d1-e892-4887-bbd8-177a890d1542" />

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
  <img width="1342" height="861" alt="1  createvpc" src="https://github.com/user-attachments/assets/8ea4d003-4389-4137-baee-b8993ad217d2" />



### Step 2: Create Private Subnet
- CIDR: `10.0.1.0/24`
- Auto-assign public IP: Disabled
  <img width="1481" height="818" alt="2 create_private_subnet" src="https://github.com/user-attachments/assets/c4dc9504-debc-4002-89d5-4d98b5850649" />


### Step 3: Route Table
- Create a route table for the subnet
  <img width="1806" height="682" alt="3 private_subnet_rt" src="https://github.com/user-attachments/assets/f05a2cfe-b660-4919-895a-d412cc8e1199" />

- Associate with private subnet
  <img width="1885" height="567" alt="4 private_rt_associate" src="https://github.com/user-attachments/assets/a43d4da8-26de-402c-a3fd-a58f26611f61" />

- Routes:
  - `10.0.0.0/16 → local`
- No Internet Gateway or NAT Gateway since we dont want any internet connectivity 


---

## Phase 1 — EC2 + SSM (Interface Endpoints)

### Step 1: Create IAM Role
<img width="1675" height="763" alt="5 createssmrole" src="https://github.com/user-attachments/assets/a4f297fe-d525-4ae7-9eaa-6ed3922be524" />

Attach policy:
- `AmazonSSMManagedInstanceCore`
  <img width="1668" height="782" alt="6 attach_ssm_policy" src="https://github.com/user-attachments/assets/34113481-5fc3-4d4a-a471-3693536d62ad" />
  <img width="1572" height="827" alt="7 create_role" src="https://github.com/user-attachments/assets/56b544e2-8ea3-4235-8d76-b889feafa090" />



---

### Step 2: Launch EC2 Instance
- Subnet: private subnet
  <img width="1832" height="810" alt="9 Create_ec2" src="https://github.com/user-attachments/assets/0e406387-6eeb-4055-b9cd-35049d4779dd" />

- Public IP: none
- Security Group:
  - Inbound: none
  - Outbound: allow TCP 443
- AMI: Amazon Linux 2 / AL2023
- Attach role as **instance profile**.
  <img width="1318" height="580" alt="10 create_ec2_settings" src="https://github.com/user-attachments/assets/a255becf-a5b9-48e3-ae94-2a8b10eeda3a" />

Expected at this stage:
- SSM (no endpoints yet). There is no public IP or any IGW in the VPC so the SSM agent cannot connect to the aws SSM endpoints. 
  <img width="1761" height="708" alt="11 SSM_agent_down" src="https://github.com/user-attachments/assets/d105dda0-aded-497e-98ef-c7de8f661e73" />
- So we will the interface endpoints to connect to SSM in the next section
---

### Step 3: Create SSM Interface Endpoints

Create the following interface endpoints:
- Go to the endpoints menu in VPC
  <img width="1908" height="752" alt="12 create_interface_endpoints1" src="https://github.com/user-attachments/assets/669d0caf-d5d2-409e-aa55-451817b8b479" />
We will create the following interface endpoints that are needed for the SSM agent to connect to the AWS SSM endpoints
- `com.amazonaws.<region>.ssm`
- `com.amazonaws.<region>.ec2messages`
- `com.amazonaws.<region>.ssmmessages`

### Steps
- Create the first interface endpoint for `com.amazonaws.<region>.ssm`
  <img width="1837" height="767" alt="13 create_interface_endpoints" src="https://github.com/user-attachments/assets/481f4de0-73d1-446d-951f-c5047f20c4c2" />
- <img width="1462" height="762" alt="14 create_interface_endpoints" src="https://github.com/user-attachments/assets/81a6e735-1a57-4b6e-9547-08f61e235d4a" />
- Select the private subnet from the menu
  <img width="1751" height="762" alt="15 create_interface_endpoints" src="https://github.com/user-attachments/assets/5f6ebba3-1028-4712-b125-38dcd51abdf0" />
- Now we need to create a security group for all the interface endpoints. This is how we will allow/deny the traffic for the interface endpoints. it’s to allow inbound to the endpoint ENI for the connection the EC2 initiates.
  <img width="1812" height="785" alt="19 ec2-ssm-sg" src="https://github.com/user-attachments/assets/305dbd73-3ae9-4546-9cc0-6dbd69cdb4e0" />
- EC2 SG outbound: allow TCP 443 to the destination or the interface endpoint. Outbound from ec2 -> inbound for interface endpoints
  <img width="1837" height="497" alt="22 ec2-ssm-sg" src="https://github.com/user-attachments/assets/ee91b5e9-7abf-45f5-b436-05cab8e15296" />

- When we click on create, we will get the below error which is expected.
  <img width="1821" height="868" alt="17 error_dns_hostname" src="https://github.com/user-attachments/assets/3515cb05-1466-4225-ae9c-df3652506dbe" />

> So to create a VPC endpoint we need to the below attributes on the VPC, otherwise we get the below error
  - DNS Support 
  - DNS hostnames
<img width="1821" height="868" alt="17 error_dns_hostname" src="https://github.com/user-attachments/assets/6c9100d3-a3f0-43e9-a208-d650f88a65ca" />

### Why `enableDnsHostnames` Must Be Enabled

An **Interface VPC Endpoint** is implemented internally as one or more **Elastic Network Interfaces (ENIs)** that AWS places inside your subnet. Each of these endpoint ENIs has a **private IP address** and also a **private DNS hostname** managed by AWS.

When **Private DNS** is enabled on an interface endpoint, AWS does not change how applications call services. Instead, it changes **what DNS returns**. A hostname such as `ssm.<region>.amazonaws.com`, which normally resolves to public AWS IP addresses, is overridden inside the VPC to resolve to the **private DNS names of the endpoint ENIs**. Those DNS names then resolve to the ENIs’ private IP addresses.

If `enableDnsHostnames` is set to **false**, the VPC is operating in a restricted DNS mode where AWS-managed DNS hostnames are not fully supported. In this mode, AWS cannot reliably associate DNS names with the endpoint ENIs, which means the DNS override required for Private DNS cannot be applied cleanly. The endpoint may exist at the networking level, but DNS cannot “point” service names to it.

Because Private DNS fundamentally depends on replacing AWS service hostnames with endpoint ENI hostnames, AWS requires `enableDnsHostnames = true`. In short: **if the VPC does not support hostnames, AWS cannot safely rewrite hostnames**.

---

### Why `enableDnsSupport` Must Be Enabled

The `enableDnsSupport` setting controls whether the VPC provides a **DNS resolver at all**. When it is enabled, instances in the VPC can query the Amazon-provided DNS resolver (the `.2` address in each subnet, such as `10.0.1.2`). This resolver is responsible for handling standard DNS lookups as well as AWS-specific DNS features.

When `enableDnsSupport` is set to **false**, the VPC effectively has no functional DNS resolver for AWS-managed name resolution. Instances may still have basic networking, but DNS queries to AWS service names cannot be resolved through the AmazonProvidedDNS mechanism.

Private DNS for interface endpoints is implemented entirely through the **VPC DNS resolver**. AWS intercepts DNS queries for service names like `ssm.<region>.amazonaws.com` and returns private endpoint addresses instead of public ones. If DNS support is disabled, this interception cannot occur. Allowing Private DNS in this state would result in a configuration that appears correct but does not function.

To prevent this silent failure scenario, AWS enforces that `enableDnsSupport` must be **true** before Private DNS can be enabled on any interface endpoint.

- Now after this is done. Create the other interface endpoints for  `com.amazonaws.<region>.ec2messages` and `com.amazonaws.<region>.ssmmessages` following the same steps
 <img width="1905" height="660" alt="21 all-interface-endpoints" src="https://github.com/user-attachments/assets/c4d7b811-f0d3-4e73-bf66-60d28fc3fa79" />
- 
- Reboot the EC2 instance
  <img width="1863" height="666" alt="23 ec2-reboot" src="https://github.com/user-attachments/assets/ac118cab-fa5b-411e-8278-8fcfcbe0d7c9" />
- Now the SSM agent will be up and runnign and we can connect to it from the console.(MIGHT NEED TO WAIT A BIT)
  <img width="1842" height="632" alt="24 ssm_agent_up" src="https://github.com/user-attachments/assets/da21c532-055d-4915-8d5c-29f97166469b" />
- If we ping google.com then the request will timeout since it cannot connect to the internet as we dont have any IGWs or configuration to allow internet connectivity.
  <img width="583" height="178" alt="25 no_internet_access" src="https://github.com/user-attachments/assets/1b324e1b-91a9-4d58-8aa3-558c5ed44563" />

> So the interface endpoints are working and we can now connect to the instance without an internet gateway, NAT gateway or any public ips.

---

## Phase 2 — S3 Access via Gateway Endpoint
### Step 1: Prepare S3 bucket that we will connect using gateway endpoints
- Create an S3 bucket and upload a file that will be read using gateway endpoints
  <img width="1547" height="805" alt="26 create_bucket" src="https://github.com/user-attachments/assets/3f620f9b-fe0b-4544-8bda-e2dc9addf0a8" />
  <img width="1870" height="560" alt="27 upload_text_file" src="https://github.com/user-attachments/assets/b4878a30-ee3c-41bb-8538-017fbe025e0d" />

### Step 2: Create S3 Gateway Endpoint
- create a gateway endpoint for S3. The process is similar to the interface endpoints but we dont need any security groups or extra networking since it works based on route tables. We just select the subnet and the route table and select S3 and click create
  <img width="1657" height="347" alt="34 endpoints_list" src="https://github.com/user-attachments/assets/cff47f1a-27b2-42d0-9a7d-a898c86411aa" />

- Add s3 full access policy to the EC2 instance profile. At present the Ec2 instance profile can only connect to SSM, so we add a permission that will allow it to read from the s3 bucket. I just granted it full access for the lab.
  <img width="1861" height="787" alt="28 add_s3_permissions" src="https://github.com/user-attachments/assets/ff218ffb-858f-4e8b-be87-fd30b61aae10" />

- Add rule in the ec2 security group since EC2 must be allowed to open an outbound TCP connection to S3 on 443. I allowed all ports for the lab. This means that the EC2 instance is allowed to initiate HTTPS connections to any IP address
  <img width="1837" height="497" alt="22 ec2-ssm-sg" src="https://github.com/user-attachments/assets/4b44e805-db8d-4437-bd09-9a80a720a7a6" />
- Now if we try to list the s3 buckets or copy the file we uploaded to the s3
  <img width="917" height="445" alt="image" src="https://github.com/user-attachments/assets/a27a9f8c-4c8a-4f55-9393-d06efde2ed14" />

---

## Key Takeaways

- Gateway endpoints are routing-based and limited to S3 and DynamoDB
- Interface endpoints are ENI-based and use Private DNS
- SSM works without inbound access or internet connectivity
- NAT Gateways are not required for private AWS architectures by default


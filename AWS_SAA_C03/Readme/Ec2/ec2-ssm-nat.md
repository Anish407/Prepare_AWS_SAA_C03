# Lab 2: Connect to a Private EC2 from Your Laptop Using AWS CLI + SSM (and Download a File from S3)

## Goal

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/b52bb08d-c6d8-4bbc-acbf-b82205a5748e" />

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
- AWS acts as a **broker** between your client (CLI) and the instance. So we never connect to the EC2 directly
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
  - VPC Endpoints (production-style) (NEXT LAB)

---

## Phase 0 — Local Machine Setup 

### Step 0.1: Verify AWS CLI
```bash
aws --version
aws sts get-caller-identity
```

### Step 0.2:
[Install Session Manager Plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/install-plugin-windows.html)

```bash
session-manager-plugin --version
```
If not installed, install it for your OS and verify again.

---

## Phase 1 — Create IAM Role for EC2

1. IAM → Roles → Create role
   <img width="1771" height="759" alt="1 create_role" src="https://github.com/user-attachments/assets/009f05bf-4524-469b-aef1-5793bdd89ec5" />
2. Attach policies:
   - `AmazonSSMManagedInstanceCore`
   <img width="1881" height="781" alt="2 add_ssm_permission" src="https://github.com/user-attachments/assets/bce4b88a-3997-4b34-87ec-838ca13a7b32" />

3. Name the role: `ec2-ssm` or anything that you will remember.
   <img width="1856" height="707" alt="3 role_name" src="https://github.com/user-attachments/assets/aeb93a6e-9168-43b5-b991-e671102df319" />

4. Create VPC 10.0.0.0.0/16
   <img width="1862" height="543" alt="4 create_vpc" src="https://github.com/user-attachments/assets/8240d95a-0921-4270-a779-5100b030980f" />

5. Create Subnets 10.0.1.0.0/24  and 10.0.2.0.0/24
   <img width="1583" height="810" alt="5 create_subnet" src="https://github.com/user-attachments/assets/e127822e-854a-4d7b-84a6-b2f23f6937b3" />
   Create 1 more subnet and make it private and dont enable public IP addresses on it. **Check other labs**
6. Create route tables
   - Public Route table:
     <img width="1841" height="707" alt="6 create_public-RT" src="https://github.com/user-attachments/assets/03f84b3e-3df3-476d-a7ca-e5b5682bb006" />
   - Private route table:
     <img width="1855" height="712" alt="7 private_rt" src="https://github.com/user-attachments/assets/23b0e25a-ff8a-43e0-963d-30bd486c85ac" />

 > Associate the public route table with the public subnet and the private route table with the private subnet. Click on Subnet associations and assign
8. Create Internet gateway
   <img width="1670" height="645" alt="8 create_igw" src="https://github.com/user-attachments/assets/c7183fd7-ddcd-4eeb-83bf-50977504bfb5" />

9. IGW associate with VPC.
    <img width="1762" height="560" alt="10 attach_igw" src="https://github.com/user-attachments/assets/46798efa-9894-4d13-bf56-321432811087" />
   
12. Create NAT
    <img width="1666" height="811" alt="9 create_nat" src="https://github.com/user-attachments/assets/5d90f337-0b74-423e-95c7-a562d0644a5c" />

13. add routes in route tables for IGW and NAT
    - Add route for IGW in public subnets route table
      <img width="1827" height="526" alt="11 add_igw_rule" src="https://github.com/user-attachments/assets/ce2810c7-0c78-4156-a94e-8c2f49bb91d7" />
    - Add route for the NAT in the private subnets route table
      <img width="1817" height="455" alt="12 add-private-subnetrt-nat" src="https://github.com/user-attachments/assets/bedce3f1-6a9d-47a6-9d4b-e4d289a1df1e" />

---

## Phase 2 — Launch Private EC2

- AMI: Amazon Linux 2023
- Subnet: Private subnet
- Public IP: Disabled
- Key pair: None
- Security Group: No inbound rules required
- Attach IAM role: `EC2-SSM-S3Read-Role`
- Tag Name: `private-ssm-ec2`

  <img width="1825" height="812" alt="13 create-ec2" src="https://github.com/user-attachments/assets/323c54c1-95e8-4118-9561-597ffd93e7de" />

  <img width="1490" height="812" alt="14 create-ec2" src="https://github.com/user-attachments/assets/21294183-fd15-472b-8278-8815994a5af1" />

  <img width="1252" height="516" alt="15 create_ec2_instanc_profile" src="https://github.com/user-attachments/assets/8a362b5c-6266-4fb5-b062-f7f7600c53f9" />


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

> **In this lab, we choose Option A, Option B will be part of another lab, where we wont use an IGW or NAT but rely on interface endpoints to connect the SSM agent and the AWS SSM service**

---

## Phase 4 — Verify SSM Registration

Console:
Systems Manager => Fleet Manager => Managed nodes
 <img width="1661" height="487" alt="20 fleet_manager" src="https://github.com/user-attachments/assets/84b2df0a-fb24-4e1e-9bff-5d3091216fec" />

Instance status should be **Online**. We can also verify this from the console
 <img width="1800" height="617" alt="19 ssm_agent_working" src="https://github.com/user-attachments/assets/6da4483f-d571-4643-825d-eb8e639b6e0e" />

---

## Phase 5 — Connect from Local AWS CLI
### Step 5.1: To connect to the EC2 instance from our local machine we need to install the SSM plugin for windows.
   - We also need to configure a profile that will enable us to connect with the AWS services. Go to IAM and security credentials and create access keys.
     <img width="1883" height="718" alt="16 create_new_access-keys" src="https://github.com/user-attachments/assets/0c9eb73e-218a-46fb-b363-86857a676bec" />
     <img width="1517" height="787" alt="17 create_access_keys" src="https://github.com/user-attachments/assets/ee81ea18-855c-4ade-b23c-88541a0fc11c" />
   - Open powershell and run the below command. Enter the access key and secret when prompted
     ```
     aws configure --profile lab1
     ```
     <img width="1016" height="188" alt="18 configure_profile" src="https://github.com/user-attachments/assets/d415a524-f03b-445c-a5cd-fd971538e2c6" />


### Step 5.1: Get Instance ID
```bash
aws ec2 describe-instances   --filters "Name=tag:Name,Values=private-ssm-ec2"   --query "Reservations[].Instances[].InstanceId"   --output text
```
 - I got an error when i ran this command, because i configured my profile with a name *lab1* but didnt mention it in the above command
   <img width="1864" height="404" alt="22 error" src="https://github.com/user-attachments/assets/845bfab9-ef4d-42fb-adb0-ac6ec5d2d6ae" />


### Step 5.2: Start Session
```bash
aws ssm start-session --target i-xxxxxxxxxxxxxxxxx [--profile lab1 (do this if needed)]
```
<img width="1697" height="420" alt="23 ssm_works" src="https://github.com/user-attachments/assets/c0032759-b9cd-41b1-8d97-4a5fd8151c97" />

### Step 5.4: Try to list all S3 buckets
  - run this command to list all the buckets
  -  ```bash
      <img width="1905" height="281" alt="24 s3_list_error" src="https://github.com/user-attachments/assets/4e4b8255-6df4-4569-8a76-74263e7617fe" />
      ```
  - This will throw an error since we havent configured the instance profile to access S3

### Step 5.5: Setup S3 bucket and permissions for EC2
  - Create an S3 bucket and upload a file with some text
     <img width="1825" height="738" alt="25 s3_bucket_created" src="https://github.com/user-attachments/assets/ae733dea-e9de-4b76-81aa-784d9be9af87" />

  -  Create a Policy that allows to List S3 buckets and GetObjects
     <img width="1208" height="596" alt="28 s3_permissions" src="https://github.com/user-attachments/assets/9ac60f5f-8c16-407b-8f7e-d5cfeae48fd8" />
    
  -  This policy will allow ListAll objects from s3 and download files from the bucket we just created
     <img width="1605" height="796" alt="29 s3_create_policy" src="https://github.com/user-attachments/assets/a4b52e19-1496-43c0-9bcf-e6d0a39ff3c2" />

  - Create a gateway endpoint for S3
    <img width="1742" height="757" alt="26 create_gateway" src="https://github.com/user-attachments/assets/ebaa436e-64ed-4d44-83d4-22ccb8f3a04e" />
  - Associate the gateway endpoint with the private subnet's route table (the subnet that contains the EC2)  
    <img width="1845" height="777" alt="27 gateway-s3" src="https://github.com/user-attachments/assets/52ea30c6-9bd3-4418-9fe6-a5a20ebf7e03" />
  - If we check the route table now, we can see that it contains a route to the s3 which the gateway endpoint added
    <img width="1587" height="452" alt="35 gateway_endpoint_RT" src="https://github.com/user-attachments/assets/2c04895a-6fe4-4930-b6dc-874704ec156a" />
    
  - Attach this policy to the EC2 instance profile role
    <img width="1876" height="785" alt="30 attach_policy_toec2role" src="https://github.com/user-attachments/assets/ac67d767-cb17-4947-916d-3ee53824b196" />
    <img width="1818" height="586" alt="31 attach_policy_toec2role" src="https://github.com/user-attachments/assets/d4e03f6e-2aa4-464b-959b-abf78faa5f3c" />
  - The role should look like this now
    <img width="1591" height="675" alt="32 ec2_role_final" src="https://github.com/user-attachments/assets/b08948a0-3beb-45e1-853e-51ef0acbf850" />



---

## Phase 6 — Download File from S3 (Inside Session)

```bash
aws sts get-caller-identity
aws s3 ls s3://<bucket>/
aws s3 cp s3://<bucket>/<key> /tmp/<file>

```
  <img width="1891" height="376" alt="33 gateway_endpoint_list_s3" src="https://github.com/user-attachments/assets/c20a41d8-8f0d-4dce-90dc-c7da25711cbf" />
  <img width="1913" height="453" alt="34 download item" src="https://github.com/user-attachments/assets/6e05f071-cbe3-4689-8e84-46d024161c42" />

---


## Key Takeaway

SSM allows you to manage private EC2 instances from your local machine using IAM and outbound-only connectivity, eliminating SSH keys, bastion hosts, and inbound access.

# AWS EC2 Lab: SSH to Private EC2 via Bastion (Agent Forwarding)

## Goal

Build a simple VPC with a **public EC2 (bastion)** and a **private EC2**, then:

1. SSH from **laptop → public EC2** using the instance public IP
2. SSH from **public EC2 → private EC2** using the private IP
3. Understand why it fails without a key on the bastion, and fix it using **SSH agent forwarding (-A)**


## End State Diagram
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/2a241f18-9af0-4801-a972-dc8f21fa2e88" />

## What You’ll Build

- VPC: `10.0.0.0/16`
- Public Subnet: `10.0.1.0/24`
- Private Subnet: `10.0.2.0/24`
- Internet Gateway attached to VPC
- Public Route Table: `0.0.0.0/0 -> IGW`
- Two EC2 instances (Amazon Linux 2023)
  - Bastion (Public): public IPv4 + private IP (example `10.0.1.143`)
  - Private EC2: private IP only (example `10.0.2.42`)
- Security Groups:
  - Bastion SG: inbound SSH from your IP
  - Private SG: inbound SSH from Bastion SG


We used **Amazon Linux 2023**, so our SSH user is **`ec2-user`**.

# Phase 1 — Network Setup (VPC + Subnets + Routes)

## Step 1: Create VPC
- CIDR: `10.0.0.0/16`
  <img width="1527" height="817" alt="1 createvpc" src="https://github.com/user-attachments/assets/762b9dbc-0cfe-42cf-af7b-23ce170e78a6" />


## Step 2: Create Subnets
Create two subnets in the VPC:

### Public Subnet
- CIDR: `10.0.1.0/24`
  <img width="1595" height="813" alt="2 create_subnet1" src="https://github.com/user-attachments/assets/fd6ef785-f6a7-4f1d-bd56-bdf8ad2f7715" />


### Private Subnet
- CIDR: `10.0.2.0/24`
  <img width="1767" height="757" alt="3 create_subnet2" src="https://github.com/user-attachments/assets/8acda1b9-da26-4c37-812f-1ca4ad49740a" />


## Step 3: Create and Attach Internet Gateway (IGW)
- Create IGW
  <img width="1606" height="668" alt="8 create_igw" src="https://github.com/user-attachments/assets/386f8b30-88c0-48aa-9bd5-6d9bf99e6974" />

- Attach IGW to the VPC
  <img width="1897" height="536" alt="9 attach_igw" src="https://github.com/user-attachments/assets/9e9e0f5f-bb37-43bb-a569-30c0b9424965" />
  <img width="1671" height="523" alt="10 attach_igw" src="https://github.com/user-attachments/assets/01a90683-5056-4154-a619-65c1015bdc9b" />



## Step 4: Create Route Tables

### Public Route Table
- Add route: `0.0.0.0/0 -> IGW`
- Associate this route table with **Public Subnet**
  <img width="1667" height="583" alt="4 create-rt-1" src="https://github.com/user-attachments/assets/37ec6824-d329-44db-99de-47b7b9cffec5" />


### Private Route Table
- <img width="1828" height="630" alt="5 create-rt-2" src="https://github.com/user-attachments/assets/98556354-b5f3-4e14-9eb6-11966be4462e" />
- Associate this route table with **Private Subnet**
  <img width="1852" height="598" alt="6 associate_privatert" src="https://github.com/user-attachments/assets/6b660e12-cd28-471b-83c4-089561c6517b" />

---

# Phase 2 — Security Groups

## Step 1: Create Bastion Security Group (Public EC2 SG)

Inbound rules:
- SSH (TCP 22) from **your public IP /32**
  - Example: `176.x.x.x/32`

Outbound rules:
- Allow all (default)

## Step 2: Create Private EC2 Security Group

Inbound rules:
- SSH (TCP 22) from **Bastion Security Group**
  - Source is the SG itself (SG-to-SG), NOT a CIDR
<img width="1051" height="682" alt="16 ec2-networksettings" src="https://github.com/user-attachments/assets/4bf7a86d-93cb-477b-87bf-f4da86270112" />
<img width="1826" height="219" alt="17 ec2-sg-networksettings" src="https://github.com/user-attachments/assets/8c27da44-1b0a-4ca8-b509-4bf299ca1e65" />


> Security groups are stateful: you do NOT need to open ephemeral ports in SGs.

### Private EC2 Security group
  <img width="1793" height="496" alt="23 private-ec2-sg" src="https://github.com/user-attachments/assets/e076d04c-d801-4e3d-bdcd-dfa708fd9daf" />

---

# Phase 3 — EC2 Instances

## Step 1: Create ONE Key Pair
- Algorithm: RSA
- Format: PEM
- Name: example `my-keypair`
  <img width="1768" height="806" alt="13 create_ec2" src="https://github.com/user-attachments/assets/f6173652-cd32-4b44-ba12-54870120d814" />
  <img width="906" height="645" alt="14 create_keypair" src="https://github.com/user-attachments/assets/7e249780-34dd-4eb6-ae1c-eae3dae14736" />


Download the `.pem` file and keep it safe.
   <img width="497" height="217" alt="15 save_keypair" src="https://github.com/user-attachments/assets/af1b76f7-c064-4ddb-a576-210cbe493dea" />


## Step 2: Launch Bastion (Public EC2)
- AMI: Amazon Linux 2023
- Subnet: Public Subnet
- Public IPv4: Enabled
- Security Group: Bastion SG
- Key Pair: `my-keypair`

Record:
- Bastion Public IP (example `52.54.200.17`)
- Bastion Private IP (example `10.0.1.143`)

## Step 3: Launch Private EC2
- AMI: Amazon Linux 2023
- Subnet: Private Subnet
- Public IPv4: Disabled
- Security Group: Private SG
- Key Pair: SAME keypair (`my-keypair`) for simplicity in this lab
  <img width="1818" height="822" alt="21 create-private-ec2" src="https://github.com/user-attachments/assets/26059b5d-8088-445f-8e63-da314a64f24b" />
  <img width="1686" height="783" alt="22 create-private-ec2" src="https://github.com/user-attachments/assets/d68539e9-fde4-4efa-9770-f78eb590c347" />

Record:
- Private EC2 private IP (example `10.0.2.42`)

---

# Phase 4 — Laptop → Bastion SSH
- <img width="745" height="516" alt="18 open_ssh" src="https://github.com/user-attachments/assets/f15646c1-a60b-4e45-a593-50309e81d999" />

## Step 1: Put the key on your Linux/WSL filesystem
If your key is on Windows (e.g., `D:\...`), copy it to your Linux home:

```bash
mkdir -p ~/.ssh
cp "/mnt/d/Projects/AWS SSA C03/Files/Images/EC2s/my-keypair.pem" ~/.ssh/
chmod 400 ~/.ssh/my-keypair.pem
```
 <img width="1073" height="137" alt="19 ec2-ssh-1" src="https://github.com/user-attachments/assets/57006ede-df33-41fb-95fc-cda1f227d22b" />

## Step 2: SSH into the bastion
```
ssh -i ~/.ssh/my-keypair.pem ec2-user@<BASTION_PUBLIC_IP>
```
<img width="1067" height="490" alt="20 ec2_ssh2" src="https://github.com/user-attachments/assets/9b2cf66e-650b-4c93-b698-b2487bcf6058" />

Expected: you land on the bastion and see the Amazon Linux banner.

## Phase 5 — Bastion → Private SSH (and the expected failure)

From inside the bastion:
```
ssh ec2-user@<private-ip-for-private-ec2>
```
> we get a Permission denied (publickey,...). The SSH failure wasn’t caused by networking or security groups, but by the bastion not having access to a private key; agent forwarding allowed the bastion to authenticate using my local SSH agent without copying keys.

My private key (my-keypair.pem) lived on my laptop. When I SSH’d into the public EC2:
 - That worked — because the key was available locally.
 - But when I tried to SSH from the public EC2 to the private EC2, the public EC2 asked:
 - “Which private key should I present?”
   - And the answer was: “None.”
 - The public EC2 did not have my private key. So the private EC2 correctly rejected the connection.

## What Is SSH Agent Forwarding?

SSH agent forwarding solves exactly this problem.
 
 ### In simple terms:
It allows a remote machine to temporarily use your local SSH keys without copying them.

#### How it works:
 - Your laptop runs ssh-agent
 - The agent holds private keys in memory
 - When you connect with ssh -A, SSH forwards a socket
 - The remote machine can ask:
 - “Do you have a key for this host?”
 - The private key never leaves your laptop

## Why Agent Forwarding Didn’t Work at First

I initially connected with:
```
ssh -A -i ~/.ssh/my-keypair.pem ec2-user@PUBLIC_IP
```

But on the public EC2:
 - echo $SSH_AUTH_SOCK: printed nothing.

Why?
 
Because I didn’t have an active ssh-agent running with keys loaded. Agent forwarding only forwards an existing agent. If no agent is running, there’s nothing to forward.

## The Fix
On my laptop:
```
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/my-keypair.pem
```
  <img width="1793" height="496" alt="23 private-ec2-sg" src="https://github.com/user-attachments/assets/9c8d854e-a5f0-42e9-856e-4148173b91bc" />


Then reconnect:
```
ssh -A ec2-user@PUBLIC_IP
```

On the public EC2:
```
echo $SSH_AUTH_SOCK
ssh-add -l
```
Now the agent socket existed, and the key was visible.

 <img width="1366" height="595" alt="image" src="https://github.com/user-attachments/assets/874d0657-24a6-4451-b307-5872835f7d4e" />



Finally:
```
ssh ec2-user@10.0.2.42
```
 <img width="1200" height="402" alt="image" src="https://github.com/user-attachments/assets/8fecb05d-9de1-4094-9cbe-1f73ce9f902d" />

























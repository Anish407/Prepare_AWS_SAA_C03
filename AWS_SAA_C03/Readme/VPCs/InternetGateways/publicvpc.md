# Lab 1 – Public Subnet, IGW, Route Tables, and SSM: Proving Internet Access the Right Way

## Goal

Build a VPC from scratch, launch an EC2 instance, connect via **SSM Session Manager**, **prove internet access**, then **break it by removing the IGW route**, and finally **fix it again**.

## Step-by-Step Lab Setup

### 1. Create an IAM Role for EC2

- Create an IAM Role with trusted entity = EC2.
- Gives the EC2 instance an AWS identity (temporary credentials via instance profile). Without this, the instance has no permissions to call AWS APIs on its own.
<img width="801" height="563" alt="Createrole1" src="https://github.com/user-attachments/assets/1670ade0-7f7a-4575-8838-ef21950ddfc2" />


> This role is required even if the instance has full internet access.
--- 
### 2. Attach AmazonSSMManagedInstanceCore to the role
- Add the managed policy AmazonSSMManagedInstanceCore to that role.
- This allows the instance to register with Systems Manager and use Session Manager for shell access.
<img width="830" height="568" alt="assignssmtorole" src="https://github.com/user-attachments/assets/020ff75c-ceee-4b24-ae20-42ebdebdd68c" />
<img width="828" height="571" alt="rolename" src="https://github.com/user-attachments/assets/b22c3cf0-5a73-4107-a8a9-3a05bb9f473e" />
### 3. create vpc
it defines our private network boundary + routing domain in AWS. Everything (subnets, route tables, IGW, etc.) lives inside a VPC.
<img width="725" height="579" alt="createvpc" src="https://github.com/user-attachments/assets/2c27a19a-40d3-4d15-8ba1-f5c0478726ed" />

### 4. create a subnet
- Carves out an IP range where resources (ENIs → EC2) can be placed. A subnet is always single-AZ.
-  A subnet is considered public if its route table has a route to an Internet Gateway (IGW).
 <img width="677" height="568" alt="createsubnet" src="https://github.com/user-attachments/assets/0c75847d-c92f-4f00-ae80-38bfdfb46a2b" />

 The subnet at present uses the main route table. The subnet inherits whatever routes are in the VPC’s main route
<img width="792" height="545" alt="defaultroutetable" src="https://github.com/user-attachments/assets/f948039e-3829-4e19-86df-68af6150a36d" />

### 5. Create the IGW
-  IGW is the VPC’s gateway to the public internet (IPv4/IPv6). It’s not useful until attached + routed.
- An IGW is a horizontally scaled, redundant, and highly available VPC component that allows communication between instances in your VPC and the internet.
<img width="824" height="368" alt="createigw" src="https://github.com/user-attachments/assets/250c4c61-a401-4f7c-ad22-d4741b7c637d" />


### 6. Attach IGW to vpc
- This makes the IGW available for routing from any subnet in the VPC.
<img width="848" height="431" alt="attachigwtovpc" src="https://github.com/user-attachments/assets/a259ed34-886e-4039-9c01-5f87b98d588d" />

> You attach IGW to the VPC, not to a subnet.

### 7. Create route table
Route tables decide where traffic goes when it leaves the subnet.
<img width="862" height="433" alt="createroutetable" src="https://github.com/user-attachments/assets/88fc6698-46d9-48f4-896f-11787b8ec7b1" />

### 8. Create a route to the IGW in the route table
- This makes the subnet public. Traffic to the internet are routed to the IGW.
- In the route table, add: 0.0.0.0/0 → igw-xxxx 
- Tells instances in associated subnets: “for any destination not in the VPC, send it to the IGW.”
<img width="851" height="370" alt="routetable3" src="https://github.com/user-attachments/assets/a1310965-4d6e-4461-97c4-31e0a68b6a21" />

 ### 8. Create an Ec2 instance in the public subnet
  - Create an EC2 in that subnet. This puts an ENI in the subnet and gives the instance a private IP from the subnet range.
 - Make sure to assign a public IPv4 address during launch. Even with an IGW route, an instance without a public IP usually can’t talk to the internet over IPv4 (it has no globally routable address).
   <img width="587" height="217" alt="ec2_autoassignIP" src="https://github.com/user-attachments/assets/647b68df-9c93-4f6e-aacb-6de00003f7fa" />

 - Assign the IAM role created earlier to the instance profile.
 <img width="820" height="395" alt="ec2_assignInstanceprofile" src="https://github.com/user-attachments/assets/941ddf3e-061f-4f3b-8138-9a133d0327c5" />


### 9. connect using Session manager and ping google.com
- Use Session Manager to connect to the instance.
<img width="842" height="377" alt="ec2_connect_ssm" src="https://github.com/user-attachments/assets/7994c33d-7059-4178-b3ab-1e90a49cbe4d" />

- ping google.com and check if the instance can connect to the internet
  
<img width="600" height="300" alt="ping google" src="https://github.com/user-attachments/assets/14f30cea-df1b-441a-8dbd-fd1b5acea22c" />

### How SSM works internally
Whatever you type in the console goes to the AWS SSM backend.
The SSM backend does not push commands into EC2.
Instead, the SSM Agent on the EC2 instance **pulls/receives** that input over an outbound connection and executes it locally.

- The SSM agent on the instance makes outbound HTTPS calls to the SSM endpoints (no inbound access needed).
- The SSM service then proxies your shell session to the instance over that existing outbound connection.
- From the instance, try pinging google.com or doing a curl to http://example.com to prove internet access.

On EC2:

- The agent receives bytes through the outbound channel it owns
- The agent executes commands locally on the instance
- The agent sends output back over the same outbound channel
- No inbound packet ever arrives at EC2

Firewalls/NACLs never see “AWS connecting in”

> Key point:
> - Public subnet + public IP + IGW route = public instance

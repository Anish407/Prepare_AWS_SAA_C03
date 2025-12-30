# Lab 1 – Public Subnet, IGW, Route Tables, and SSM: Proving Internet Access the Right Way

## Goal

Build a VPC from scratch, launch an EC2 instance, connect via **SSM Session Manager**, **prove internet access**, then **break it by removing the IGW route**, and finally **fix it again**.

## Step-by-Step Lab Setup

### 1. Create an IAM Role for EC2

- Create an IAM Role with trusted entity = EC2.
- Gives the EC2 instance an AWS identity (temporary credentials via instance profile). Without this, the instance has no permissions to call AWS APIs on its own.

> This role is required even if the instance has full internet access.
--- 
### 2. Attach AmazonSSMManagedInstanceCore to the role
- Add the managed policy AmazonSSMManagedInstanceCore to that role.
- This allows the instance to register with Systems Manager and use Session Manager for shell access.

### 3. create vpc
it defines our private network boundary + routing domain in AWS. Everything (subnets, route tables, IGW, etc.) lives inside a VPC.

### 4. create a subnet
- Carves out an IP range where resources (ENIs → EC2) can be placed. A subnet is always single-AZ.
-  A subnet is considered public if its route table has a route to an Internet Gateway (IGW).
 
 The subnet at present uses the main route table. The subnet inherits whatever routes are in the VPC’s main route

### 5. Create the IGW
-  IGW is the VPC’s gateway to the public internet (IPv4/IPv6). It’s not useful until attached + routed.
- An IGW is a horizontally scaled, redundant, and highly available VPC component that allows communication between instances in your VPC and the internet.


### 6. Attach IGW to vpc
- This makes the IGW available for routing from any subnet in the VPC.

> You attach IGW to the VPC, not to a subnet.

### 7. Create route table
Route tables decide where traffic goes when it leaves the subnet.

### 8. Create a route to the IGW in the route table
- This makes the subnet public. Traffic to the internet are routed to the IGW.
- In the route table, add: 0.0.0.0/0 → igw-xxxx 
- Tells instances in associated subnets: “for any destination not in the VPC, send it to the IGW.”

 ### 8. Create an Ec2 instance in the public subnet
  - Create an EC2 in that subnet. This puts an ENI in the subnet and gives the instance a private IP from the subnet range.
 - Make sure to assign a public IPv4 address during launch. Even with an IGW route, an instance without a public IP usually can’t talk to the internet over IPv4 (it has no globally routable address).
 - Assign the IAM role created earlier to the instance profile.

### 9. connect using Session manager and ping google.com
- Use Session Manager to connect to the instance.

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
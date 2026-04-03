# CloudFront -> ALB -> ECS (Fargate) -> Static HTML Lab
This lab builds a private containerized web app flow where **CloudFront** sends traffic to an **Application Load Balancer**, the ALB forwards to an **ECS Fargate service**, and the ECS task pulls its image from **Amazon ECR using VPC endpoints**.

---

## Architecture Diagram

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/bc54d0d5-7d11-4e0a-ae93-d52303be89c7" />

---

## What we are building

**Request flow**

1. User calls CloudFront.
2. CloudFront forwards the request to the ALB origin.
3. ALB forwards the request to an ECS target group.
4. ECS Fargate task serves a static HTML page.
5. ECS task pulls the container image from ECR **privately** using VPC endpoints.
6. Container logs go to CloudWatch Logs.

---

## Why this lab matters

This lab teaches the core pieces you will reuse later for a real web app:

- **CloudFront** for edge delivery, HTTPS, caching, and a stable public entry point.
- **ALB** for Layer 7 routing and integration with ECS services.
- **ECS Fargate** for running containers without managing EC2 servers.
- **ECR + VPC endpoints** so private subnets can pull images without public internet access.
- **CloudWatch Logs** so you can actually debug task startup.

When we later replace the static HTML page with a real app that talks to **S3**, **SSM**, **Secrets Manager**, or **RDS**, the same networking and IAM rules still apply.

---
## Final target design for this lab

To keep the lab simple and reliable, build this in two phases:

### Make the application work
- CloudFront
- Public ALB
- ECS Fargate in private subnets
- ECR endpoints
- S3 gateway endpoint
- CloudWatch Logs endpoint

---
## Step 1 - Create the sample HTML app

Create a folder like this:

```text
alblab/
├── Dockerfile
└── index.html
```

### `Dockerfile`

```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
```

Build locally:

```bash
docker build -t ecs-static-html-lab .
```

Test locally:

```bash
docker run -d -p 8080:80 ecs-static-html-lab
```

Open `http://localhost:8080`.

---

## Step 2 - Create an ECR repository

Create an ECR repository, for example:

- Repository name: `ecs-static-html-lab`
<img width="1463" height="727" alt="image" src="https://github.com/user-attachments/assets/19e4ea6b-ac13-4a87-9077-21a90da0ba9f" />

### Step 2.1: Configure your aws cli and create a profile
<img width="1232" height="182" alt="image" src="https://github.com/user-attachments/assets/82f96c9a-3819-404d-b218-661e251a4bf7" />

Then authenticate and push:

```bash
aws ecr get-login-password --region us-east-1 --profile ecslab \
| docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

```bash
docker tag ecs-static-html-lab:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ecs-static-html-lab:latest
```

```bash
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ecs-static-html-lab:latest
```
<img width="1302" height="487" alt="image" src="https://github.com/user-attachments/assets/fbbb44e5-1d96-436e-817e-f7b25196e8be" />

Save the final image URI. You need it in the ECS task definition.
## Step 3 - Create the VPC and subnets

Create a VPC, for example:

- VPC CIDR: `10.0.0.0/16`


Create at least:

- **2 public subnets** in different AZs
- **2 private subnets** in different AZs

Example:

- Public subnet A: `10.0.1.0/24`
- Public subnet B: `10.0.2.0/24`
- Private subnet A: `10.0.11.0/24`
- Private subnet B: `10.0.12.0/24`

<img width="652" height="753" alt="image" src="https://github.com/user-attachments/assets/40f5fa2b-b04e-41df-989b-ff9bd96ea2a3" />
<img width="627" height="685" alt="image" src="https://github.com/user-attachments/assets/10f32101-802a-4322-ace0-352f82b6e84e" />


Attach an **Internet Gateway** to the VPC.
<img width="1840" height="545" alt="image" src="https://github.com/user-attachments/assets/eef26712-ebf3-4de2-81d5-321bf1324b59" />

### Route tables

**Public route table**
- Local route
- `0.0.0.0/0` -> Internet Gateway
<img width="1377" height="815" alt="image" src="https://github.com/user-attachments/assets/4292c784-a02b-4cb2-b2d2-d9b342bfd2cc" />
<img width="1375" height="810" alt="image" src="https://github.com/user-attachments/assets/0266c241-e85f-4f18-a4be-02a3ea989fa5" />

**Private route table**
- Local route
- No internet route required since we are using endpoints only for this lab, we will use Interface endpoints for ecr and cloudwatch and gateway endpoints for s3
<img width="1653" height="792" alt="image" src="https://github.com/user-attachments/assets/b127302e-7ec9-4ce7-8952-38e62cddfe73" />

Associate:
- Public subnets -> public route table
- Private subnets -> private route table

---
## Step 4 - Create security groups
Create the following security groups 
- CloudFront/ALB security group
   <img width="1507" height="782" alt="image" src="https://github.com/user-attachments/assets/686b0aac-718a-4298-89d8-096acd85e593" />
- ECS task security group
   <img width="1248" height="702" alt="image" src="https://github.com/user-attachments/assets/559fbfee-3e1b-465e-839d-85c3b93c8b81" />
- VPC Endpoint security group
  <img width="1848" height="743" alt="image" src="https://github.com/user-attachments/assets/4d2d3b74-82be-455f-9965-2e054752a3d3" />


### CloudFront/ALB security group

Create an ALB security group:

- Inbound: `HTTP 80` from the source you decide for the lab
- Outbound: allow to ECS task security group or all outbound

<img width="1871" height="415" alt="image" src="https://github.com/user-attachments/assets/03350bce-2db1-433c-a526-e3d3a6cab465" />

```For a first working lab, keeping the ALB public is simpler. We can make the ALB private and use VPC endpoints to connect from cloudfront later.```

### ECS task security group

1. Create a security group for ECS tasks:


- Inbound: `HTTP 80` from the **ALB security group**
- Outbound: allow all outbound for now

<img width="1906" height="455" alt="image" src="https://github.com/user-attachments/assets/7662b21a-db4a-460e-bc1f-f173009b4c73" />

### Endpoint security group

Create a security group for interface endpoints:

- Inbound: `HTTPS 443` from the ECS task security group
- Outbound: default

<img width="1622" height="606" alt="image" src="https://github.com/user-attachments/assets/2c471621-1ac8-4cec-a32b-3d0185ea1654" />

Why this matters:
- Your ECS task talks to ECR API, ECR Docker endpoint, and CloudWatch Logs using **443**.
- If the endpoint SG does not allow the ECS task SG, image pull or log publishing fails.

---

## Step 5 - Create the VPC endpoints

This is the part most people miss.

Create these endpoints:

### Interface endpoints

In the **private subnets**, create:

- `com.amazonaws.us-east-1.ecr.api`
- `com.amazonaws.us-east-1.ecr.dkr`
- `com.amazonaws.us-east-1.logs`


  <img width="1598" height="752" alt="image" src="https://github.com/user-attachments/assets/1785cc67-9626-4500-9891-bb716face3c5" />
  <img width="1496" height="807" alt="image" src="https://github.com/user-attachments/assets/60098a34-a868-4b7e-a8e2-5b88c539ab13" />
- Select the private subnets
  <img width="1870" height="562" alt="image" src="https://github.com/user-attachments/assets/6b357808-867a-490d-834e-1e5662da95ce" />
- Also select the security group as the endpoint-sg we created
  <img width="1583" height="807" alt="image" src="https://github.com/user-attachments/assets/45872bd8-b171-4cf5-8431-5d596ee1c1c3" />


Attach the **endpoint security group**.

Enable **Private DNS**.
---

### Gateway endpoint

Create the **S3 gateway endpoint**:

- `com.amazonaws.us-east-1.s3`
<img width="1446" height="797" alt="image" src="https://github.com/user-attachments/assets/73cf80e1-c649-454c-a56f-e6c9e5910598" />

Associate it with the **private route table**.
<img width="1831" height="613" alt="image" src="https://github.com/user-attachments/assets/e0163af5-53c4-43c9-9299-27c824b54d19" />

### Why each endpoint exists

- **ecr.api** -> ECS/Fargate talks to the ECR API.
- **ecr.dkr** -> Docker image pull path.
- **logs** -> container logs to CloudWatch Logs.
- **s3 gateway** -> actual image layers are stored in S3.

If you later add app calls to AWS services, you will likely add more endpoints such as:

- `ssm`
- `secretsmanager`
- `kms`
- `ecs`
- `ec2messages`
- `ssmmessages`

---

## Step 6 - Create IAM roles

### A. Task execution role

This role is used by **ECS/Fargate infrastructure**, not by your code.
1. Create a role (trust policy)
<img width="1802" height="795" alt="image" src="https://github.com/user-attachments/assets/3d47207f-1df5-4011-b3a4-02006d5b5dbe" />
2. Use the AWS managed policy:
  - `AmazonECSTaskExecutionRolePolicy`
 <img width="1367" height="795" alt="image" src="https://github.com/user-attachments/assets/506e3c89-3fda-4a75-a5d5-a50f94180111" /> 

This role is responsible for:

- Pulling the image from ECR
- Writing logs to CloudWatch Logs

Name example:
- `ecsTaskExecutionRole`

### B. Task role

This role is used by **your application code inside the container**.
<img width="1506" height="795" alt="image" src="https://github.com/user-attachments/assets/16a5205a-583b-4a70-9ff6-cbf88db5ff02" />

For this static HTML lab, you do not need any real permissions yet. But i just added s3 fullaccess.

Later, when your application calls:
- S3 -> add S3 permissions here
- SSM Parameter Store -> add SSM permissions here
- Secrets Manager -> add secrets permissions here

Name example:
- `ecsAppTaskRole`






















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































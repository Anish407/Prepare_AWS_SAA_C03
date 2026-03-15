# AWS Edge Architecture Lab  
Route53 + CloudFront + S3 (OAC) + ALB + ECS Fargate + .NET 8 API

## Goal

This lab demonstrates a **modern AWS edge architecture** where:

- Users access the system through a **custom domain**
- DNS is managed by **Route 53**
- **CloudFront** acts as the global CDN and entry point
- Static content is served from **private S3 using OAC**
- Dynamic API requests go to **ECS Fargate containers behind an ALB**
- The application runs as a **Dockerized .NET 8 Web API**
- The container image is stored in **Amazon ECR**

This architecture mirrors real production systems used in large-scale web platforms.


# ECS Fargate Service Connect HTTPS Lab

## Goal

Build a complete ECS Fargate lab from the beginning with three ASP.NET Core APIs, CloudFront, an HTTPS Application Load Balancer, and ECS Service Connect TLS for the internal service path.

Final architecture:

```text
Client
  -> HTTPS
CloudFront
  -> HTTPS
Application Load Balancer
  -> HTTPS target group on port 8080
ServiceConnectDemo.Api1 ECS service
  -> ECS Service Connect TLS
ServiceConnectDemo.Api2 ECS service
  -> ECS Service Connect TLS
ServiceConnectDemo.Api3 ECS service
```

The three APIs are:

| API | Role | Publicly exposed? |
| --- | --- | --- |
| `ServiceConnectDemo.Api1` | Entry API behind the ALB | Yes, through CloudFront and ALB |
| `ServiceConnectDemo.Api2` | Internal API called by Api1 | No |
| `ServiceConnectDemo.Api3` | Internal API called by Api2 | No |

The test endpoint is:

```text
/chain
```

Expected final response:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```

Reference documentation:

- Amazon ECS Service Connect: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect.html
- Service Connect concepts: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-concepts-deploy.html
- Service Connect TLS: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-tls.html
- Enable Service Connect TLS: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/enable-service-connect-tls.html

---

## Important Service Connect TLS Concept

Service Connect uses AWS Cloud Map as the namespace layer, but the application should not call Cloud Map private DNS names directly.

Do not configure the app to call:

```text
api2.serviceconnectdemo.local
api3.serviceconnectdemo.local
```

Configure the app to call Service Connect endpoint names:

```text
http://api2:8080
http://api3:8080
```

Even when Service Connect TLS is enabled, the application code does not perform the TLS handshake with Api2 or Api3. The application sends traffic to the Service Connect endpoint name, the local Service Connect proxy handles the route, and TLS is applied between the Service Connect agents.

So in this lab:

```text
Application setting uses: http://api2:8080
Service Connect encrypts: Api1 proxy -> Api2 proxy
```

For the ALB to Api1 hop, the ALB uses an HTTPS target group. With Service Connect TLS enabled on Api1, ALB traffic routes through the Service Connect agent by default in `awsvpc` mode.

---

## Step 1: Choose Lab Values

Use these names throughout the lab.

| Resource | Name |
| --- | --- |
| Region | `eu-north-1`, or your preferred region |
| VPC | `serviceconnectdemo-vpc` |
| ECS cluster | `serviceconnectdemo-cluster` |
| Service Connect namespace | `serviceconnectdemo.local` |
| Api1 ECS service | `serviceconnectdemo-api1` |
| Api2 ECS service | `serviceconnectdemo-api2` |
| Api3 ECS service | `serviceconnectdemo-api3` |
| Api1 ECR repository | `serviceconnectdemo-api1` |
| Api2 ECR repository | `serviceconnectdemo-api2` |
| Api3 ECR repository | `serviceconnectdemo-api3` |
| Api1 Service Connect name | `api1` |
| Api2 Service Connect name | `api2` |
| Api3 Service Connect name | `api3` |
| Api1 HTTPS target group | `serviceconnectdemo-api1-https-tg` |
| ALB | `serviceconnectdemo-alb` |

All containers listen on:

```text
8080
```

---

## Step 2: Run The APIs Locally

From the repository root:

```powershell
docker compose up --build
```

Test:

```text
http://localhost:5081/chain
```

Expected response includes:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```

Stop the local containers:

```powershell
docker compose down
```

---

## Step 3: Create ECR Repositories

Create three private ECR repositories:

```text
serviceconnectdemo-api1
serviceconnectdemo-api2
serviceconnectdemo-api3
```

Authenticate Docker to ECR:

```powershell
aws ecr get-login-password --region <region> --profile <profile-name> |
docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
```

Build images from the repository root:

```powershell
docker build -f .\ServiceConnectDemo.Api1\Dockerfile -t serviceconnectdemo-api1 .
docker build -f .\ServiceConnectDemo.Api2\Dockerfile -t serviceconnectdemo-api2 .
docker build -f .\ServiceConnectDemo.Api3\Dockerfile -t serviceconnectdemo-api3 .
```

Tag images:

```powershell
docker tag serviceconnectdemo-api1:latest <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api1:latest
docker tag serviceconnectdemo-api2:latest <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api2:latest
docker tag serviceconnectdemo-api3:latest <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api3:latest
```

Push images:

```powershell
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api1:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api2:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api3:latest
```

---

## Step 4: Create The VPC

Create a VPC:

```text
Name: serviceconnectdemo-vpc
IPv4 CIDR: 10.0.0.0/16
DNS resolution: Enabled
DNS hostnames: Enabled
```

Create subnets in at least two Availability Zones:

| Subnet | CIDR | Type | Purpose |
| --- | --- | --- | --- |
| `public-subnet-a` | `10.0.0.0/24` | Public | ALB |
| `public-subnet-b` | `10.0.1.0/24` | Public | ALB |
| `private-subnet-a` | `10.0.10.0/24` | Private | ECS tasks |
| `private-subnet-b` | `10.0.11.0/24` | Private | ECS tasks |

The ALB requires at least two public subnets in different Availability Zones.

Create and attach an Internet Gateway:

```text
Name: serviceconnectdemo-igw
Attach to: serviceconnectdemo-vpc
```

Create a public route table:

| Destination | Target |
| --- | --- |
| `10.0.0.0/16` | local |
| `0.0.0.0/0` | Internet Gateway |

Associate the public route table with both public subnets.

Create a private route table:

| Destination | Target |
| --- | --- |
| `10.0.0.0/16` | local |

Associate the private route table with both private subnets.

This lab uses VPC endpoints instead of a NAT Gateway for private ECS task access to AWS services.

---

## Step 5: Create Security Groups

Create these security groups:

| Security group | Purpose |
| --- | --- |
| `serviceconnectdemo-alb-sg` | Attached to ALB |
| `serviceconnectdemo-api1-sg` | Attached to Api1 ECS tasks |
| `serviceconnectdemo-api2-sg` | Attached to Api2 ECS tasks |
| `serviceconnectdemo-api3-sg` | Attached to Api3 ECS tasks |
| `serviceconnectdemo-endpoints-sg` | Attached to VPC interface endpoints |

Inbound rules:

| Security group | Source | Port | Purpose |
| --- | --- | ---: | --- |
| ALB SG | CloudFront origin-facing prefix list, or `0.0.0.0/0` for lab testing | 443 | CloudFront to ALB |
| Api1 SG | ALB SG | 8080 | ALB HTTPS target group to Api1 |
| Api2 SG | Api1 SG | 8080 | Api1 to Api2 through Service Connect |
| Api3 SG | Api2 SG | 8080 | Api2 to Api3 through Service Connect |
| Endpoint SG | Api1 SG, Api2 SG, Api3 SG | 443 | Private access to AWS APIs |

Outbound rules:

| Security group | Destination | Port | Purpose |
| --- | --- | ---: | --- |
| ALB SG | Api1 SG | 8080 | ALB to Api1 |
| Api1 SG | Api2 SG | 8080 | Api1 to Api2 |
| Api2 SG | Api3 SG | 8080 | Api2 to Api3 |
| Api1 SG, Api2 SG, Api3 SG | Endpoint SG | 443 | ECR, logs, secrets, certificates, KMS |

Api2 and Api3 should not allow public inbound traffic.

---

## Step 6: Create VPC Endpoints

Create these interface endpoints in the private subnets:

```text
com.amazonaws.<region>.ecr.api
com.amazonaws.<region>.ecr.dkr
com.amazonaws.<region>.logs
com.amazonaws.<region>.secretsmanager
com.amazonaws.<region>.kms
com.amazonaws.<region>.acm-pca
```

Create this gateway endpoint:

```text
com.amazonaws.<region>.s3
```

Endpoint settings:

```text
VPC: serviceconnectdemo-vpc
Subnets: private-subnet-a and private-subnet-b
Private DNS: Enabled
Security group: serviceconnectdemo-endpoints-sg
```

Associate the S3 gateway endpoint with the private route table.

Important:

```text
ECR image pulls need the S3 gateway endpoint because ECR image layers are stored in S3.
```

---

## Step 7: Create The Service Connect Namespace

Go to:

```text
ECS -> Clusters -> Namespaces
```

Create:

```text
Namespace: serviceconnectdemo.local
Type: Private DNS namespace
VPC: serviceconnectdemo-vpc
```

Do not manually create these Cloud Map services:

```text
api2.serviceconnectdemo.local
api3.serviceconnectdemo.local
```

ECS Service Connect creates the required Cloud Map service entries from the ECS service configuration.

---

## Step 8: Create ECS Cluster

Create an ECS cluster:

```text
Name: serviceconnectdemo-cluster
Infrastructure: AWS Fargate
```

---

## Step 9: Create IAM Roles

Create or use an ECS task execution role:

```text
Role name: ecsTaskExecutionRole
Trusted service: ecs-tasks.amazonaws.com
Policy: AmazonECSTaskExecutionRolePolicy
```

Create an ECS infrastructure role for Service Connect TLS:

```text
Role name: ecsInfrastructureRoleForServiceConnectDemo
Trusted service: ecs.amazonaws.com
Purpose: ECS infrastructure role
```

This infrastructure role lets ECS manage Service Connect TLS resources such as:

```text
AWS Private CA
Secrets Manager secrets
KMS keys, if using a customer managed KMS key
```

Keep this role separate from:

```text
ECS task execution role
ECS task role
```

---

## Step 10: Create AWS Private CA

Go to:

```text
AWS Private CA -> Private certificate authorities -> Create CA
```

For a lab:

```text
Mode: Short-lived certificate
Type: Root CA
Key algorithm: RSA 2048 or ECDSA 256
```

Add the required tag:

```text
Key: AmazonECSManaged
Value: true
```

Create and activate the CA.

Important:

```text
AWS Private CA can create ongoing cost.
Delete or disable it after the lab if you do not need it.
```

---

## Step 11: Request Public ACM Certificates

For the ALB HTTPS listener, request a public ACM certificate in the same region as the ALB.

Example ALB origin domain:

```text
api-origin.example.com
```

Validate the certificate using DNS validation in Route 53.

For a CloudFront custom domain, request a separate public ACM certificate in:

```text
us-east-1
```

Example CloudFront domain:

```text
api.example.com
```

If you use the default CloudFront distribution domain, you do not need a custom CloudFront viewer certificate.

---

## Step 12: Create Task Definitions

Create one Fargate task definition per API.

Common settings:

```text
Launch type: Fargate
Network mode: awsvpc
CPU: 0.5 vCPU
Memory: 1 GB
Task execution role: ecsTaskExecutionRole
Log driver: awslogs
```

Service Connect adds a proxy sidecar, so do not size the task as if only the app container exists.

### Api1 Task Definition

Container:

```text
Name: ServiceConnectDemo.Api1
Image: <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api1:latest
Container port: 8080
Protocol: TCP
Port name: api1-http
App protocol: HTTP
```

Environment variables:

```text
ASPNETCORE_HTTP_PORTS=8080
Downstream__Api2BaseUrl=http://api2:8080
```

### Api2 Task Definition

Container:

```text
Name: ServiceConnectDemo.Api2
Image: <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api2:latest
Container port: 8080
Protocol: TCP
Port name: api2-http
App protocol: HTTP
```

Environment variables:

```text
ASPNETCORE_HTTP_PORTS=8080
Downstream__Api3BaseUrl=http://api3:8080
```

### Api3 Task Definition

Container:

```text
Name: ServiceConnectDemo.Api3
Image: <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api3:latest
Container port: 8080
Protocol: TCP
Port name: api3-http
App protocol: HTTP
```

Environment variables:

```text
ASPNETCORE_HTTP_PORTS=8080
```

---

## Step 13: Create The Api1 HTTPS Target Group

Create an ALB target group for Api1:

```text
Target type: IP addresses
Name: serviceconnectdemo-api1-https-tg
Protocol: HTTPS
Port: 8080
VPC: serviceconnectdemo-vpc
Protocol version: HTTP1
Health check protocol: HTTPS
Health check path: /health
Health check port: Traffic port
Success codes: 200
```

Do not manually register targets. ECS will register the Api1 task IPs when the Api1 service is created.

---

## Step 14: Create The Application Load Balancer

Create an internet-facing ALB:

```text
Name: serviceconnectdemo-alb
Scheme: Internet-facing
VPC: serviceconnectdemo-vpc
Subnets: public-subnet-a and public-subnet-b
Security group: serviceconnectdemo-alb-sg
Listener: HTTPS 443
Certificate: ACM certificate for the ALB hostname
Default action: forward to serviceconnectdemo-api1-https-tg
```

Recommended listener security policy:

```text
ELBSecurityPolicy-TLS13-1-2-2021-06, or another current TLS 1.2/TLS 1.3 policy
```

If using Route 53, create an alias record for the ALB:

```text
api-origin.example.com -> serviceconnectdemo-alb
```

---

## Step 15: Create Api3 ECS Service

Create the deepest backend first.

Go to:

```text
ECS -> Clusters -> serviceconnectdemo-cluster -> Services -> Create
```

Use:

```text
Launch type: Fargate
Task definition: ServiceConnectDemo.Api3
Service name: serviceconnectdemo-api3
Desired tasks: 1
VPC: serviceconnectdemo-vpc
Subnets: private-subnet-a and private-subnet-b
Security group: serviceconnectdemo-api3-sg
Public IP: Disabled
Load balancer: None
```

Service Connect:

```text
Service Connect: Enabled
Namespace: serviceconnectdemo.local
Service type: Client and server
Port name: api3-http
Discovery name: api3
Client alias DNS name: api3
Client alias port: 8080
TLS: Enabled
AWS Private CA: <private-ca-arn>
IAM role: ecsInfrastructureRoleForServiceConnectDemo
KMS key: AWS owned key, or customer managed symmetric key
```

Create the service and wait for steady state.

Verify the running task has:

```text
ServiceConnectDemo.Api3 container
Service Connect proxy container
```

---

## Step 16: Create Api2 ECS Service

Create Api2 after Api3.

Use:

```text
Launch type: Fargate
Task definition: ServiceConnectDemo.Api2
Service name: serviceconnectdemo-api2
Desired tasks: 1
VPC: serviceconnectdemo-vpc
Subnets: private-subnet-a and private-subnet-b
Security group: serviceconnectdemo-api2-sg
Public IP: Disabled
Load balancer: None
```

Service Connect:

```text
Service Connect: Enabled
Namespace: serviceconnectdemo.local
Service type: Client and server
Port name: api2-http
Discovery name: api2
Client alias DNS name: api2
Client alias port: 8080
TLS: Enabled
AWS Private CA: <private-ca-arn>
IAM role: ecsInfrastructureRoleForServiceConnectDemo
KMS key: AWS owned key, or customer managed symmetric key
```

Create the service and wait for steady state.

Check Api2 logs. Api2 should call:

```text
http://api3:8080
```

The Service Connect agents encrypt the traffic between Api2 and Api3.

---

## Step 17: Create Api1 ECS Service

Create Api1 last because it depends on Api2.

Use:

```text
Launch type: Fargate
Task definition: ServiceConnectDemo.Api1
Service name: serviceconnectdemo-api1
Desired tasks: 1
VPC: serviceconnectdemo-vpc
Subnets: private-subnet-a and private-subnet-b
Security group: serviceconnectdemo-api1-sg
Public IP: Disabled
```

Load balancer:

```text
Load balancer type: Application Load Balancer
Container: ServiceConnectDemo.Api1
Container port: 8080
Target group: serviceconnectdemo-api1-https-tg
```

Service Connect:

```text
Service Connect: Enabled
Namespace: serviceconnectdemo.local
Service type: Client and server
Port name: api1-http
Discovery name: api1
Client alias DNS name: api1
Client alias port: 8080
TLS: Enabled
AWS Private CA: <private-ca-arn>
IAM role: ecsInfrastructureRoleForServiceConnectDemo
KMS key: AWS owned key, or customer managed symmetric key
```

Important ALB and Service Connect TLS settings:

```text
Use awsvpc network mode.
Use an HTTPS target group.
Target group health check port must match the container port, 8080.
Do not configure ingressPortOverride.
```

Create the service and wait for steady state.

Check Api1 logs. Api1 should call:

```text
http://api2:8080
```

The Service Connect agents encrypt the traffic between Api1 and Api2.

---

## Step 18: Verify ECS Services

For each service, confirm:

```text
Desired tasks: 1
Running tasks: 1
Deployment status: Completed
Service Connect: Enabled
TLS: Enabled
Namespace: serviceconnectdemo.local
```

For each task, confirm two containers:

```text
Application container
Service Connect proxy container
```

Check CloudWatch logs for app startup errors.

---

## Step 19: Verify Api1 Target Group Health

Go to:

```text
EC2 -> Target Groups -> serviceconnectdemo-api1-https-tg -> Targets
```

Expected:

```text
Target type: IP
Port: 8080
Health: Healthy
```

If unhealthy, check:

```text
Api1 SG allows inbound 8080 from ALB SG
ALB SG allows outbound 8080 to Api1 SG
Target group protocol is HTTPS
Health check protocol is HTTPS
Health check path is /health
Health check port is 8080
Api1 Service Connect TLS is enabled
Api1 service is attached to the HTTPS target group
No ingressPortOverride is configured
```

---

## Step 20: Test The ALB

Call the ALB custom domain:

```text
https://<alb-custom-domain>/health
https://<alb-custom-domain>/chain
```

Expected `/chain` response includes:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```

If the ALB certificate is for a custom domain, test using the custom domain so the TLS hostname matches the certificate.

---

## Step 21: Create CloudFront Distribution

Create a CloudFront distribution:

```text
Origin domain: ALB custom domain, for example api-origin.example.com
Origin protocol policy: HTTPS only
Viewer protocol policy: Redirect HTTP to HTTPS
Allowed methods: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
Cache policy: CachingDisabled
Origin request policy: forward headers/query strings needed for API testing
```

If using a custom CloudFront domain:

```text
Alternate domain name: api.example.com
Viewer certificate: ACM certificate from us-east-1
```

Create a Route 53 alias:

```text
api.example.com -> CloudFront distribution
```

Wait for CloudFront deployment to finish.

---

## Step 22: Final CloudFront Test

Test:

```text
https://<cloudfront-domain>/health
https://<cloudfront-domain>/chain
```

Expected `/chain` response includes:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```

Final path:

```text
Client
  -> HTTPS
CloudFront
  -> HTTPS
ALB
  -> HTTPS target group on port 8080
Api1 Service Connect proxy
  -> Service Connect TLS
Api2 Service Connect proxy
  -> Service Connect TLS
Api3 Service Connect proxy
```

---

## Step 23: Verify Service Connect Names And TLS

Check application logs:

```text
Api1 should call http://api2:8080
Api2 should call http://api3:8080
```

The apps should not call:

```text
api2.serviceconnectdemo.local
api3.serviceconnectdemo.local
```

To verify TLS, use the ECS Service Connect TLS verification method from the AWS documentation. The key idea is:

```text
Service Connect initiates TLS at the source Service Connect agent.
Service Connect terminates TLS at the destination Service Connect agent.
The application code never sees the TLS handshake.
```

---

## Troubleshooting

### Service Connect endpoint does not resolve

Check:

```text
Client service has Service Connect enabled
Destination service has Service Connect enabled
Both services use namespace serviceconnectdemo.local
Discovery names are api2 and api3
Client aliases are api2 and api3
The client service was redeployed after the destination endpoint was created
```

### ECS says port name is missing

Each task definition must have a named port mapping:

```text
Api1: api1-http
Api2: api2-http
Api3: api3-http
```

### TLS deployment is stuck

Check:

```text
AWS Private CA is active
AWS Private CA has AmazonECSManaged=true tag
ECS infrastructure role is selected
Secrets Manager endpoint or NAT path exists
KMS endpoint or NAT path exists if using customer managed KMS
ACM PCA endpoint or NAT path exists
Task CPU and memory have room for the proxy
```

### Api1 target group is unhealthy

Check:

```text
Target group protocol is HTTPS
Health check protocol is HTTPS
Health check port is 8080
Api1 SG allows inbound 8080 from ALB SG
Api1 service is attached to the target group
No ingressPortOverride is configured
Api1 uses awsvpc network mode
ALB listener uses a TLS 1.2/TLS 1.3 policy
```

### CloudFront returns 502

Check:

```text
Origin domain matches the ALB certificate hostname
CloudFront origin protocol policy is HTTPS only
ALB listener certificate is valid
ALB target group has healthy targets
CloudFront behavior forwards the required HTTP methods
```

### .NET gets TLS or certificate errors calling Api2 or Api3

Check the downstream URLs.

Use:

```text
http://api2:8080
http://api3:8080
```

Do not use these application settings for Service Connect TLS:

```text
https://api2:8080
https://api3:8080
```

Service Connect TLS is proxy-to-proxy encryption. The application code should not need private CA certificates for Api2 or Api3.

---

## Completion Checklist

```text
- Docker Compose local /chain test works
- ECR repositories created
- Images built, tagged, and pushed
- VPC created with DNS resolution and DNS hostnames enabled
- Public subnets created for ALB
- Private subnets created for ECS
- Internet Gateway and route tables configured
- Required VPC endpoints created
- Security groups created
- Service Connect namespace serviceconnectdemo.local created
- ECS cluster created
- ECS task execution role created
- ECS infrastructure role created
- AWS Private CA created and tagged AmazonECSManaged=true
- Public ACM certificate created for ALB
- Optional CloudFront custom domain certificate created in us-east-1
- Task definitions created with named port mappings
- Api1 uses Downstream__Api2BaseUrl=http://api2:8080
- Api2 uses Downstream__Api3BaseUrl=http://api3:8080
- HTTPS target group for Api1 created
- ALB HTTPS listener created
- Api3 ECS service created with Service Connect TLS
- Api2 ECS service created with Service Connect TLS
- Api1 ECS service created with Service Connect TLS and ALB target group
- Api1 target group is healthy
- ALB /chain test works
- CloudFront distribution created
- CloudFront origin protocol policy is HTTPS only
- CloudFront /chain test works
```

---

## Cleanup

Delete resources that are only for the lab:

```text
CloudFront distribution
Route 53 records
ALB
Target group
ECS services
ECS cluster
Task definition revisions
ECR repositories
AWS Private CA
Secrets Manager secrets created for Service Connect TLS
Customer managed KMS key, if created
VPC endpoints
Security groups
Subnets
Route tables
Internet Gateway
VPC
```

Watch costs especially for:

```text
AWS Private CA
NAT Gateway, if used
VPC interface endpoints
ALB
CloudFront
```

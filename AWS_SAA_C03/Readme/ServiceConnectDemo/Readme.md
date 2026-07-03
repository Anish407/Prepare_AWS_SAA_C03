# ServiceConnectDemo Phase 1 README

## Goal

Run three ASP.NET Core Web APIs as Docker containers and deploy them to ECS Fargate behind CloudFront and an Application Load Balancer.




Phase 1 architecture:

```text
Client -> HTTPS -> CloudFront -> HTTPS -> Application Load Balancer -> ServiceConnectDemo.Api1
ServiceConnectDemo.Api1 -> ServiceConnectDemo.Api2 -> ServiceConnectDemo.Api3
```

## Phase 1
In Phase 1, CloudFront to ALB uses HTTPS. The ALB terminates HTTPS and forwards traffic to `ServiceConnectDemo.Api1` on HTTP port `8080`. The internal calls from Api1 to Api2 and Api2 to Api3 also use HTTP in Phase 1.

<img width="1491" height="1055" alt="image" src="https://github.com/user-attachments/assets/4af4bfcf-62ae-4072-b47f-c820fde1a4b6" />

## Phase 2 will add ECS Service Connect and internal HTTPS.

## Projects

| Project | Role | Local URL | Container port |
| --- | --- | --- | ---: |
| `ServiceConnectDemo.Api1` | Public API called by ALB | `http://localhost:5081` | 8080 |
| `ServiceConnectDemo.Api2` | Internal API called by Api1 | Docker network only | 8080 |
| `ServiceConnectDemo.Api3` | Internal API called by Api2 | Docker network only | 8080 |

Each API exposes:

```text
/health
/chain
```

`/chain` is the end-to-end test endpoint.

## Step 1: Run Locally With Docker Compose

From the repository root:

```powershell
docker compose up --build
```

Open:

```text
http://localhost:5081/chain
```

Expected result: the JSON response includes all three services:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```
<img width="500" height="269" alt="image" src="https://github.com/user-attachments/assets/8be606b6-6f1d-4e18-b270-b68573f4b1b9" />

Only Api1 is mapped to the host:

```yaml
ports:
  - "5081:8080"
```

This means:

```text
localhost:5081 -> Api1 container port 8080
```

Api2 and Api3 also listen on container port `8080`, but they are only reachable inside the Docker Compose network:

```text
http://serviceconnectdemo-api2:8080
http://serviceconnectdemo-api3:8080
```

Stop the local containers:

```powershell
docker compose down
```

## Step 2: Create ECR Repositories

Create three private ECR repositories:

```text
serviceconnectdemo-api1
serviceconnectdemo-api2
serviceconnectdemo-api3
```

<img width="789" height="379" alt="image" src="https://github.com/user-attachments/assets/5e3517b5-957e-40e2-aa0e-503d519ca411" />

### Configure the Aws cli
<img width="283" height="19" alt="image" src="https://github.com/user-attachments/assets/6e38e697-567d-4a3a-ad3a-32c8c57ae37b" />


Authenticate Docker to ECR:

```powershell
aws ecr get-login-password --region eu-north-1 --profile my-dev-profile 
| docker login --username AWS --password-stdin 123456789012.dkr.ecr.eu-north-1.amazonaws.com
```

## Step 3: Build And Push Docker Images

Build the images:

```powershell
docker build -f .\ServiceConnectDemo.Api1\Dockerfile -t serviceconnectdemo-api1 .
docker build -f .\ServiceConnectDemo.Api2\Dockerfile -t serviceconnectdemo-api2 .
docker build -f .\ServiceConnectDemo.Api3\Dockerfile -t serviceconnectdemo-api3 .
```

<img width="781" height="349" alt="image" src="https://github.com/user-attachments/assets/cd527105-71a0-44bf-aee4-a48453e209a5" />


Tag the images:

```powershell
docker tag serviceconnectdemo-api1:latest <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api1:latest
docker tag serviceconnectdemo-api2:latest <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api2:latest
docker tag serviceconnectdemo-api3:latest <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api3:latest
```

Push the images:

```powershell
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api1:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api2:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/serviceconnectdemo-api3:latest
```
<img width="392" height="230" alt="image" src="https://github.com/user-attachments/assets/bba12fb3-c4d5-4de9-96fd-7fc43984bf75" />


## Step 4: Create VPC, Subnets, Route Table, And VPC Endpoints

For this lab, use one Availability Zone with:

```text
1 public subnet for the Application Load Balancer
1 private subnet for ECS Fargate tasks
VPC endpoints instead of a NAT Gateway
```

This is fine for a lab. For production, use at least two Availability Zones.

### VPC

Create a VPC:

```text
Name: serviceconnectdemo-vpc
IPv4 CIDR: 10.0.0.0/16
DNS resolution: Enabled
DNS hostnames: Enabled
```
<img width="332" height="387" alt="image" src="https://github.com/user-attachments/assets/fe174ac7-d5a5-49ab-9ef2-df048128260a" />
<img width="303" height="230" alt="image" src="https://github.com/user-attachments/assets/cc282e27-7956-41f9-a36c-f471201f35e3" />
<img width="340" height="333" alt="image" src="https://github.com/user-attachments/assets/9af17736-c1ce-410c-8ab7-0a20528c5749" />

The DNS settings are required for Cloud Map private DNS names such as:

```text
api2.serviceconnectdemo.local
api3.serviceconnectdemo.local
```

### Subnets

Create one public subnet and one private subnet in the same Availability Zone.

Example:

| Subnet | AZ | CIDR | Purpose |
| --- | --- | --- | --- |
| `public-subnet-a` | AZ A | `10.0.0.0/24` | ALB |
| `private-subnet-a` | AZ A | `10.0.10.0/24` | ECS Fargate tasks |

### Internet Gateway

Create and attach an Internet Gateway:

```text
Name: serviceconnectdemo-igw
Attach to: serviceconnectdemo-vpc
```
<img width="486" height="121" alt="image" src="https://github.com/user-attachments/assets/5902c815-0c92-4891-b859-b568cffed413" />

### Public Route Table

Create a public route table and associate it with the public subnet.

Routes:

| Destination | Target |
| --- | --- |
| `10.0.0.0/16` | local |
| `0.0.0.0/0` | Internet Gateway |

The ALB uses the public subnet.

### Private Route Table

Create a private route table and associate it with the private subnet.

Routes:

| Destination | Target |
| --- | --- |
| `10.0.0.0/16` | local |

Do not add an Internet Gateway route to the private route table.

Since this lab uses VPC endpoints instead of a NAT Gateway, the ECS tasks will reach required AWS services through private endpoints.

### VPC Endpoints

Create these endpoints so private ECS tasks can pull images from ECR and write logs without internet access.

Interface endpoints:

| Service | Endpoint type | Required for |
| --- | --- | --- |
| `com.amazonaws.<region>.ecr.api` | Interface | ECR API calls |
| `com.amazonaws.<region>.ecr.dkr` | Interface | Docker image pulls from ECR |
| `com.amazonaws.<region>.logs` | Interface | CloudWatch Logs |
| `com.amazonaws.<region>.secretsmanager` | Interface | Only if using Secrets Manager |
| `com.amazonaws.<region>.kms` | Interface | Only if using KMS-encrypted logs or secrets |
| `com.amazonaws.<region>.ssmmessages` | Interface | Only if using ECS Exec |

<img width="803" height="331" alt="image" src="https://github.com/user-attachments/assets/5d9b985b-29cc-4379-a469-b0be0d8fe636" />


Gateway endpoint:

| Service | Endpoint type | Required for |
| --- | --- | --- |
| `com.amazonaws.<region>.s3` | Gateway | ECR image layer download from S3 |

Important: ECR image pulls need the S3 gateway endpoint. Do not skip it.

### Interface Endpoint Configuration

Create an endpoint security group:

```text
Name: serviceconnectdemo-endpoints-sg
Inbound: HTTPS 443 from ECS task security groups
Outbound: HTTPS 443 or all traffic
```
<img width="622" height="176" alt="image" src="https://github.com/user-attachments/assets/7f00165d-9795-4df0-b915-a7bc486a899a" />



For each interface endpoint:

```text
VPC: serviceconnectdemo-vpc
Subnet: private-subnet-a
Private DNS: Enabled
Security group: endpoint security group
```


The ECS tasks call the interface endpoints over HTTPS port `443`.

### S3 Gateway Endpoint Configuration

For the S3 gateway endpoint:

```text
VPC: serviceconnectdemo-vpc
Route table: private route table
```

AWS adds the S3 route to the private route table automatically.

### ECS Task Subnet Configuration

When creating ECS services, use:

```text
Subnet: private-subnet-a
Assign public IP: Disabled
```

The ECS tasks should not need public IPs.

### ALB Subnet Configuration

For a real Application Load Balancer, AWS requires at least two subnets in two Availability Zones.

For a strict one-AZ lab, you have two options:

```text
Option 1: Add a second public subnet in another AZ only for the ALB.
Option 2: Skip ALB temporarily and test ECS directly through another lab path.
```

Recommended lab approach:

```text
Keep ECS tasks in one private subnet/AZ.
Create a second tiny public subnet in another AZ only because ALB requires two AZs.
Attach both public subnets to the ALB.
```

Example ALB subnet layout:

| Subnet | AZ | CIDR | Purpose |
| --- | --- | --- | --- |
| `public-subnet-a` | AZ A | `10.0.0.0/24` | ALB |
| `public-subnet-b` | AZ B | `10.0.1.0/24` | ALB only |
| `private-subnet-a` | AZ A | `10.0.10.0/24` | ECS Fargate tasks |

## Step 5: Create Security Groups

Create one security group for the ALB and one per ECS service.

Recommended inbound rules:

| Security group | Inbound source | Port |
| --- | --- | ---: |
| ALB SG | CloudFront origin-facing prefix list or internet for lab testing | 443 |
| Api1 SG | ALB SG | 8080 |
| Api2 SG | Api1 SG | 8080 |
| Api3 SG | Api2 SG | 8080 |

<img width="922" height="341" alt="image" src="https://github.com/user-attachments/assets/839f2d48-c32f-42c3-8a88-9380d01e1b0a" />

## Security Group Inbound And Outbound Rules

The traffic chain should be:

```text
ALB -> Api1 -> Api2 -> Api3
```

So the security groups should allow:

```text
ALB sends HTTP traffic to Api1 on port 8080
Api1 sends HTTP traffic to Api2 on port 8080
Api2 sends HTTP traffic to Api3 on port 8080
```

### Security Groups To Create

Create these security groups:

| Security group | Purpose |
| --- | --- |
| `serviceconnectdemo-alb-sg` | Attached to the Application Load Balancer |
| `serviceconnectdemo-api1-sg` | Attached to Api1 ECS tasks |
| `serviceconnectdemo-api2-sg` | Attached to Api2 ECS tasks |
| `serviceconnectdemo-api3-sg` | Attached to Api3 ECS tasks |
| `serviceconnectdemo-endpoints-sg` | Attached to VPC interface endpoints |

### ALB Security Group

Inbound rules:

| Type | Protocol | Port | Source |
| --- | --- | ---: | --- |
| HTTPS | TCP | 443 | CloudFront origin-facing managed prefix list, or `0.0.0.0/0` for lab testing |

Outbound rules:

| Type | Protocol | Port | Destination |
| --- | --- | ---: | --- |
| Custom TCP | TCP | 8080 | `serviceconnectdemo-api1-sg` |

The ALB receives HTTPS traffic from CloudFront and forwards HTTP traffic to Api1 on container port `8080`.

### Api1 ECS Task Security Group

Inbound rules:

| Type | Protocol | Port | Source |
| --- | --- | ---: | --- |
| Custom TCP | TCP | 8080 | `serviceconnectdemo-alb-sg` |

Outbound rules:

| Type | Protocol | Port | Destination |
| --- | --- | ---: | --- |
| Custom TCP | TCP | 8080 | `serviceconnectdemo-api2-sg` |
| HTTPS | TCP | 443 | `serviceconnectdemo-endpoints-sg` |

Api1 accepts traffic only from the ALB. Api1 calls Api2 using:

```text
http://api2.serviceconnectdemo.local:8080
```

Api1 also needs HTTPS `443` outbound to VPC endpoints so it can write logs and interact with required AWS services.

### Api2 ECS Task Security Group

Inbound rules:

| Type | Protocol | Port | Source |
| --- | --- | ---: | --- |
| Custom TCP | TCP | 8080 | `serviceconnectdemo-api1-sg` |

Outbound rules:

| Type | Protocol | Port | Destination |
| --- | --- | ---: | --- |
| Custom TCP | TCP | 8080 | `serviceconnectdemo-api3-sg` |
| HTTPS | TCP | 443 | `serviceconnectdemo-endpoints-sg` |

Api2 accepts traffic only from Api1. Api2 calls Api3 using:

```text
http://api3.serviceconnectdemo.local:8080
```

### Api3 ECS Task Security Group

Inbound rules:

| Type | Protocol | Port | Source |
| --- | --- | ---: | --- |
| Custom TCP | TCP | 8080 | `serviceconnectdemo-api2-sg` |

Outbound rules:

| Type | Protocol | Port | Destination |
| --- | --- | ---: | --- |
| HTTPS | TCP | 443 | `serviceconnectdemo-endpoints-sg` |

Api3 accepts traffic only from Api2. Api3 does not call another internal API, but it still needs outbound HTTPS `443` for CloudWatch Logs and other AWS service access through VPC endpoints.

### VPC Interface Endpoint Security Group

Attach this security group to the interface endpoints, for example:

```text
ECR API endpoint
ECR DKR endpoint
CloudWatch Logs endpoint
Secrets Manager endpoint, if used
KMS endpoint, if used
SSM Messages endpoint, if using ECS Exec
```

Inbound rules:

| Type | Protocol | Port | Source |
| --- | --- | ---: | --- |
| HTTPS | TCP | 443 | `serviceconnectdemo-api1-sg` |
| HTTPS | TCP | 443 | `serviceconnectdemo-api2-sg` |
| HTTPS | TCP | 443 | `serviceconnectdemo-api3-sg` |

Outbound rules:

| Type | Protocol | Port | Destination |
| --- | --- | ---: | --- |
| All traffic | All | All | `0.0.0.0/0` |

The interface endpoint security group must allow inbound HTTPS from the ECS task security groups. Otherwise, private tasks cannot use ECR, CloudWatch Logs, or other endpoint-backed AWS services.

### S3 Gateway Endpoint

The S3 gateway endpoint does not use a security group.

Associate it with the private route table used by the ECS task subnet.

This is required because ECR image layers are downloaded from S3.

### Final Security Group Flow

```text
CloudFront
  -> HTTPS 443
ALB SG
  -> HTTP 8080
Api1 SG
  -> HTTP 8080
Api2 SG
  -> HTTP 8080
Api3 SG
```


Api2 and Api3 should not allow public inbound traffic.

## Step 6: Create AWS Cloud Map Service Discovery

Cloud Map gives Api2 and Api3 private DNS names inside the VPC. Api1 will call Api2 by DNS name, and Api2 will call Api3 by DNS name.

Use this naming for the lab:

| Item | Value |
| --- | --- |
| Private namespace | `serviceconnectdemo.local` |
| Api2 discovery service | `api2` |
| Api3 discovery service | `api3` |
| Api2 DNS name | `api2.serviceconnectdemo.local` |
| Api3 DNS name | `api3.serviceconnectdemo.local` |

The internal URLs will be:

```text
http://api2.serviceconnectdemo.local:8080
http://api3.serviceconnectdemo.local:8080
```


## Step 7: Create ECS Cluster

Create an ECS cluster for Fargate.

Example name:

```text
serviceconnectdemo-cluster
```

## Step 8: Create Task Execution Role

Create or use an ECS task execution role with permissions for:

```text
Pulling images from ECR
Writing logs to CloudWatch Logs
```

AWS managed policy:

```text
AmazonECSTaskExecutionRolePolicy
```

## Step 9: Create Task Definitions

Create one Fargate task definition per API.

Common settings:

```text
Launch type: Fargate
Network mode: awsvpc
CPU/Memory: choose small lab values, for example 0.25 vCPU and 0.5 GB memory
Container port: 8080
Protocol: HTTP
Log driver: awslogs
```

Api1 container environment variables:

```text
ASPNETCORE_HTTP_PORTS=8080
Downstream__Api2BaseUrl=http://api2.serviceconnectdemo.local:8080
```
<img width="809" height="280" alt="image" src="https://github.com/user-attachments/assets/b03bb974-f597-480d-90df-9313acdf5612" />

Api2 container environment variables:

```text
ASPNETCORE_HTTP_PORTS=8080
Downstream__Api3BaseUrl=http://api3.serviceconnectdemo.local:8080
```

Api3 container environment variables:

```text
ASPNETCORE_HTTP_PORTS=8080
```

## Step 10: Create ECS services
## Create ECS Services From AWS Console

### Create Api3 ECS Service

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
Subnets: private-subnet-a
Security group: serviceconnectdemo-api3-sg
Public IP: Disabled
Load balancer: None
```

Enable service discovery:

```text
Service discovery: Enabled
Namespace: serviceconnectdemo.local
Service discovery name: api3
DNS record type: A
TTL: 10 seconds
```
<img width="766" height="335" alt="image" src="https://github.com/user-attachments/assets/8aa354b4-e330-4926-bb13-d6c44d293e28" />

This creates:

```text
api3.serviceconnectdemo.local
```

### Create Api2 ECS Service

Create another ECS service:

```text
Launch type: Fargate
Task definition: ServiceConnectDemo.Api2
Service name: serviceconnectdemo-api2
Desired tasks: 1
VPC: serviceconnectdemo-vpc
Subnets: private-subnet-a
Security group: serviceconnectdemo-api2-sg
Public IP: Disabled
Load balancer: None
```

Enable service discovery:

```text
Service discovery: Enabled
Namespace: serviceconnectdemo.local
Service discovery name: api2
DNS record type: A
TTL: 10 seconds
```

This creates:
<img width="899" height="423" alt="image" src="https://github.com/user-attachments/assets/b9e30858-ba25-4f9d-acc2-cd8e79ba5cef" />


```text
api2.serviceconnectdemo.local
```

### Create Api1 ECS Service

Create the public API service last:

```text
Launch type: Fargate
Task definition: ServiceConnectDemo.Api1
Service name: serviceconnectdemo-api1
Desired tasks: 1
VPC: serviceconnectdemo-vpc
Subnets: private-subnet-a
Security group: serviceconnectdemo-api1-sg
Public IP: Disabled
```

Load balancer configuration:

```text
Load balancer type: Application Load Balancer
Container: ServiceConnectDemo.Api1
Container port: 8080
Target group: serviceconnectdemo-api1-tg
```
<img width="728" height="362" alt="image" src="https://github.com/user-attachments/assets/a1762feb-55e1-47b9-970e-a140466154fe" />



---

## Step 11: Create Target Group For Api1

Create an ALB target group for Api1:

```text
Target type: IP
Protocol: HTTP
Port: 8080
Health check path: /health
Success codes: 200
```

Only `ServiceConnectDemo.Api1` is registered with this target group.

## Step 11: Create Application Load Balancer

Create an internet-facing or internal ALB depending on your CloudFront origin design.

For a simple lab, use:

```text
Type: Application Load Balancer
Scheme: Internet-facing
Subnets: Public subnets
Listener: HTTPS 443
Certificate: ACM certificate in the same region as the ALB
Default action: Forward to Api1 target group
```

The ALB receives HTTPS traffic and forwards HTTP to Api1 on port `8080`.

## Step 13: Validate ALB

After the Api1 ECS service is healthy in the target group, test the ALB:

```text
https://<alb-dns-name>/chain
```

Expected response includes:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```

If this fails, check:

```text
Api1 target group health
Api1 task logs
Api2 task logs
Api3 task logs
Security group rules
Cloud Map DNS resolution
Downstream__Api2BaseUrl
Downstream__Api3BaseUrl
```

## Step 14: Create CloudFront Distribution

Create a CloudFront distribution with the ALB as the origin.

Recommended settings:

```text
Origin domain: ALB DNS name or a custom DNS name pointing to the ALB
Origin protocol policy: HTTPS only
Viewer protocol policy: Redirect HTTP to HTTPS
Allowed methods: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
Cache policy: CachingDisabled
Origin request policy: forward required headers and query strings for API testing
```

Certificate rules:

```text
ALB HTTPS certificate: ACM certificate in the ALB region
CloudFront viewer certificate: ACM certificate in us-east-1 if using a custom CloudFront domain
```

## Step 15: Validate CloudFront

Test:

```text
https://<cloudfront-domain>/chain
```

Expected response includes:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```

Phase 1 is complete when the CloudFront URL successfully returns the full chain response.

## Phase 1 Checklist

```text
[ ] Docker Compose chain works locally
[ ] ECR repositories created
[ ] Images pushed to ECR
[ ] VPC/subnets/NAT or VPC endpoints ready
[ ] Security groups created
[ ] Private service discovery for Api2 and Api3 ready
[ ] ECS cluster created
[ ] ECS task execution role created
[ ] Three task definitions created
[ ] Api1 target group created
[ ] ALB HTTPS listener created
[ ] Three ECS services running in private subnets
[ ] Api1 is healthy in ALB target group
[ ] ALB /chain test works
[ ] CloudFront distribution created
[ ] CloudFront /chain test works
```

## Ready For Phase 2

After Phase 1 works, Phase 2 will replace the temporary Phase 1 private service discovery path with ECS Service Connect and configure internal service-to-service HTTPS.

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/66d71bf7-a7c4-4cb2-91b0-1abf3779fc55" />



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

Gateway endpoint:

| Service | Endpoint type | Required for |
| --- | --- | --- |
| `com.amazonaws.<region>.s3` | Gateway | ECR image layer download from S3 |

Important: ECR image pulls need the S3 gateway endpoint. Do not skip it.

### Interface Endpoint Configuration

For each interface endpoint:

```text
VPC: serviceconnectdemo-vpc
Subnet: private-subnet-a
Private DNS: Enabled
Security group: endpoint security group
```

Create an endpoint security group:

```text
Name: serviceconnectdemo-endpoints-sg
Inbound: HTTPS 443 from ECS task security groups
Outbound: HTTPS 443 or all traffic
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

### Option A: Create Cloud Map From The ECS Console

Use this option if you are creating services manually in the AWS console.

Create the namespace:

```text
ECS console -> Clusters -> your cluster -> Service discovery namespaces -> Create namespace
Namespace type: Private
Namespace name: serviceconnectdemo.local
VPC: same VPC used by the ECS services
```

When creating the `ServiceConnectDemo.Api2` ECS service, enable service discovery:

```text
Service discovery: Turn on
Namespace: serviceconnectdemo.local
Service discovery name: api2
DNS record type: A
DNS TTL: 10 seconds
Health check: ECS-managed health
```

When creating the `ServiceConnectDemo.Api3` ECS service, enable service discovery:

```text
Service discovery: Turn on
Namespace: serviceconnectdemo.local
Service discovery name: api3
DNS record type: A
DNS TTL: 10 seconds
Health check: ECS-managed health
```

Api1 does not need a Cloud Map name for Phase 1 because the ALB calls Api1 through the target group.

### Option B: Create Cloud Map With AWS CLI

Create the private DNS namespace:

```powershell
aws servicediscovery create-private-dns-namespace `
  --name serviceconnectdemo.local `
  --vpc <vpc-id> `
  --region <region>
```

Save the returned namespace operation ID, then check the operation until it succeeds:

```powershell
aws servicediscovery get-operation `
  --operation-id <operation-id> `
  --region <region>
```

Get the namespace ID:

```powershell
aws servicediscovery list-namespaces `
  --region <region>
```

Create the Api2 discovery service:

```powershell
aws servicediscovery create-service `
  --name api2 `
  --namespace-id <namespace-id> `
  --dns-config "NamespaceId=<namespace-id>,DnsRecords=[{Type=A,TTL=10}],RoutingPolicy=MULTIVALUE" `
  --health-check-custom-config FailureThreshold=1 `
  --region <region>
```

Create the Api3 discovery service:

```powershell
aws servicediscovery create-service `
  --name api3 `
  --namespace-id <namespace-id> `
  --dns-config "NamespaceId=<namespace-id>,DnsRecords=[{Type=A,TTL=10}],RoutingPolicy=MULTIVALUE" `
  --health-check-custom-config FailureThreshold=1 `
  --region <region>
```

Save the returned Cloud Map service IDs. You will attach those service IDs when you create the Api2 and Api3 ECS services.

### Cloud Map Requirements

The VPC must have DNS support enabled:

```text
enableDnsSupport=true
enableDnsHostnames=true
```

The ECS services must use `awsvpc` networking. Fargate tasks already require this.

The security groups must allow the actual traffic after DNS resolves:

```text
Api1 SG -> Api2 SG on TCP 8080
Api2 SG -> Api3 SG on TCP 8080
```

Cloud Map only solves naming. It does not open network paths.

### Cloud Map Validation

After Api2 and Api3 tasks are running, check that instances were registered:

```powershell
aws servicediscovery list-instances `
  --service-id <api2-cloudmap-service-id> `
  --region <region>

aws servicediscovery list-instances `
  --service-id <api3-cloudmap-service-id> `
  --region <region>
```

From an ECS Exec shell, a temporary EC2 instance, or another tool running inside the same VPC, verify DNS resolution:

```powershell
nslookup api2.serviceconnectdemo.local
nslookup api3.serviceconnectdemo.local
```

Then verify HTTP connectivity:

```powershell
curl http://api2.serviceconnectdemo.local:8080/health
curl http://api3.serviceconnectdemo.local:8080/health
```

Both should return healthy responses.

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
Health check path: /health
Log driver: awslogs
```

Api1 container environment variables:

```text
ASPNETCORE_HTTP_PORTS=8080
Downstream__Api2BaseUrl=http://api2.serviceconnectdemo.local:8080
```

Api2 container environment variables:

```text
ASPNETCORE_HTTP_PORTS=8080
Downstream__Api3BaseUrl=http://api3.serviceconnectdemo.local:8080
```

Api3 container environment variables:

```text
ASPNETCORE_HTTP_PORTS=8080
```

## Step 10: Create Target Group For Api1

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

## Step 12: Create ECS Services

Create three ECS services:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```

Use:

```text
Launch type: Fargate
Subnets: Private subnets
Assign public IP: Disabled
Desired tasks: 1 for lab
```

Attach only Api1 to the ALB target group.

Attach Api2 and Api3 to the Cloud Map discovery services created in Step 6:

```text
ServiceConnectDemo.Api2 -> Cloud Map service api2.serviceconnectdemo.local
ServiceConnectDemo.Api3 -> Cloud Map service api3.serviceconnectdemo.local
```

If you use the ECS console, this is done by enabling service discovery while creating each ECS service.

If you use the AWS CLI, pass the `serviceRegistries` setting when creating each ECS service. Use the Cloud Map service ARN for Api2 and Api3.

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

<img width="1619" height="972" alt="image" src="https://github.com/user-attachments/assets/c39b2850-7efe-466c-bcbb-a9d94222c0e9" />


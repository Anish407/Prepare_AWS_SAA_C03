# ServiceConnectDemo Phase 2 README

## Goal

Continue the existing ServiceConnectDemo lab by replacing the Phase 1 internal Cloud Map DNS calls with ECS Service Connect and enabling HTTPS/TLS for the full request path.

Target architecture:

```text
Client
  -> HTTPS
CloudFront
  -> HTTPS
Application Load Balancer
  -> HTTPS
ServiceConnectDemo.Api1 ECS service
  -> Service Connect TLS
ServiceConnectDemo.Api2 ECS service
  -> Service Connect TLS
ServiceConnectDemo.Api3 ECS service
```

Phase 1 proved this path:

```text
CloudFront -> HTTPS -> ALB -> HTTP -> Api1
Api1 -> Cloud Map DNS -> HTTP -> Api2
Api2 -> Cloud Map DNS -> HTTP -> Api3
```

Phase 2 changes the internal service-to-service path:

```text
Api1 -> Service Connect endpoint -> Api2
Api2 -> Service Connect endpoint -> Api3
```

Important:

```text
Service Connect still uses AWS Cloud Map behind the scenes.
The application should stop calling api2.serviceconnectdemo.local and api3.serviceconnectdemo.local directly.
The application should call Service Connect names such as api2 and api3.
```

Reference documentation:

- Amazon ECS Service Connect: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect.html
- Service Connect components: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-concepts-deploy.html
- Service Connect TLS: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-tls.html
- Configure Service Connect with AWS CLI: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/create-service-connect.html

---

## Recommended Phase 2 Order

Do this in two passes:

```text
Pass 1: Enable Service Connect without TLS and verify Api1 -> Api2 -> Api3.
Pass 2: Enable Service Connect TLS and switch the full path to HTTPS.
```

This avoids debugging CloudFront, ALB HTTPS, ECS, Service Connect, AWS Private CA, IAM roles, Secrets Manager, and app settings all at once.

---

## Complete Lab Walkthrough

Use this section as the full runbook for completing Phase 2 from the Phase 1 environment.

### Step 1: Confirm Phase 1 Is Working

Before changing anything, test the current CloudFront URL:

```text
https://<cloudfront-domain>/chain
```

Expected response:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```

Do not continue until this works. Phase 2 should start from a known-good baseline.

### Step 2: Record The Existing Phase 1 Values

Write down these values before updating services:

```text
AWS region
AWS account ID
ECS cluster name
VPC ID
Private subnet used by ECS tasks
Public subnets used by ALB
ALB name
ALB security group
Api1 security group
Api2 security group
Api3 security group
VPC endpoint security group, if using endpoints
Current Api1 HTTP target group
ALB HTTPS listener
CloudFront distribution domain
ALB custom domain, if used
ACM certificate ARN for the ALB HTTPS listener
```

Also record the current Phase 1 environment variables:

```text
Api1: Downstream__Api2BaseUrl=http://api2.serviceconnectdemo.local:8080
Api2: Downstream__Api3BaseUrl=http://api3.serviceconnectdemo.local:8080
Api3: no downstream URL
```

### Step 3: Confirm VPC DNS Settings

Go to:

```text
VPC -> Your VPC -> Actions -> Edit VPC settings
```

Confirm:

```text
DNS resolution: Enabled
DNS hostnames: Enabled
```

Service Connect uses Cloud Map as its namespace layer. Keeping VPC DNS enabled is the correct baseline for this lab.

### Step 4: Keep The Existing Cloud Map Namespace

Keep:

```text
serviceconnectdemo.local
```

Do not delete the old Phase 1 Cloud Map services yet:

```text
api2.serviceconnectdemo.local
api3.serviceconnectdemo.local
```

During Phase 2, leave them in place until the Service Connect version is fully working.

The application will stop using these names:

```text
api2.serviceconnectdemo.local
api3.serviceconnectdemo.local
```

And start using these Service Connect endpoint names:

```text
api2
api3
```

### Step 5: Create New Task Definition Revision For Api3

Go to:

```text
ECS -> Task definitions -> ServiceConnectDemo.Api3 -> Create new revision
```

Update the container port mapping:

```text
Container port: 8080
Protocol: TCP
Port name: api3-http
App protocol: HTTP
```

Keep environment variables:

```text
ASPNETCORE_HTTP_PORTS=8080
```

Save the new task definition revision.

### Step 6: Create New Task Definition Revision For Api2

Go to:

```text
ECS -> Task definitions -> ServiceConnectDemo.Api2 -> Create new revision
```

Update the container port mapping:

```text
Container port: 8080
Protocol: TCP
Port name: api2-http
App protocol: HTTP
```

For the first pass without TLS, set:

```text
ASPNETCORE_HTTP_PORTS=8080
Downstream__Api3BaseUrl=http://api3:8080
```

Save the new task definition revision.

### Step 7: Create New Task Definition Revision For Api1

Go to:

```text
ECS -> Task definitions -> ServiceConnectDemo.Api1 -> Create new revision
```

Update the container port mapping:

```text
Container port: 8080
Protocol: TCP
Port name: api1-http
App protocol: HTTP
```

For the first pass without TLS, set:

```text
ASPNETCORE_HTTP_PORTS=8080
Downstream__Api2BaseUrl=http://api2:8080
```

Save the new task definition revision.

### Step 8: Check Task CPU And Memory

Service Connect adds a proxy sidecar container to each ECS task.

If your task size is very small, increase it before enabling Service Connect.

Good lab starting point:

```text
CPU: 0.5 vCPU
Memory: 1 GB
```

The app container and Service Connect proxy share the task resources.

### Step 9: Confirm Security Groups For The Non-TLS Pass

Inbound rules:

| Security group | Source | Port |
| --- | --- | ---: |
| ALB SG | CloudFront origin-facing prefix list, or internet for lab testing | 443 |
| Api1 SG | ALB SG | 8080 |
| Api2 SG | Api1 SG | 8080 |
| Api3 SG | Api2 SG | 8080 |

Outbound rules:

| Security group | Destination | Port |
| --- | --- | ---: |
| ALB SG | Api1 SG | 8080 |
| Api1 SG | Api2 SG | 8080 |
| Api2 SG | Api3 SG | 8080 |
| Api1 SG, Api2 SG, Api3 SG | VPC endpoint SG or NAT path | 443 |

Do not expose Api2 or Api3 publicly.

### Step 10: Enable Service Connect On Api3 Without TLS

Go to:

```text
ECS -> Clusters -> serviceconnectdemo-cluster -> Services -> serviceconnectdemo-api3 -> Update
```

Use:

```text
Task definition revision: latest Api3 revision with api3-http port name
Service Connect: Enabled
Namespace: serviceconnectdemo.local
Service Connect service type: Client and server
Port name: api3-http
Discovery name: api3
Client alias DNS name: api3
Client alias port: 8080
TLS: Disabled
Load balancer: None
```

Deploy and wait for steady state.

Verify the new task has:

```text
Api3 application container
Service Connect proxy container
```

### Step 11: Enable Service Connect On Api2 Without TLS

Go to:

```text
ECS -> Clusters -> serviceconnectdemo-cluster -> Services -> serviceconnectdemo-api2 -> Update
```

Use:

```text
Task definition revision: latest Api2 revision with api2-http port name
Service Connect: Enabled
Namespace: serviceconnectdemo.local
Service Connect service type: Client and server
Port name: api2-http
Discovery name: api2
Client alias DNS name: api2
Client alias port: 8080
TLS: Disabled
Load balancer: None
```

Confirm:

```text
Downstream__Api3BaseUrl=http://api3:8080
```

Deploy and wait for steady state.

### Step 12: Enable Service Connect On Api1 Without TLS

Go to:

```text
ECS -> Clusters -> serviceconnectdemo-cluster -> Services -> serviceconnectdemo-api1 -> Update
```

Use:

```text
Task definition revision: latest Api1 revision with api1-http port name
Service Connect: Enabled
Namespace: serviceconnectdemo.local
Service Connect service type: Client and server
Port name: api1-http
Discovery name: api1
Client alias DNS name: api1
Client alias port: 8080
TLS: Disabled
Load balancer: keep the existing Phase 1 HTTP target group for now
```

Confirm:

```text
Downstream__Api2BaseUrl=http://api2:8080
```

Deploy and wait for steady state.

### Step 13: Test Service Connect Without TLS

Call:

```text
https://<cloudfront-domain>/chain
```

Expected response:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```

At this point the path is:

```text
Client -> HTTPS -> CloudFront -> HTTPS -> ALB -> HTTP -> Api1
Api1 -> http://api2:8080 through Service Connect
Api2 -> http://api3:8080 through Service Connect
```

Check CloudWatch logs:

```text
Api1 should call http://api2:8080
Api2 should call http://api3:8080
```

Fix any issue here before enabling TLS.

### Step 14: Create Or Choose AWS Private CA

Service Connect TLS requires AWS Private Certificate Authority.

Go to:

```text
AWS Private CA -> Private certificate authorities -> Create CA
```

Recommended lab values:

```text
Mode: Short-lived certificate
Type: Root CA for lab, or subordinate CA if you already have a CA hierarchy
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
Delete or disable lab resources after the lab if you do not need them.
```

### Step 15: Create The ECS Infrastructure IAM Role

Service Connect TLS needs an ECS infrastructure role.

Go to:

```text
IAM -> Roles -> Create role
```

Use:

```text
Trusted entity type: AWS service
Use case: Elastic Container Service
Role purpose: ECS infrastructure role
```

Name:

```text
ecsInfrastructureRoleForServiceConnectDemo
```

Attach the permissions required by the current Amazon ECS infrastructure role documentation.

This role is used by ECS to manage Service Connect TLS resources such as:

```text
AWS Private CA
Secrets Manager secrets
KMS, if using a customer managed KMS key
```

This role is different from:

```text
ECS task execution role
ECS task role
```

Keep those existing roles.

### Step 16: Choose The KMS Key

For a lab, use:

```text
AWS owned key
```

If you choose a customer managed symmetric KMS key, make sure the ECS infrastructure role can use it.

### Step 17: Confirm VPC Endpoints Or NAT For TLS

If your ECS tasks run in private subnets with no NAT Gateway, confirm the required VPC endpoints exist.

Already needed from Phase 1:

```text
ECR API interface endpoint
ECR DKR interface endpoint
CloudWatch Logs interface endpoint
S3 gateway endpoint
```

Needed or commonly needed for Phase 2 TLS:

```text
Secrets Manager interface endpoint
KMS interface endpoint, if using a customer managed KMS key
ACM PCA interface endpoint, if your setup requires private access to Private CA APIs
```

Endpoint security group inbound rule:

| Type | Source | Port |
| --- | --- | ---: |
| HTTPS | Api1 SG | 443 |
| HTTPS | Api2 SG | 443 |
| HTTPS | Api3 SG | 443 |

### Step 18: Create An HTTPS Target Group For Api1

In Phase 1, the ALB target group used HTTP.

Create a new target group:

```text
EC2 -> Target Groups -> Create target group
```

Use:

```text
Target type: IP addresses
Target group name: serviceconnectdemo-api1-https-tg
Protocol: HTTPS
Port: 8080
VPC: serviceconnectdemo-vpc
Protocol version: HTTP1
Health check protocol: HTTPS
Health check path: /health
Health check port: Traffic port
Success codes: 200
```

Do not manually register task IPs. ECS should manage registration when the Api1 service is updated.

### Step 19: Enable Service Connect TLS On Api3

Go to:

```text
ECS -> Clusters -> serviceconnectdemo-cluster -> Services -> serviceconnectdemo-api3 -> Update
```

Use:

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
KMS key: AWS owned key, or selected customer managed key
Load balancer: None
```

Deploy and wait for steady state.

Check ECS service events for certificate, secret, or KMS errors.

### Step 20: Create HTTPS Task Revision For Api2

Create a new Api2 task definition revision.

Change:

```text
Downstream__Api3BaseUrl=https://api3:8080
```

Keep:

```text
Port name: api2-http
Container port: 8080
App protocol: HTTP
```

Save the new revision.

### Step 21: Enable Service Connect TLS On Api2

Update `serviceconnectdemo-api2`.

Use:

```text
Task definition revision: latest Api2 HTTPS revision
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
KMS key: AWS owned key, or selected customer managed key
Load balancer: None
```

Deploy and wait for steady state.

Check Api2 logs. It should call:

```text
https://api3:8080
```

### Step 22: Create HTTPS Task Revision For Api1

Create a new Api1 task definition revision.

Change:

```text
Downstream__Api2BaseUrl=https://api2:8080
```

Keep:

```text
Port name: api1-http
Container port: 8080
App protocol: HTTP
```

Save the new revision.

### Step 23: Enable Service Connect TLS On Api1 And Attach HTTPS Target Group

Update `serviceconnectdemo-api1`.

Use:

```text
Task definition revision: latest Api1 HTTPS revision
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
KMS key: AWS owned key, or selected customer managed key
```

Load balancer settings:

```text
Load balancer type: Application Load Balancer
Container: ServiceConnectDemo.Api1
Container port: 8080
Target group: serviceconnectdemo-api1-https-tg
```

Deploy and wait for steady state.

### Step 24: Update The ALB HTTPS Listener

Go to:

```text
EC2 -> Load Balancers -> serviceconnectdemo ALB -> Listeners
```

Keep:

```text
Protocol: HTTPS
Port: 443
Certificate: ACM public certificate for the ALB hostname
```

Update default action:

```text
Forward to: serviceconnectdemo-api1-https-tg
```

For this lab:

```text
ALB listener: HTTPS 443
ALB target group: HTTPS 8080
Health check: HTTPS /health on port 8080
```

### Step 25: Confirm Final Security Groups

Final inbound rules:

| Security group | Source | Port | Purpose |
| --- | --- | ---: | --- |
| ALB SG | CloudFront origin-facing prefix list, or internet for lab testing | 443 | CloudFront to ALB |
| Api1 SG | ALB SG | 8080 | ALB HTTPS target group to Api1 |
| Api2 SG | Api1 SG | 8080 | Api1 to Api2 through Service Connect |
| Api3 SG | Api2 SG | 8080 | Api2 to Api3 through Service Connect |
| Endpoint SG | Api1 SG, Api2 SG, Api3 SG | 443 | Private AWS service access |

Final outbound rules:

| Security group | Destination | Port | Purpose |
| --- | --- | ---: | --- |
| ALB SG | Api1 SG | 8080 | ALB to Api1 |
| Api1 SG | Api2 SG | 8080 | Api1 to Api2 |
| Api2 SG | Api3 SG | 8080 | Api2 to Api3 |
| Api1 SG, Api2 SG, Api3 SG | Endpoint SG or NAT path | 443 | AWS APIs, logs, secrets, certificates |

### Step 26: Verify Api1 HTTPS Target Group Health

Go to:

```text
EC2 -> Target Groups -> serviceconnectdemo-api1-https-tg -> Targets
```

Expected:

```text
Api1 task IP is registered
Port: 8080
Health status: Healthy
```

If unhealthy, check:

```text
Target group protocol is HTTPS
Health check protocol is HTTPS
Health check path is /health
Health check port is 8080
Api1 SG allows inbound 8080 from ALB SG
Api1 has Service Connect TLS enabled
Api1 service is attached to the HTTPS target group
```

### Step 27: Verify CloudFront Origin Settings

Go to:

```text
CloudFront -> Distributions -> <distribution> -> Origins
```

Confirm:

```text
Origin domain: ALB DNS name or ALB custom hostname
Origin protocol policy: HTTPS only
```

Behavior:

```text
Viewer protocol policy: Redirect HTTP to HTTPS
Cache policy: CachingDisabled for API testing
Allowed methods: all methods needed by the API
```

### Step 28: Final Test

Test health:

```text
https://<cloudfront-domain>/health
```

Test the full chain:

```text
https://<cloudfront-domain>/chain
```

Expected response:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```

Final traffic flow:

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

### Step 29: Verify Logs And Service Connect State

For each ECS task, verify there are two containers:

```text
Application container
Service Connect proxy container
```

Check ECS service configuration:

```text
Service Connect enabled
Namespace: serviceconnectdemo.local
TLS enabled
Correct discovery name
Correct client alias
```

Check CloudWatch logs:

```text
Api1 should call https://api2:8080
Api2 should call https://api3:8080
```

The apps should no longer call:

```text
api2.serviceconnectdemo.local
api3.serviceconnectdemo.local
```

---

## Troubleshooting

### The chain endpoint fails after switching to short names

Check that the client service has Service Connect enabled.

Common mistake:

```text
Api2 has Service Connect enabled, but Api1 does not.
```

Api1 must have Service Connect enabled so its local proxy can resolve `api2`.

### ECS says the port name is missing

Check the task definition container port mapping.

Service Connect needs a named port:

```text
name: api2-http
containerPort: 8080
```

### ALB target group is unhealthy after switching to HTTPS

Check:

```text
Target group protocol is HTTPS
Health check protocol is HTTPS
Health check path is /health
Health check port is 8080
Api1 service has Service Connect TLS enabled
Api1 service uses awsvpc mode
No ingressPortOverride is configured
Api1 security group allows inbound 8080 from ALB SG
```

### Service deployment is stuck

Check:

```text
AWS Private CA exists and is active
AWS Private CA has tag AmazonECSManaged=true
ECS infrastructure role is selected
Secrets Manager access is available
KMS access is available if using a customer managed key
Task CPU and memory have room for the proxy
```

### HTTPS client errors inside .NET

If the application calls:

```text
https://api2:8080
```

and gets certificate or TLS errors, confirm that the request is going through Service Connect and that TLS is enabled for the destination service.

Do not try to manually install private CA certificates into the .NET app for Service Connect TLS. The intended model is that the Service Connect proxies handle TLS for the service-to-service connection.

---

## Phase 2 Checklist

```text
- Phase 1 /chain test worked before starting
- Existing VPC, ALB, CloudFront, ECS, and security group values were recorded
- VPC DNS resolution and DNS hostnames are enabled
- Existing Cloud Map namespace serviceconnectdemo.local is kept during migration
- Api3 task definition has port name api3-http
- Api2 task definition has port name api2-http
- Api1 task definition has port name api1-http
- Task CPU and memory have room for the Service Connect proxy
- Api3 Service Connect works without TLS
- Api2 Service Connect works without TLS
- Api1 Service Connect works without TLS
- Api1 calls http://api2:8080 during the non-TLS pass
- Api2 calls http://api3:8080 during the non-TLS pass
- CloudFront /chain works with Service Connect before TLS
- AWS Private CA exists and is active
- AWS Private CA has AmazonECSManaged=true tag
- ECS infrastructure IAM role exists
- KMS option is selected
- Required VPC endpoints or NAT path are available
- Api1 HTTPS target group exists on port 8080
- Api3 Service Connect TLS is enabled
- Api2 Service Connect TLS is enabled
- Api1 Service Connect TLS is enabled
- Api1 calls https://api2:8080
- Api2 calls https://api3:8080
- ALB HTTPS listener forwards to the Api1 HTTPS target group
- Api1 HTTPS target group is healthy
- CloudFront origin uses HTTPS only
- CloudFront /health works
- CloudFront /chain returns Api1, Api2, and Api3
```

## Cleanup Notes

After the lab, consider cleaning up:

```text
AWS Private CA
Service Connect TLS Secrets Manager secrets created by ECS
Customer managed KMS key, if created only for this lab
Unused Phase 1 Cloud Map services
Unused HTTP target groups
Old ECS task definition revisions
CloudFront distribution
ALB
ECS services
ECS cluster
ECR repositories
VPC endpoints
VPC
```

Be careful with the AWS Private CA. It can create ongoing cost if left active.

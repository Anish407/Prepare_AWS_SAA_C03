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

## Final Naming

Use one Service Connect namespace:

```text
serviceconnectdemo.local
```

Use these Service Connect endpoint names:

| ECS service | Service Connect role | Endpoint name | Port |
| --- | --- | --- | ---: |
| `serviceconnectdemo-api1` | Client-server | `api1` | 8080 |
| `serviceconnectdemo-api2` | Client-server | `api2` | 8080 |
| `serviceconnectdemo-api3` | Client-server | `api3` | 8080 |

Why make all three client-server?

```text
Api1 receives traffic from the ALB and calls Api2.
Api2 receives traffic from Api1 and calls Api3.
Api3 receives traffic from Api2.
```

Api3 does not call another service, but it still needs to be a Service Connect server because Api2 calls it.

---

## Step 1: Update Application URLs

In Phase 1, Api1 and Api2 used Cloud Map DNS names:

```text
Downstream__Api2BaseUrl=http://api2.serviceconnectdemo.local:8080
Downstream__Api3BaseUrl=http://api3.serviceconnectdemo.local:8080
```

For Service Connect without TLS, use:

```text
Downstream__Api2BaseUrl=http://api2:8080
Downstream__Api3BaseUrl=http://api3:8080
```

For the final TLS version, use:

```text
Downstream__Api2BaseUrl=https://api2:8080
Downstream__Api3BaseUrl=https://api3:8080
```

The short names work because the Service Connect proxy in each task knows the namespace endpoints.

---

## Step 2: Update Task Definition Port Mappings

Service Connect requires named port mappings.

For each API task definition, make sure the container port mapping has:

```json
{
  "name": "api1-http",
  "containerPort": 8080,
  "protocol": "tcp",
  "appProtocol": "http"
}
```

Use unique names per task definition:

| API | Port mapping name |
| --- | --- |
| Api1 | `api1-http` |
| Api2 | `api2-http` |
| Api3 | `api3-http` |

Keep:

```text
containerPort: 8080
protocol: tcp
appProtocol: http
```

For TLS with Service Connect, the application can still listen on HTTP inside the container. Service Connect TLS encrypts traffic between Service Connect proxies.

---

## Step 3: Create Or Reuse The Service Connect Namespace

You can reuse the Phase 1 namespace:

```text
serviceconnectdemo.local
```

Service Connect uses a Cloud Map namespace as the logical boundary for service discovery. You do not need to manually create `api2.serviceconnectdemo.local` and `api3.serviceconnectdemo.local` records for Phase 2.

If you already created Cloud Map services for Phase 1, leave them alone during the migration. Once Phase 2 works, you can clean up the old Phase 1 Cloud Map service discovery entries if nothing else uses them.

---

## Step 4: Enable Service Connect On Api3

Start with the deepest backend.

Go to:

```text
ECS -> Clusters -> serviceconnectdemo-cluster -> Services -> serviceconnectdemo-api3 -> Update
```

Enable Service Connect:

```text
Service Connect: Enabled
Namespace: serviceconnectdemo.local
Service Connect service type: Client and server
Port name: api3-http
Discovery name: api3
Client alias DNS name: api3
Client alias port: 8080
```

Deploy the service and wait until the new Api3 task is running.

Verify the task has two containers:

```text
ServiceConnectDemo.Api3 application container
Service Connect proxy container
```

---

## Step 5: Enable Service Connect On Api2

Api2 both receives calls from Api1 and calls Api3.

Update `serviceconnectdemo-api2`:

```text
Service Connect: Enabled
Namespace: serviceconnectdemo.local
Service Connect service type: Client and server
Port name: api2-http
Discovery name: api2
Client alias DNS name: api2
Client alias port: 8080
```

Set the Api2 environment variable:

```text
Downstream__Api3BaseUrl=http://api3:8080
```

Deploy the service and wait for replacement tasks.

---

## Step 6: Enable Service Connect On Api1

Api1 receives traffic from the ALB and calls Api2.

Update `serviceconnectdemo-api1`:

```text
Service Connect: Enabled
Namespace: serviceconnectdemo.local
Service Connect service type: Client and server
Port name: api1-http
Discovery name: api1
Client alias DNS name: api1
Client alias port: 8080
```

Set the Api1 environment variable:

```text
Downstream__Api2BaseUrl=http://api2:8080
```

Keep the existing ALB target group association for Api1 for now.

Deploy the service and wait for replacement tasks.

---

## Step 7: Test Service Connect Without TLS

Call the existing CloudFront URL:

```text
https://<cloudfront-domain>/chain
```

Expected response:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```

At this point, the external path is still HTTPS:

```text
Client -> HTTPS -> CloudFront -> HTTPS -> ALB
```

The internal path should now use Service Connect names:

```text
Api1 -> http://api2:8080
Api2 -> http://api3:8080
```

If this fails, check:

```text
Api1 environment variable Downstream__Api2BaseUrl
Api2 environment variable Downstream__Api3BaseUrl
Task definition port mapping names
Service Connect namespace
Service Connect endpoint names
Security group rules
Api1, Api2, Api3 CloudWatch logs
```

---

## Step 8: Prepare For Service Connect TLS

Service Connect TLS requires AWS Private CA.

Create or choose a private certificate authority:

```text
AWS Private CA mode: Short-lived certificate mode recommended
Required tag: AmazonECSManaged = true
```

Important cost note:

```text
AWS Private CA has a cost.
Service Connect rotates certificates automatically.
Do not leave the private CA running after the lab if you do not need it.
```

Service Connect TLS also uses Secrets Manager to store private key material managed by ECS.

---

## Step 9: Create The ECS Infrastructure IAM Role

Service Connect TLS needs an ECS infrastructure role that lets ECS manage certificates and related resources.

Create the ECS infrastructure role using the AWS documentation for:

```text
Amazon ECS infrastructure IAM role
```

The role is used by ECS, not by your application code.

You will select this role when enabling TLS in the ECS Service Connect configuration.

---

## Step 10: Enable TLS On Api3

Update `serviceconnectdemo-api3` first.

In Service Connect configuration, enable TLS:

```text
TLS: Enabled
AWS Private CA: <your-private-ca-arn>
IAM role: <ecs-infrastructure-role>
KMS key: AWS owned key, or your own symmetric KMS key
```

Keep:

```text
Port name: api3-http
Discovery name: api3
Client alias DNS name: api3
Client alias port: 8080
```

Deploy and wait for the new Api3 task.

---

## Step 11: Enable TLS On Api2

Update `serviceconnectdemo-api2` and enable the same TLS settings:

```text
TLS: Enabled
AWS Private CA: <your-private-ca-arn>
IAM role: <ecs-infrastructure-role>
KMS key: AWS owned key, or your own symmetric KMS key
```

Change Api2's downstream URL:

```text
Downstream__Api3BaseUrl=https://api3:8080
```

Deploy and wait for the new Api2 task.

---

## Step 12: Enable TLS On Api1

Update `serviceconnectdemo-api1` and enable Service Connect TLS:

```text
TLS: Enabled
AWS Private CA: <your-private-ca-arn>
IAM role: <ecs-infrastructure-role>
KMS key: AWS owned key, or your own symmetric KMS key
```

Change Api1's downstream URL:

```text
Downstream__Api2BaseUrl=https://api2:8080
```

Deploy and wait for the new Api1 task.

---

## Step 13: Change ALB To HTTPS Toward Api1

In Phase 1, the ALB forwarded HTTP to Api1.

For HTTPS throughout, create or update the Api1 target group:

```text
Target type: IP
Protocol: HTTPS
Port: 8080
Health check protocol: HTTPS
Health check path: /health
Health check port: traffic port, or explicitly 8080
Success codes: 200
```

The ALB listener remains:

```text
Protocol: HTTPS
Port: 443
Certificate: ACM public certificate for the ALB domain
Default action: Forward to Api1 HTTPS target group
```

AWS notes for Service Connect TLS with ALB:

```text
Use awsvpc network mode.
Use an HTTPS target group.
Configure the health check port to match the Service Connect service container port.
Avoid ingressPortOverride for the Service Connect service.
```

For this lab:

```text
Container port: 8080
Health check port: 8080
```

---

## Step 14: Security Group Updates

The logical ports remain the same:

```text
ALB -> Api1 on 8080
Api1 -> Api2 on 8080
Api2 -> Api3 on 8080
```

The difference is that the traffic is now HTTPS/TLS instead of plain HTTP where Service Connect TLS is involved.

Recommended inbound rules:

| Security group | Inbound source | Port |
| --- | --- | ---: |
| ALB SG | CloudFront origin-facing prefix list, or internet for lab testing | 443 |
| Api1 SG | ALB SG | 8080 |
| Api2 SG | Api1 SG | 8080 |
| Api3 SG | Api2 SG | 8080 |

Outbound rules:

| Security group | Destination | Port |
| --- | --- | ---: |
| Api1 SG | Api2 SG | 8080 |
| Api2 SG | Api3 SG | 8080 |
| Api1 SG, Api2 SG, Api3 SG | VPC endpoint SG | 443 |

If using VPC endpoints, make sure you have endpoints for services used by ECS and TLS:

```text
ECR API
ECR DKR
S3 gateway endpoint
CloudWatch Logs
Secrets Manager
KMS, if using a customer managed KMS key
AWS Private CA, if private tasks need private endpoint access for your setup
```

If you do not have the required endpoints and no NAT Gateway, deployments or certificate operations may fail.

---

## Step 15: Final Test

Call the public CloudFront URL:

```text
https://<cloudfront-domain>/chain
```

Expected response includes all three APIs:

```text
ServiceConnectDemo.Api1
ServiceConnectDemo.Api2
ServiceConnectDemo.Api3
```

Final traffic path:

```text
Client
  -> HTTPS
CloudFront
  -> HTTPS
ALB
  -> HTTPS target group on port 8080
Api1 Service Connect proxy
  -> TLS
Api2 Service Connect proxy
  -> TLS
Api3 Service Connect proxy
```

---

## Step 16: Verify Service Connect Is Being Used

Check the ECS tasks for each service.

Each task should have:

```text
Application container
Service Connect proxy container
```

Check ECS service events for:

```text
Service Connect enabled
New deployment completed
Tasks steady state
```

Check CloudWatch metrics for Service Connect.

Check CloudWatch logs for each application:

```text
Api1 should call https://api2:8080
Api2 should call https://api3:8080
```

The application should no longer log calls to:

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
- Api1, Api2, and Api3 task definitions have named port mappings
- Api3 has Service Connect enabled as client-server
- Api2 has Service Connect enabled as client-server
- Api1 has Service Connect enabled as client-server
- Api1 calls api2 instead of api2.serviceconnectdemo.local
- Api2 calls api3 instead of api3.serviceconnectdemo.local
- Service Connect works without TLS
- AWS Private CA is created or selected
- AWS Private CA has AmazonECSManaged=true tag
- ECS infrastructure IAM role exists
- Service Connect TLS is enabled on Api1, Api2, and Api3
- Api1 calls https://api2:8080
- Api2 calls https://api3:8080
- ALB target group uses HTTPS on port 8080
- CloudFront /chain returns all three API names
```

## Cleanup Notes

After the lab, consider cleaning up:

```text
AWS Private CA
Service Connect TLS Secrets Manager secrets created by ECS
Unused Phase 1 Cloud Map services
Unused HTTP target groups
Old ECS task definition revisions
CloudFront distribution
ALB
ECS services
ECR repositories
VPC endpoints
```

Be careful with the AWS Private CA. It can create ongoing cost if left active.

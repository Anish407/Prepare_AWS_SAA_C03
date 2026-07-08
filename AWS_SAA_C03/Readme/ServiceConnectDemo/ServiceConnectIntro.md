# Amazon ECS Service Connect - Practical README

This README explains Amazon ECS Service Connect using a practical two-service architecture. It covers how Service Connect works, how proxies are created, how load balancing works, how traffic flows between ECS tasks, and what to know before using it in production.

Reference documentation:

- Amazon ECS Service Connect components: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-concepts-deploy.html
- Use Service Connect to connect Amazon ECS services: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect.html
- Encrypt Amazon ECS Service Connect traffic: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-tls.html
- Configure Service Connect with AWS CLI: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/create-service-connect.html

---

## 1. What is ECS Service Connect?

Amazon ECS Service Connect is an ECS-native way to manage service-to-service communication between ECS services.

Instead of every service needing to know the IP addresses of other running tasks, Service Connect gives services stable internal names such as:

```text
http://orders:8080
http://payments:8080
http://products:8080
```

Your application calls the service name. The Service Connect proxy handles discovery, load balancing, retries, timeouts, outlier detection, and optional TLS encryption.

Simple definition:

```text
ECS Service Connect = service discovery + managed sidecar proxy + traffic management for ECS services
```

It is useful when one ECS service needs to call another ECS service.

---

## 2. The problem it solves

Assume you have two ECS services:

```text
frontend-service  --->  orders-service
```

Each service can have multiple ECS tasks.

```text
frontend-service
  frontend-task-1
  frontend-task-2

orders-service
  orders-task-1
  orders-task-2
  orders-task-3
```

Each task receives its own private IP address. These IPs are not stable. When ECS replaces a task, the old IP disappears and a new IP appears.

Without Service Connect, the frontend needs a reliable way to discover the current orders tasks.

Common approaches are:

```text
1. Internal ALB
   frontend -> internal ALB -> orders tasks

2. Cloud Map DNS service discovery
   frontend -> orders.local -> task IPs

3. ECS Service Connect
   frontend app -> frontend local proxy -> selected orders task proxy -> orders app
```

Service Connect is usually cleaner than creating an internal ALB for every ECS-to-ECS service call.

---

## 3. Key concepts

### 3.1 Namespace

A namespace is the logical boundary where services discover each other.

Example:

```text
Namespace: myapp.local
```

Inside this namespace, you may have services such as:

```text
frontend
orders
payments
products
```

A service inside the namespace can call another Service Connect endpoint using its configured name.

Example:

```text
http://orders:8080
```

Important:

- A Service Connect namespace is backed by AWS Cloud Map.
- One ECS service can be associated with one Service Connect namespace.
- Services need to be in the same namespace to use the Service Connect endpoint names.

---

### 3.2 Client service

A client service makes requests to other services.

Example:

```text
frontend-service
```

It may not need to expose an internal endpoint, but it needs to call backend services.

Example:

```text
frontend-service -> orders-service
frontend-service -> products-service
```

---

### 3.3 Client-server service

A client-server service receives requests from other services.

Example:

```text
orders-service
payments-service
products-service
```

These services expose a named port through Service Connect.

Example:

```text
orders:8080
```

---

### 3.4 Service Connect proxy

When Service Connect is enabled, ECS adds a managed proxy sidecar to each new task.

Example task without Service Connect:

```text
orders-task
  orders-app-container
```

Example task with Service Connect:

```text
orders-task
  orders-app-container
  service-connect-proxy-container
```

Important:

- The proxy is added by ECS.
- The proxy is not directly added by you in the task definition.
- The proxy runs as a sidecar container in the same task.
- Your app does not directly manage the proxy.

---

## 4. How many proxies are created?

One Service Connect proxy is created per ECS task that has Service Connect enabled.

It is not one proxy per ECS service.

It is not one central proxy for the whole cluster.

It is one proxy per running task.

Example:

```text
Service A: 3 tasks
Service B: 4 tasks
```

If both services have Service Connect enabled:

```text
Total Service Connect proxies = 3 + 4 = 7 proxies
```

Visual example:

```text
Service A
  Task A1: App + Proxy
  Task A2: App + Proxy
  Task A3: App + Proxy

Service B
  Task B1: App + Proxy
  Task B2: App + Proxy
  Task B3: App + Proxy
  Task B4: App + Proxy
```

Rule:

```text
Number of Service Connect proxies = number of running ECS tasks with Service Connect enabled
```

Production implication:

```text
More tasks = more proxies = more CPU and memory overhead
```

So you must account for proxy resources when sizing ECS tasks.

---

## 5. How traffic flows

Assume this setup:

```text
frontend-service calls orders-service
```

Your frontend application calls:

```text
http://orders:8080/api/orders
```

Traffic flow:

```text
frontend app container
        |
        v
frontend task local Service Connect proxy
        |
        v
selected orders task Service Connect proxy
        |
        v
orders app container
```

More detailed flow:

```text
1. The frontend app sends a request to http://orders:8080.
2. The local Service Connect proxy in the frontend task handles the request.
3. The proxy knows that 'orders' is a Service Connect endpoint in the namespace.
4. The proxy has a list of available orders tasks.
5. The proxy selects one backend task.
6. The request is sent to the selected orders task's Service Connect proxy.
7. The destination proxy forwards the request to the orders application container.
8. The response returns through the same path.
```

Important:

```text
The application does not choose the destination task.
The caller-side Service Connect proxy chooses the destination task.
```

---

## 6. How does Service Connect know which proxy/task to call?

When a service is configured as a Service Connect client-server service, ECS registers the service endpoint in the namespace.

Conceptually, the namespace has information like this:

```text
orders -> [
  orders-task-1 endpoint,
  orders-task-2 endpoint,
  orders-task-3 endpoint
]
```

Each client-side Service Connect proxy can use this information to resolve the service name.

So when the frontend app calls:

```text
http://orders:8080
```

The frontend task proxy understands:

```text
orders = backend service with multiple available task endpoints
```

Then it chooses a destination.

---

## 7. How load balancing works

Service Connect uses client-side load balancing through the local proxy.

If `orders-service` has 3 tasks:

```text
orders-task-1
orders-task-2
orders-task-3
```

The frontend task proxy distributes requests across them.

Example:

```text
Request 1 -> orders-task-1
Request 2 -> orders-task-2
Request 3 -> orders-task-3
Request 4 -> orders-task-1
Request 5 -> orders-task-2
Request 6 -> orders-task-3
```

This is round-robin style load balancing.

Important:

```text
Load balancing is distributed.
There is no central Service Connect load balancer.
Each caller task's proxy performs its own load balancing.
```

Example with two frontend tasks:

```text
frontend-task-1 proxy -> balances across orders tasks
frontend-task-2 proxy -> balances across orders tasks
```

Visual:

```text
frontend-task-1
  frontend app
    |
    v
  proxy-A1
    |
    | chooses orders-task-2
    v
  orders-task-2 proxy
    |
    v
  orders app

frontend-task-2
  frontend app
    |
    v
  proxy-A2
    |
    | chooses orders-task-3
    v
  orders-task-3 proxy
    |
    v
  orders app
```

---

## 8. What happens when tasks scale?

Assume `orders-service` scales from 3 tasks to 5 tasks.

Before scaling:

```text
orders -> [
  orders-task-1,
  orders-task-2,
  orders-task-3
]
```

After scaling:

```text
orders -> [
  orders-task-1,
  orders-task-2,
  orders-task-3,
  orders-task-4,
  orders-task-5
]
```

The Service Connect namespace and ECS-managed proxy behavior allow clients to discover the new backend tasks.

From the application's perspective, nothing changes.

The app still calls:

```text
http://orders:8080
```

---

## 9. What happens when a task dies?

Assume this backend service:

```text
orders-task-1
orders-task-2
orders-task-3
```

If `orders-task-2` crashes, ECS stops it and may start a replacement:

```text
orders-task-4
```

The target list changes from:

```text
orders -> [
  orders-task-1,
  orders-task-2,
  orders-task-3
]
```

to:

```text
orders -> [
  orders-task-1,
  orders-task-3,
  orders-task-4
]
```

The client proxies eventually use the updated list.

Service Connect also has outlier detection behavior. If a destination fails repeatedly, the proxy can temporarily avoid that target.

Production implication:

```text
Service Connect reduces the pain of task churn, but it does not remove the need for correct health checks, graceful shutdown, sensible timeouts, and retry strategy.
```

---

## 10. Ports and endpoint names

Service Connect depends heavily on named port mappings in the ECS task definition.

Example task definition port mapping:

```json
{
  "portMappings": [
    {
      "name": "orders-api",
      "containerPort": 8080,
      "protocol": "tcp",
      "appProtocol": "http"
    }
  ]
}
```

The port name is important:

```text
orders-api
```

Service Connect references this named port when creating the service endpoint.

Example Service Connect configuration:

```text
portName: orders-api
discoveryName: orders
clientAlias:
  dnsName: orders
  port: 8080
```

Then clients can call:

```text
http://orders:8080
```

You can expose a different client alias port than the container port, but be careful. Your security groups and NACLs still need to allow the correct traffic path.

---

## 11. HTTP, HTTPS, TLS, and Service Connect

By default, your application may call another service using HTTP:

```text
http://orders:8080
```

If Service Connect TLS is not enabled, the service-to-service traffic is not encrypted by Service Connect.

If Service Connect TLS is enabled, ECS Service Connect can encrypt traffic between Service Connect proxies using TLS.

Conceptually:

```text
frontend app
  -> local frontend proxy
  -> encrypted TLS traffic between proxies
  -> orders proxy
  -> orders app
```

Important:

```text
The application code does not need to manage TLS certificates.
The Service Connect proxies handle TLS between themselves.
```

Service Connect TLS uses AWS Private CA for certificates.

Production implication:

```text
Service Connect TLS improves service-to-service encryption, but AWS Private CA has cost and operational implications.
Do not enable it blindly without understanding the price and certificate authority lifecycle.
```

Recommended lab order:

```text
1. First get Service Connect working without TLS.
2. Verify service-to-service calls work.
3. Then enable Service Connect TLS.
4. Verify traffic encryption.
```

Do not start with TLS, Private CA, IAM infrastructure roles, Service Connect, ECS, ALB, and CloudFront all at once. Debugging becomes unnecessarily painful.

---

## 12. Service Connect vs internal ALB

### Internal ALB pattern

```text
frontend-service -> internal ALB -> orders-service tasks
```

An internal ALB is useful when:

```text
- Consumers are not only ECS services.
- You need path-based routing.
- You need host-based routing.
- You need a stable endpoint outside the ECS Service Connect namespace.
- Multiple applications or VPC-level consumers need to call the service.
- You want central L7 routing rules.
```

### Service Connect pattern

```text
frontend-service -> frontend local proxy -> selected orders task proxy -> orders app
```

Service Connect is useful when:

```text
- ECS service A calls ECS service B.
- You want stable service names.
- You do not want an internal ALB per service.
- You want ECS-managed service discovery.
- You want proxy-level retries, timeouts, and outlier detection.
- You want optional service-to-service TLS without app certificate handling.
```

Honest recommendation:

```text
For ECS-to-ECS internal calls, prefer Service Connect unless you have a clear reason to use an internal ALB.
```

---

## 13. Service Connect vs Cloud Map

Service Connect uses AWS Cloud Map, but it is not just Cloud Map.

### Cloud Map only

```text
frontend app -> DNS lookup -> backend task IP -> backend app
```

The application or HTTP client must handle many things itself:

```text
- DNS behavior
- retries
- bad target handling
- connection reuse
- timeout strategy
- load distribution behavior
```

### Service Connect

```text
frontend app -> local Service Connect proxy -> backend Service Connect proxy -> backend app
```

Service Connect gives you:

```text
- service discovery
- load balancing
- retries
- timeout handling
- outlier detection
- optional TLS
- ECS-native configuration
```

Simple comparison:

```text
Cloud Map = service discovery
Service Connect = service discovery + traffic management
```

---

## 14. Service Connect vs VPC Lattice

Use Service Connect when:

```text
- The main communication is ECS service to ECS service.
- Services are part of the ECS ecosystem.
- You want a lightweight service-mesh-like feature without introducing a full service mesh.
```

Use VPC Lattice when:

```text
- You need ECS, Lambda, EC2, and other compute types to communicate consistently.
- You need cross-VPC service access.
- You need cross-account service networks.
- You want central auth policies for service access.
- You need a broader service networking layer beyond ECS.
```

For a simple ECS microservices architecture, Service Connect is usually enough.

For multi-account, multi-VPC, mixed-compute architectures, VPC Lattice may be a better fit.

---

## 15. Example production-style architecture

```text
                         Internet
                            |
                            v
                      Amazon CloudFront
                            |
                            v
                       Public ALB
                            |
                            v
                   frontend ECS service
                  +----------------------+
                  | frontend container   |
                  | Service Connect proxy|
                  +----------+-----------+
                             |
                             | http://orders:8080
                             v
                    orders ECS service
                  +----------------------+
                  | Service Connect proxy|
                  | orders container     |
                  +----------+-----------+
                             |
                             | http://payments:8080
                             v
                   payments ECS service
                  +----------------------+
                  | Service Connect proxy|
                  | payments container   |
                  +----------------------+
```

Recommended split:

```text
External traffic:
User -> CloudFront -> ALB -> frontend ECS service

Internal service-to-service traffic:
frontend ECS service -> Service Connect -> backend ECS service
backend ECS service -> Service Connect -> another internal ECS service
```

---

## 16. Practical .NET example

In a .NET frontend service, the code can use the Service Connect endpoint name.

```csharp
builder.Services.AddHttpClient("OrdersClient", client =>
{
    client.BaseAddress = new Uri("http://orders:8080");
});
```

Usage:

```csharp
var client = httpClientFactory.CreateClient("OrdersClient");
var response = await client.GetAsync("/api/orders");
```

The application does not need to know:

```text
- ECS task IPs
- Cloud Map internals
- proxy IPs
- backend task count
```

It only needs to know:

```text
http://orders:8080
```

---

## 17. Deployment behavior and rollout order

When you enable Service Connect on an existing ECS service, ECS creates a new service deployment.

Existing running tasks do not magically get Service Connect behavior.

This means:

```text
Old tasks may not have the Service Connect proxy.
New tasks will have the Service Connect proxy.
```

Recommended rollout order:

```text
1. Enable Service Connect on backend/client-server service first.
2. Wait for ECS to deploy replacement backend tasks.
3. Enable Service Connect on frontend/client service.
4. Wait for ECS to deploy replacement frontend tasks.
5. Update or verify frontend calls to the Service Connect endpoint name.
```

Example:

```text
orders-service is backend.
frontend-service is client.
```

Rollout:

```text
1. Enable Service Connect on orders-service.
2. Verify orders tasks are running with Service Connect proxy.
3. Enable Service Connect on frontend-service.
4. Verify frontend tasks are running with Service Connect proxy.
5. Test frontend -> orders call.
```

---

## 18. Production checklist

### 18.1 Task sizing

Service Connect adds a proxy sidecar to each task.

You must allocate enough CPU and memory for the proxy.

Good practice:

```text
- Add extra CPU and memory headroom for the proxy.
- Load test with realistic traffic.
- Watch CPU and memory for both app and proxy behavior.
```

Do not size tasks as if only your app container exists.

---

### 18.2 Health checks

Service Connect does not remove the need for healthy backend tasks.

Use proper health checks:

```text
- Container health checks
- ALB health checks for externally exposed services
- Application-level readiness endpoints
- Graceful shutdown handling
```

Bad health checks cause bad routing decisions.

---

### 18.3 Timeouts

Do not rely blindly on defaults.

Define timeouts intentionally:

```text
- HTTP client timeout in application code
- Service Connect timeout configuration
- ALB idle timeout if ALB is involved
- API Gateway or CloudFront timeout if used externally
```

For long-running operations, prefer asynchronous processing using SQS, EventBridge, Step Functions, or background workers.

A backend API call that takes minutes is usually a design smell.

---

### 18.4 Retries

Retries are useful but dangerous if misused.

Bad retry strategy can cause retry storms.

Example problem:

```text
orders-service is slow
frontend retries aggressively
many frontend tasks retry at the same time
orders-service receives even more traffic
outage becomes worse
```

Production advice:

```text
- Use retries only for transient failures.
- Use exponential backoff in application clients where appropriate.
- Avoid retrying non-idempotent operations unless idempotency keys are used.
- Monitor retry counts and latency.
```

---

### 18.5 Idempotency

If a request can be retried, the backend operation should ideally be idempotent.

Example:

```text
POST /orders
```

If the client retries after a timeout, the backend may create two orders unless idempotency is handled.

Better:

```text
POST /orders
Idempotency-Key: abc-123
```

Backend logic:

```text
If request with same idempotency key was already processed, return the original result.
```

This is very important in payment, order, booking, and job-submission systems.

---

### 18.6 Security groups and networking

Even with Service Connect, VPC networking rules still matter.

Check:

```text
- ECS task security groups
- Inbound rules between services
- Outbound rules from clients
- NACL rules
- Route tables
- VPC endpoints if no NAT Gateway is used
```

Service Connect does not bypass security groups.

If traffic is blocked at the network level, the proxy cannot magically fix it.

---

### 18.7 TLS and encryption

For production, decide whether service-to-service encryption is required.

Options:

```text
1. No Service Connect TLS
   Simpler setup, but traffic between services is not encrypted by Service Connect.

2. Service Connect TLS with AWS Private CA
   Stronger security, but more cost and operational complexity.

3. Application-level HTTPS/mTLS
   More app responsibility, certificate management complexity moves into the application/runtime.
```

Good production approach:

```text
- Use TLS where compliance or security requirements demand it.
- Understand AWS Private CA cost before enabling Service Connect TLS.
- Verify TLS is actually enabled.
- Document certificate authority ownership and lifecycle.
```

---

### 18.8 Observability

For production, you need visibility into service-to-service communication.

Monitor:

```text
- ECS service desired/running task count
- task restarts
- container CPU and memory
- Service Connect metrics
- HTTP 5xx errors
- latency p50/p95/p99
- retry rates
- timeout rates
- failed connections
- CloudWatch logs
- application logs with correlation IDs
```

Strong recommendation:

```text
Add correlation IDs to every inbound request and propagate them across service calls.
```

Example:

```text
x-correlation-id: 2f8a7c1e-9a0d-4e5d-b4f2-91f0f3a12345
```

Without correlation IDs, debugging distributed ECS services becomes painful.

---

### 18.9 Graceful shutdown

When ECS stops a task, your application should handle shutdown gracefully.

Why this matters:

```text
- ECS may replace tasks during deployments.
- Auto scaling may stop tasks.
- Failed health checks may trigger replacements.
```

Good practice:

```text
- Stop accepting new requests.
- Finish in-flight requests where possible.
- Respect SIGTERM.
- Configure appropriate stop timeout.
- Avoid killing long-running work abruptly.
```

---

### 18.10 Deployment safety

When using Service Connect in production:

```text
- Use rolling deployments carefully.
- Monitor errors during deployment.
- Avoid changing port names casually.
- Avoid changing discovery names casually.
- Test service communication after each deployment.
```

Changing endpoint names or port names can break clients.

Treat Service Connect names like API contracts.

---

### 18.11 Cost awareness

Service Connect itself may not be the biggest cost, but production usage has indirect costs:

```text
- More CPU/memory per task due to proxy sidecar
- More CloudWatch logs and metrics
- AWS Private CA cost if TLS is enabled
- Extra task capacity needed at scale
```

Do not ignore the sidecar cost in high-scale services.

---

### 18.12 Compatibility checks

Before using Service Connect, verify support for your workload.

Known important considerations:

```text
- Works with ECS services, not standalone tasks.
- Linux Fargate platform version must support it.
- Windows containers are not supported.
- HTTP/1.0 is not supported.
- Some deployment types are not supported.
- Service Connect TLS requires supported networking mode.
```

Always check the latest AWS documentation before committing to an architecture.

---

## 19. Common mistakes

### Mistake 1: Thinking there is one proxy per service

Wrong:

```text
orders-service has one proxy
```

Correct:

```text
Each orders task has its own proxy
```

---

### Mistake 2: Forgetting to enable Service Connect on the client service

If only the backend is configured but the client tasks do not have Service Connect enabled, the client may not resolve the Service Connect endpoint as expected.

Correct approach:

```text
Enable Service Connect on both sides where needed:
- backend as client-server
- frontend as client
```

---

### Mistake 3: Forgetting named port mappings

Service Connect depends on named ports.

Bad:

```json
{
  "containerPort": 8080
}
```

Better:

```json
{
  "name": "orders-api",
  "containerPort": 8080,
  "protocol": "tcp",
  "appProtocol": "http"
}
```

---

### Mistake 4: Not accounting for proxy resources

Bad assumption:

```text
My app needs 512 CPU and 1024 MB, so the ECS task needs exactly that.
```

Better:

```text
My app needs resources, and the Service Connect proxy also needs resources.
I should add headroom and load test.
```

---

### Mistake 5: Using Service Connect for the wrong problem

Service Connect is not a universal networking solution.

Use it for:

```text
ECS service-to-service communication
```

Do not force it for:

```text
- public ingress
- non-ECS consumers
- broad cross-account service networking
- replacing all API Gateway/ALB use cases
```

---

## 20. Recommended lab design

Start with this:

```text
CloudFront -> public ALB -> frontend ECS service -> Service Connect -> backend ECS service
```

Services:

```text
frontend-service
backend-service / orders-service
```

Minimum features:

```text
- ECS Fargate
- awsvpc networking
- one ECS cluster
- one Service Connect namespace
- frontend service with Service Connect client configuration
- backend service with Service Connect client-server configuration
- backend port mapping with a name
- frontend calls http://orders:8080
```

Suggested phases:

```text
Phase 1: Deploy backend service normally.
Phase 2: Enable Service Connect on backend.
Phase 3: Deploy frontend with Service Connect enabled.
Phase 4: Make frontend call backend using Service Connect endpoint.
Phase 5: Scale backend service to multiple tasks and test load balancing.
Phase 6: Stop one backend task and observe recovery.
Phase 7: Add logging, correlation IDs, and metrics.
Phase 8: Optionally enable Service Connect TLS.
```

---

## 21. Mental model to remember

Best simple mental model:

```text
Every ECS task gets a smart local networking assistant.
```

Your app says:

```text
Call orders.
```

The local proxy says:

```text
I know the available orders tasks.
I will pick one.
I will route the request.
I can retry or avoid bad targets.
If TLS is enabled, I will encrypt traffic to the destination proxy.
```

---

## 22. Final summary

ECS Service Connect gives ECS services a stable and managed way to communicate with each other.

Important points:

```text
- One proxy is created per ECS task.
- The caller-side proxy performs load balancing.
- Service Connect uses a namespace backed by Cloud Map.
- Your app calls stable names like http://orders:8080.
- The proxy handles discovery, load balancing, retries, timeouts, and outlier detection.
- TLS can be enabled using AWS Private CA.
- It is best for ECS-to-ECS internal service communication.
- It does not replace CloudFront, public ALB, API Gateway, or VPC Lattice in all cases.
```

For your ECS architecture, a clean starting pattern is:

```text
External request path:
User -> CloudFront -> ALB -> frontend ECS service

Internal request path:
frontend ECS service -> Service Connect -> backend ECS service
```

That gives you a practical, production-relevant ECS service-to-service communication model without creating unnecessary internal load balancers for every backend service.

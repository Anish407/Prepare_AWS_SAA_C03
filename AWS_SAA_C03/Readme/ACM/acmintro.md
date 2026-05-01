# AWS Certificate Manager (ACM) — SAA-C03 Exam README

> Goal: understand AWS Certificate Manager deeply enough for the AWS Certified Solutions Architect Associate SAA-C03 exam and real-world AWS architecture decisions.

---

## 1. What ACM Is

AWS Certificate Manager, usually called **ACM**, is the AWS service used to provision, store, manage, deploy, and renew **SSL/TLS X.509 certificates** for AWS workloads.

In simple terms:

```text
User/browser/client
        |
        | HTTPS / TLS
        v
CloudFront / ALB / API Gateway / other ACM-integrated service
        |
        v
Your application
```

ACM helps you avoid manually buying certificates, uploading private keys, tracking expiry dates, and renewing certificates yourself.

For the SAA-C03 exam, ACM normally appears in questions about:

- HTTPS for websites and APIs
- CloudFront custom domains
- Application Load Balancer HTTPS listeners
- API Gateway custom domains
- Regional vs global services
- Certificate renewal
- Public vs private certificates
- DNS validation vs email validation
- Imported certificates
- Private CA / internal PKI
- Security and encryption in transit

---

## 2. Why ACM Matters Architecturally

Without ACM, you would usually need to:

1. Buy or request a certificate from a public certificate authority.
2. Generate or manage the private key.
3. Upload the certificate and key to your servers or load balancers.
4. Track expiry dates.
5. Renew and redeploy the certificate before expiry.
6. Avoid leaking private keys.

ACM removes a large part of that operational burden when used with supported AWS services.

The exam often tests whether you choose the managed AWS option instead of building your own certificate lifecycle process.

### Exam mindset

If the question says:

> A company needs HTTPS for an internet-facing application running behind an Application Load Balancer and wants automatic certificate renewal.

The likely answer is:

> Use AWS Certificate Manager to request a public certificate and attach it to the ALB HTTPS listener.

Not:

> Install certificates manually on EC2 instances.

---

## 3. Core Concepts You Must Know

## 3.1 SSL/TLS Certificate

A TLS certificate proves the identity of a domain and enables encrypted communication.

Example:

```text
https://api.example.com
```

The browser checks that:

- The certificate is valid.
- The certificate is not expired.
- The certificate is trusted by a recognized certificate authority.
- The certificate covers `api.example.com`.
- The certificate chain is valid.

If these checks pass, the browser establishes a secure HTTPS connection.

---

## 3.2 Public Certificate

A **public certificate** is trusted by browsers, operating systems, and public clients.

Use public ACM certificates for:

- Public websites
- Public APIs
- CloudFront distributions
- Internet-facing Application Load Balancers
- API Gateway custom domains

Example:

```text
www.example.com  -> CloudFront -> S3 / ALB / API Gateway
api.example.com  -> ALB -> ECS / EC2 / Lambda target
```

Public ACM certificates require **domain ownership validation**.

---

## 3.3 Private Certificate

A **private certificate** is used inside private networks and internal systems. It is not automatically trusted by public browsers unless the client trusts your private CA.

Use private certificates for:

- Internal APIs
- Service-to-service TLS
- Internal load balancers
- Mutual TLS inside an organization
- Private workloads in VPCs
- Enterprise PKI scenarios

Private certificates are issued using **AWS Private Certificate Authority**, commonly called **AWS Private CA**.

Example:

```text
Internal service A ---> HTTPS ---> Internal service B
                         certificate issued by AWS Private CA
```

Private certificates are useful when the certificate should not be publicly trusted or when the domain is private/internal.

---

## 3.4 Imported Certificate

An **imported certificate** is a certificate obtained outside ACM and uploaded into ACM.

You may import a certificate when:

- Your company already uses a third-party certificate authority.
- You have an Extended Validation or Organization Validation certificate from another provider.
- You need to reuse an existing certificate.
- You need a certificate type not directly issued by ACM.

Important exam point:

```text
ACM does not automatically renew imported certificates.
```

You must renew the certificate externally and re-import it before it expires.

---

## 4. Types of Certificates in ACM

| Type | Issued by | Publicly trusted? | Managed renewal? | Common use |
|---|---|---:|---:|---|
| Public ACM certificate | ACM public CA | Yes | Yes, if validation remains valid and certificate is in use | Public websites/APIs |
| Private ACM certificate | AWS Private CA | No, unless clients trust your CA | Yes for eligible ACM-managed private certs | Internal TLS |
| Imported certificate | External CA or internal CA | Depends on issuer | No | Existing enterprise certs |
| Exportable public certificate | ACM public CA, export enabled at creation | Yes | ACM-managed in ACM, but external deployment still needs operational care | EC2/on-prem/container workloads outside integrated services |

---

## 5. ACM and AWS Service Integration

ACM certificates are commonly used with AWS services that terminate TLS.

## 5.1 Application Load Balancer

A common architecture:

```text
Browser
  |
  | HTTPS
  v
Application Load Balancer :443
  |  ACM certificate attached to HTTPS listener
  v
Target group
  |
  v
EC2 / ECS / IP targets / Lambda
```

The ALB receives the HTTPS request and performs TLS termination.

After TLS termination, traffic from ALB to targets may be:

- HTTP
- HTTPS

For many internal applications, ALB to target is HTTP inside a private VPC. For stricter security, you can use HTTPS between ALB and targets as well.

### Exam pattern

Question:

> Users need secure HTTPS access to an application running on EC2 instances behind a load balancer. The company wants AWS to manage certificate renewal.

Answer:

> Request a public certificate in ACM and attach it to an HTTPS listener on an Application Load Balancer.

---

## 5.2 Network Load Balancer

NLB can also use TLS listeners with ACM certificates.

Common use cases:

- Very high performance TCP/TLS workloads
- Static IP needs
- Preserving client IP
- TLS termination at NLB

Typical exam distinction:

| Need | Better choice |
|---|---|
| HTTP routing, path-based routing, host-based routing | ALB |
| TCP/UDP/TLS, static IP, ultra-low latency | NLB |

---

## 5.3 CloudFront

CloudFront is a global CDN. For custom HTTPS domains on CloudFront, ACM has a special regional rule.

```text
Viewer
  |
  | HTTPS to www.example.com
  v
CloudFront distribution
  | ACM certificate must be in us-east-1
  v
Origin: S3 / ALB / API Gateway / custom origin
```

### Critical exam point

```text
For CloudFront viewer certificates, request or import the ACM certificate in us-east-1.
```

Even if your origin is in `eu-north-1`, `eu-west-1`, or any other Region, the certificate attached to the CloudFront distribution must be in **US East (N. Virginia), us-east-1**.

### CloudFront has two TLS relationships

CloudFront can use TLS in two different places:

```text
Viewer/browser ---> CloudFront ---> Origin
        TLS #1              TLS #2
```

### TLS #1: Viewer to CloudFront

For a custom domain like:

```text
https://www.example.com
```

You need a certificate attached to CloudFront.

This certificate must be in:

```text
us-east-1
```

### TLS #2: CloudFront to Origin

If CloudFront connects to an ALB origin using HTTPS, the origin also needs a valid certificate.

For an ALB origin, the certificate for the ALB can be in the same Region as the ALB.

Example:

```text
Viewer -> CloudFront using cert in us-east-1
CloudFront -> ALB in eu-north-1 using ALB cert in eu-north-1
```

This is a very common exam trap.

---

## 5.4 API Gateway Custom Domains

API Gateway can use ACM certificates for custom domain names.

Example:

```text
https://api.example.com/orders
```

Instead of exposing:

```text
https://abc123.execute-api.eu-north-1.amazonaws.com/prod/orders
```

You configure:

- ACM certificate
- API Gateway custom domain
- Base path mapping / API mapping
- Route 53 alias record

### Regional vs edge-optimized API Gateway

Exam-level rule:

| API Gateway endpoint type | Certificate location |
|---|---|
| Regional custom domain | Same Region as the API/custom domain |
| Edge-optimized custom domain | us-east-1, because it uses CloudFront underneath |

---

## 5.5 Elastic Beanstalk

Elastic Beanstalk environments that use load balancers can use ACM certificates through the underlying load balancer.

Exam view:

```text
Elastic Beanstalk app + HTTPS = attach ACM certificate to the load balancer used by the environment.
```

---

## 5.6 CloudFormation and CDK

ACM certificates can be created using IaC.

Example CDK-style thinking:

```text
Hosted zone in Route 53
        |
        v
ACM certificate with DNS validation
        |
        v
ALB / CloudFront / API Gateway
```

Important practical point:

- DNS validation works best when the domain is hosted in Route 53.
- CloudFormation/CDK can automatically create validation records in Route 53 if it controls the hosted zone.
- If DNS is external, you usually need to manually create CNAME validation records.

---

## 6. Domain Validation

ACM must verify that you control the domain before issuing a public certificate.

ACM supports multiple validation methods, but for SAA-C03 you mainly need to understand:

1. DNS validation
2. Email validation

---

## 6.1 DNS Validation

DNS validation is the recommended approach for most AWS architectures.

ACM gives you CNAME records like:

```text
Name:  _abc123.example.com
Value: _xyz987.acm-validations.aws
```

You add the CNAME record to your DNS provider.

If your domain is hosted in Route 53, ACM can often help create the validation record automatically.

### Why DNS validation is preferred

DNS validation is preferred because:

- It supports automatic renewal.
- It is easy to automate with Route 53.
- It avoids dependency on mailbox access.
- It works well with IaC.
- It can validate wildcard certificates.

### Exam rule

```text
Choose DNS validation when the requirement says automatic renewal, automation, Route 53, or least operational overhead.
```

---

## 6.2 Email Validation

Email validation sends approval emails to domain administrative contacts.

Examples:

```text
admin@example.com
administrator@example.com
hostmaster@example.com
postmaster@example.com
webmaster@example.com
```

The domain owner must click approval links.

### Problems with email validation

Email validation is weaker operationally because:

- Someone must receive and approve email.
- Renewal may require manual action.
- It is harder to automate.
- Emails can be missed.
- Admin mailboxes may not exist.

### Exam rule

```text
Avoid email validation when the question asks for automation or least operational effort.
```

---

## 6.3 You Must Validate Every Domain Name

If your certificate covers multiple names, each name must be validated.

Example certificate:

```text
example.com
www.example.com
api.example.com
*.dev.example.com
```

ACM needs proof that you control the relevant domains.

---

## 7. Certificate Names, SANs, and Wildcards

## 7.1 Common Name and SAN

A certificate can contain:

- Common Name, also called CN
- Subject Alternative Names, also called SANs

Modern TLS clients rely heavily on SANs.

Example:

```text
Common Name: example.com
SANs:
  - example.com
  - www.example.com
  - api.example.com
```

The certificate must cover the exact domain used by the client.

---

## 7.2 Wildcard Certificates

A wildcard certificate can cover multiple subdomains at one level.

Example:

```text
*.example.com
```

This covers:

```text
api.example.com
www.example.com
shop.example.com
```

But it does not cover:

```text
example.com
v1.api.example.com
```

To cover both root and one-level subdomains, request:

```text
example.com
*.example.com
```

### Exam trap

`*.example.com` does not automatically cover `example.com`.

---

## 7.3 Multi-Domain Certificate

A single certificate can cover multiple names:

```text
example.com
www.example.com
api.example.com
admin.example.net
```

This is useful when one AWS endpoint serves multiple names.

Be careful not to overload a certificate with too many unrelated domains. Operationally, replacing or validating such a certificate becomes more complex.

---

## 8. Regional Behavior

This is one of the most important ACM exam topics.

## 8.1 ACM Certificates Are Regional

ACM certificates are regional resources.

If you request a certificate in:

```text
eu-north-1
```

You cannot attach that same certificate ARN to an ALB in:

```text
eu-west-1
```

You must request or import a separate certificate in each Region where a regional AWS service needs it.

Example:

```text
ALB in eu-north-1 -> ACM cert in eu-north-1
ALB in eu-west-1  -> ACM cert in eu-west-1
```

---

## 8.2 CloudFront Exception

CloudFront is global, but ACM certificates for CloudFront viewer HTTPS must be in:

```text
us-east-1
```

This is probably the most common ACM exam fact.

### Correct architecture

```text
Route 53 alias
    |
    v
CloudFront distribution
    |
    | Viewer certificate from ACM us-east-1
    v
Origin in any supported Region
```

---

## 9. Renewal Behavior

## 9.1 ACM-Managed Public Certificates

ACM can automatically renew public certificates when:

- The certificate is issued by ACM.
- The certificate is associated with an integrated AWS service.
- Domain validation remains valid.
- DNS validation records still exist if DNS validation was used.

### Exam rule

```text
ACM-managed public certificate + DNS validation + in use = automatic renewal.
```

---

## 9.2 DNS Validation and Renewal

With DNS validation, keep the CNAME validation record in DNS.

Do not delete it after the certificate is issued.

Bad practice:

```text
Create ACM certificate
Add CNAME
Certificate issued
Delete CNAME because certificate is now active
```

Why this is bad:

```text
Future renewal may fail.
```

Correct practice:

```text
Keep the ACM validation CNAME record in DNS permanently.
```

---

## 9.3 Email Validation and Renewal

Email validation may require manual approval during renewal.

This is why DNS validation is usually the better answer for exam scenarios requiring low operational overhead.

---

## 9.4 Imported Certificates

Imported certificates are not automatically renewed by ACM.

You are responsible for:

- Tracking expiry.
- Getting a renewed certificate from the external CA.
- Re-importing the renewed certificate.
- Ensuring the private key and certificate chain are correct.

### Exam rule

```text
If the certificate was imported, ACM will not manage renewal.
```

---

## 10. Can You Export ACM Certificates?

This topic has become more nuanced.

Historically, ACM public certificates were mainly intended for ACM-integrated AWS services and the private key was not exportable.

Current ACM supports **exportable public certificates** when exportability is enabled at certificate creation. ACM also supports exporting eligible private certificates issued through AWS Private CA.

For exam purposes, use this practical rule:

| Scenario | Exam-friendly answer |
|---|---|
| Need HTTPS on ALB, CloudFront, API Gateway | Use ACM certificate directly with the AWS service |
| Need certificate on EC2 manually | Prefer ALB/CloudFront in front, or use an exportable/imported/private certificate depending on requirements |
| Need private internal PKI certificate on non-integrated host | Use AWS Private CA and export private certificate if appropriate |
| Need existing third-party certificate | Import it into ACM, but manage renewal yourself |

Do not assume every ACM certificate can be exported. Export behavior depends on certificate type and how it was created.

---

## 11. ACM with Route 53

ACM and Route 53 work very well together.

Common pattern:

```text
Route 53 hosted zone: example.com
        |
        | DNS validation CNAME
        v
ACM certificate: example.com, *.example.com
        |
        v
CloudFront / ALB / API Gateway
```

Benefits:

- Easier DNS validation
- Easier automation
- Alias records to AWS targets
- Cleaner custom domain setup

### Route 53 alias records

For AWS endpoints, you often use Route 53 alias records instead of raw CNAMEs.

Examples:

```text
www.example.com -> Alias to CloudFront distribution
api.example.com -> Alias to ALB
```

Important:

- Alias records can point apex/root domains to AWS resources.
- CNAME cannot normally be used at the zone apex.

Example:

```text
example.com -> Alias to CloudFront
```

This is valid in Route 53.

---

## 12. ACM with CloudFront — Detailed Exam Notes

## 12.1 Custom Domain Requirement

If you want this:

```text
https://www.example.com
```

Instead of this:

```text
https://d111111abcdef8.cloudfront.net
```

You need:

1. Alternate domain name configured in CloudFront.
2. ACM certificate covering `www.example.com`.
3. Certificate in `us-east-1`.
4. DNS record pointing `www.example.com` to CloudFront.

---

## 12.2 Certificate Must Match Alias

If CloudFront alternate domain name is:

```text
app.example.com
```

The ACM certificate must include:

```text
app.example.com
```

or a matching wildcard:

```text
*.example.com
```

If the certificate only covers:

```text
www.example.com
```

It cannot be used for:

```text
app.example.com
```

---

## 12.3 CloudFront Origin HTTPS

If origin is ALB:

```text
Viewer -> CloudFront -> ALB
```

You may need two certificates:

1. Viewer certificate in `us-east-1` for CloudFront.
2. Origin certificate in the ALB Region for ALB HTTPS listener.

Example:

```text
CloudFront viewer domain: www.example.com
Origin ALB domain: origin.example.com
```

Certificates:

```text
ACM us-east-1: www.example.com
ACM eu-north-1: origin.example.com
```

---

## 13. ACM with ALB — Detailed Exam Notes

## 13.1 HTTPS Listener

To enable HTTPS on ALB:

1. Request/import ACM certificate in the same Region as the ALB.
2. Create HTTPS listener on port 443.
3. Attach certificate to listener.
4. Configure listener rules.
5. Forward to target groups.

Example:

```text
ALB listener :443
  certificate: api.example.com
  rule: /orders/* -> orders target group
  rule: /payments/* -> payments target group
```

---

## 13.2 HTTP to HTTPS Redirect

Common best practice:

```text
Port 80 listener  -> redirect to HTTPS 443
Port 443 listener -> forward to target group
```

Exam scenario:

> A company wants all HTTP traffic redirected to HTTPS.

Answer:

> Configure an ALB HTTP listener rule to redirect HTTP to HTTPS.

---

## 13.3 Multiple Certificates on ALB

ALB supports Server Name Indication, usually called SNI.

SNI allows one HTTPS listener to serve multiple certificates for different hostnames.

Example:

```text
api.example.com    -> certificate A
admin.example.com  -> certificate B
shop.example.net   -> certificate C
```

Client sends the hostname during TLS negotiation. ALB selects the correct certificate.

Exam keyword:

```text
multiple secure websites on same ALB listener
```

Likely answer:

```text
Use SNI with multiple ACM certificates on ALB.
```

---

## 14. ACM with API Gateway — Detailed Exam Notes

## 14.1 Regional Custom Domain

For a regional API Gateway custom domain:

```text
api.example.com -> Regional API Gateway endpoint
```

Use an ACM certificate in the same Region as the API Gateway custom domain.

---

## 14.2 Edge-Optimized Custom Domain

Edge-optimized API Gateway uses CloudFront behind the scenes.

Therefore, certificate must be in:

```text
us-east-1
```

Exam trap:

```text
API Gateway edge-optimized custom domain = us-east-1 certificate
API Gateway regional custom domain = same Region certificate
```

---

## 15. ACM Private CA

AWS Private CA lets you create private certificate authorities without managing your own CA servers.

Use it when you need private trust inside an organization.

Examples:

- Internal service certificates
- Internal mTLS
- Kubernetes internal certificates
- IoT device certificates
- Enterprise private PKI
- Internal ALB HTTPS

Architecture:

```text
AWS Private CA
      |
      v
Private certificate issued through ACM
      |
      v
Internal ALB / service / workload
```

---

## 15.1 Public ACM vs AWS Private CA

| Requirement | Use |
|---|---|
| Public browser-trusted website | ACM public certificate |
| Internal-only service certificate | ACM private certificate with AWS Private CA |
| Existing corporate CA certificate | Import certificate into ACM |
| Need to operate private PKI hierarchy | AWS Private CA |

---

## 15.2 Cost Warning

AWS Private CA is not just a free ACM feature. It has separate pricing.

Exam questions may not focus on detailed pricing, but architecturally you should know:

```text
Public ACM certificates are often free for integrated AWS services.
AWS Private CA has separate cost.
```

Do not create AWS Private CA unless you need private PKI.

---

## 16. Security Notes

## 16.1 Private Key Protection

ACM manages private keys for ACM-issued certificates.

For normal ACM-integrated public certificates, you do not manually handle the private key. This reduces the risk of private key leakage.

Exam mindset:

```text
Managed certificate + no manual private key handling = safer and lower operational overhead.
```

---

## 16.2 Encryption in Transit

ACM is about encryption in transit.

Do not confuse it with:

| Requirement | AWS service/concept |
|---|---|
| Encrypt traffic over HTTPS/TLS | ACM + TLS-enabled AWS service |
| Encrypt S3 objects at rest | SSE-S3 / SSE-KMS |
| Encrypt EBS volumes | EBS encryption / KMS |
| Encrypt RDS storage | RDS encryption / KMS |
| Manage encryption keys | AWS KMS |
| Store secrets | AWS Secrets Manager / SSM Parameter Store |

---

## 16.3 ACM Is Not a Web Application Firewall

ACM provides certificates for TLS.

It does not protect against:

- SQL injection
- Cross-site scripting
- Bot attacks
- DDoS by itself
- Bad API requests

For those, use services such as:

- AWS WAF
- AWS Shield
- CloudFront security controls
- API Gateway throttling and authorizers

---

## 17. Common Exam Scenarios

## Scenario 1: Public Website on S3 + CloudFront

Requirement:

> Host a static website using S3 and CloudFront with custom HTTPS domain.

Solution:

```text
S3 bucket private
CloudFront distribution
ACM public certificate in us-east-1
Route 53 alias record to CloudFront
```

Do not use S3 website endpoint with HTTPS directly. S3 static website endpoints do not support HTTPS directly with your custom certificate. Use CloudFront.

---

## Scenario 2: ECS Service Behind ALB

Requirement:

> ECS service should be accessible securely over HTTPS.

Solution:

```text
ACM certificate in same Region as ALB
ALB HTTPS listener on 443
Forward to ECS target group
Optional HTTP -> HTTPS redirect
```

---

## Scenario 3: Multi-Region ALBs

Requirement:

> Same app is deployed in two Regions, each with its own ALB. Both need HTTPS for `api.example.com`.

Solution:

```text
Request/import ACM certificate in each Region.
Attach each regional certificate to the ALB in that Region.
Use Route 53 latency/failover/weighted routing as needed.
```

Important:

```text
You cannot copy one ACM certificate ARN across Regions.
```

---

## Scenario 4: CloudFront in Front of ALB

Requirement:

> Use CloudFront globally in front of an ALB origin and support HTTPS end-to-end.

Solution:

```text
Viewer -> CloudFront:
  ACM certificate in us-east-1 for www.example.com

CloudFront -> ALB:
  ALB certificate in ALB Region for origin.example.com or matching origin hostname
```

---

## Scenario 5: Existing Third-Party Certificate

Requirement:

> Company already has a certificate from an external CA and wants to use it with ALB.

Solution:

```text
Import certificate into ACM in the same Region as ALB.
Attach imported certificate to ALB HTTPS listener.
Manually handle future renewal and re-import.
```

---

## Scenario 6: Internal Microservices Need TLS

Requirement:

> Internal services need encrypted communication using private certificates.

Solution:

```text
Use AWS Private CA.
Issue private certificates through ACM.
Attach to internal ALB or distribute/export where appropriate.
Ensure clients trust the private CA.
```

---

## Scenario 7: Need Automatic Renewal

Requirement:

> Least operational overhead for certificate renewal.

Best answer:

```text
Use ACM-issued certificate with DNS validation and keep DNS validation records in place.
```

Avoid:

```text
Imported certificates
Email validation
Manual renewal scripts
Certificates installed directly on EC2
```

---

## 18. ACM Decision Table

| Requirement | Best answer |
|---|---|
| HTTPS for CloudFront custom domain | ACM public certificate in us-east-1 |
| HTTPS for ALB | ACM certificate in same Region as ALB |
| HTTPS for regional API Gateway custom domain | ACM certificate in same Region |
| HTTPS for edge-optimized API Gateway custom domain | ACM certificate in us-east-1 |
| Automatic renewal | ACM-issued certificate + DNS validation |
| Existing external certificate | Import into ACM; renew manually |
| Internal-only TLS | AWS Private CA + ACM private certificate |
| Multiple domains on one ALB listener | SNI + multiple ACM certificates |
| Root domain to CloudFront or ALB | Route 53 alias record |
| Wildcard subdomains | `*.example.com`, but also add `example.com` if root is needed |
| Multi-Region same domain | Request/import certificate separately per Region |

---

## 19. Common Mistakes

## Mistake 1: Creating CloudFront Certificate in the Wrong Region

Wrong:

```text
CloudFront certificate in eu-north-1
```

Correct:

```text
CloudFront viewer certificate in us-east-1
```

---

## Mistake 2: Assuming ACM Certificate Can Be Used in Every Region

Wrong:

```text
One ACM certificate can be attached to ALBs in all Regions.
```

Correct:

```text
ACM certificates are regional. Request/import certificates per Region.
```

---

## Mistake 3: Deleting DNS Validation CNAME

Wrong:

```text
Delete validation CNAME after certificate is issued.
```

Correct:

```text
Keep validation CNAME for automatic renewal.
```

---

## Mistake 4: Thinking Wildcard Covers the Root Domain

Wrong:

```text
*.example.com covers example.com
```

Correct:

```text
*.example.com covers api.example.com, www.example.com, etc.
It does not cover example.com.
```

Use:

```text
example.com
*.example.com
```

---

## Mistake 5: Expecting Imported Certificates to Auto-Renew

Wrong:

```text
Imported certificate will be renewed by ACM.
```

Correct:

```text
Imported certificate must be renewed externally and re-imported.
```

---

## Mistake 6: Confusing ACM with KMS

Wrong:

```text
Use ACM to encrypt S3 objects at rest.
```

Correct:

```text
Use ACM for TLS certificates and encryption in transit.
Use KMS/SSE for encryption at rest.
```

---

## Mistake 7: Installing Certificates Directly on EC2 When ALB Is Better

Less ideal:

```text
Install TLS certificate manually on every EC2 instance.
```

Better architecture:

```text
Terminate TLS at ALB using ACM certificate.
Forward traffic to EC2 targets.
```

This reduces operational burden and centralizes certificate management.

---

## 20. Exam Keywords and What They Usually Mean

| Keyword in question | Think |
|---|---|
| custom domain with CloudFront | ACM certificate in us-east-1 |
| least operational overhead | ACM-managed cert + DNS validation |
| automatic renewal | DNS validation, ACM-issued certificate, keep CNAME |
| imported certificate | no ACM-managed renewal |
| internal PKI | AWS Private CA |
| private certificate | AWS Private CA + ACM |
| multiple HTTPS domains on one ALB | SNI |
| HTTPS for ALB | certificate in same Region as ALB |
| regional API Gateway custom domain | certificate in same Region |
| edge-optimized API Gateway | us-east-1 certificate |
| wildcard certificate | covers one subdomain level, not apex |
| root/apex domain to AWS target | Route 53 alias |

---

## 21. Real Architecture Examples

## 21.1 Public Web App with CloudFront and ALB

```text
User
  |
  | HTTPS www.example.com
  v
Route 53 alias record
  |
  v
CloudFront distribution
  | viewer cert: ACM us-east-1
  |
  | HTTPS origin.example.com
  v
Application Load Balancer in eu-north-1
  | origin cert: ACM eu-north-1
  v
ECS Fargate service
```

Key learning:

- CloudFront viewer cert is in `us-east-1`.
- ALB cert is in the ALB Region.
- Route 53 points the user-facing domain to CloudFront.

---

## 21.2 Internal Application with Private TLS

```text
Internal client
  |
  | HTTPS internal-api.company.local
  v
Internal ALB
  | private cert from ACM / AWS Private CA
  v
Private ECS service
```

Key learning:

- Use private certificates when public trust is not needed.
- Clients must trust the private CA.
- This is different from public ACM certificates.

---

## 21.3 API Gateway Custom Domain

```text
Client
  |
  | HTTPS api.example.com
  v
Route 53 alias
  |
  v
API Gateway custom domain
  | ACM certificate
  v
API stage / Lambda integration
```

Key learning:

- Regional API uses cert in same Region.
- Edge-optimized API uses cert in `us-east-1`.

---

## 22. Troubleshooting Checklist

## Certificate stuck in Pending Validation

Check:

- Did you add the DNS CNAME record?
- Did you add it to the public hosted zone, not only private hosted zone?
- Did you add the record exactly as ACM gave it?
- Is DNS propagated?
- Are all SANs validated?
- If using email validation, did the domain owner approve the email?

---

## CloudFront cannot use certificate

Check:

- Is the certificate in `us-east-1`?
- Is the certificate issued, not pending?
- Does the certificate cover the CloudFront alternate domain name?
- Is the alternate domain name added to the distribution?

---

## ALB cannot use certificate

Check:

- Is the certificate in the same Region as the ALB?
- Is the certificate issued?
- Is the certificate associated with HTTPS/TLS listener?
- Does the security group allow inbound 443?
- Does Route 53 point to the ALB?

---

## Automatic renewal failed

Check:

- Is the certificate still in use?
- Were DNS validation records removed?
- Is the domain still valid and publicly resolvable?
- Was it an imported certificate?
- Was email validation used and renewal approval missed?

---

## 23. SAA-C03 Practice Questions

## Question 1

A company hosts a static website using S3 and CloudFront. They want users to access it using `https://www.example.com`. What should they do?

### Answer

Request an ACM public certificate in `us-east-1`, attach it to the CloudFront distribution, add `www.example.com` as an alternate domain name, and create a Route 53 alias record to CloudFront.

### Why

CloudFront requires ACM viewer certificates in `us-east-1`.

---

## Question 2

An application runs behind an ALB in `eu-west-1`. The company needs HTTPS and automatic certificate renewal. What is the best solution?

### Answer

Request an ACM public certificate in `eu-west-1` using DNS validation and attach it to the ALB HTTPS listener.

### Why

ALB is regional, so the certificate must be in the same Region as the ALB. DNS validation supports automated renewal.

---

## Question 3

A company imported a third-party certificate into ACM. The certificate expired and users now receive browser warnings. Why did this happen?

### Answer

ACM does not automatically renew imported certificates. The company must renew the certificate externally and re-import it into ACM.

---

## Question 4

A company needs TLS certificates for internal services that are not publicly accessible. The certificates should be issued from a private CA. What should they use?

### Answer

Use AWS Private CA with ACM private certificates.

---

## Question 5

A company has an ALB serving `api.example.com` and `admin.example.com` on the same HTTPS listener. Each hostname needs a different certificate. What feature should be used?

### Answer

Use SNI with multiple ACM certificates attached to the ALB HTTPS listener.

---

## Question 6

A team created an ACM certificate for `*.example.com`, but users accessing `https://example.com` get certificate errors. Why?

### Answer

`*.example.com` does not cover the root domain `example.com`. The certificate must also include `example.com`.

---

## 24. Brutal Exam Summary

If you remember only these points, remember these:

1. **CloudFront custom HTTPS requires ACM certificate in `us-east-1`.**
2. **ALB uses ACM certificate in the same Region as the ALB.**
3. **API Gateway regional custom domain uses same-Region ACM certificate.**
4. **API Gateway edge-optimized custom domain uses `us-east-1` certificate.**
5. **ACM certificates are regional except CloudFront has the `us-east-1` viewer certificate rule.**
6. **DNS validation is better than email validation for automation and renewal.**
7. **Keep ACM DNS validation CNAME records. Do not delete them.**
8. **Imported certificates are not automatically renewed by ACM.**
9. **Use AWS Private CA for private/internal certificates.**
10. **Wildcard `*.example.com` does not cover `example.com`.**
11. **Use ALB/CloudFront/API Gateway with ACM instead of manually installing certs on EC2 when possible.**
12. **ACM is for encryption in transit, not encryption at rest.**

---

## 25. Final Mental Model

Think of ACM as the managed certificate layer for AWS edge and load balancing services.

```text
Need public HTTPS?
  -> ACM public certificate

Need HTTPS on CloudFront?
  -> Certificate in us-east-1

Need HTTPS on ALB/NLB/API Gateway regional?
  -> Certificate in the same Region

Need automatic renewal?
  -> ACM-issued certificate + DNS validation + keep validation records

Need existing external certificate?
  -> Import into ACM, but renewal is your job

Need internal/private TLS?
  -> AWS Private CA + ACM private certificate
```

For the SAA-C03 exam, ACM questions are usually not about cryptography details. They are about choosing the correct managed AWS service, the correct Region, the correct validation method, and the lowest-operational-overhead architecture.

---

## 26. Source Notes

This README is based on AWS documentation for the SAA-C03 exam scope, AWS Certificate Manager, CloudFront certificate requirements, ACM DNS/email validation, ACM renewal behavior, imported certificates, ACM quotas, and AWS Private CA.


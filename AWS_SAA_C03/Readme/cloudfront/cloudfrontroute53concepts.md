# DNS, Route 53, CloudFront & Domain Ownership -- Complete Guide

This document explains:

-   How domain ownership works
-   Difference between registrar and hosted zone
-   How Route 53 fits into global DNS
-   How name servers work
-   How to buy or move a domain
-   How CloudFront integrates with Route 53
-   How SSL certificates fit into the picture
-   How origins work (S3, ALB, etc.)
-   Enterprise-level architectural patterns

------------------------------------------------------------------------

# 1. What Does "Owning a Domain" Mean?

Owning a domain means:

-   You registered it with a domain registrar
-   You pay yearly registration fees
-   Your information is stored in the global domain registry database
    (WHOIS)
-   The global DNS root knows which name servers are authoritative for
    it

Creating a hosted zone does NOT mean you own a domain.

Domain registration and DNS hosting are separate systems.

------------------------------------------------------------------------

# 2. Registrar vs Hosted Zone

## Registrar

A registrar: - Sells you domain names - Registers your domain in the
global registry (.com, .net, etc.) - Stores legal ownership data -
Controls name server delegation at the registry level

Examples: - Route 53 (also acts as registrar) - GoDaddy - Namecheap

## Hosted Zone (Route 53)

A hosted zone: - Is an authoritative DNS database - Stores DNS records -
Answers DNS queries for your domain - Does NOT register or own domains

It contains records like:

-   A (IPv4 mapping)
-   AAAA (IPv6 mapping)
-   CNAME (name → name)
-   ALIAS (AWS-specific mapping)
-   MX (mail routing)
-   TXT (verification/SPF/DKIM)
-   NS (delegation records)

------------------------------------------------------------------------

# 3. What Do Name Servers Actually Contain?

Name servers contain:

-   DNS record mappings
-   Instructions for resolving subdomains
-   Delegation information for child domains

They do NOT contain:

-   Website content
-   Files
-   Application code
-   SSL certificates

They simply answer: "Where should this name go?"

------------------------------------------------------------------------

# 4. Buying a New Domain (Correct Flow)

## Option A -- Buy via Route 53

1.  Register domain in Route 53
2.  AWS automatically:
    -   Registers domain in global registry
    -   Creates hosted zone
    -   Assigns name servers
3.  You just add DNS records

No manual name server changes required.

## Option B -- Buy from Another Registrar

1.  Buy domain at registrar
2.  Create hosted zone in Route 53
3.  Copy Route 53 name servers
4.  Change name servers at registrar

Only then does Route 53 become authoritative.

------------------------------------------------------------------------

# 5. Moving an Existing Domain to Route 53 DNS

1.  Create hosted zone in Route 53
2.  Copy its name servers
3.  Update name servers at current registrar
4.  Wait for propagation

Important: When you change name servers, all previous DNS records stop
working. You must recreate: - MX records - Email settings - TXT
records - SPF/DKIM records - Everything

------------------------------------------------------------------------

# 6. DNS Resolution Flow (Step-by-Step)

User types:

https://app.myapp.com

Flow:

1.  Browser asks recursive resolver
2.  Resolver asks root servers
3.  Root points to .com registry
4.  .com registry returns authoritative name servers
5.  Resolver asks those name servers
6.  Hosted zone returns final answer (CloudFront, ALB, etc.)
7.  Browser connects to that endpoint

Each layer is separate and independent.

------------------------------------------------------------------------

# 7. CloudFront + Route 53 Integration

CloudFront has two important settings:

## Alternate Domain Name (CNAME)

Tells CloudFront: "I expect traffic for this hostname."

## SSL Certificate (ACM)

Must: - Match hostname - Be created in us-east-1 (for CloudFront)

Route 53 then creates:

Type: A\
Alias: Yes\
Target: CloudFront distribution

This makes:

app.myapp.com → CloudFront

------------------------------------------------------------------------

# 8. Wildcard Certificate Rules

\*.myapp.com covers: - api.myapp.com - app.myapp.com

It does NOT cover: - x.y.myapp.com

For that, you need: - \*.sub.myapp.com

Wildcards only replace ONE label.

------------------------------------------------------------------------

# 9. CloudFront Origins

CloudFront is a CDN + reverse proxy.

It can point to:

-   S3 bucket
-   Application Load Balancer (ALB)
-   EC2 instance
-   ECS (via ALB)
-   API Gateway
-   External HTTP server

CloudFront does NOT host content itself. It caches and forwards requests
to origin.

------------------------------------------------------------------------

# 10. Alias Record vs CloudFront Alias

These are different layers:

CloudFront Alternate Domain Name: Application layer configuration.

Route 53 Alias Record: DNS layer mapping.

Both must match for HTTPS to work properly.

------------------------------------------------------------------------

# 11. Hosted Zone Is NOT Global

Creating a hosted zone does NOT:

-   Register the domain
-   Update .com registry
-   Make it globally authoritative

Only the registrar updates the registry.

The global DNS root must know which name servers are authoritative.

------------------------------------------------------------------------

# 12. Enterprise Architecture Patterns

In enterprise setups:

-   Domain registered in central account
-   Root hosted zone managed centrally
-   Subdomains delegated via NS records
-   Application accounts manage their own hosted zones
-   ACM certs validated via DNS
-   CloudFront distributions per environment

Example:

Root domain: mycompany.com\
Delegated subdomain: app.mycompany.com

Root zone adds NS record delegating control to another account.

This enables multi-account isolation.

------------------------------------------------------------------------

# 13. Final Mental Model

There are 4 independent layers:

1.  Registry Layer (.com registry)
2.  Registrar Layer (where domain is purchased)
3.  Authoritative DNS Layer (Route 53 hosted zone)
4.  Application Layer (CloudFront → S3/ALB)

Each layer has a different responsibility.

Understanding this separation is critical for cloud architecture design.

------------------------------------------------------------------------

# 14. Common Mistakes

-   Creating hosted zone without registering domain
-   Forgetting to change name servers at registrar
-   Wrong ACM region for CloudFront (must be us-east-1)
-   Certificate not matching hostname
-   Not recreating MX records when moving DNS

------------------------------------------------------------------------

# Conclusion

If you need a new domain:

1.  Register it
2.  Ensure registry points to your name servers
3.  Create hosted zone (if not auto-created)
4.  Add DNS records
5.  Attach certificate
6.  Connect to CloudFront (if needed)
7.  Set origin (S3 / ALB / etc.)

DNS is infrastructure-level internet plumbing. Once you understand these
layers, CloudFront and Route 53 become straightforward.

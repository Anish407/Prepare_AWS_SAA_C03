# EC2 Basics
Amazon Elastic Compute Cloud (Amazon EC2) is a web service that provides resizable compute capacity in the cloud. It is designed to make web-scale cloud computing easier for developers. Here are some of the basic concepts and features of EC2:

# Labs
- [Connect to private ec2 using ssh from a public ec2](./ec2ssh.md)
- [Connect to private ec2 using SSM , IGW and NAT](./ec2-ssm-nat.md)
- [Elastic Ips](./ElasticIps.md)
- [EC2 Placement groups](./placementgroups.md)
- [AWS Outpost](./outposts.md)

## Key Concepts
- **Instances**: Virtual servers that run applications on the AWS infrastructure. You can choose from a variety of instance types based on your needs for CPU, memory, storage, and networking capacity.
- **Amazon Machine Images (AMIs)**: Pre-configured templates for your instances that include the operating system, application server, and applications. You can use standard AMIs provided by AWS or create your own custom AMIs.
- **Instance Types**: Different configurations of CPU, memory, storage, and networking capacity for your instances. Examples include General Purpose (t2.micro, m5.large), Compute Optimized (c5.large), and Memory Optimized (r5.large).
- **Elastic Block Store (EBS)**: Persistent block storage volumes that can be attached to your EC2 instances. EBS volumes are used for data that requires frequent updates and can be detached and reattached to different instances.
- **Security Groups**: Virtual firewalls that control inbound and outbound traffic to your instances. You can define rules to allow or deny specific types of traffic based on IP addresses, protocols, and ports.
- **Key Pairs**: Cryptographic keys used for secure SSH access to your instances. You create a key pair and use the private key to connect to your instance.
- **Elastic IP Addresses**: Static IPv4 addresses that can be associated with your instances. They allow you to maintain a consistent IP address even if you stop and start your instance.
- **Auto Scaling**: A service that automatically adjusts the number of EC2 instances in response to changes in demand. It helps ensure that you have the right amount of compute capacity to handle your application load.

# Elastic Network Interfaces (ENI) – Summary

## What is an ENI?
An **Elastic Network Interface (ENI)** is a **logical networking component inside a VPC** that represents a **virtual network card** for EC2 instances.

- Every EC2 instance has **at least one ENI**
- ENIs are created **automatically** when launching EC2, but can also be **created and managed manually**
- Security groups are applied **to ENIs**, not directly to EC2 instances

---

## Core ENI Concepts (Very Important)

### 1. Availability Zone Bound
- An ENI is **bound to a single Availability Zone**
- It can only be attached to EC2 instances **within the same AZ**
- Reason: EC2 instances themselves cannot span AZs

### 2. Detachable & Reusable
- ENIs can be:
  - Attached
  - Detached
  - Reattached
- Useful for:
  - Failover
  - Instance replacement
  - Preserving IPs and security group rules

### 3. Security Groups Travel with the ENI
- When you assign a security group to an EC2 instance, it is actually assigned to the **ENI**
- If the ENI is moved to another EC2 instance, the **security group rules move with it**

---

## ENI Attributes

An ENI can have the following attributes:

### IP Addresses
- **Primary private IPv4** (from subnet CIDR)
- **Primary private IPv6** (if subnet supports IPv6)
- **Secondary private IPv4 addresses**
- **Elastic IP (EIP)** per private IPv4 address
- **One ephemeral public IPv4 address**

### Security
- One or more **Security Groups** attached

---

## Ephemeral Public IPv4 Address

### What is it?
- A **temporary public IPv4 address**
- Assigned from **Amazon’s public IP pool**
- Automatically assigned when:
  - EC2 is launched in a public subnet
  - Public IP assignment is enabled

### When is it released?
The ephemeral public IPv4 address is released when:
- The EC2 instance is **stopped**
- The instance is **hibernated**
- The instance is **terminated**
- An **Elastic IP (EIP)** is associated with the ENI

Once released, the IP goes back to Amazon’s pool.

---

## ENI IP Lifecycle

### Instance Start
- ENI receives:
  - A **private IPv4** from the subnet CIDR
  - A **public IPv4** from Amazon’s pool (ephemeral)
  - A **public DNS name**

### Instance Stop
- **Public IPv4 is released**
- **Private IPv4 remains unchanged**

### Instance Restart
- A **new public IPv4** is assigned
- You should **never assume the same public IP will be reused**

---

## Key Takeaways on ENIs and IPs

- ENIs are the **true networking layer** of EC2
- Security groups apply to **ENIs, not instances**
- Ephemeral public IPs are **temporary and unstable**
- Use **Elastic IPs** if you need a stable public IP
- ENIs enable **advanced networking scenarios** like failover and IP preservation

---

# Elastic IP Addresses (EIP) – Summary

## What is an Elastic IP (EIP)?
An **Elastic IP (EIP)** is a **static, public IPv4 address** that you can associate with AWS compute resources (typically EC2).

- The IP address **never changes**
- It is **not ephemeral**
- Used when a **fixed public IPv4 address is required**

---

## Core EIP Concepts

### 1. Static Public IPv4
- EIPs are **permanent public IPv4 addresses**
- Unlike ephemeral public IPs, they do **not change** on:
  - Stop
  - Start
  - Reboot
  - Instance replacement

### 2. Region-Bound
- An EIP is created **inside a single AWS region**
- It **cannot be moved across regions**
- You must allocate a new EIP per region if needed

### 3. Allocation & Association Model
- You first **allocate** an EIP to your account
- Then **associate** it with a resource:
  - EC2 instance
  - ENI (recommended)
- Reassociation is possible without changing the IP

---

## DNS Impact

- When an EIP is associated:
  - The **public IPv4 address changes**
  - The **public DNS name also changes**
- DNS updates are automatic but important to understand for troubleshooting

---

## Limits & Cost Considerations

- Default **soft limit**: **5 EIPs per region per account**
- Soft limit means:
  - You can request an increase
  - Needing many EIPs usually indicates **poor architecture**
- AWS **charges** for:
  - Allocated but unused EIPs
  - Encourages minimal usage

---
## Elastic IP (EIP) – Cost & Charging Model (Important)

Elastic IPs are **not always free**. AWS charges based on **usage state**, not whether the IP was used in the past.

### When an EIP is FREE
An Elastic IP is **free of charge** only when:
- It is **associated with a running EC2 instance**
- Only **one EIP** is attached to that instance

This is the **only free scenario**.

---

### When an EIP is CHARGED
You are charged **per hour** in the following cases:

1. **Allocated but not associated**
   - EIP is reserved in your account
   - Not attached to any resource

2. **Associated with a stopped instance**
   - EC2 instance is stopped
   - EIP remains reserved

3. **Multiple EIPs on a single instance**
   - Only one EIP per running instance is free
   - Additional EIPs incur charges

AWS charges to prevent **IPv4 address hoarding**.

---

### Common Real-World Mistake
Stopping EC2 instances to save cost **does NOT stop EIP charges**.

If an instance is stopped:
- Either **release the EIP**
- Or accept ongoing charges

---

### Exam Rule to Remember
> **Elastic IPs are free only when attached to a running EC2 instance**

Any other state → **charged**

---

### Architecture Guidance
- Prefer **DNS-based designs** over static IPs
- Use EIPs only when a **fixed public IPv4 is absolutely required**
- Best practice: associate EIP to an **ENI**, not directly to EC2

---


## When to Use an EIP

### Valid Use Cases
- Exam scenarios requiring a **static IPv4**
- Legacy systems requiring **IP allowlisting**
- Failover scenarios where IP must remain unchanged

### Strongly Discouraged in Real Architectures
- Scaling workloads
- Load-balanced applications
- Modern cloud-native systems

Instead, prefer:
- **DNS names**
- **Load balancers**
- **Service discovery**

DNS stays constant even when underlying IPs change.

---

## Key Takeaways on Elastic IPs

- EIPs are **static public IPv4 addresses**
- They are **region-scoped**
- They can be **moved between resources**
- Use them **only when absolutely required**
- Prefer **DNS-based architectures** whenever possible

---

## Security Groups vs ENIs Common Misconception Important

Changing or attaching a security group does NOT mean that an Elastic Network Interface ENI is being moved.

### Correct Mental Model
- Security Groups are attached to ENIs
- ENIs are attached to EC2 instances
- Security Groups are reusable rule sets
- ENIs are concrete network identities

---

## What Happens in Different Scenarios

### Changing a Security Group on an EC2 Instance
- AWS updates the security group configuration on the existing ENI
- The ENI remains attached to the same EC2 instance
- No detach or reattach occurs

Same ENI  
New or updated security group rules  

---

### Attaching the Same Security Group to Another EC2 Instance
- Each EC2 instance has its own ENI
- The same security group object is referenced by multiple ENIs
- No ENI is shared or moved

Same security group  
Different ENIs  

This is sharing rules, not sharing network interfaces.

---

### Actually Moving an ENI Rare Scenario
An ENI is moved only when you:
1. Detach the ENI from one EC2 instance
2. Attach it to another EC2 instance
3. Ensure both instances are in the same Availability Zone

In this case, the following move together:
- Private IP address
- Security groups
- MAC address
- Network identity

---

## Summary Table

| Action | ENI Moved | Security Group Moved |
|------|----------|----------------------|
| Change SG on EC2 | No | Updated |
| Attach same SG to another EC2 | No | Shared |
| Detach and reattach ENI | Yes | Yes |

---

## Key Rule to Remember
Security groups are shared.  
ENIs are not.

Confusing these two leads to networking bugs, broken access, and hard to debug AWS issues, especially when working with ECS, load balancers, and scaling systems.

---
## Multiple ENIs vs Multiple Security Groups on an EC2 Instance

### Can an EC2 Instance Have More Than One ENI?
Yes. An EC2 instance can have:
- One **primary ENI** (always present)
- One or more **secondary ENIs**

All ENIs:
- Must be in the **same Availability Zone**
- Are limited by the **instance type**

The exact number of ENIs depends on the instance size, but for exams it is enough to know that multiple ENIs are supported.

---

### Why Use Multiple ENIs?
Common use cases include:
- Separating different types of network traffic
- Applying different security group rules per interface
- Network appliances such as firewalls or proxies
- Failover scenarios where ENIs are moved between instances

Most workloads do not require multiple ENIs, but AWS supports this design.

---

## What Happens When You Add Multiple Security Groups?

Adding multiple security groups to an EC2 instance:
- Does **not** create additional ENIs
- Adds all security groups to the **same ENI**

Security groups are applied to the ENI, not directly to the EC2 instance.

---

### How Multiple Security Groups Are Evaluated
Security groups are:
- Stateful
- Allow-only
- Evaluated as a union of rules

If **any** attached security group allows the traffic, the traffic is allowed.
There are no explicit deny rules in security groups.

Example:
- One security group allows SSH
- Another allows HTTP

Result:
- Both SSH and HTTP are allowed

---

## Multiple ENIs vs Multiple Security Groups

| Concept | Description |
|------|------------|
| Multiple ENIs | Multiple network interfaces with separate IPs and MAC addresses |
| Multiple Security Groups | Multiple rule sets applied to the same ENI |
| Adding Security Groups | Updates rules on an existing ENI |
| Adding ENIs | Creates a new network interface |

---

## Key Rule to Remember 
Security groups are shared rule sets.
ENIs are distinct network interfaces.

Confusing these two leads to networking and security issues, especially in scaled or container-based systems.

---

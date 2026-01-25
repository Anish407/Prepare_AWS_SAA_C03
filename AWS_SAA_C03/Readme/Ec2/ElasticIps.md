# Elastic IP Addresses (EIPs) in AWS

## Overview

An **Elastic IP (EIP)** is a static, public IPv4 address allocated to your AWS account. Unlike ephemeral public IPs assigned to EC2 instances at launch, an EIP:

- Persists across instance stop/start cycles
- Can be remapped to another EC2 or ENI quickly
- Provides a stable public endpoint for external access

This makes EIPs useful for scenarios requiring fixed IP addresses, whitelisting, or predictable network endpoints.

---

## Use Cases

- Corporate firewall whitelisting
- Legacy clients that do not support DNS-based routing
- On-premises to cloud connectivity
- Disaster recovery and failover
- Outbound calls to APIs that require static public IPs

---
    
  # Lab Exercise:

  - Create an EC2 instance in a public subnet
    <img width="1351" height="807" alt="1 create_ec2" src="https://github.com/user-attachments/assets/efa19634-a3ca-427b-b338-f48ca7ae5df2" />
  - Enable Auto-assign Public IP. This is done to show the difference between a Public IP and an Elastic IP.
    <img width="1150" height="792" alt="2 create_ec2" src="https://github.com/user-attachments/assets/65bbcadb-6243-455d-a88d-15835d86c6c6" />
  - We also attach an internet gateway to the VPC and add a route in the route table to allow internet access.
    <img width="1697" height="437" alt="3 IGW" src="https://github.com/user-attachments/assets/0d8f1b89-32e9-4b35-91ad-2c539395c123" />
  - View the auto assigned IP Address in the aws console, this is not an elastic IP and will change everytime we restart the instance.
     <img width="1882" height="776" alt="4 auto_assignedIp" src="https://github.com/user-attachments/assets/b17f0472-c3c0-40e4-8afb-565f3958a5a6" />
  - Next , stop the Ec2 instance and observe that the Public IP changes when you start the instance again.
    <img width="1872" height="745" alt="5 stopped_instance" src="https://github.com/user-attachments/assets/35a276d1-a330-42ec-a6b0-549e774242a7" />
  -  Restart it to check the new IP Address
    <img width="1666" height="813" alt="6 restarted" src="https://github.com/user-attachments/assets/51a4c0dc-4426-4e10-b501-3e9804f41881" />
  - Create an Elastic IP and associate it with the EC2 instance.
    <img width="1910" height="830" alt="7 EIP1" src="https://github.com/user-attachments/assets/639cd5cc-21da-4004-b6d5-bca3ee3527fb" />
    <img width="1823" height="819" alt="8 EIP2" src="https://github.com/user-attachments/assets/28321279-8847-40c0-a5d8-ba99eda718d2" />
    <img width="1912" height="452" alt="9 EIP3" src="https://github.com/user-attachments/assets/1267bf3f-7ba6-461d-9f2a-eca86a5484f1" />
  - Associate the EIP to the EC2 instance
    <img width="1916" height="572" alt="10 Allocate_EIP" src="https://github.com/user-attachments/assets/276f0a25-c5ae-4939-b960-11edb4f21886" />
    <img width="1775" height="653" alt="11  Associate_EIP" src="https://github.com/user-attachments/assets/d096132f-94b5-4fc6-9063-214dd87923ec" />
    <img width="1877" height="781" alt="12 EIP_attached" src="https://github.com/user-attachments/assets/6148caa7-fe82-4635-98d1-51472d91f6f8" />

  - Stop the EC2 instance again and start it. Observe that the Elastic IP remains the same.
    <img width="1902" height="745" alt="13 EC2_stopped" src="https://github.com/user-attachments/assets/04dce35c-fadd-48df-b154-098dbfbb6adb" />
    <img width="1883" height="792" alt="14 Ec2_restarted" src="https://github.com/user-attachments/assets/ab18b581-2397-4b36-98f1-1c7a62713ef6" />

  - Finally, Disassociate the Elastic IP from the EC2 instance and release it.
    <img width="1907" height="730" alt="15 Dissaociate_EIP" src="https://github.com/user-attachments/assets/f62c93cb-2872-4a70-9228-bf051d2726da" />

  - Releasing the EIP
    <img width="1887" height="700" alt="16 Release" src="https://github.com/user-attachments/assets/71e123b8-58fd-4c6d-b3a1-5b87a2a36b2b" />


  # Concepts
  ## Pricing Model

Elastic IPs are not fully “free”. Charges apply when:

- The EIP is **allocated but not associated**
- You allocate **multiple EIPs per instance**
- You **remap** an EIP excessively within an hour

Public IPv4 addresses are scarce, and AWS charges to avoid waste.

---

## Important Facts

- EIPs are **region-scoped**, not global
- Stopping an EC2 instance **does not** release the EIP
- Releasing an EIP returns it to AWS – you may **not** get it back
- You need a quota increase for more than 5 EIPs per region
- EIPs can be attached to **ENIs**, which is ideal for HA failover
- Security Groups still apply even if an EIP is assigned
- EIPs **cannot** be used directly on NAT Gateways (they have their own IPs)
- Network Load Balancers (NLBs) can support **static EIPs**, ALBs cannot

---

## Less-Known but Important Details

### ENI-Based Failover
Associating EIPs with ENIs instead of instances allows:
- Fast failover between instances
- Zero DNS propagation delays
- Cleaner blue/green deployments

### BYOIP (Bring Your Own IP)
AWS allows advertising your own IPv4 ranges for:
- Telcos
- Financial institutions
- Compliance-regulated organizations

### IPv6 Considerations
EIPs exist only for IPv4.  
IPv6 global addresses are inherently static and do not require EIPs.

### Resource Sharing
If using AWS RAM for shared VPCs:
- The EIP belongs to the **owning account**
- Only association happens cross-account within the shared VPC

---

## When Not To Use EIPs

Avoid EIPs when using managed services with better patterns:

- **Load Balancing:** Use ALB/NLB DNS
- **Global Distribution:** Use CloudFront
- **API Exposure:** Use API Gateway
- **Private Service Access:** Use VPC Endpoints / PrivateLink
- **Service Discovery:** Use Cloud Map or DNS

These options avoid static-IP architectural bottlenecks entirely.

---

## Operational Good Practices

- **Tag EIPs** with owner/environment
- **Release unused EIPs** to avoid charges
- **Monitor idle EIPs** via CloudWatch billing alerts
- **Prefer IPv6** where modern clients support it
- Use **NLB with static EIPs** instead of attaching EIPs directly to instances

---

## Summary

Elastic IPs provide stable public IPv4 endpoints within AWS. They are useful but come with financial and architectural constraints due to IPv4 scarcity. Modern AWS designs try to minimize Elastic IP usage by leveraging DNS-based routing, load balancers, and managed edge services.

  
  
  ### Further Reading:
    - [AWS Elastic IP Documentation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html)

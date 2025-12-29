# Internet gateways
(IGW) are horizontally scaled, redundant, and highly available VPC components that allow communication between instances in your VPC and the internet. They serve two main purposes:
- Provide a target in your VPC route tables for internet-routable traffic
- Perform network address translation (NAT) for instances that have been assigned public IPv4 addresses
- An internet gateway is a fully managed AWS resource that you can attach to your VPC to enable internet access for resources within the VPC. It is a horizontally scaled, redundant, and highly available VPC component that allows communication between instances in your VPC and the internet.
- To enable internet access for resources within a VPC, you need to attach an internet gateway to the VPC and configure the appropriate route tables and security groups.
- An internet gateway is a critical component for enabling internet connectivity in a VPC, and it is essential for hosting public-facing applications and services in AWS.
- To create an internet gateway, you can use the AWS Management Console, AWS CLI, or AWS SDKs. Once created, you can attach the internet gateway to your VPC and configure the necessary route tables and security groups to allow internet access for your resources.

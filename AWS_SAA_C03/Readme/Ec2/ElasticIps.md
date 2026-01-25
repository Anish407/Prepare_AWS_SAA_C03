# Elastic Ips

An Elastic IP address is a static, public IPv4 address designed for dynamic cloud computing. It is associated with your AWS account and can be easily remapped to any instance in your account, allowing you to maintain a consistent IP address even if you stop and start your instances.
## Key Features of Elastic IPs:
1. **Static IP Address**: Unlike regular public IP addresses that can change when an instance is stopped and started, Elastic IPs remain constant until you choose to release them.
1. **Remapping**: You can quickly remap an Elastic IP address to another instance in your account, which is useful for failover scenarios.
1. **Cost**: AWS provides one Elastic IP address per account for free, but additional Elastic IPs incur charges. Additionally, if an Elastic IP is not associated with a running instance, you may be charged for it.
1. **Association**: An Elastic IP can be associated with an instance or a network interface. You can also associate it with a NAT gateway.
1. **Limitations**: There are limits on the number of Elastic IPs you can allocate per region, which can be increased by requesting a limit increase from AWS support.
 ## Use Cases:
 - **High Availability**: Use Elastic IPs to quickly switch traffic to a standby instance in case of failure.
 ### Concepts to Remember:
    - Elastic IPs are tied to your AWS account, not to a specific instance.
    - You can have multiple Elastic IPs, but be aware of the associated costs. Elastic IPs should be used judiciously to avoid unnecessary charges.
    - Always release Elastic IPs that are no longer needed to avoid incurring charges.
    - We pay for Elastic IPs that are not associated with a running instance. So if you have an EC2 that you stop, make sure to either associate the Elastic IP with another running instance or release it.
  # Lab Exercise:

  - Create an EC2 instance in a public subnet
  - Enable Auto-assign Public IP. This is done to show the difference between a Public IP and an Elastic IP.
  - We also attach an internet gateway to the VPC and add a route in the route table to allow internet access.
  - Next , stop the Ec2 instance and observe that the Public IP changes when you start the instance again.
  - Create an Elastic IP and associate it with the EC2 instance.
  - Stop the EC2 instance again and start it. Observe that the Elastic IP remains the same.
  - Finally, Disassociate the Elastic IP from the EC2 instance and release it.
  
  
  
  
  ### Further Reading:
    - [AWS Elastic IP Documentation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html)
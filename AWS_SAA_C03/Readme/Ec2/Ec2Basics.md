# EC2 Basics
Amazon Elastic Compute Cloud (Amazon EC2) is a web service that provides resizable compute capacity in the cloud. It is designed to make web-scale cloud computing easier for developers. Here are some of the basic concepts and features of EC2:
## Key Concepts
- **Instances**: Virtual servers that run applications on the AWS infrastructure. You can choose from a variety of instance types based on your needs for CPU, memory, storage, and networking capacity.
- **Amazon Machine Images (AMIs)**: Pre-configured templates for your instances that include the operating system, application server, and applications. You can use standard AMIs provided by AWS or create your own custom AMIs.
- **Instance Types**: Different configurations of CPU, memory, storage, and networking capacity for your instances. Examples include General Purpose (t2.micro, m5.large), Compute Optimized (c5.large), and Memory Optimized (r5.large).
- **Elastic Block Store (EBS)**: Persistent block storage volumes that can be attached to your EC2 instances. EBS volumes are used for data that requires frequent updates and can be detached and reattached to different instances.
- **Security Groups**: Virtual firewalls that control inbound and outbound traffic to your instances. You can define rules to allow or deny specific types of traffic based on IP addresses, protocols, and ports.
- **Key Pairs**: Cryptographic keys used for secure SSH access to your instances. You create a key pair and use the private key to connect to your instance.
- **Elastic IP Addresses**: Static IPv4 addresses that can be associated with your instances. They allow you to maintain a consistent IP address even if you stop and start your instance.
- **Auto Scaling**: A service that automatically adjusts the number of EC2 instances in response to changes in demand. It helps ensure that you have the right amount of compute capacity to handle your application load.

# Labs
- [Connect to private ec2 using ssh from a public ec2](./ec2ssh.md)
- [Connect to private ec2 using SSM , IGW and NAT](./ec2-ssm-nat.md)
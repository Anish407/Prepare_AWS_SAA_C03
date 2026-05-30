# AWS Systems Manager Run Command Lab: Update SSM Agent on a Private EC2 Instance Using Interface Endpoints

## 1. Goal

The goal of this lab is to update the **AWS Systems Manager Agent (SSM Agent)** on an EC2 instance that is running in a **private subnet**, without using SSH, without a public IP address, and without a NAT Gateway.

The EC2 instance will communicate with AWS Systems Manager privately through **VPC Interface Endpoints**.

By the end of this lab, you should understand:

- What AWS Systems Manager is
- What SSM Agent is
- What Run Command is
- Why EC2 needs an IAM role and trust policy
- Why private EC2 instances need VPC endpoints for Systems Manager
- How to create SSM interface endpoints
- How to confirm that a private EC2 instance is a managed node
- How to use Run Command to update the SSM Agent
- How to verify the SSM Agent version after the update

---

## 2. Lab Architecture

```text
+-------------------------+
| AWS Console / AWS CLI   |
+-----------+-------------+
            |
            | SendCommand API
            v
+-------------------------+
| AWS Systems Manager     |
| - Run Command           |
| - AWS-UpdateSSMAgent    |
+-----------+-------------+
            |
            | AWS PrivateLink
            v
+-------------------------+
| VPC Interface Endpoints |
| - ssm                   |
| - ssmmessages           |
| - ec2messages           |
+-----------+-------------+
            |
            | Private IP traffic inside VPC
            v
+-------------------------+
| Private EC2 Instance    |
| - No public IP          |
| - No SSH                |
| - SSM Agent installed   |
| - IAM instance profile  |
+-------------------------+
```

---

## 3. What This Lab Proves

This lab proves that an EC2 instance does not need public internet access to be managed by AWS Systems Manager.

The instance only needs:

```text
1. SSM Agent installed and running
2. IAM role with Systems Manager permissions
3. Network path to Systems Manager using VPC interface endpoints
```

There is no SSH.

There is no public IP.

There is no NAT Gateway.

---

## 4. What Is AWS Systems Manager?

**AWS Systems Manager**, often called **SSM**, is a service used to manage AWS resources and servers.

For EC2 instances, Systems Manager can be used for:

- Running commands
- Starting shell sessions
- Patching instances
- Collecting inventory
- Managing configuration
- Automating operational tasks

In a traditional setup, you may connect like this:

```text
Admin → SSH → EC2 Instance
```

With Systems Manager, the model becomes:

```text
Admin → Systems Manager API → SSM Agent → EC2 Instance
```

This is more secure because the EC2 instance does not need inbound SSH access.

---

## 5. What Is SSM Agent?

**SSM Agent** is software installed inside the EC2 instance.

It is responsible for:

- Communicating with AWS Systems Manager
- Receiving instructions
- Running commands locally
- Returning command status and output

Important mental model:

```text
Systems Manager does not directly reach into your EC2 instance.
The SSM Agent running inside the instance communicates with Systems Manager.
```

If the SSM Agent is stopped, missing, outdated, or unable to reach Systems Manager, Run Command will not work.

Many Amazon Linux AMIs already include SSM Agent.

---

## 6. What Is Run Command?

**Run Command** is a feature of AWS Systems Manager that allows you to run commands on managed instances without logging in.

In this lab, Run Command is used for one task:

```text
Update the SSM Agent.
```

The AWS-managed SSM document used is:

```text
AWS-UpdateSSMAgent
```

You will also use:

```text
AWS-RunShellScript
```

to check the currently installed SSM Agent version.

---

## 7. What Are Interface Endpoints?

An **interface endpoint** allows resources inside your VPC to privately connect to supported AWS services using AWS PrivateLink.

For this lab, the private EC2 instance needs to communicate with Systems Manager.

So we create these interface endpoints:

```text
com.amazonaws.<region>.ssm
com.amazonaws.<region>.ssmmessages
com.amazonaws.<region>.ec2messages
```

For example, in Stockholm region:

```text
com.amazonaws.eu-north-1.ssm
com.amazonaws.eu-north-1.ssmmessages
com.amazonaws.eu-north-1.ec2messages
```

These endpoints allow the private EC2 instance to communicate with Systems Manager without internet access.

---

## 8. Why Three Endpoints?

For Systems Manager communication, the important endpoints are:

| Endpoint | Purpose |
|---|---|
| `ssm` | Systems Manager API operations |
| `ssmmessages` | Communication channel used by SSM Agent |
| `ec2messages` | Message delivery support for managed instances |

If one of these is missing, the instance may not appear online or Run Command may not work correctly.

---

## 9. Services Used

| Service | Purpose |
|---|---|
| VPC | Network boundary |
| Private Subnet | Hosts the EC2 instance |
| EC2 | Instance where SSM Agent runs |
| IAM | Role and instance profile for EC2 |
| Systems Manager | Sends the Run Command |
| SSM Agent | Receives and runs commands |
| VPC Interface Endpoints | Private connectivity to Systems Manager |
| Security Groups | Controls traffic between EC2 and endpoints |

---

## 10. Step 1: Create a VPC

- Create a VPC:
  <img width="914" height="364" alt="image" src="https://github.com/user-attachments/assets/861bd2d4-8d55-4f14-846f-d8f3566c2edf" />

- Enable DNS support and DNS hostnames:
  <img width="299" height="350" alt="image" src="https://github.com/user-attachments/assets/93ee39ac-df79-4a3f-9106-eba82d3213ee" />

These DNS settings are important because interface endpoints use private DNS. I dont add a public subnet here as its not required for this lab and the EC2 that we will provision will live in the private VPC

---

## 12. Step 2: Create a Private Subnet

- Create a private subnet:
  <img width="167" height="133" alt="image" src="https://github.com/user-attachments/assets/2d18e803-70dc-4a12-b508-4b95fb7b24c0" />

This subnet will not have:

- Internet Gateway route
- NAT Gateway route
- Public IP assignment

That is intentional.

---

## 13. Step 3: Create Route Table for Private Subnet

- Create a route table:
  <img width="141" height="129" alt="image" src="https://github.com/user-attachments/assets/9f5426d1-4e58-4119-a06b-c717d2122574" />

- Associate the route table with the private subnet:
  <img width="935" height="252" alt="image" src="https://github.com/user-attachments/assets/a7203b07-6c53-4cd0-bcc2-109915d1d34a" />

> Do not add a route to an Internet Gateway or NAT Gateway. This confirms that the instance will not have internet access.

---

## 14. Step 4: Create Security Groups

You need two security groups:

```text
1. EC2 security group
2. VPC endpoint security group
```

### 14.1 Create EC2 Security Group

- Do not add inbound rules.
  <img width="892" height="391" alt="image" src="https://github.com/user-attachments/assets/a8812742-be20-4cf9-8198-560c3b037c66" />

- The EC2 instance does not need inbound SSH.

### 14.2 Create Endpoint Security Group

- Allow HTTPS from the EC2 security group to the endpoint security group:
  <img width="822" height="296" alt="image" src="https://github.com/user-attachments/assets/fe8950fc-37c8-4235-a623-105f547a7cd8" />

This means:

```text
Only resources using the EC2 security group can connect to the VPC endpoints on port 443.
```

---

## 15. Step 5: Create VPC Interface Endpoints for Systems Manager

- Create the `ssm` endpoint:
- Create the `ssmmessages` endpoint:
- Create the `ec2messages` endpoint:

Wait until the endpoints are available:

Expected state:

```text
available
```

---

## 16. Step 6: Create IAM Role for EC2

The EC2 instance needs an IAM role.

This role needs two things:

```text
1. Trust policy
2. Permission policy
```

- The trust policy allows EC2 to assume the role.
  <img width="889" height="386" alt="image" src="https://github.com/user-attachments/assets/6e60b6b0-0c83-4415-9bb0-e5298a773aa0" />
  <img width="767" height="342" alt="image" src="https://github.com/user-attachments/assets/49b35e02-85d4-41f3-89ad-869d7331c64d" />

- The permission policy allows the role to communicate with Systems Manager.
- Attach the AWS managed policy:
  <img width="947" height="301" alt="image" src="https://github.com/user-attachments/assets/c4e3087f-0e6b-4c0c-8f76-1414e5c3bf7c" />
- Create the role
  <img width="926" height="395" alt="image" src="https://github.com/user-attachments/assets/aacc7af2-0735-4c88-8095-a0f400e920a4" />
 
Wait a minute for IAM propagation.

---

## 17. Step 7: Launch Private EC2 Instance

- Get the latest Amazon Linux 2023 AMI:
- Launch the private EC2 instance:
- Confirm that the instance has no public IP:

---

## 18. Step 8: Verify the Instance Is Online in Systems Manager

If it shows `Online`, the private EC2 instance is successfully communicating with Systems Manager through the interface endpoints.

If it does not show up, check:

```text
- IAM role attached?
- AmazonSSMManagedInstanceCore attached?
- Trust policy allows ec2.amazonaws.com?
- SSM Agent installed?
- VPC endpoints available?
- Private DNS enabled?
- Endpoint security group allows 443 from EC2 security group?
- EC2 subnet route table associated correctly?
- EC2 has no blocked NACL rules?
```

---

## 19. Step 9: Check Current SSM Agent Version

Use Run Command with `AWS-RunShellScript`:

Example output:

```text
SSM Agent version: 3.x.x.x
```

---

## 20. Console Option

You can also run the update from the AWS Console.

Go to:

```text
AWS Console → Systems Manager → Run Command
```

Choose:

```text
Run command
```

Search for:

```text
AWS-UpdateSSMAgent
```

Select the private EC2 instance.

Run the command.

Then check:

```text
Systems Manager → Run Command → Command history
```

To verify the version, run another command using:

```text
AWS-RunShellScript
```

Command:

```bash
amazon-ssm-agent -version
```

---

## 21. Step 11: Verify SSM Agent Version After Update

Run:

- Get the output:

```bash
aws ssm get-command-invocation \
  --command-id $COMMAND_ID \
  --instance-id $INSTANCE_ID \
  --query "StandardOutputContent" \
  --output text
```

Compare the version before and after the update.

---

## 23. What Actually Happened?

When the private EC2 instance started:

```text
1. EC2 received temporary credentials from the IAM instance profile.
2. SSM Agent used those credentials.
3. SSM Agent resolved Systems Manager service DNS names to private endpoint IPs.
4. SSM Agent communicated with Systems Manager through AWS PrivateLink.
5. The instance appeared as a managed node.
```

When you ran `AWS-UpdateSSMAgent`:

```text
1. You called the Systems Manager SendCommand API.
2. Systems Manager created a command using the AWS-UpdateSSMAgent document.
3. The SSM Agent on the private EC2 instance received the command.
4. The agent update process ran on the instance.
5. The result was sent back to Systems Manager.
```

No SSH was used.

No public IP was used.

No NAT Gateway was used.

---

## 24. Common Mistakes

### Mistake 1: Creating Endpoints but Forgetting Private DNS

If private DNS is disabled, the instance may not automatically resolve normal AWS service names to private endpoint IPs.

Fix:

```text
Enable Private DNS on the interface endpoints.
```

---

### Mistake 2: Endpoint Security Group Does Not Allow 443

The endpoint security group must allow inbound HTTPS from the EC2 instance security group.

Required rule:

```text
Endpoint SG inbound:
TCP 443 from EC2 SG
```

---

### Mistake 3: EC2 Has No IAM Role

The instance must have an instance profile attached.

The role must have:

```text
AmazonSSMManagedInstanceCore
```

---

### Mistake 4: Missing Trust Policy

The role must trust EC2:

```json
{
  "Effect": "Allow",
  "Principal": {
    "Service": "ec2.amazonaws.com"
  },
  "Action": "sts:AssumeRole"
}
```

Without this, EC2 cannot assume the role.

---

### Mistake 5: Missing One of the SSM Endpoints

For this lab, create all three:

```text
ssm
ssmmessages
ec2messages
```

Do not create only `ssm` and assume everything will work.

---

### Mistake 6: Expecting Ping or Internet to Work

This private instance has no NAT and no Internet Gateway route.

So commands like this should fail:

```bash
ping google.com
curl https://example.com
```

That is expected.

The instance can reach Systems Manager privately because of the VPC endpoints.

---

## 25. Troubleshooting Checklist

If the instance does not appear in Systems Manager:

```text
IAM:
[ ] EC2 role exists
[ ] Trust policy allows ec2.amazonaws.com
[ ] AmazonSSMManagedInstanceCore policy attached
[ ] Instance profile attached to EC2

EC2:
[ ] Instance is running
[ ] Amazon Linux AMI includes SSM Agent
[ ] SSM Agent is running
[ ] No public IP expected

VPC:
[ ] VPC DNS support enabled
[ ] VPC DNS hostnames enabled
[ ] ssm endpoint exists
[ ] ssmmessages endpoint exists
[ ] ec2messages endpoint exists
[ ] Private DNS enabled on endpoints
[ ] Endpoint security group allows inbound 443 from EC2 SG
[ ] EC2 SG allows outbound 443
[ ] NACL does not block traffic
```

---

## 26. Cleanup

Terminate the EC2 instance:

```bash
aws ec2 terminate-instances \
  --instance-ids $INSTANCE_ID
```

Delete VPC endpoints:

```bash
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query "VpcEndpoints[*].VpcEndpointId" \
  --output text
```

Then delete each endpoint:

```bash
aws ec2 delete-vpc-endpoints \
  --vpc-endpoint-ids <endpoint-id-1> <endpoint-id-2> <endpoint-id-3>
```

Delete security groups:

```bash
aws ec2 delete-security-group \
  --group-id $EC2_SG_ID

aws ec2 delete-security-group \
  --group-id $ENDPOINT_SG_ID
```

Remove role from instance profile:

```bash
aws iam remove-role-from-instance-profile \
  --instance-profile-name EC2PrivateSSMInstanceProfile \
  --role-name EC2PrivateSSMRole
```

Delete instance profile:

```bash
aws iam delete-instance-profile \
  --instance-profile-name EC2PrivateSSMInstanceProfile
```

Detach the policy:

```bash
aws iam detach-role-policy \
  --role-name EC2PrivateSSMRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
```

Delete the role:

```bash
aws iam delete-role \
  --role-name EC2PrivateSSMRole
```

Disassociate the route table if required:

```bash
aws ec2 describe-route-tables \
  --route-table-ids $PRIVATE_RT_ID \
  --query "RouteTables[0].Associations[*].RouteTableAssociationId" \
  --output text
```

Delete the route table:

```bash
aws ec2 delete-route-table \
  --route-table-id $PRIVATE_RT_ID
```

Delete the subnet:

```bash
aws ec2 delete-subnet \
  --subnet-id $PRIVATE_SUBNET_ID
```

Delete the VPC:

```bash
aws ec2 delete-vpc \
  --vpc-id $VPC_ID
```

---

## 27. Key Takeaways

- A private EC2 instance can be managed by Systems Manager without SSH.
- The instance does not need a public IP.
- The instance does not need a NAT Gateway if interface endpoints are used.
- SSM Agent must be installed and running.
- The EC2 instance needs an IAM role with `AmazonSSMManagedInstanceCore`.
- The IAM role must trust `ec2.amazonaws.com`.
- The VPC needs interface endpoints for `ssm`, `ssmmessages`, and `ec2messages`.
- Endpoint security groups must allow HTTPS from the EC2 instance.
- Run Command can update SSM Agent using `AWS-UpdateSSMAgent`.

---

## 28. One-Minute Explanation

In this lab, we created an EC2 instance in a private subnet with no public IP and no internet access. To allow Systems Manager to manage the instance, we created interface endpoints for `ssm`, `ssmmessages`, and `ec2messages`. The EC2 instance used an IAM role with `AmazonSSMManagedInstanceCore`, and the role trusted the EC2 service. After the SSM Agent connected privately to Systems Manager through the endpoints, the instance appeared as an online managed node. We then used Run Command with the `AWS-UpdateSSMAgent` document to update the SSM Agent without SSH, without a bastion host, and without a NAT Gateway.

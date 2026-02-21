# Lab  

## Prerequisites
- Create 2 ec2 instances using CDK
- 


## Step 1
- Create a Private Hosted Zone in Route 53 and connect from another Ec2 instance in the same VPC
  <img width="1481" height="735" alt="image" src="https://github.com/user-attachments/assets/032f7297-a55d-4ba0-bf58-36caf3886043" />
- Select the VPC
  <img width="1855" height="522" alt="image" src="https://github.com/user-attachments/assets/25f89e43-f9e1-4f53-bfe9-b5034aa0afe7" />
- The private hosted zone is created
  <img width="1552" height="651" alt="image" src="https://github.com/user-attachments/assets/213d007d-797a-49a2-9a78-fbe8e7e2ddcf" />

## Step 2: 

- Create A Record in private hosted zone
  <img width="1858" height="830" alt="image" src="https://github.com/user-attachments/assets/8d340dfc-d4b2-483c-bebb-944f9bf59528" />

> Note that the value is the second EC2 instance's private IP

- Now the hosted zone contains an A record which points to the destination Ec2's Ip Address
  <img width="1521" height="692" alt="image" src="https://github.com/user-attachments/assets/a05f8257-fc59-4cf2-be0f-dadc0644e015" />

- Now we can ping the destination EC2 using the name we just created
  <img width="1040" height="703" alt="image" src="https://github.com/user-attachments/assets/46fd9285-3361-4010-8947-e8ddbf440d64" />





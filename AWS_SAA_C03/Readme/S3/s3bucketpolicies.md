# S3 bucket policies

# Lab

## Diagram
<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/b4c7d3af-ea4c-41ef-99e1-9f8a0d0adae2" />

## Phase Summary

> ### Key Learning Across Phases
> ```
> PHASE 1: WHO doesn't matter  
>          Public bucket → everyone can access
>
> PHASE 2: WHO matters  
>          Only cloud_user allowed
>
> PHASE 3: WHO + WHERE matters  
>          ec2_user allowed only via VPC endpoint
> ```
|



## Description
- create 2 IAM users with programmatic access ex: clouduser and ec2_user
- ec2_user will have access to EC2 and clouduser will have access to S3
- create a bucket and add a bucket policy that allows everyone to list the contents
- we can see even with ec2 permission , the ec2_user can list the contents of the bucket because of the bucket policy that allows everyone to list the contents
- next we limit the access to the cloud user and try the list command again, which will explain how we can block access to buckets using bucket policies
- now we will create an ec2 instance and allow the ec2 user to access the bucket using gateway endpoints
- the bucket policy will be updated to allow access only from the VPC endpoint, which will ensure that only resources within the VPC can access the bucket, even if the user has permissions to access S3.
- then we use ssm to connect to the ec2 instance and try to access the bucket, which will work because we have allowed access from the VPC endpoint in the bucket policy.
- next we will try to access the bucket from outside the VPC, which will fail because the bucket policy only allows access from the VPC endpoint.

# Phase 1: Understand that Bucket policies Overrides IAM Permissions
## Objective:
Demonstrate that S3 bucket policies can grant access independently of IAM permissions.

## Steps

- Create the users in IAM
  <img width="1853" height="642" alt="2 userlist" src="https://github.com/user-attachments/assets/d10a9900-65f7-4ba6-9ba1-cc8f1861f49e" />
- grant the ec2_user ec2 permissions
  <img width="1835" height="627" alt="image" src="https://github.com/user-attachments/assets/baf60bf2-2f2c-4c3e-9396-d54128ac942c" />
- Create the bucket
  <img width="1775" height="727" alt="image" src="https://github.com/user-attachments/assets/5d8ec30d-b11d-47ee-93a7-6cce52c77a43" />
  <img width="1741" height="750" alt="image" src="https://github.com/user-attachments/assets/893c1160-819d-49e5-92f1-2297b50e55dc" />
- create a folder called public and add a text file to it
  <img width="1890" height="548" alt="image" src="https://github.com/user-attachments/assets/fc257b74-7f36-455a-b602-6afd65226ece" />
- Now we will setup the profiles for both users to login via the cli
  - create access keys for the users
    <img width="1553" height="411" alt="image" src="https://github.com/user-attachments/assets/dcee1370-37c3-4aa3-bd3f-0033cf565faf" />
  - Configure the aws cli
    <img width="966" height="281" alt="image" src="https://github.com/user-attachments/assets/dfd8555f-fc91-4cf5-8452-23cbf22b0c4c" />
- For the first part of the demo, we will turn off public access just to create a bucket policy that allows everyone to connect to the s3 bucket, if its turned on then the bucket policy that allows everyone to connect will conflict and AWS wont let us create the bucket policy
  <img width="1902" height="603" alt="image" src="https://github.com/user-attachments/assets/2428f205-6d69-4926-8bd8-9de626c1c022" />

- Now create a bucket policy that allows everyone to connect to the bucket,
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Statement1",
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:ListBucket",
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::anish-bucket-policies-182736",
                "arn:aws:s3:::anish-bucket-policies-182736/*"
            ]
        }
    ]
    }
  ```

>  ```
>       "arn:aws:s3:::anish-bucket-policies-182736",
>       "arn:aws:s3:::anish-bucket-policies-182736/*"
>  ```
>  We need to add 2 entries in the resource section because they serve different purposes. The first one (arn:aws:s3:::anish-bucket-policies-182736) is for the bucket  and the next one
> (arn:aws:s3:::anish-bucket-policies-182736/*) is for the objects in that bucket
  
- We now try to list all the s3 buckets in the account using the 2 users
  <img width="1472" height="327" alt="image" src="https://github.com/user-attachments/assets/1289cd3d-1528-4ccd-adbe-49b00e997b9c" />

> we can see that the ec2 user doesnt have the permision to list all the buckets in the account but still can list the contents in the bucket we created. The ec2-user wasnt granted any permissions on the s3 bucket. It only has ec2 permissions, but still is able to access the s3 bucket. This is because the bucket policies and not the IAM role

# Phase 2: Restrict Access to a Specific IAM User (cloud_user)
## Objective:
Show how public access can be revoked using bucket policies, and how access can be limited to a single IAM principal.

### Steps:

- Now we update the bucket policy to only allow the cloud_user to access the bucket
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Statement1",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::320819923295:user/cloud_user"
            },
            "Action": [
                "s3:ListBucket",
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::anish-bucket-policies-182736",
                "arn:aws:s3:::anish-bucket-policies-182736/*"
            ]
        }
    ]
   }
  ```
- Lets try running the same commands
  <img width="1499" height="278" alt="image" src="https://github.com/user-attachments/assets/1b6a087a-d60f-4218-9460-4991bf5c8d71" />

> we can see that the ec2-user can no longer list the bucket contents
- lets revert it back and change the principal to allow everyone and test again
  <img width="1445" height="472" alt="image" src="https://github.com/user-attachments/assets/44616e28-3c3f-409f-80d1-25df86a2323b" />

> we can see that now we can list the contents using the ec2-user
- In phase 3 of this lab, we will try to grant the ec2 user to access the s3 using s3 gateway endpoints from a private ec2 instance using SSM, So lets revert our changes and use the same policy mentioned above to grant the access to the cloud_user alone by changing the principal in the policy back to the cloud_users ARN
  ```
  	"Principal": {
			    "AWS":"arn:aws:iam::[Accountnumber]:user/cloud_user"
			},
  ```

# Phase 3: Allow ec2-user to connect using s3 gateway endpoints and AWS SSM

- Create the VPC
  <img width="1575" height="756" alt="image" src="https://github.com/user-attachments/assets/c73b2e47-2d8d-425f-91a2-5552c3f5e9ec" />

- Create 2 subnets in the VPC
   <img width="1423" height="331" alt="image" src="https://github.com/user-attachments/assets/66a2cc6e-503f-487e-aae8-16369ddc1dae" />

- The public subnet will have the IGW and the NAT and we will configure the route tables accordingly. This is done so that we can connect to the EC2 instance using SSM and without any public IPs
- Create route tables for the subnets and associate them with the subnets
  <img width="1551" height="391" alt="image" src="https://github.com/user-attachments/assets/5e592411-f2af-4c69-a128-4b57320fa1f7" />
  <img width="1613" height="745" alt="image" src="https://github.com/user-attachments/assets/1784fe47-ec78-4ee7-b205-98c3d03bbb56" />

- Create an Internet gateway (IGW) and attach it to our VPC
  <img width="1903" height="361" alt="image" src="https://github.com/user-attachments/assets/a891c2bb-2cc2-457c-bd0d-4d963abb4412" />
- Add route in the public route table to the IGW
  <img width="1825" height="440" alt="image" src="https://github.com/user-attachments/assets/79af25da-eca6-4887-8d3d-6d333b3afe68" />
- in the private route table add a route to the NAT
  <img width="1748" height="548" alt="image" src="https://github.com/user-attachments/assets/2db7f93b-5161-4184-a8ec-202600ef64d0" />
- create a role that the EC2 instance will need to connect to AWS SSM service
  <img width="1493" height="763" alt="image" src="https://github.com/user-attachments/assets/7c79552f-fe28-4541-9ac9-6108bbacdfd5" />
- create an EC2
  <img width="1505" height="813" alt="image" src="https://github.com/user-attachments/assets/b2341f31-afd0-457a-b8c4-70a144712c16" />
  Also Select the instance profile as the role we previously created
  <img width="1126" height="417" alt="image" src="https://github.com/user-attachments/assets/5f3c15fa-9f59-4fa0-b278-d8c5b820cbe7" />
- ensure everything works by connecting to the ec2 using SSM
  <img width="1782" height="737" alt="image" src="https://github.com/user-attachments/assets/2a066f8f-631b-4b63-bb28-0df84612d610" />
- To let the user access the ec2 using SSM, we will grant the user full access to aws ssm (full access is not neeeded but that is not the intention for the lab)
  <img width="1442" height="760" alt="image" src="https://github.com/user-attachments/assets/2a8c20cf-e572-4012-80a8-129995bb9ace" />
- SSM into the EC2 instance
  ```bash
  aws ssm start-session --target i-xxxxxxxxxxxxxxxxx --profile ec2-user
  ```
  <img width="1283" height="447" alt="image" src="https://github.com/user-attachments/assets/6776638b-d2e8-4ca1-9fe3-0063aa0265e5" />
- try to list the contents in the S3 buckets
  <img width="1467" height="266" alt="image" src="https://github.com/user-attachments/assets/d8e0058c-9b14-45e9-a0cb-1bac35572066" />
 > The first time the command worked because i forgot to change the s3 bucket policy to remove the public access . Then I changed the principal to only allow access to the cloud_users ARN. so now it doesnt allow the ec2-user to list the s3 contents. The bucket policy now looks like the below
  <img width="645" height="452" alt="image" src="https://github.com/user-attachments/assets/198919d8-1d5b-4e94-8a5a-c39c0f246087" />
- Now lets allow the EC2 to list s3 contents via a S3 gateway endpoint
- Create the gateway endpoint
  <img width="1665" height="732" alt="image" src="https://github.com/user-attachments/assets/1c90356f-739c-4fc6-a0b6-db2dd54f1d40" />
  <img width="1873" height="781" alt="image" src="https://github.com/user-attachments/assets/418d8743-72bf-4958-84bf-4d77fca4d662" />
  - We select the S3 gateway endpoint service and choose our vpc and the private route table since the EC2 is in the private subnet and it uses the private route table and we select full access
- We can check the private route table to see the route that was created for the s3 endpoint
  <img width="1702" height="720" alt="image" src="https://github.com/user-attachments/assets/1f6443ff-d813-4b27-9a53-11205668f461" />
- Now we update the bucket policy to allow list permissions via the gateway endpoint, we paste the s3 gateway endpoints id in the bucket policy
  <img width="1673" height="781" alt="image" src="https://github.com/user-attachments/assets/ff3f3012-afae-4556-8e1a-fd734bb9ef94" />
- So the policy now looks like this.

 ```json
{
	            "Sid": "AllowOnlyFromVPCE",
	            "Effect": "Allow",
	            "Principal": "*",
	            "Action": [
	                "s3:ListBucket",
	                "s3:GetObject"
	            ],
	            "Resource": [
	                "arn:aws:s3:::anish-bucket-policies-182736",
	                "arn:aws:s3:::anish-bucket-policies-182736/*"
	            ],
	            "Condition": {
	                "StringEquals": {
	                    "aws:sourceVpce": "vpce-099c13df0b1a03451"
	                }
	            }
	        }
 ```

- Now we can connect to the s3 instance using the ec2, this however doesnt mean that the ec2-user has the permission to connect to the s3. Its the S3 endpoint that is granted permission to list the bucket contents. So anyone, who has the permissions to connect to the EC2 using SSM will be able to list the bucket contents
  <img width="892" height="228" alt="image" src="https://github.com/user-attachments/assets/969acfc3-0493-4546-a419-f22b3ec9abba" />

### Final bucket policy
``` json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "OnlyAllowCloudUser",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::320819923295:user/cloud_user"
            },
            "Action": [
                "s3:ListBucket",
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::anish-bucket-policies-182736",
                "arn:aws:s3:::anish-bucket-policies-182736/*"
            ]
        },
        {
            "Sid": "AllowOnlyFromVPCE",
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:ListBucket",
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::anish-bucket-policies-182736",
                "arn:aws:s3:::anish-bucket-policies-182736/*"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:sourceVpce": "vpce-099c13df0b1a03451"
                }
            }
        }
    ]
}
```	


















  








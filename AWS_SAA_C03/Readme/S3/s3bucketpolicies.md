# S3 bucket policies

# lab
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

# Phase 3: Allow ec2-user to connect using s3 gateway endpoints









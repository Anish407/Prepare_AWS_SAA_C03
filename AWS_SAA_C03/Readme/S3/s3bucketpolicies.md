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


## Steps


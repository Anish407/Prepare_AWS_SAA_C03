# EC2 Instance profiles
It is a way to attach an IAM role to an EC2 instance, allowing applications running on that instance to securely access AWS services without needing to manage long-term credentials.
It lets an EC2 Instance Profile is the thing that lets an EC2 instance “be” an IAM role without you stuffing access keys onto the box.

When you attach an instance profile, EC2 automatically makes temporary credentials available to software on the instance via the Instance Metadata Service (IMDS).
## Key Concepts
- **IAM Role**: A set of permissions that define what actions are allowed on which AWS resources.
- **Instance Profile**: A container for an IAM role that can be attached to an EC2 instance. Each instance profile can contain only one role.
- **Temporary Credentials**: When an EC2 instance is launched with an instance profile, AWS automatically provides temporary security credentials to the instance, which applications can use to access AWS services.
- **Security**: Using instance profiles enhances security by eliminating the need to store AWS credentials on the instance.
- **Automatic Rotation**: The temporary credentials provided to the instance are automatically rotated by AWS, reducing the risk of credential compromise.
- **Use Cases**: Commonly used for applications running on EC2 instances that need to access services like S3, DynamoDB, or SQS.
- **Best Practices**: Always use instance profiles for EC2 instances instead of embedding AWS credentials in application code or configuration files.

# Hands on task
1. Create an S3 bucket and upload a file:
  - s3://<your-bucket>/public/hello.txt
  - s3://<your-bucket>/private/secret.txt

2. Create an IAM role with the following permissions:
<img width="1600" height="982" alt="image" src="https://github.com/user-attachments/assets/e636f234-f271-45a4-bca2-2c39e4307287" />

  - Add permissions AmazonSSMInstanceManagedInstanceCore. This is required to connect to the instance using SSM.
<img width="1600" height="1039" alt="image" src="https://github.com/user-attachments/assets/dbf540f2-8e40-492b-9765-920a20be0aa7" />

3. Add a custom policy that allows read access to the public prefix of the S3 bucket:
  - Create a policy with the following JSON, replacing <your-bucket> with your actual bucket name:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::<your-bucket>/public/*"
        }
    ]
}
```
<img width="1239" height="459" alt="image" src="https://github.com/user-attachments/assets/a8e9797a-9129-4619-b73e-dba04f032215" />

<img width="1600" height="805" alt="image" src="https://github.com/user-attachments/assets/4dcaa644-9cb6-4343-8d4a-64e162ff6594" />


4. Attach the IAM role to an EC2 instance:
  - Launch a new EC2 instance or use an existing one.
  - Attach the IAM role created in step 2 to the EC2 instance. by selecting the instance profile created along with the role.
  <img width="1600" height="1038" alt="image" src="https://github.com/user-attachments/assets/e22466b5-ec3a-465b-b99c-8b0708a0ae07" />

  - Launch the instance.
5. Connect to the EC2 instance using AWS Systems Manager Session Manager:
cd to the user home directory and try to run the aws cli command to download the public file.
```bash
aws s3 cp s3://<your-bucket>/public/hello.txt .
```
At first the uploading failed because i added the wrong permission s3:getobjectacl instead of s3:getobject. But then i replaced it with the correct permission to make it work

<img width="1270" height="793" alt="image" src="https://github.com/user-attachments/assets/f16230d5-3bb7-4ed5-b0ba-836411485d82" />

<img width="1191" height="342" alt="image" src="https://github.com/user-attachments/assets/8998a8d1-50f0-45a2-ad6b-38df35708037" />


## Key points

- Trust policy answers only one question. “Who is allowed to assume this role?”. It’s an authentication / assume-step gate, not an authorization list for S3.
- Even if you try to shove S3 actions into a trust policy:
  - S3 will ignore it, because S3 never evaluates a role’s trust policy when authorizing s3:GetObject.
  - Trust policies don’t even use the same evaluation context as identity permissions. They’re evaluated by STS during AssumeRole, not by S3 during GetObject.
  - Bucket is in the same AWS account, so we dont need separate s3 resource policies. The permission added to the trust role is enough.
  - Permission policies (identity-based) attached to the role
    - Purpose: WHAT the role can do after assumed
    - Evaluated by: the target service (S3, DynamoDB, etc.). This is where s3:GetObject, s3:ListBucket, etc. go.




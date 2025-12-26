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
image
  - Add permissions AmazonSSMInstanceManagedInstanceCore. This is required to connect to the instance using SSM.
  image
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
image 
image

4. Attach the IAM role to an EC2 instance:
  - Launch a new EC2 instance or use an existing one.
  - Attach the IAM role created in step 2 to the EC2 instance. by selecting the instance profile created along with the role.
  image
  - Launch the instance.
5. Connect to the EC2 instance using AWS Systems Manager Session Manager:
cd to the user home directory and try to run the aws cli command to download the public file.
```bash
aws s3 cp s3://<your-bucket>/public/hello.txt .
```
image  
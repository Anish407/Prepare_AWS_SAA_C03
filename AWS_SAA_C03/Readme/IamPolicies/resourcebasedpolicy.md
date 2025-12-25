## Resource based policies

A resource-based policy is a type of IAM policy that you can attach to an AWS resource. It defines who (which AWS accounts or IAM users) can access the resource and what actions they can perform on it. Resource-based policies are commonly used with services like Amazon S3, Amazon SNS, Amazon SQS, and AWS Lambda.

### Key Features of Resource-Based Policies:
1. **Attached to Resources**: Unlike identity-based policies that are attached to users, groups, or roles, resource-based policies are directly attached to the resource itself.
1. **Cross-Account Access**: Resource-based policies can grant permissions to users or roles in different AWS accounts, enabling cross-account access.
1. **Fine-Grained Control**: They allow for fine-grained control over who can access the resource and what actions they can perform.
1. **Policy Structure**: Resource-based policies use the same JSON structure as identity-based policies, including elements like `Effect`, `Action`, `Resource`, and `Condition`.
1. **Examples of Services Using Resource-Based Policies**:
   - **Amazon S3**: Bucket policies that define access permissions for S3 buckets.
   - **AWS Lambda**: Resource policies that control which AWS accounts or services can invoke a Lambda function.
   - **Amazon SNS**: Topic policies that manage access to SNS topics.
   - **Amazon SQS**: Queue policies that define who can send messages to or receive messages from an SQS queue.

#### What a resource-based policy is (and why it matters)

A resource-based policy is a JSON policy attached to the AWS resource itself (bucket, queue, key, function, etc.). It answers:

> “Who is allowed to access this resource, and under what conditions?”

Key differences vs identity-based policies:
- Identity-based policy (on user/role/group): what this identity can do.
- Resource-based policy (on the resource): who can access this resource.
- Resource-based policies include a Principal (who). Identity-based policies do not.

   #### Example 
1. In this example, we create an s3 bucket and add the following folders

image1
image2

2. Then we create 2 users
  - fake_user
  - fake_user2

The main folder public and "reports/public/*"  contains text files that can be read by the 
fake_user.

The folder "reports/confidential/*" contains text files that can only be read by the fake_user2.

The s3 bucket policy is as follows:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowListOnlyPublicAndReportsPublicPrefix",
            "Effect": "Allow",
            "Principal": {
                "AWS": "AIDAQ3EGUETK3STVILZ5Q"
            },
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::rbp-challenge",
            "Condition": {
                "StringLike": {
                    "s3:prefix": [
                        "reports/public/",
                        "reports/public/*",
                        "public/",
                        "public/*"
                    ]
                }
            }
        },
        {
            "Sid": "AllowGetObjectPublicAndReportsPublic",
            "Effect": "Allow",
            "Principal": {
                "AWS": "AIDAQ3EGUETK3STVILZ5Q"
            },
            "Action": "s3:GetObject",
            "Resource": [
                "arn:aws:s3:::rbp-challenge/public/*",
                "arn:aws:s3:::rbp-challenge/reports/public/*"
            ]
        },
        {
            "Sid": "AllowGetObjectPublicAndReportsPublicAndConfidential",
            "Effect": "Allow",
            "Principal": {
                "AWS": "AIDAQ3EGUETKXO754UJQK"
            },
            "Action": "s3:GetObject",
            "Resource": [
                "arn:aws:s3:::rbp-challenge/public/*",
                "arn:aws:s3:::rbp-challenge/reports/public/*",
                "arn:aws:s3:::rbp-challenge/reports/confidential/*"
            ]
        }
    ]
}
```

### Testing the application

- Configure the profile for the fake_user and fake_user2 using the AWS CLI.
- Login as fake_user and try to read the files in the public and reports/public folders. You should have access. use the following command:
  ```bash
  aws s3 --profile fake_user1 cp s3://rbp-challenge/public/public.txt . .
  aws s3 --profile fake_user1 cp s3://rbp-challenge/reports/public/report1.txt .
  ```
- Try to download the files in the reports/confidential folder as fake_user1. You should get an Access Denied error. use the following command:
  ```bash
  aws s3 --profile fake_user1 cp s3://rbp-challenge/reports/public/confidential.txt .
  ```

  - Now login as fake_user2 and try to read the files in the public, reports/public and reports/confidential folders. You should have access to all the files. use the following command:
```bash
 aws s3 --profile fake_user1 cp s3://rbp-challenge/reports/public/confidential.txt .
```
image

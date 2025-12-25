## IAM Roles
A role is an AWS identity with permissions that is meant to be assumed (temporarily) by someone/something else. They are
- Short-term credentials
- You don’t “log in as a role” permanently — you assume it and get temporary credentials.
- Roles are how AWS services (ECS/Lambda/EC2) get permissions without baking secrets into code.Used by applications, services, or users needing temporary access.
- Cross-account access: Account A assumes role in Account B.

### Roles have two main policies:
   1) **Permission policy (WHAT you can do after assuming)**:  ex: what can I do once I am me?
     - Attached to the role (inline or managed).
     -  Example: s3:GetObject, sqs:SendMessage, etc.
      
  2) **Trust policy (WHO can assume the role)**: ex: who can become me?
      -  what the role can do (like an identity-based policy)
       - Controls sts:AssumeRole. It contains a Principal element. 
       -  Example principals: an IAM user, another role, or an AWS service like ecs-tasks.amazonaws.com
  
  ### STS (Security Token Service)

  It doesn’t “authorize” anything by itself — it just issues temporary credentials that inherit permissions from whatever you assumed/federated into.

   - Used to assume roles and get temporary credentials.
   - Sts issues temporary security credentials (Access Key ID, Secret Access Key, Session Token).

   Those credentials are then used to sign AWS API requests (SigV4) just like normal keys — except they expire and must include the session token.

   #### Step-by-step

    1.  Caller already has identity

Could be an IAM user, a role attached to ECS/Lambda, or a federated identity.

 - Caller calls STS:
 - AssumeRole(RoleArn, RoleSessionName, …)
 - AWS checks two things:
    - Caller has permission to call sts:AssumeRole on that role (identity policy on the caller side).
    - The role trust policy allows this caller as a Principal.

- If both pass, STS returns temporary credentials for that role.
- Caller uses those temp creds to call services like S3/SQS/etc.

# Exercise 1: Create a user and create a trust policy and then give the user just s3 acess in the **CONSOLE**

 1.  Create a user and copy the arn
 2. Create a role (trust policy)
 image
 Add the user arn in the principal section of the trust policy
 ```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "UserAllowedS3",
			"Effect": "Allow",
			"Principal": {
				"AWS": "arn:aws:iam::[accountnumber]:user/fake_user1" (Copied from step 1)
			},
			"Action": "sts:AssumeRole"
		}
	]
}
 ```
   3. Attach s3 read only access policy to the role
	image
  4. Now login as the user created in step 1
	 We can see that the user has no permissions to s3
    image
 5. Now we will assume the role created using the console
	image
 6. Now we can see that the user has s3 read only access
	image

# Test the scenario using aws cli

1. login using the fake_user
```
$env:AWS_PROFILE="fake_user1"
aws sts get-caller-identity
```
2. run the command
```
aws s3 ls --profile fake_user1
```
we get an error as the user has no permissions to s3
3. Now assume the role using the below command
```
aws sts assume-role --role-arn arn:aws:iam::[Accountnumber]:role/s3_access_trust_policy --role-session-name lab1 --profile fake_user1
```
4. We get the temporary credentials in the output
5.  Now inorder to run the s3 command we need to export the temporary credentials as env variables
 we can open the file that contains the aws credentails and create a new profile for the assumed role
	image
6. Now run the s3 command using the new profile
```
aws s3 ls --profile assumed_trustpolicy
```
Now we will be able to list the buckets as the role has s3 read only access
image

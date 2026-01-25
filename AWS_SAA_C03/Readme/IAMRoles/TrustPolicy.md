## IAM Roles
A role is an AWS identity with permissions that is meant to be assumed (temporarily) by someone/something else. They are
- Short-term credentials
- You don’t “log in as a role” permanently — you assume it and get temporary credentials.
- Roles are how AWS services (ECS/Lambda/EC2) get permissions without baking secrets into code.Used by applications, services, or users needing temporary access.
- Cross-account access: Account A assumes role in Account B.

> A trust policy always lives on the role being assumed.
> Never on the caller.

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
<img width="1600" height="1038" alt="image" src="https://github.com/user-attachments/assets/210d58fb-64c8-4380-909a-c6c33eb31cad" />

 Add the user arn in the principal section of the trust policy
 <img width="1339" height="715" alt="image" src="https://github.com/user-attachments/assets/9047df43-d8a1-46f6-9e67-168707c0424c" />

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
<img width="1600" height="938" alt="image" src="https://github.com/user-attachments/assets/dcb366b9-2748-4d83-8a3b-b114c034420d" />
<img width="1600" height="918" alt="image" src="https://github.com/user-attachments/assets/b5aa0de5-5cc1-47ff-8857-f9bcd08a9b5a" />

  4. Now login as the user created in step 1
	 We can see that the user has no permissions to s3
  <img width="1411" height="1102" alt="image" src="https://github.com/user-attachments/assets/11ba5896-be7b-4416-8d0a-723468e56bb2" />

 5. Now we will assume the role created using the console
    <img width="1600" height="753" alt="image" src="https://github.com/user-attachments/assets/bdf5a9cf-c2be-4dc0-8394-bfa8b32a1403" />

	<img width="1384" height="915" alt="image" src="https://github.com/user-attachments/assets/d5976f1b-b22a-4bf6-8e91-57c6b9b0616e" />
    > The user doesnt have access to any other resource since the trust policy only has permissions assigned for s3
    <img width="1303" height="391" alt="image" src="https://github.com/user-attachments/assets/bff37010-c85e-406a-836f-9f0384fe42f8" />

 6. Now we can see that the user has s3 read only access
   So we create a bucket 
	<img width="1600" height="917" alt="image" src="https://github.com/user-attachments/assets/4c195bb1-f526-44d2-a662-6514bffdbd87" />


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
<img width="1267" height="162" alt="image" src="https://github.com/user-attachments/assets/abb33c92-fcf8-42e5-91f1-b73927065d31" />

3. Now assume the role using the below command
```
aws sts assume-role --role-arn arn:aws:iam::[Accountnumber]:role/s3_access_trust_policy --role-session-name lab1 --profile fake_user1
```
4. We get the temporary credentials in the output
5.  Now inorder to run the s3 command we need to export the temporary credentials as env variables
 we can open the file that contains the aws credentails and create a new profile for the assumed role
	<img width="1264" height="373" alt="image" src="https://github.com/user-attachments/assets/427c0e5a-53be-4162-8f36-6e70a23cd1b1" />
	```
	[assumed_trustpolicy]
	ignore_configured_endpoint_urls=false
	region=us-east-1
	role_arn=arn:aws:iam::{Accountnumber}:role/s3_access_trust_policy
	source_profile=fake_user1
	toolkit_artifact_guid=131cd5e7-dff9-4eff-bbb5-88439b399313
	```
6. Now run the s3 command using the new profile
```
aws s3 ls --profile assumed_trustpolicy
```
Now we will be able to list the buckets as the role has s3 read only access
<img width="955" height="116" alt="image" src="https://github.com/user-attachments/assets/cd874f06-9d79-480a-9d23-00678a5bcfd9" />


# IAM Lab #01 — Identity-based policy (Group) + S3 access from a .NET Web API

This lab proves (with real errors + real API calls) how an **identity-based IAM policy** controls what your app can do in S3.

### what was  created:
- An S3 bucket with `public/` and `private/` objects
- An IAM **user** in an IAM **group**
- A **group policy** that:
  - lets the user *use the S3 console* (bucket list UI support)
  - lets the user list objects in *one bucket*
  - lets the user **read only `public/*`**
- A .NET Web API endpoint that reads S3 objects using AWS credentials (local dev)


## Important notes

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ConsoleListBuckets",
            "Effect": "Allow",
            "Action": "s3:ListAllMyBuckets",
            "Resource": "*"
        },
        {
            "Sid": "ConsoleGetBucketLocationAllBuckets",
            "Effect": "Allow",
            "Action": "s3:GetBucketLocation",
            "Resource": "arn:aws:s3:::*"
        },
        {
            "Sid": "ListAllObjectsInLabBucket",
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::[BucketName]"
        },
        {
            "Sid": "ReadOnlyPublicPrefix",
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::[BucketName]/public/*"
        }
    ]
}
```
- ConsoleListBuckets: The S3 console UI needs this to show the bucket list page, even if the user can't access all buckets. It 
Lists bucket names in the account. It does not grant access to view or download objects inside any bucket. So downloading objects still requires additional permissions and will fail. The console needs this permission "GetBucketLocation" to list all the buckets along with the "ListAllMyBuckets" permission.
- ListAllObjectsInLabBucket: This allows listing objects in the specified bucket. Without this permission, the user cannot see the objects in the bucket, even if they have permissions to access specific objects.
- ListAllObjectsInLabBucket: Listing object keys in the specific bucket iam-lab-s3. This only lists keys (filenames/prefixes). It does not allow reading object content. So, The user can see both public/ and private/ objects listed (because listing is allowed for the whole bucket).
- ReadOnlyPublicPrefix: This allows reading (GetObject) only objects under the public/ prefix. Any attempt to read objects outside this prefix (like private/) will be denied.

---

### Testing the setup
1. Generate the access key and secret key for the IAM user (fake_user) and not the root user using the below command:
 ```
  aws configure --profile iam-lab-user
   ```
   Enter the access key and secret key when prompted.(also the region)
2. Now in the extension we can see that we have registered 
```
  services.AddDefaultAWSOptions(configuration.GetAWSOptions());
```
what this does is it will read the credentials from the default profile which we have configured in the previous step. 
Remember that the region and profile name are read from the appsettings.json file. This is done so that we dont have to specify the access key and secret key in the code directly.

The profile name is optional if you are using the default profile. Aws finds out the profile name from the appsettings.json file and gets the access key and secret key from the credentials file.

3. Use the AWS S3 console with the IAM user credentials:
   - You should see the bucket in the list.
   - You should see both `public/` and `private/` objects listed.
   - Attempting to open/download a `public/` object should succeed.
   - Attempting to open/download a `private/` object should fail with an access denied error.

4. Since the user hasnt been granted any permission on the private prefix, any attempt to access objects under the private/ prefix will result in an Access Denied error.

5. Test the .NET Web API endpoint:
   - Accessing the endpoint to read a `public/` object should succeed and return the object content.
   - Accessing the endpoint to read a `private/` object should fail with an access denied error. We get the following error
   User: arn:aws:iam::[AccountNumber]:user/iam-lab-user is not authorized to perform: s3:GetObject on resource: \"arn:aws:s3:::[BucketName]/private/secret.txt\" because no identity-based policy allows the s3:GetObject action

  6. now to grant the user access to the private prefix, we need to update the group policy to include the following statement
  
      ```      
      {
      "Sid": "ReadOnlyPrivatePrefix",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::iam-lab-s3-anish-3498/private/*"
    }
    ```
7. After updating the policy, we can test the .NET Web API endpoint again to read a `private/` object. This time it should succeed and return the object content.



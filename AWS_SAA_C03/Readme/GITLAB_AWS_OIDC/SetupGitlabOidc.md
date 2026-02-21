# Setup the gitlab OIDC with AWS to run pipelines


## Step 1 - Create the Identity provider in aws
<img width="1847" height="658" alt="image" src="https://github.com/user-attachments/assets/b5e87077-adaa-46bd-bc84-fcf93081fcee" />

Keep note of the ARN for the provider we just added. This will be required in the next step where we will create a trust policy
<img width="1880" height="750" alt="image" src="https://github.com/user-attachments/assets/2e2c7ebd-d86b-4e9b-8344-c7e4b34de064" />

## Step 2: Create a policy that defines what can be done using the token

<img width="1487" height="692" alt="image" src="https://github.com/user-attachments/assets/f844066a-445d-43e8-85c1-f1ca7795146d" />

<img width="1547" height="522" alt="image" src="https://github.com/user-attachments/assets/5550b9c8-4049-4e49-9b2d-9e5d1644f834" />


I created a policy with some s3 actions on my account. Even though i gave it access to all my buckets, its better to lock it to specific resources.

## Step 3 — AWS: Create an IAM Role that trusts GitLab tokens

1. Create a custom trust policy in IAM 
<img width="1862" height="532" alt="image" src="https://github.com/user-attachments/assets/d08b284d-d9e6-48e9-beeb-d130e022c70f" />

2. Paste the following json in the trust policy document and replace it the actual values
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/gitlab.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "gitlab.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "gitlab.com:sub": "project_path:learngitlab3324139/gitlabawsoidc:ref_type:branch:ref:main"
        }
      }
    }
  ]
}
```

3. Inside the "Principal" section, replace the ARN with the exact ARN of the OIDC Identity Provider that you created in Step 1.
   ```json
    "Principal": {
        "Federated": "arn:aws:iam::851725212263:oidc-provider/gitlab.com"
      },
    ```
   This ARN must exactly match the OIDC provider in your AWS account. If it doesn’t match, AWS will reject the token during validation.
4. In the condition we have mentioned that the sub claim in the token will be
```code
    `project_path:learngitlab3324139/gitlabawsoidc:ref_type:branch:ref:main` . 
```
It means that the IAM role can only be assumed by:
- The GitLab project learngitlab3324139/gitlabawsoidc
- A pipeline running on a branch
- Specifically the main branch

In other words, this trust policy restricts AWS role access to a single repository and a single branch.

5.  aud = sts.amazonaws.com? Because your GitLab job should request the token with that audience, and AWS should require it.
That’s the standard pattern in GitLab’s AWS OIDC guidance.

6. Add the policy to the trust policy we created in Step 2
   <img width="1903" height="761" alt="image" src="https://github.com/user-attachments/assets/4ce16625-bf69-4c7c-a33a-e1bee690fb57" />


## Setup gitlab to connect to AWS

1. I created 2 variables in the gitlab CICD sections, they will be used by the job to connect to aws. 
   <img width="1811" height="893" alt="image" src="https://github.com/user-attachments/assets/2320d03e-8915-4e5d-91eb-dc84927e7232" />
   - The ROLE_ARN is the ARN for the trust policy we created
   - Region: specifies the region the account is in.
  
2. The gitlab job will look like this
    ```yml
    oidc_test:
      image: amazon/aws-cli:2
      id_tokens:
        AWS_TOKEN:
          aud: sts.amazonaws.com
      variables:
        AWS_DEFAULT_REGION: $AWS_REGION
      script:
        - echo "$AWS_TOKEN" > /tmp/web_identity_token
        - export AWS_WEB_IDENTITY_TOKEN_FILE=/tmp/web_identity_token
        - export AWS_ROLE_ARN=$ROLE_ARN
        - aws sts get-caller-identity
    ```

#### What This Pipeline Does

This job allows GitLab CI to authenticate to AWS using OIDC (OpenID Connect) and assume an IAM role without storing AWS access keys.

The flow is:
- GitLab generates an OIDC ID token for the job
- The AWS CLI exchanges that token for temporary AWS credentials
- The job runs AWS commands using those temporary credentials




# Registering the gitlab runner

1. Get the gitlab runner from [here](https://docs.gitlab.com/runner/install/)

2. Downloading the exe to a folder
   <img width="930" height="480" alt="image" src="https://github.com/user-attachments/assets/8f90d107-226c-4c2b-b19a-d56cf17187fc" />
3. Run the follwoing command to register the runner
  ```bash
   gitlab-runner register
  ```   

   <img width="1454" height="474" alt="image" src="https://github.com/user-attachments/assets/d320506e-c490-423b-bf68-2f7c6ab0af4b" />















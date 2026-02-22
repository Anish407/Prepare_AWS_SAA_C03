# Setup the gitlab OIDC with AWS to run pipelines

-----------------------------------

# Registering the gitlab runner

1. Get the gitlab runner from [here](https://docs.gitlab.com/runner/install/) and also install Docker desktop

2. Install GitLab Runner on Windows

Create a directory:

``` powershell
mkdir C:\GitLab-Runner
cd C:\GitLab-Runner
```
Place `gitlab-runner.exe` inside that folder.

Install and start the service:

``` powershell
.\gitlab-runner.exe install
.\gitlab-runner.exe start
```

Verify service is running:

``` powershell
Get-Service gitlab-runner
```

3. Create a Runner in GitLab

Go to:

Project -> Settings -> CI/CD -> Runners -> Create Runner

<img width="1475" height="585" alt="image" src="https://github.com/user-attachments/assets/ad1cf4a9-0694-437f-a669-6f13ab33dab8" />


You will receive:

-   GitLab URL
-   Registration token

<img width="1242" height="741" alt="image" src="https://github.com/user-attachments/assets/40667503-7708-4bfe-83c6-1938fdc9872b" />

  
4. # Step 4 -- Register the Runner

Run:

``` powershell
.\gitlab-runner.exe register
```

Provide the following details when prompted:

GitLab instance URL:

    https://gitlab.com/

Registration token: (Paste token from GitLab)

Description:

    local-docker-runner

Tags:

    local,docker,aws

Executor:

    docker

Default Docker image:

    amazon/aws-cli:latest


5. Verify Runner in GitLab

Go back to GitLab and confirm the runner shows as:

local-docker-runner (online)

6. Use the Runner in .gitlab-ci.yml

Add tags to force jobs to use your runner:

``` yaml
oidc_test:
  stage: test
  tags:
    - local
  image:
    name: amazon/aws-cli:latest
    entrypoint: [""]
  script:
    - aws --version
```
    
-------------------

## Step 1 - Create the Identity provider in aws
- URL: https://gitlab.com
- Audience: pick sts.amazonaws.com (recommended, and common)
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



# Create an S3 bucket and put a file in it
<img width="1250" height="487" alt="image" src="https://github.com/user-attachments/assets/446947a6-ab3e-4191-85dc-8d588bc87199" />

we will list the files in this bucket from gitlab using the gitlab OIDC flow

# Create the gitlab Pipeline

```yml
oidc_test:
  stage: test
  image:
    name: amazon/aws-cli:latest
    entrypoint: [""]
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
    - aws s3 ls s3://gitlab-oidc-demo
```
- Run the pipeline
<img width="751" height="456" alt="image" src="https://github.com/user-attachments/assets/b8a71ff0-7896-4a3b-aa93-0ae8c3aa9956" />

- The gitlab job now successfully connects to aws and lists the bucket contents
<img width="1221" height="328" alt="image" src="https://github.com/user-attachments/assets/17933a6d-a1db-4cd1-8673-e66a0e302178" />










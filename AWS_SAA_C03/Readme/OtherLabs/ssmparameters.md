# AWS Systems Manager Parameter Store IAM + KMS + AssumeRole Lab

## Goal

This lab demonstrates how to secure AWS Systems Manager Parameter Store using:

- IAM path-based access
- SecureString parameters encrypted with AWS KMS
- STS AssumeRole for temporary privilege elevation
- Environment-specific admin roles
- A platform-level super admin role

The lab uses only two environments:

```text
/app/dev/*
/app/prod/*
```

You will create two normal users:

```text
dev-user
prod-user
```

You will also create one platform/admin user:

```text
platform-admin-user
```

The normal users can read only their own environment's non-sensitive parameters by default. They cannot decrypt SecureString parameters directly.

To decrypt SecureString parameters, they must assume an environment-specific role.

A separate platform admin user can assume a super admin role that can read and decrypt all parameters across both environments.

---

## What You Will Build

```text
Users:
  dev-user
  prod-user
  platform-admin-user

Roles:
  DevParameterAdminRole
  ProdParameterAdminRole
  ParameterStoreSuperAdminRole

KMS Keys:
  alias/ssm-dev-key
  alias/ssm-prod-key

Parameter paths:
  /app/dev/*
  /app/prod/*
```

---

## Access Model

| Identity | Dev String | Dev SecureString | Prod String | Prod SecureString |
|---|---:|---:|---:|---:|
| `dev-user` | Yes | No | No | No |
| `prod-user` | No | No | Yes | No |
| `DevParameterAdminRole` | Yes | Yes | No | No |
| `ProdParameterAdminRole` | No | No | Yes | Yes |
| `ParameterStoreSuperAdminRole` | Yes | Yes | Yes | Yes |

---

## Important Learning Point

A SecureString parameter has two permission layers:

```text
1. SSM permission
   Example: ssm:GetParameter

2. KMS permission
   Example: kms:Decrypt
```

If a user has `ssm:GetParameter` but does not have `kms:Decrypt`, the user may be able to access normal String parameters, but cannot decrypt SecureString values.

This is the core security pattern in this lab.

---

## Prerequisites

You need:

- AWS CLI installed
- An admin AWS CLI profile configured
- Permission to create IAM users, IAM roles, IAM policies, KMS keys, and SSM parameters

Check your AWS CLI:

```bash
aws --version
```

Check your current identity:

```bash
aws sts get-caller-identity
```

Set environment variables:

```bash
export AWS_REGION=eu-north-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Optional: verify values
echo $AWS_REGION
echo $AWS_ACCOUNT_ID
```

You can replace `eu-north-1` with your preferred AWS region.

---

# Phase 1: Create KMS Keys

You will create separate KMS keys for dev and prod.

This makes the lab easier to understand because dev roles get decrypt access only to the dev key, and prod roles get decrypt access only to the prod key.

---

## 1.1 Create Dev KMS Key

```bash
DEV_KMS_KEY_ID=$(aws kms create-key \
  --description "KMS key for dev SSM SecureString parameters" \
  --query KeyMetadata.KeyId \
  --output text \
  --region $AWS_REGION)

echo $DEV_KMS_KEY_ID
```

Create alias:

```bash
aws kms create-alias \
  --alias-name alias/ssm-dev-key \
  --target-key-id $DEV_KMS_KEY_ID \
  --region $AWS_REGION
```

Get Dev KMS key ARN:

```bash
DEV_KMS_KEY_ARN=$(aws kms describe-key \
  --key-id alias/ssm-dev-key \
  --query KeyMetadata.Arn \
  --output text \
  --region $AWS_REGION)

echo $DEV_KMS_KEY_ARN
```

---

## 1.2 Create Prod KMS Key

```bash
PROD_KMS_KEY_ID=$(aws kms create-key \
  --description "KMS key for prod SSM SecureString parameters" \
  --query KeyMetadata.KeyId \
  --output text \
  --region $AWS_REGION)

echo $PROD_KMS_KEY_ID
```

Create alias:

```bash
aws kms create-alias \
  --alias-name alias/ssm-prod-key \
  --target-key-id $PROD_KMS_KEY_ID \
  --region $AWS_REGION
```

Get Prod KMS key ARN:

```bash
PROD_KMS_KEY_ARN=$(aws kms describe-key \
  --key-id alias/ssm-prod-key \
  --query KeyMetadata.Arn \
  --output text \
  --region $AWS_REGION)

echo $PROD_KMS_KEY_ARN
```
<img width="874" height="310" alt="image" src="https://github.com/user-attachments/assets/24e57818-18b1-4605-a58b-86e3ab1fa976" />

---

# Phase 2: Create Parameter Store Values

You will create String and SecureString parameters.

Normal String parameters:

```text
/app/dev/db-url
/app/dev/api-url
/app/prod/db-url
/app/prod/api-url
```

SecureString parameters:

```text
/app/dev/db-password
/app/dev/api-key
/app/prod/db-password
/app/prod/api-key
```

---

## 2.1 Create Dev String Parameters

```bash
aws ssm put-parameter \
  --name "/app/dev/db-url" \
  --value "dev-db.example.internal" \
  --type String \
  --overwrite \
  --region $AWS_REGION

aws ssm put-parameter \
  --name "/app/dev/api-url" \
  --value "https://dev-api.example.com" \
  --type String \
  --overwrite \
  --region $AWS_REGION
```
<img width="926" height="406" alt="image" src="https://github.com/user-attachments/assets/6cef5c5c-27ac-4892-893a-33784c2b550f" />
<img width="860" height="397" alt="image" src="https://github.com/user-attachments/assets/fdbc49c4-2b65-4e19-85a1-4ad4f0ebbb9b" />

---

## 2.2 Create Prod String Parameters

```bash
aws ssm put-parameter \
  --name "/app/prod/db-url" \
  --value "prod-db.example.internal" \
  --type String \
  --overwrite \
  --region $AWS_REGION

aws ssm put-parameter \
  --name "/app/prod/api-url" \
  --value "https://api.example.com" \
  --type String \
  --overwrite \
  --region $AWS_REGION
```
<img width="560" height="194" alt="image" src="https://github.com/user-attachments/assets/7ec9e6c3-1fc0-42ee-ab3c-23a56b00725c" />

---

## 2.3 Create Dev SecureString Parameters

These values are encrypted using the dev KMS key.

```bash
aws ssm put-parameter \
  --name "/app/dev/db-password" \
  --value "dev-password-123" \
  --type SecureString \
  --key-id "$DEV_KMS_KEY_ARN" \
  --overwrite \
  --region $AWS_REGION

```
<img width="874" height="403" alt="image" src="https://github.com/user-attachments/assets/20e51a39-d3b7-4896-9825-61c1e8cce3ed" />

---

## 2.4 Create Prod SecureString Parameters

These values are encrypted using the prod KMS key.

```bash
aws ssm put-parameter \
  --name "/app/prod/db-password" \
  --value "prod-password-123" \
  --type SecureString \
  --key-id "$PROD_KMS_KEY_ARN" \
  --overwrite \
  --region $AWS_REGION

```
<img width="859" height="406" alt="image" src="https://github.com/user-attachments/assets/87a06fd4-3d80-421e-a92e-ea72a8c96b0d" />

---

## 2.5 Verify Parameters as Admin

```bash
aws ssm get-parameters-by-path \
  --path "/app" \
  --recursive \
  --with-decryption \
  --region $AWS_REGION
```

Expected result: you should see all dev and prod parameters with decrypted SecureString values.

---

# Phase 3: Create IAM Users

Create three users:

```text
dev-user
prod-user
platform-admin-user
```

```bash
aws iam create-user --user-name dev-user
aws iam create-user --user-name prod-user
aws iam create-user --user-name platform-admin-user
```

---

## 3.1 Create Access Keys

Create access keys for each user:

```bash
aws iam create-access-key --user-name dev-user
aws iam create-access-key --user-name prod-user
aws iam create-access-key --user-name platform-admin-user
```

Save the returned values:

```text
AccessKeyId
SecretAccessKey
```

You will use them to create AWS CLI profiles.

---

## 3.2 Configure AWS CLI Profiles

Configure `dev-user` profile:

```bash
aws configure --profile dev-user
```

Configure `prod-user` profile:

```bash
aws configure --profile prod-user
```

Configure `platform-admin-user` profile:

```bash
aws configure --profile platform-admin-user
```

Use:

```text
AWS Access Key ID:     value from create-access-key
AWS Secret Access Key: value from create-access-key
Default region:        eu-north-1
Default output:        json
```

Test each profile:

```bash
aws sts get-caller-identity --profile dev-user
aws sts get-caller-identity --profile prod-user
aws sts get-caller-identity --profile platform-admin-user
```

---

# Phase 4: Create Default User Policies

Default users should have limited SSM read access to their own environment only.

They should not have `kms:Decrypt`.

This is intentional.

---

## 4.1 Create Dev User Default Policy

Create policy document:

```bash
cat > dev-user-default-ssm-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOnlyDevParameters",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/app/dev/*"
    }
  ]
}
EOF
```

Create IAM policy:

```bash
DEV_USER_POLICY_ARN=$(aws iam create-policy \
  --policy-name DevUserDefaultSsmReadPolicy \
  --policy-document file://dev-user-default-ssm-policy.json \
  --query Policy.Arn \
  --output text)

echo $DEV_USER_POLICY_ARN
```

Attach policy to `dev-user`:

```bash
aws iam attach-user-policy \
  --user-name dev-user \
  --policy-arn "$DEV_USER_POLICY_ARN"
```

---

## 4.2 Create Prod User Default Policy

Create policy document:

```bash
cat > prod-user-default-ssm-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOnlyProdParameters",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/app/prod/*"
    }
  ]
}
EOF
```

Create IAM policy:

```bash
PROD_USER_POLICY_ARN=$(aws iam create-policy \
  --policy-name ProdUserDefaultSsmReadPolicy \
  --policy-document file://prod-user-default-ssm-policy.json \
  --query Policy.Arn \
  --output text)

echo $PROD_USER_POLICY_ARN
```

Attach policy to `prod-user`:

```bash
aws iam attach-user-policy \
  --user-name prod-user \
  --policy-arn "$PROD_USER_POLICY_ARN"
```

---

# Phase 5: Test Default User Access

At this point:

```text
dev-user can read /app/dev/* String parameters.
prod-user can read /app/prod/* String parameters.
Neither user can decrypt SecureString parameters.
Neither user can read the other environment.
```

---

## 5.1 Test dev-user Access

### Should succeed: dev-user reads dev String parameter

```bash
aws ssm get-parameter \
  --name "/app/dev/db-url" \
  --profile dev-user \
  --region $AWS_REGION
```

Expected: success.

---

### Should fail: dev-user decrypts dev SecureString

```bash
aws ssm get-parameter \
  --name "/app/dev/db-password" \
  --with-decryption \
  --profile dev-user \
  --region $AWS_REGION
```

Expected: failure.

Why?

Because `dev-user` has `ssm:GetParameter`, but does not have `kms:Decrypt` on the dev KMS key.

---

### Should fail: dev-user reads prod String parameter

```bash
aws ssm get-parameter \
  --name "/app/prod/db-url" \
  --profile dev-user \
  --region $AWS_REGION
```

Expected: `AccessDeniedException`.

---

## 5.2 Test prod-user Access

### Should succeed: prod-user reads prod String parameter

```bash
aws ssm get-parameter \
  --name "/app/prod/db-url" \
  --profile prod-user \
  --region $AWS_REGION
```

Expected: success.

---

### Should fail: prod-user decrypts prod SecureString

```bash
aws ssm get-parameter \
  --name "/app/prod/db-password" \
  --with-decryption \
  --profile prod-user \
  --region $AWS_REGION
```

Expected: failure.

Why?

Because `prod-user` has `ssm:GetParameter`, but does not have `kms:Decrypt` on the prod KMS key.

---

### Should fail: prod-user reads dev String parameter

```bash
aws ssm get-parameter \
  --name "/app/dev/db-url" \
  --profile prod-user \
  --region $AWS_REGION
```

Expected: `AccessDeniedException`.

---

# Phase 6: Create Environment Admin Roles

Now create two environment-specific admin roles:

```text
DevParameterAdminRole
ProdParameterAdminRole
```

These roles can decrypt SecureString values only in their own environment.

---

## 6.1 Create DevParameterAdminRole Trust Policy

This role trusts only `dev-user`.

```bash
cat > dev-parameter-admin-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TrustDevUser",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${AWS_ACCOUNT_ID}:user/dev-user"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
```

Create role:

```bash
aws iam create-role \
  --role-name DevParameterAdminRole \
  --assume-role-policy-document file://dev-parameter-admin-trust-policy.json
```

---

## 6.2 Attach Permissions to DevParameterAdminRole

Create policy document:

```bash
cat > dev-parameter-admin-permissions-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadDevParameters",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/app/dev/*"
    },
    {
      "Sid": "DecryptDevSecureStrings",
      "Effect": "Allow",
      "Action": "kms:Decrypt",
      "Resource": "${DEV_KMS_KEY_ARN}"
    }
  ]
}
EOF
```

Attach as inline role policy:

```bash
aws iam put-role-policy \
  --role-name DevParameterAdminRole \
  --policy-name DevParameterAdminPermissions \
  --policy-document file://dev-parameter-admin-permissions-policy.json
```

---

## 6.3 Create ProdParameterAdminRole Trust Policy

This role trusts only `prod-user`.

```bash
cat > prod-parameter-admin-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TrustProdUser",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${AWS_ACCOUNT_ID}:user/prod-user"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
```

Create role:

```bash
aws iam create-role \
  --role-name ProdParameterAdminRole \
  --assume-role-policy-document file://prod-parameter-admin-trust-policy.json
```

---

## 6.4 Attach Permissions to ProdParameterAdminRole

Create policy document:

```bash
cat > prod-parameter-admin-permissions-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadProdParameters",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/app/prod/*"
    },
    {
      "Sid": "DecryptProdSecureStrings",
      "Effect": "Allow",
      "Action": "kms:Decrypt",
      "Resource": "${PROD_KMS_KEY_ARN}"
    }
  ]
}
EOF
```

Attach as inline role policy:

```bash
aws iam put-role-policy \
  --role-name ProdParameterAdminRole \
  --policy-name ProdParameterAdminPermissions \
  --policy-document file://prod-parameter-admin-permissions-policy.json
```

---

# Phase 7: Allow Users to Assume Environment Admin Roles

The role trust policy alone is not enough.

The user also needs permission to call `sts:AssumeRole`.

So you need both:

```text
Role trust policy:
  Who is allowed to assume this role?

User permission policy:
  Is this user allowed to call sts:AssumeRole on this role?
```

---

## 7.1 Allow dev-user to Assume DevParameterAdminRole

Create policy document:

```bash
cat > allow-dev-user-assume-dev-admin-role.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAssumeDevParameterAdminRole",
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/DevParameterAdminRole"
    }
  ]
}
EOF
```

Create policy:

```bash
DEV_ASSUME_POLICY_ARN=$(aws iam create-policy \
  --policy-name AllowDevUserAssumeDevParameterAdminRole \
  --policy-document file://allow-dev-user-assume-dev-admin-role.json \
  --query Policy.Arn \
  --output text)

echo $DEV_ASSUME_POLICY_ARN
```

Attach to `dev-user`:

```bash
aws iam attach-user-policy \
  --user-name dev-user \
  --policy-arn "$DEV_ASSUME_POLICY_ARN"
```

---

## 7.2 Allow prod-user to Assume ProdParameterAdminRole

Create policy document:

```bash
cat > allow-prod-user-assume-prod-admin-role.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAssumeProdParameterAdminRole",
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ProdParameterAdminRole"
    }
  ]
}
EOF
```

Create policy:

```bash
PROD_ASSUME_POLICY_ARN=$(aws iam create-policy \
  --policy-name AllowProdUserAssumeProdParameterAdminRole \
  --policy-document file://allow-prod-user-assume-prod-admin-role.json \
  --query Policy.Arn \
  --output text)

echo $PROD_ASSUME_POLICY_ARN
```

Attach to `prod-user`:

```bash
aws iam attach-user-policy \
  --user-name prod-user \
  --policy-arn "$PROD_ASSUME_POLICY_ARN"
```

---

# Phase 8: Test Dev Environment Admin Elevation

Now `dev-user` should be able to assume `DevParameterAdminRole`.

---

## 8.1 Assume DevParameterAdminRole as dev-user

```bash
aws sts assume-role \
  --role-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:role/DevParameterAdminRole" \
  --role-session-name "dev-admin-session" \
  --profile dev-user \
  --region $AWS_REGION
```

The output contains temporary credentials:

```json
{
  "Credentials": {
    "AccessKeyId": "...",
    "SecretAccessKey": "...",
    "SessionToken": "...",
    "Expiration": "..."
  }
}
```

Export the temporary credentials:

```bash
export AWS_ACCESS_KEY_ID="PASTE_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="PASTE_SECRET_ACCESS_KEY"
export AWS_SESSION_TOKEN="PASTE_SESSION_TOKEN"
```

Verify identity:

```bash
aws sts get-caller-identity --region $AWS_REGION
```

Expected ARN format:

```text
arn:aws:sts::<account-id>:assumed-role/DevParameterAdminRole/dev-admin-session
```

---

## 8.2 Test Dev Admin Access

### Should succeed: decrypt dev SecureString

```bash
aws ssm get-parameter \
  --name "/app/dev/db-password" \
  --with-decryption \
  --region $AWS_REGION
```

Expected: success.

---

### Should fail: decrypt prod SecureString

```bash
aws ssm get-parameter \
  --name "/app/prod/db-password" \
  --with-decryption \
  --region $AWS_REGION
```

Expected: `AccessDeniedException`.

Why?

Because `DevParameterAdminRole` has access only to:

```text
/app/dev/*
```

and can decrypt only using:

```text
alias/ssm-dev-key
```

---

## 8.3 Clear Temporary Credentials

```bash
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN
```

Verify that normal `dev-user` still cannot decrypt SecureString:

```bash
aws ssm get-parameter \
  --name "/app/dev/db-password" \
  --with-decryption \
  --profile dev-user \
  --region $AWS_REGION
```

Expected: failure.

---

# Phase 9: Test Prod Environment Admin Elevation

Now `prod-user` should be able to assume `ProdParameterAdminRole`.

---

## 9.1 Assume ProdParameterAdminRole as prod-user

```bash
aws sts assume-role \
  --role-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ProdParameterAdminRole" \
  --role-session-name "prod-admin-session" \
  --profile prod-user \
  --region $AWS_REGION
```

Export the temporary credentials:

```bash
export AWS_ACCESS_KEY_ID="PASTE_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="PASTE_SECRET_ACCESS_KEY"
export AWS_SESSION_TOKEN="PASTE_SESSION_TOKEN"
```

Verify identity:

```bash
aws sts get-caller-identity --region $AWS_REGION
```

Expected ARN format:

```text
arn:aws:sts::<account-id>:assumed-role/ProdParameterAdminRole/prod-admin-session
```

---

## 9.2 Test Prod Admin Access

### Should succeed: decrypt prod SecureString

```bash
aws ssm get-parameter \
  --name "/app/prod/db-password" \
  --with-decryption \
  --region $AWS_REGION
```

Expected: success.

---

### Should fail: decrypt dev SecureString

```bash
aws ssm get-parameter \
  --name "/app/dev/db-password" \
  --with-decryption \
  --region $AWS_REGION
```

Expected: `AccessDeniedException`.

---

## 9.3 Clear Temporary Credentials

```bash
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN
```

Verify that normal `prod-user` still cannot decrypt SecureString:

```bash
aws ssm get-parameter \
  --name "/app/prod/db-password" \
  --with-decryption \
  --profile prod-user \
  --region $AWS_REGION
```

Expected: failure.

---

# Phase 10: Create Super Admin Role

Now create a platform-level role that can read and decrypt everything.

This role should not be assumable by `dev-user` or `prod-user`.

Only `platform-admin-user` should be allowed to assume it.

---

## 10.1 Create ParameterStoreSuperAdminRole Trust Policy

```bash
cat > parameter-store-super-admin-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TrustPlatformAdminUser",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${AWS_ACCOUNT_ID}:user/platform-admin-user"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
```

Create role:

```bash
aws iam create-role \
  --role-name ParameterStoreSuperAdminRole \
  --assume-role-policy-document file://parameter-store-super-admin-trust-policy.json
```

---

## 10.2 Attach Permissions to ParameterStoreSuperAdminRole

Create policy document:

```bash
cat > parameter-store-super-admin-permissions-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadAllAppParameters",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/app/*"
    },
    {
      "Sid": "DecryptDevAndProdSecureStrings",
      "Effect": "Allow",
      "Action": "kms:Decrypt",
      "Resource": [
        "${DEV_KMS_KEY_ARN}",
        "${PROD_KMS_KEY_ARN}"
      ]
    }
  ]
}
EOF
```

Attach as inline role policy:

```bash
aws iam put-role-policy \
  --role-name ParameterStoreSuperAdminRole \
  --policy-name ParameterStoreSuperAdminPermissions \
  --policy-document file://parameter-store-super-admin-permissions-policy.json
```

---

# Phase 11: Allow platform-admin-user to Assume Super Admin Role

Create policy document:

```bash
cat > allow-platform-admin-assume-super-admin-role.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAssumeParameterStoreSuperAdminRole",
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ParameterStoreSuperAdminRole"
    }
  ]
}
EOF
```

Create policy:

```bash
SUPER_ADMIN_ASSUME_POLICY_ARN=$(aws iam create-policy \
  --policy-name AllowPlatformAdminAssumeParameterStoreSuperAdminRole \
  --policy-document file://allow-platform-admin-assume-super-admin-role.json \
  --query Policy.Arn \
  --output text)

echo $SUPER_ADMIN_ASSUME_POLICY_ARN
```

Attach to `platform-admin-user`:

```bash
aws iam attach-user-policy \
  --user-name platform-admin-user \
  --policy-arn "$SUPER_ADMIN_ASSUME_POLICY_ARN"
```

---

# Phase 12: Test Super Admin Access

---

## 12.1 Assume Super Admin Role

```bash
aws sts assume-role \
  --role-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ParameterStoreSuperAdminRole" \
  --role-session-name "platform-super-admin-session" \
  --profile platform-admin-user \
  --region $AWS_REGION
```

Export the temporary credentials:

```bash
export AWS_ACCESS_KEY_ID="PASTE_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="PASTE_SECRET_ACCESS_KEY"
export AWS_SESSION_TOKEN="PASTE_SESSION_TOKEN"
```

Verify identity:

```bash
aws sts get-caller-identity --region $AWS_REGION
```

Expected ARN format:

```text
arn:aws:sts::<account-id>:assumed-role/ParameterStoreSuperAdminRole/platform-super-admin-session
```

---

## 12.2 Read and Decrypt All Parameters

```bash
aws ssm get-parameters-by-path \
  --path "/app" \
  --recursive \
  --with-decryption \
  --region $AWS_REGION
```

Expected: success.

You should see all parameters:

```text
/app/dev/db-url
/app/dev/api-url
/app/dev/db-password
/app/dev/api-key
/app/prod/db-url
/app/prod/api-url
/app/prod/db-password
/app/prod/api-key
```

---

## 12.3 Clear Temporary Credentials

```bash
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN
```

---

# Phase 13: Negative Tests

These tests prove that the role boundaries are working.

---

## 13.1 dev-user Should Not Assume Prod Role

```bash
aws sts assume-role \
  --role-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ProdParameterAdminRole" \
  --role-session-name "dev-trying-prod-admin" \
  --profile dev-user \
  --region $AWS_REGION
```

Expected: failure.

Reason:

```text
dev-user does not have permission to assume ProdParameterAdminRole.
ProdParameterAdminRole also does not trust dev-user.
```

---

## 13.2 prod-user Should Not Assume Dev Role

```bash
aws sts assume-role \
  --role-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:role/DevParameterAdminRole" \
  --role-session-name "prod-trying-dev-admin" \
  --profile prod-user \
  --region $AWS_REGION
```

Expected: failure.

---

## 13.3 dev-user Should Not Assume Super Admin Role

```bash
aws sts assume-role \
  --role-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ParameterStoreSuperAdminRole" \
  --role-session-name "dev-trying-super-admin" \
  --profile dev-user \
  --region $AWS_REGION
```

Expected: failure.

---

## 13.4 prod-user Should Not Assume Super Admin Role

```bash
aws sts assume-role \
  --role-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ParameterStoreSuperAdminRole" \
  --role-session-name "prod-trying-super-admin" \
  --profile prod-user \
  --region $AWS_REGION
```

Expected: failure.

---

# Phase 14: Optional Break/Fix Tests

These tests help you understand exactly which permissions are required.

---

## Break/Fix Test 1: Remove kms:Decrypt from DevParameterAdminRole

If you remove this permission from `DevParameterAdminRole`:

```json
{
  "Effect": "Allow",
  "Action": "kms:Decrypt",
  "Resource": "DEV_KMS_KEY_ARN"
}
```

Then `DevParameterAdminRole` can still read normal dev String parameters, but cannot decrypt dev SecureString values.

Expected failure:

```bash
aws ssm get-parameter \
  --name "/app/dev/db-password" \
  --with-decryption \
  --region $AWS_REGION
```

Lesson:

```text
SSM read access is not enough for SecureString decryption.
You also need KMS decrypt access.
```

---

## Break/Fix Test 2: Give Dev Role Prod KMS Decrypt But Not Prod SSM Access

If `DevParameterAdminRole` had `kms:Decrypt` on the prod KMS key but no SSM access to `/app/prod/*`, it still could not read prod parameters.

Lesson:

```text
KMS permission alone is not enough.
You also need SSM permission to retrieve the parameter.
```

---

## Break/Fix Test 3: Give Dev Role Prod SSM Access But Not Prod KMS Decrypt

If `DevParameterAdminRole` had SSM access to `/app/prod/*`, but did not have `kms:Decrypt` on the prod KMS key, it could read prod String parameters but not decrypt prod SecureString values.

Lesson:

```text
For SecureString, both SSM and KMS permissions are required.
```

---

# Phase 15: Cleanup

Clean up all resources to avoid leaving IAM users, access keys, roles, policies, parameters, and KMS keys in your account.

---

## 15.1 Delete Parameters

```bash
aws ssm delete-parameter --name "/app/dev/db-url" --region $AWS_REGION
aws ssm delete-parameter --name "/app/dev/api-url" --region $AWS_REGION
aws ssm delete-parameter --name "/app/dev/db-password" --region $AWS_REGION
aws ssm delete-parameter --name "/app/dev/api-key" --region $AWS_REGION

aws ssm delete-parameter --name "/app/prod/db-url" --region $AWS_REGION
aws ssm delete-parameter --name "/app/prod/api-url" --region $AWS_REGION
aws ssm delete-parameter --name "/app/prod/db-password" --region $AWS_REGION
aws ssm delete-parameter --name "/app/prod/api-key" --region $AWS_REGION
```

---

## 15.2 Detach User Policies

```bash
aws iam detach-user-policy \
  --user-name dev-user \
  --policy-arn "$DEV_USER_POLICY_ARN"

aws iam detach-user-policy \
  --user-name dev-user \
  --policy-arn "$DEV_ASSUME_POLICY_ARN"

aws iam detach-user-policy \
  --user-name prod-user \
  --policy-arn "$PROD_USER_POLICY_ARN"

aws iam detach-user-policy \
  --user-name prod-user \
  --policy-arn "$PROD_ASSUME_POLICY_ARN"

aws iam detach-user-policy \
  --user-name platform-admin-user \
  --policy-arn "$SUPER_ADMIN_ASSUME_POLICY_ARN"
```

---

## 15.3 Delete Customer Managed Policies

```bash
aws iam delete-policy --policy-arn "$DEV_USER_POLICY_ARN"
aws iam delete-policy --policy-arn "$DEV_ASSUME_POLICY_ARN"
aws iam delete-policy --policy-arn "$PROD_USER_POLICY_ARN"
aws iam delete-policy --policy-arn "$PROD_ASSUME_POLICY_ARN"
aws iam delete-policy --policy-arn "$SUPER_ADMIN_ASSUME_POLICY_ARN"
```

---

## 15.4 Delete Role Inline Policies

```bash
aws iam delete-role-policy \
  --role-name DevParameterAdminRole \
  --policy-name DevParameterAdminPermissions

aws iam delete-role-policy \
  --role-name ProdParameterAdminRole \
  --policy-name ProdParameterAdminPermissions

aws iam delete-role-policy \
  --role-name ParameterStoreSuperAdminRole \
  --policy-name ParameterStoreSuperAdminPermissions
```

---

## 15.5 Delete Roles

```bash
aws iam delete-role --role-name DevParameterAdminRole
aws iam delete-role --role-name ProdParameterAdminRole
aws iam delete-role --role-name ParameterStoreSuperAdminRole
```

---

## 15.6 Delete User Access Keys

List access keys:

```bash
aws iam list-access-keys --user-name dev-user
aws iam list-access-keys --user-name prod-user
aws iam list-access-keys --user-name platform-admin-user
```

Delete each access key:

```bash
aws iam delete-access-key \
  --user-name dev-user \
  --access-key-id ACCESS_KEY_ID

aws iam delete-access-key \
  --user-name prod-user \
  --access-key-id ACCESS_KEY_ID

aws iam delete-access-key \
  --user-name platform-admin-user \
  --access-key-id ACCESS_KEY_ID
```

Replace `ACCESS_KEY_ID` with the actual access key IDs from the list command.

---

## 15.7 Delete Users

```bash
aws iam delete-user --user-name dev-user
aws iam delete-user --user-name prod-user
aws iam delete-user --user-name platform-admin-user
```

---

## 15.8 Schedule KMS Key Deletion

KMS keys cannot be deleted immediately. You must schedule deletion.

```bash
aws kms schedule-key-deletion \
  --key-id "$DEV_KMS_KEY_ID" \
  --pending-window-in-days 7 \
  --region $AWS_REGION

aws kms schedule-key-deletion \
  --key-id "$PROD_KMS_KEY_ID" \
  --pending-window-in-days 7 \
  --region $AWS_REGION
```

---

# Final Summary

This lab demonstrates a realistic AWS security pattern:

```text
Normal users:
  Can read non-sensitive configuration only in their own environment.

Environment admin roles:
  Can decrypt SecureString values only in their own environment.

Super admin role:
  Can read and decrypt everything, but only a platform admin user can assume it.
```

The most important lesson is that SecureString access requires both:

```text
ssm:GetParameter
kms:Decrypt
```

This lab also teaches why AWS roles are powerful:

```text
Permanent user permissions stay limited.
Temporary assumed role permissions provide controlled elevation.
```

That is a core AWS security design pattern used in real projects.

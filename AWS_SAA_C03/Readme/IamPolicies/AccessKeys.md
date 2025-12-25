# AWS CLI Login Using Access Keys (Access Key ID + Secret Access Key)

This guide explains how to authenticate the AWS CLI using **access keys** (Access Key ID + Secret Access Key), how profiles work, and the most common mistakes.

> Access keys are long-lived credentials. Prefer **SSO** or **IAM Roles** where possible.

---

## What are Access Keys?

An **access key** is a pair of credentials for an IAM user (or sometimes temporary credentials from STS):

- **Access Key ID**: public identifier (looks like `AKIA...`)
- **Secret Access Key**: private secret (shown only once when created)

These are used by the AWS CLI to sign requests using **SigV4**.

---

## Where AWS CLI Stores Them

By default, credentials live in:

- `~/.aws/credentials` (Access Key + Secret, and optionally session token)
- `~/.aws/config` (region, output format, and profile settings)

On Windows:
- `%UserProfile%\.aws\credentials`
- `%UserProfile%\.aws\config`

---

## Quick Setup: `aws configure`

Create a default profile:

```bash
aws configure
```
Create a named profile:
```Named profile
aws configure --profile myprofile
```

## Verify Which Identity You’re Using
```
aws sts get-caller-identity --profile myprofile
```

## Listing All Configured Profiles
```
aws configure list-profiles
```

> If the keys are compromised we can deactivate and then delete them. We can also activate it back from the aws console.
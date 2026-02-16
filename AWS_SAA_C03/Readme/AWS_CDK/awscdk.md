# CDK Labs

- [1. Create a PrivateEC2 and connect to it using SSM, NAT and IGW](../../../private-ec2-ssm-igw-nat-cdk/private_ec2_ssm_igw_nat_cdk/private_ec2_ssm_igw_nat_cdk_stack.py)

# AWS CDK Constructs Deep Dive

## Overview

This document explains the core AWS CDK concepts:

-   Application (App)
-   Stack
-   Resource
-   Construct Tree
-   L1, L2, and L3 Constructs
-   Creating Your Own L3 Constructs
-   Architectural Best Practices

------------------------------------------------------------------------

# 1. CDK Application (App)

The CDK Application is the root of everything.

It: - Instantiates stacks - Builds the construct tree - Synthesizes
CloudFormation templates

Example (Python):

``` python
app = cdk.App()
MyStack(app, "MyStack")
app.synth()
```

Running:

    cdk synth

Generates CloudFormation from your construct tree.

------------------------------------------------------------------------

# 2. Stack

A Stack is a unit of deployment.

Each stack: - Synthesizes to ONE CloudFormation template - Deploys as
ONE CloudFormation stack - Can be deployed independently

Example:

``` python
class MyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
```

You can structure real systems like:

-   NetworkingStack (VPC, subnets, NAT)
-   ComputeStack (ECS, ALB)
-   DatabaseStack (RDS)
-   MonitoringStack (CloudWatch)

------------------------------------------------------------------------

# 3. Resources

Resources represent actual AWS services.

Examples:

-   VPC
-   S3 Bucket
-   ECS Cluster
-   IAM Role
-   RDS Database

Example:

``` python
vpc = ec2.Vpc(self, "MyVpc")
```

Nothing is created until:

    cdk deploy

------------------------------------------------------------------------

# 4. Constructs

Everything in CDK is a Construct.

Construct signature:

``` python
SomeConstruct(scope, id, props)
```

Constructs form a tree:

    App
     └── Stack
          ├── Vpc
          ├── Cluster
          └── Service

------------------------------------------------------------------------

# 5. L1 Constructs (Low-Level)

L1 constructs map directly to CloudFormation.

Example:

``` python
bucket = s3.CfnBucket(self, "MyBucket")
```

Characteristics: - 1:1 CloudFormation mapping - No defaults - No helper
methods

Use when you need low-level control.

------------------------------------------------------------------------

# 6. L2 Constructs (Service Abstractions)

L2 constructs represent AWS services with intelligence.

Example:

``` python
bucket = s3.Bucket(self, "MyBucket",
    versioned=True,
    encryption=s3.BucketEncryption.S3_MANAGED
)
```

L2 adds: - Defaults - Helper methods - Security best practices

Example helper:

``` python
bucket.grant_read(role)
```

------------------------------------------------------------------------

# 7. L3 Constructs (Patterns)

L3 constructs represent architectural patterns composed of multiple
resources.

They are NOT official CDK types --- they are conceptual patterns.

Example:

``` python
from aws_cdk.aws_ecs_patterns import ApplicationLoadBalancedFargateService

service = ApplicationLoadBalancedFargateService(
    self, "MyService",
    cluster=cluster,
    task_image_options={
        "image": ecs.ContainerImage.from_registry("nginx")
    }
)
```

Behind the scenes this creates:

-   ECS Cluster
-   Task Definition
-   Service
-   Application Load Balancer
-   Listener
-   Target Group
-   IAM Roles
-   Security Groups
-   Log Groups

L3 = Multiple L2 resources combined into a reusable architecture.

------------------------------------------------------------------------

# 8. More L3 Examples

## Lambda + API Gateway

``` python
api = apigateway.LambdaRestApi(
    self, "MyApi",
    handler=my_lambda
)
```

Creates: - API Gateway - Lambda - Permissions - Deployment stage

------------------------------------------------------------------------

## CloudFront + S3 Pattern

``` python
from aws_solutions_constructs.aws_cloudfront_s3 import CloudFrontToS3
```

Creates: - Private S3 bucket - CloudFront distribution - Origin access
control - Bucket policy - Logging

------------------------------------------------------------------------

# 9. Creating Your Own L3 Construct

If you create a reusable construct that composes multiple services, it
is conceptually an L3 pattern.

Example:

``` python
class SecureWebAppPattern(Construct):

    def __init__(self, scope: Construct, id: str, *, vpc: ec2.Vpc):
        super().__init__(scope, id)

        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        service = ecs.FargateService(
            self, "Service",
            cluster=cluster,
            task_definition=ecs.FargateTaskDefinition(
                self, "TaskDef",
                cpu=256,
                memory_limit_mib=512
            )
        )

        alb = elbv2.ApplicationLoadBalancer(
            self, "ALB",
            vpc=vpc,
            internet_facing=False
        )
```

This pattern: - Enforces architecture - Encodes best practices - Hides
complexity - Standardizes infrastructure

That is a real L3 construct.

------------------------------------------------------------------------

# 10. When To Use L3

Use L3 for:

-   Rapid prototyping
-   Internal tooling
-   Repeated architecture
-   Standardization

Avoid L3 when:

-   You need fine-grained control
-   Enterprise security requirements are strict
-   You need full IAM customization
-   You need custom scaling logic

Always inspect:

    cdk synth

And review the generated CloudFormation template.

------------------------------------------------------------------------

# 11. Senior-Level Perspective

L3 constructs are how platform engineering teams standardize
infrastructure.

Enterprise teams often build internal construct libraries like:

-   company-networking
-   company-ecs-patterns
-   company-security-standards

This enables:

-   Consistency
-   Security enforcement
-   Reduced cognitive load
-   Faster onboarding

------------------------------------------------------------------------

# Final Summary

-   App → Root container
-   Stack → Deployment unit
-   Resource → AWS service object
-   L1 → CloudFormation mapping
-   L2 → Smart service abstraction
-   L3 → Architectural pattern

Architects understand what constructs generate.

Always synthesize. Always inspect. Always understand IAM and networking
defaults.

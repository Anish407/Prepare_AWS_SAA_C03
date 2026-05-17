# AWS CloudFormation - SAA-C03 Exam Notes and Practical Examples

> Goal: understand CloudFormation well enough for the AWS Solutions Architect Associate exam and for real project work where infrastructure must be repeatable, automated, and consistent across environments.

---

## 1. What is AWS CloudFormation?

AWS CloudFormation is AWS's native Infrastructure as Code service.

Instead of manually creating infrastructure in the AWS Console, you describe your desired infrastructure in a template file. CloudFormation reads that template and creates, updates, or deletes the resources as a managed unit called a stack.

Common resources you can define include:

- VPCs
- Subnets
- Route tables
- Security groups
- EC2 instances
- Auto Scaling groups
- Load balancers
- S3 buckets
- IAM roles and policies
- Lambda functions
- DynamoDB tables
- RDS databases
- EventBridge rules
- CloudWatch alarms

The big idea is this:

```text
Template file -> CloudFormation stack -> AWS resources
```

CloudFormation is not just a deployment tool. It also becomes the source of truth for the infrastructure it manages.

---

## 2. Why CloudFormation matters

CloudFormation is important because it gives you repeatability.

Without IaC, you might create infrastructure manually in the console. That works for learning, but it becomes dangerous in real projects because people forget steps, environments drift, and no one knows exactly what was created.

With CloudFormation, the architecture is declared in code.

This helps with:

- repeatable deployments
- consistent environments
- version control
- rollback
- cost tracking through tags
- easier disaster recovery
- multi-account and multi-region deployments
- safer infrastructure updates

Example scenario:

You need the same VPC, ECS cluster, ALB, IAM roles, and CloudWatch alarms in dev, test, preprod, and prod.

Bad approach:

```text
Create everything manually four times in the AWS Console.
```

Better approach:

```text
Use one CloudFormation template.
Pass different parameters for each environment.
Deploy one stack per environment.
```

---

## 3. CloudFormation core concepts

### Template

A template is a JSON or YAML file that describes the resources you want CloudFormation to manage.

YAML is usually preferred by humans because it is easier to read.

JSON works too, but for larger templates it becomes noisy and harder to maintain.

### Stack

A stack is the deployed instance of a CloudFormation template.

For example:

```text
network-dev-stack
network-prod-stack
app-dev-stack
app-prod-stack
```

Each stack contains resources created from the template.

Important exam point:

CloudFormation stacks are regional resources.

That means if you deploy a stack in `eu-north-1`, it lives in `eu-north-1`. If you need the same architecture in `us-east-1`, you deploy another stack there.

### StackSet

A StackSet lets you deploy the same CloudFormation template across multiple AWS accounts and multiple AWS Regions.

This is important for organization-wide infrastructure.

Examples:

- deploy IAM roles into all accounts
- deploy CloudTrail across all accounts
- deploy AWS Config rules across all accounts
- deploy backup policies across regions
- bootstrap baseline networking/security resources

Think of it like this:

```text
CloudFormation Stack = one region/account deployment
CloudFormation StackSet = many account/region deployments from one template
```

---

## 4. Is CloudFormation free?

CloudFormation itself is free to use for AWS resources.

You pay for the resources CloudFormation creates.

Example:

If a template creates:

- 2 EC2 instances
- 1 RDS database
- 1 NAT Gateway
- 1 Application Load Balancer

CloudFormation does not add an extra charge for managing those resources. But you still pay for EC2, RDS, NAT Gateway, and ALB.

Brutal real-world warning:

CloudFormation being free does not mean your lab is free. A badly written template can create expensive resources very quickly, especially NAT Gateways, large RDS instances, OpenSearch domains, load balancers, and multi-AZ databases.

---

## 5. CloudFormation template formats

CloudFormation supports two main template formats:

- YAML
- JSON

YAML example:

```yaml
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
```

JSON example:

```json
{
  "Resources": {
    "MyBucket": {
      "Type": "AWS::S3::Bucket"
    }
  }
}
```

Both do the same thing.

For learning and real projects, YAML is usually easier.

---

## 6. Main sections of a CloudFormation template

A CloudFormation template is divided into sections.

Only the `Resources` section is required.

Common sections:

| Section | Required? | Purpose |
|---|---:|---|
| `AWSTemplateFormatVersion` | No | Template format version. Usually `2010-09-09`. |
| `Description` | No | Human-readable explanation of what the template does. |
| `Metadata` | No | Extra information about the template. |
| `Parameters` | No | Input values passed when creating or updating the stack. |
| `Mappings` | No | Static lookup tables inside the template. |
| `Conditions` | No | Logic to decide whether resources/properties should be created. |
| `Transform` | No | Applies macros or transforms such as AWS SAM or AWS::Include. |
| `Resources` | Yes | AWS resources to create, update, or delete. |
| `Outputs` | No | Values returned after stack creation, often used by humans or other stacks. |
| `Rules` | No | Validates parameter combinations before stack creation/update. |

---

## 7. Resources section

The `Resources` section is the heart of the template.

This is where you define the AWS resources.

Example: create an S3 bucket.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Simple S3 bucket example

Resources:
  DemoBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: my-demo-cloudformation-bucket-12345
      Tags:
        - Key: Environment
          Value: Dev
        - Key: Project
          Value: CloudFormationLearning
```

Explanation:

```text
DemoBucket = logical ID inside the template
AWS::S3::Bucket = CloudFormation resource type
Properties = configuration for that resource
```

The logical ID is not always the final physical resource name.

For example, if you do not specify `BucketName`, CloudFormation creates a unique physical name.

---

## 8. Parameters section

Parameters let you reuse the same template with different values.

This is very important for deploying the same architecture to different environments.

Example:

```yaml
Parameters:
  EnvironmentName:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - test
      - prod
    Description: Environment name

  InstanceType:
    Type: String
    Default: t3.micro
    AllowedValues:
      - t3.micro
      - t3.small
      - t3.medium
    Description: EC2 instance type
```

Then reference the parameter using `!Ref`:

```yaml
Resources:
  DemoInstance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !Ref InstanceType
```

Real-world use:

```text
dev  -> t3.micro
prod -> t3.medium or larger
```

Do not hardcode values that change between environments.

Good parameter candidates:

- environment name
- instance type
- VPC ID
- subnet IDs
- allowed CIDR ranges
- database instance class
- domain name
- certificate ARN

Bad parameter candidates:

- secrets
- passwords
- API keys

For secrets, use AWS Secrets Manager or SSM Parameter Store dynamic references instead.

---

## 9. Mappings section

Mappings are static lookup tables.

They are useful when a value depends on another value, such as the AWS Region.

Example: choose an AMI based on the region.

```yaml
Mappings:
  RegionMap:
    us-east-1:
      AmiId: ami-0abcdef1234567890
    us-west-2:
      AmiId: ami-0123456789abcdef0
    eu-north-1:
      AmiId: ami-0fedcba9876543210
```

Use it with `!FindInMap`:

```yaml
ImageId: !FindInMap [RegionMap, !Ref AWS::Region, AmiId]
```

This means:

```text
Look inside RegionMap.
Find the key matching the current AWS Region.
Return the AmiId value.
```

Important:

Mappings are static. If AMI IDs change, you must update the template.

In real projects, AWS Systems Manager Parameter Store public parameters are often better for latest AMI lookup.

Example:

```yaml
Parameters:
  LatestAmazonLinuxAmi:
    Type: AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>
    Default: /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64
```

---

## 10. Conditions section

Conditions let you create resources only when a certain condition is true.

Example:

```yaml
Parameters:
  EnvironmentName:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - prod

Conditions:
  IsProd: !Equals [!Ref EnvironmentName, prod]
```

Use condition on a resource:

```yaml
Resources:
  ProdOnlyBucket:
    Type: AWS::S3::Bucket
    Condition: IsProd
    Properties:
      Tags:
        - Key: Environment
          Value: !Ref EnvironmentName
```

This bucket is created only when `EnvironmentName` is `prod`.

Real-world use cases:

- create Multi-AZ database only in prod
- enable deletion protection only in prod
- create alarms only in test/prod
- create NAT Gateway only when private internet access is required
- create expensive resources only when needed

---

## 11. Outputs section

Outputs return useful values from a stack.

Example:

```yaml
Outputs:
  BucketName:
    Description: Name of the created S3 bucket
    Value: !Ref DemoBucket

  BucketArn:
    Description: ARN of the created S3 bucket
    Value: !GetAtt DemoBucket.Arn
```

Common outputs:

- VPC ID
- subnet IDs
- ALB DNS name
- S3 bucket name
- Lambda function ARN
- API Gateway URL
- RDS endpoint

Outputs are also useful for cross-stack references.

Example:

A network stack creates a VPC and exports its VPC ID.

```yaml
Outputs:
  VpcId:
    Description: VPC ID
    Value: !Ref MyVpc
    Export:
      Name: MyApp-VpcId
```

Another stack imports it:

```yaml
VpcId: !ImportValue MyApp-VpcId
```

This lets you separate infrastructure into multiple stacks.

Example:

```text
network-stack -> VPC, subnets, route tables
security-stack -> IAM roles, security groups
app-stack -> ECS services, ALB, target groups
monitoring-stack -> alarms, dashboards
```

---

## 12. Transform section

The `Transform` section tells CloudFormation to process the template using a macro or transform.

Examples:

```yaml
Transform: AWS::Serverless-2016-10-31
```

This is used by AWS SAM to expand simplified serverless syntax into standard CloudFormation resources.

Another example:

```yaml
Transform: AWS::Include
```

This can include template snippets stored separately, such as in S3.

Important correction:

Do not think of `Transform` as simply phased out. It is still used, especially with SAM and macros. For the SAA exam, you usually only need to recognize that transforms/macros allow CloudFormation to process and expand templates before deployment.

---

## 13. Intrinsic functions

Intrinsic functions are built-in CloudFormation functions used inside templates.

Common ones for the exam:

| Function | Short form | Purpose |
|---|---|---|
| `Ref` | `!Ref` | References a parameter or resource. |
| `Fn::GetAtt` | `!GetAtt` | Gets an attribute of a resource. |
| `Fn::FindInMap` | `!FindInMap` | Looks up a value in a mapping. |
| `Fn::Sub` | `!Sub` | Substitutes variables into a string. |
| `Fn::Join` | `!Join` | Joins values together. |
| `Fn::If` | `!If` | Conditional value selection. |
| `Fn::ImportValue` | `!ImportValue` | Imports an exported output from another stack. |
| `Fn::Select` | `!Select` | Selects one item from a list. |
| `Fn::Split` | `!Split` | Splits a string into a list. |

Example using `!Sub`:

```yaml
BucketName: !Sub '${EnvironmentName}-${AWS::AccountId}-${AWS::Region}-logs'
```

This produces something like:

```text
dev-123456789012-eu-north-1-logs
```

Pseudo parameters used above:

- `AWS::AccountId`
- `AWS::Region`
- `AWS::StackName`
- `AWS::Partition`
- `AWS::NoValue`

---

## 14. Full example: EC2 instance with parameters, mappings, tags, and outputs

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: EC2 instance example using parameters, mappings, tags, and outputs

Parameters:
  EnvironmentName:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - test
      - prod
    Description: Environment name

  InstanceType:
    Type: String
    Default: t3.micro
    AllowedValues:
      - t3.micro
      - t3.small
      - t3.medium
    Description: EC2 instance type

Mappings:
  RegionMap:
    us-east-1:
      AmiId: ami-0abcdef1234567890
    us-west-2:
      AmiId: ami-0123456789abcdef0
    eu-north-1:
      AmiId: ami-0fedcba9876543210

Conditions:
  IsProd: !Equals [!Ref EnvironmentName, prod]

Resources:
  DemoSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Allow SSH for demo only
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 10.0.0.0/8
      Tags:
        - Key: Name
          Value: !Sub '${EnvironmentName}-demo-sg'
        - Key: Environment
          Value: !Ref EnvironmentName

  DemoInstance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: !FindInMap [RegionMap, !Ref AWS::Region, AmiId]
      InstanceType: !Ref InstanceType
      SecurityGroupIds:
        - !Ref DemoSecurityGroup
      Tags:
        - Key: Name
          Value: !Sub '${EnvironmentName}-demo-instance'
        - Key: Environment
          Value: !Ref EnvironmentName
        - Key: CostCenter
          Value: Learning

  ProdOnlyAlarm:
    Type: AWS::CloudWatch::Alarm
    Condition: IsProd
    Properties:
      AlarmDescription: CPU alarm for production instance
      Namespace: AWS/EC2
      MetricName: CPUUtilization
      Dimensions:
        - Name: InstanceId
          Value: !Ref DemoInstance
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: 80
      ComparisonOperator: GreaterThanThreshold

Outputs:
  InstanceId:
    Description: EC2 instance ID
    Value: !Ref DemoInstance

  SecurityGroupId:
    Description: Security group ID
    Value: !Ref DemoSecurityGroup
```

Important note:

The AMI IDs above are placeholders. In a real deployment, use valid AMI IDs for the selected regions or use SSM public parameters.

---

## 15. Tags in CloudFormation

Tags are key-value pairs applied to resources.

Example:

```yaml
Tags:
  - Key: Environment
    Value: Prod
  - Key: Owner
    Value: PlatformTeam
  - Key: CostCenter
    Value: Finance
```

Why tags matter:

- cost allocation
- ownership
- automation
- compliance
- cleanup
- identifying environment

CloudFormation also adds stack-related tags to many supported resources, such as stack name and stack ID.

This is useful because you can identify which stack created a resource.

For real projects, define a tagging standard early.

Example standard:

```text
Environment = dev/test/prod
Application = sales-platform
Owner = platform-team
CostCenter = engineering
ManagedBy = cloudformation
```

---

## 16. Change Sets

A change set lets you preview what CloudFormation will do before applying an update.

This is extremely important in production.

Example:

You change an RDS property in the template.

CloudFormation might say:

```text
Modify DBInstance
Replacement: True
```

That means CloudFormation may delete and recreate the database.

That is a huge red flag.

Use change sets to avoid surprises.

Basic flow:

```text
Update template -> Create change set -> Review changes -> Execute change set
```

Exam tip:

If the question says you need to preview infrastructure changes before applying them, think CloudFormation Change Sets.

---

## 17. Drift Detection

Drift means the real AWS resource no longer matches the CloudFormation template.

Example:

CloudFormation created a security group with port 443 open.

Someone manually edits it in the console and opens port 22 from the internet.

Now the resource has drifted.

Drift detection helps identify this.

Important limitations:

- Not every resource type supports drift detection.
- Some properties may not be fully detected.
- Drift detection tells you there is a mismatch; you still need to decide how to fix it.

Exam tip:

If the question says resources were manually changed outside CloudFormation and you need to detect the difference, think Drift Detection.

---

## 18. Custom Resources

Not every AWS feature or third-party operation is always directly supported by CloudFormation.

Custom resources allow you to run custom logic during stack operations.

Usually this is implemented with Lambda.

Flow:

```text
CloudFormation stack create/update/delete
        -> invokes custom resource
        -> Lambda runs custom logic
        -> Lambda sends success/failure response back to CloudFormation
```

Use cases:

- create something not supported natively
- call an external API
- perform custom setup during deployment
- copy files between S3 buckets
- run account bootstrap logic
- configure resources after creation

Be careful:

Custom resources can make stacks harder to debug. If the Lambda fails or does not return a response correctly, the stack can hang or roll back.

For the exam:

If CloudFormation does not support a required resource or action natively, custom resource is the likely answer.

---

## 19. Stack policies

A stack policy protects critical resources from accidental updates.

Example:

You may want to prevent accidental replacement of a production RDS database.

A stack policy can deny updates to that logical resource unless explicitly overridden.

Use case:

```text
Protect important stateful resources from accidental modification during stack update.
```

This is not the same as IAM.

IAM controls who can call CloudFormation APIs.

Stack policies control what updates are allowed inside a stack.

---

## 20. DeletionPolicy and UpdateReplacePolicy

These are very important for real projects.

By default, when you delete a stack, CloudFormation deletes the resources in the stack.

For stateful resources, this can be dangerous.

Example:

```yaml
Resources:
  MyDatabase:
    Type: AWS::RDS::DBInstance
    DeletionPolicy: Snapshot
    UpdateReplacePolicy: Snapshot
    Properties:
      DBInstanceClass: db.t3.micro
      Engine: postgres
      AllocatedStorage: 20
```

Common options:

| Policy | Meaning |
|---|---|
| `Delete` | Delete the resource. Default for many resources. |
| `Retain` | Keep the resource even if the stack is deleted. |
| `Snapshot` | Take a snapshot before deletion or replacement, where supported. |

Use these for:

- RDS databases
- EBS volumes
- ElastiCache clusters
- Redshift clusters
- production S3 buckets

Brutal warning:

Many developers learn this only after deleting a lab or test stack and accidentally deleting something they cared about.

---

## 21. Rollback behavior

If stack creation fails, CloudFormation usually rolls back and deletes resources it already created.

Example:

```text
Create VPC -> success
Create subnet -> success
Create EC2 -> fails
Rollback starts
Delete subnet
Delete VPC
```

This is good because it avoids half-created infrastructure.

But sometimes rollback makes debugging harder because the failed resources disappear.

For learning, you can disable rollback during stack creation to inspect failed resources.

For production, be careful with disabling rollback.

---

## 22. Nested stacks

Nested stacks let you split large templates into smaller templates.

Example:

```text
root-stack
  -> network-stack
  -> security-stack
  -> database-stack
  -> application-stack
```

Use nested stacks when templates become too large or when you want reusable infrastructure building blocks.

However, do not overuse them too early. They add complexity.

For small labs, one template is fine.

For production-scale systems, separate stacks or nested stacks are often cleaner.

---

## 23. CloudFormation vs CDK vs Terraform

### CloudFormation

CloudFormation is the native AWS IaC engine.

You write YAML or JSON templates directly.

### AWS CDK

AWS CDK lets you define infrastructure using programming languages like TypeScript, Python, Java, C#, or Go.

CDK synthesizes CloudFormation templates.

So CDK does not replace CloudFormation in AWS. It generates CloudFormation.

```text
CDK code -> synthesized CloudFormation template -> CloudFormation stack -> AWS resources
```

### Terraform

Terraform is a multi-cloud IaC tool.

It can manage AWS, Azure, GCP, GitHub, Datadog, Kubernetes, and many other providers.

For AWS SAA exam questions, if the answer choices include CloudFormation, CloudFormation is usually the expected AWS-native IaC answer.

---

## 24. CloudFormation deployment commands

Validate a template:

```bash
aws cloudformation validate-template \
  --template-body file://template.yaml
```

Create a stack:

```bash
aws cloudformation create-stack \
  --stack-name demo-stack \
  --template-body file://template.yaml \
  --parameters ParameterKey=EnvironmentName,ParameterValue=dev \
  --capabilities CAPABILITY_NAMED_IAM
```

Update a stack:

```bash
aws cloudformation update-stack \
  --stack-name demo-stack \
  --template-body file://template.yaml \
  --parameters ParameterKey=EnvironmentName,ParameterValue=dev \
  --capabilities CAPABILITY_NAMED_IAM
```

Delete a stack:

```bash
aws cloudformation delete-stack \
  --stack-name demo-stack
```

Describe stacks:

```bash
aws cloudformation describe-stacks \
  --stack-name demo-stack
```

Create a change set:

```bash
aws cloudformation create-change-set \
  --stack-name demo-stack \
  --change-set-name demo-change-set \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

Execute a change set:

```bash
aws cloudformation execute-change-set \
  --stack-name demo-stack \
  --change-set-name demo-change-set
```

---

## 25. IAM capabilities in CloudFormation

If a template creates or modifies IAM resources, you often need to acknowledge that explicitly.

Common capabilities:

```text
CAPABILITY_IAM
CAPABILITY_NAMED_IAM
CAPABILITY_AUTO_EXPAND
```

Use `CAPABILITY_NAMED_IAM` when your template creates IAM resources with custom names.

Example:

```bash
--capabilities CAPABILITY_NAMED_IAM
```

Why AWS requires this:

IAM resources are security-sensitive. AWS wants you to explicitly acknowledge that CloudFormation may create or modify permissions.

---

## 26. Important exam tips

### Tip 1: Repeatable infrastructure means CloudFormation

If the question says:

```text
Deploy the same infrastructure repeatedly
Deploy across multiple environments
Use Infrastructure as Code
Automate AWS resource provisioning
```

Think CloudFormation.

### Tip 2: Multi-account and multi-region deployment means StackSets

If the question says:

```text
Deploy the same baseline resources across many AWS accounts and regions
```

Think CloudFormation StackSets.

### Tip 3: Preview changes before applying means Change Sets

If the question says:

```text
Need to know what will change before updating production infrastructure
```

Think Change Sets.

### Tip 4: Manual changes outside template means Drift Detection

If the question says:

```text
Resources were changed manually and you need to detect differences
```

Think Drift Detection.

### Tip 5: Unsupported resource/action means Custom Resource

If the question says:

```text
CloudFormation does not support this action directly
```

Think Custom Resource backed by Lambda.

### Tip 6: Protect stateful resources

If the template includes databases, buckets, or volumes, think about:

- `DeletionPolicy`
- `UpdateReplacePolicy`
- stack policies
- snapshots
- backups

### Tip 7: YAML is easier, JSON is valid

For the exam, know both are supported.

For real life, use YAML unless your organization has a reason to use JSON.

---

## 27. Mini lab: create an S3 bucket with parameters and outputs

Create a file named `s3-bucket.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: S3 bucket created using CloudFormation

Parameters:
  EnvironmentName:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - test
      - prod

Resources:
  DemoBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${EnvironmentName}-${AWS::AccountId}-${AWS::Region}-cfn-demo'
      VersioningConfiguration:
        Status: Enabled
      Tags:
        - Key: Environment
          Value: !Ref EnvironmentName
        - Key: ManagedBy
          Value: CloudFormation

Outputs:
  BucketName:
    Description: Created bucket name
    Value: !Ref DemoBucket

  BucketArn:
    Description: Created bucket ARN
    Value: !GetAtt DemoBucket.Arn
```

Deploy it:

```bash
aws cloudformation create-stack \
  --stack-name cfn-s3-demo \
  --template-body file://s3-bucket.yaml \
  --parameters ParameterKey=EnvironmentName,ParameterValue=dev
```

Check output:

```bash
aws cloudformation describe-stacks \
  --stack-name cfn-s3-demo \
  --query "Stacks[0].Outputs"
```

Delete it:

```bash
aws cloudformation delete-stack \
  --stack-name cfn-s3-demo
```

---

## 28. Mini lab: understand drift

1. Deploy a stack that creates a security group.
2. Go to the AWS Console.
3. Manually edit the security group rule.
4. Run drift detection on the stack.
5. Check whether CloudFormation reports the resource as drifted.

Lesson:

CloudFormation manages resources based on the template, but people can still manually change resources unless you restrict access using IAM and governance controls.

---

## 29. CloudFormation best practices

Use parameters for values that vary between environments.

Use outputs for values that humans, pipelines, or other stacks need.

Use tags consistently.

Use change sets before production updates.

Use drift detection to find manual changes.

Use StackSets for multi-account/multi-region baselines.

Use `DeletionPolicy` and `UpdateReplacePolicy` for stateful resources.

Do not store secrets directly in templates.

Avoid hardcoding AMI IDs unless this is a temporary lab.

Keep templates modular when they become large.

Use source control for templates.

Use CI/CD to validate and deploy templates.

Review IAM resources carefully.

Use least privilege for CloudFormation execution roles.

---

## 30. Common beginner mistakes

### Mistake 1: Thinking CloudFormation is free, so the lab is free

Wrong. CloudFormation is free, but the resources are not.

### Mistake 2: Hardcoding everything

If you hardcode VPC IDs, subnet IDs, AMI IDs, and names everywhere, your template becomes painful to reuse.

### Mistake 3: Not using Change Sets

Updating production stacks without a change set is risky.

### Mistake 4: Forgetting region scope

Stacks are regional. A stack in `eu-north-1` does not automatically deploy to `us-east-1`.

### Mistake 5: Deleting stacks without checking stateful resources

Deleting a stack can delete the resources inside it.

Use deletion policies for important data.

### Mistake 6: Manually changing resources after deployment

Manual changes cause drift.

The correct fix is usually to update the template and redeploy, not keep clicking in the console.

---

## 31. Mental model for the exam

Use this simple mapping:

| Scenario | Likely answer |
|---|---|
| Need Infrastructure as Code on AWS | CloudFormation |
| Need same template across accounts/regions | StackSets |
| Need preview before update | Change Sets |
| Need detect manual changes | Drift Detection |
| Need unsupported action/resource | Custom Resource |
| Need protect resource from stack deletion | DeletionPolicy / Retain / Snapshot |
| Need pass environment-specific values | Parameters |
| Need return resource IDs/URLs | Outputs |
| Need region-based lookup | Mappings + FindInMap |
| Need create resource only in prod | Conditions |
| Need reusable generated serverless resources | Transform / SAM |

---

## 32. Final summary

CloudFormation lets you define AWS infrastructure as code using YAML or JSON templates.

The template is deployed as a stack.

The only required section is `Resources`, but for real projects you will often use `Parameters`, `Mappings`, `Conditions`, `Outputs`, and `Transform`.

For the AWS SAA exam, remember these strongly:

- CloudFormation is AWS-native Infrastructure as Code.
- Stacks are regional.
- StackSets deploy across multiple accounts and regions.
- Change Sets preview changes.
- Drift Detection finds manual changes.
- Custom Resources handle unsupported actions.
- Tags help with cost tracking and ownership.
- The service is free, but the resources it creates are not.

For real projects, CloudFormation is powerful, but raw YAML can become painful as systems grow. That is why many teams use AWS CDK to generate CloudFormation while still letting CloudFormation manage the actual deployment.

---

## References

- AWS CloudFormation template sections: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-anatomy.html
- AWS CloudFormation template formats: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-formats.html
- AWS CloudFormation parameters: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html
- AWS CloudFormation change sets: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html
- AWS CloudFormation drift detection: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-stack-drift.html
- AWS CloudFormation StackSets: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cloudformation-stackset.html

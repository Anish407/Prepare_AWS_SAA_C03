# AWS Infrastructure Composer with CloudFormation

## Labs
- [Cloudformation Infra Composer](./infracomposer.md)

## Purpose of this README

This README explains AWS Infrastructure Composer from a CloudFormation point of view. It is focused on theory, exam understanding, and real project usage. It avoids step-by-step build instructions and deployment walkthroughs.

---

## 1. What is AWS Infrastructure Composer?

AWS Infrastructure Composer is a visual infrastructure design tool from AWS. It helps you visually compose AWS architectures and generate Infrastructure as Code templates.

In simple terms:

> AWS Infrastructure Composer is a visual editor for AWS CloudFormation and AWS SAM templates.

It lets you drag AWS resources onto a canvas, connect them, configure their properties, and inspect the generated template.

AWS describes Infrastructure Composer as a tool for visually composing modern applications on AWS. As you build visually, it creates AWS CloudFormation and AWS Serverless Application Model templates.

Important point:

> Infrastructure Composer is not the deployment engine. CloudFormation is still the deployment engine.

Infrastructure Composer helps you create, understand, and edit templates. CloudFormation uses those templates to create and manage AWS resources.

---

## 2. Old name: AWS Application Composer

AWS Infrastructure Composer was previously known as AWS Application Composer.

The new name is more accurate because the tool is not limited only to application-level resources. It is positioned as a visual way to compose AWS infrastructure backed by CloudFormation.

For exam or interview questions, both names may appear, but the current name is:

> AWS Infrastructure Composer

---

## 3. Why Infrastructure Composer exists

CloudFormation templates are powerful, but they can become difficult to read and maintain, especially when the architecture has many resources.

Infrastructure Composer helps with this problem by providing a visual canvas.

It is useful for:

- Understanding how resources are connected
- Creating a starting CloudFormation or SAM template
- Visualizing existing templates
- Explaining architecture to others
- Reducing YAML/JSON authoring friction
- Learning CloudFormation resource relationships
- Building serverless application templates faster

However, it does not remove the need to understand CloudFormation.

Brutal truth:

> Composer can draw the boxes and generate some template structure, but it cannot make bad architecture good. You still need to understand networking, IAM, security, cost, availability, and CloudFormation behavior.

---

## 4. Relationship with CloudFormation

CloudFormation is the core AWS Infrastructure as Code service. It creates, updates, and deletes AWS resources using templates.

Infrastructure Composer sits above CloudFormation.

```text
Infrastructure Composer
        |
        v
CloudFormation / SAM template
        |
        v
CloudFormation stack deployment
        |
        v
AWS resources
```

Composer produces or edits the template. CloudFormation manages the actual stack lifecycle.

### Key distinction

| Area | CloudFormation | Infrastructure Composer |
|---|---|---|
| Main purpose | Deploy and manage infrastructure | Visually create and edit IaC templates |
| Type | Infrastructure as Code service | Visual design/editor tool |
| Input | YAML/JSON template | Visual canvas or existing template |
| Output | AWS resources | CloudFormation/SAM template |
| Manages stacks | Yes | No, not by itself |
| Used in CI/CD | Yes | Usually indirectly |
| Best for | Repeatable deployments | Visualization and template authoring |

---

## 5. Relationship with AWS SAM

AWS SAM stands for AWS Serverless Application Model.

SAM is an extension of CloudFormation for serverless applications. It provides shorter syntax for resources like Lambda, API Gateway, DynamoDB event sources, and serverless workflows.

Infrastructure Composer can work with both:

- Standard CloudFormation templates
- AWS SAM templates

This is why Composer is especially useful for serverless architectures.

Example SAM resource type:

```yaml
Type: AWS::Serverless::Function
```

Example raw CloudFormation Lambda resource type:

```yaml
Type: AWS::Lambda::Function
```

The SAM version is shorter. During deployment, SAM transforms the template into standard CloudFormation resources.

---

## 6. Relationship with AWS CDK

AWS CDK is a code-first Infrastructure as Code framework. You write infrastructure using programming languages like TypeScript, Python, Java, C#, or Go. CDK then synthesizes CloudFormation templates.

Infrastructure Composer is visual-first. CDK is code-first.

| Area | Infrastructure Composer | AWS CDK |
|---|---|---|
| Style | Visual canvas | Programming language |
| Output | CloudFormation/SAM template | CloudFormation template |
| Best for | Learning, visualization, quick prototypes | Production-grade reusable IaC |
| Reusability | Limited | Strong through constructs/classes |
| Good for complex platforms | Limited | Much better |
| Learning curve | Lower | Higher |

For a serious developer or architect, CDK usually matters more long term. Composer is still useful because it helps you understand the resource relationships visually.

---

## 7. Where Infrastructure Composer can be used

Infrastructure Composer can be used from different places:

| Location | Use case |
|---|---|
| AWS Infrastructure Composer console | Visual design in the AWS console |
| CloudFormation console mode | Visualize and edit templates from CloudFormation |
| AWS Toolkit for Visual Studio Code | Local template editing and visualization |
| Local sync mode | Keep visual changes synchronized with local template files |

The Visual Studio Code integration is important for real development because templates should normally live in Git, not only in the AWS console.

---

## 8. What Infrastructure Composer can do

Infrastructure Composer can help you:

- Create a new CloudFormation or SAM template visually
- Import an existing template and display it as a diagram
- Add resources using a visual canvas
- Configure resource properties
- Connect supported resources together
- Generate YAML-based IaC templates
- Keep a visual diagram and template synchronized
- Improve understanding of resource dependencies
- Accelerate serverless template authoring

It is especially strong for common serverless services such as:

- AWS Lambda
- Amazon API Gateway
- Amazon EventBridge
- Amazon SQS
- AWS Step Functions
- Amazon DynamoDB

It can also work with CloudFormation-supported resources more broadly, but the visual experience is usually best for commonly used modern/serverless services.

---

## 9. What Infrastructure Composer does not do

Infrastructure Composer does not magically solve infrastructure design.

It does not replace:

- CloudFormation knowledge
- IAM knowledge
- Networking knowledge
- Security design
- Cost optimization
- Change Sets
- Drift Detection
- Stack Policies
- DeletionPolicy
- Backups
- CI/CD
- Git review process
- Environment promotion strategy

It also does not remove the need to manually review generated templates.

A visual diagram can look clean while the generated infrastructure still has bad IAM permissions, missing retention policies, weak security boundaries, or expensive resources.

---

## 10. Typical conceptual workflow

A safe theoretical workflow looks like this:

```text
Design visually in Infrastructure Composer
        |
        v
Review generated CloudFormation/SAM template
        |
        v
Commit template to Git
        |
        v
Review through pull request
        |
        v
Validate template
        |
        v
Create CloudFormation Change Set
        |
        v
Review deployment impact
        |
        v
Deploy through controlled pipeline
```

The important lesson is that Composer should not become a shortcut around review and governance.

For production systems, the generated template should be treated like source code.

---

## 11. Important CloudFormation concepts you still need

Even when using Infrastructure Composer, you still need to understand the following CloudFormation concepts.

### Resources

The `Resources` section defines the AWS resources that CloudFormation creates.

Example:

```yaml
Resources:
  OrdersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      BillingMode: PAY_PER_REQUEST
```

This is the only required section in a CloudFormation template.

### Parameters

Parameters allow the same template to be reused with different values.

Example use cases:

- Environment name
- Instance type
- VPC ID
- Subnet IDs
- Allowed CIDR range

Conceptual example:

```yaml
Parameters:
  EnvironmentName:
    Type: String
    AllowedValues:
      - dev
      - test
      - prod
```

### Outputs

Outputs expose useful values after stack creation.

Examples:

- API endpoint URL
- Load balancer DNS name
- DynamoDB table name
- VPC ID
- SQS queue URL

### Mappings

Mappings are static lookup tables inside the template.

Example use cases:

- Region-specific AMI IDs
- Environment-specific instance sizes
- Region-specific configuration values

### Conditions

Conditions decide whether a resource or property should be created or configured.

Example use cases:

- Create expensive resources only in production
- Enable alarms only in production
- Create a bastion host only in development

### Intrinsic functions

Intrinsic functions are used to reference and combine values inside templates.

Common examples:

| Function | Purpose |
|---|---|
| `!Ref` | Reference parameter or resource value |
| `!GetAtt` | Get an attribute from a resource |
| `!Sub` | String substitution |
| `!Join` | Join values into a string |
| `!FindInMap` | Look up values from mappings |
| `!If` | Conditional value selection |

Infrastructure Composer may generate these, but you need to understand what they mean.

---

## 12. Infrastructure Composer and Change Sets

A Change Set is a CloudFormation feature that shows what will happen before a stack update is executed.

This matters because a small visual change in Composer can still cause a major infrastructure change.

Examples of dangerous update effects:

- A database may be replaced
- A table may be recreated
- A security group may be modified
- A Lambda role may lose permissions
- A queue may be replaced because of a name change
- A load balancer listener may be changed

Composer helps edit the template. Change Sets help understand the deployment impact.

Exam memory:

> Use Change Sets when you need to preview CloudFormation stack changes before applying them.

---

## 13. Infrastructure Composer and Drift Detection

Drift Detection is a CloudFormation feature that detects whether resources have changed outside CloudFormation.

Example:

A developer manually changes a security group rule in the AWS console. CloudFormation no longer matches the actual resource state. That is drift.

Composer may help visualize templates, but it is not the main drift control feature. Drift Detection belongs to CloudFormation.

Exam memory:

> Use Drift Detection when you need to identify manual changes made outside CloudFormation.

---

## 14. Infrastructure Composer and Stack Policies

Stack Policies protect stack resources from unwanted updates.

They are useful for critical resources such as:

- RDS databases
- DynamoDB tables
- S3 buckets
- Production security groups
- Production IAM roles

Example concept:

```json
{
  "Statement": [
    {
      "Effect": "Deny",
      "Action": "Update:*",
      "Principal": "*",
      "Resource": "LogicalResourceId/ProductionDatabase"
    }
  ]
}
```

This is not an IAM policy. It is a CloudFormation stack policy.

Difference:

| Policy type | Protects against |
|---|---|
| IAM policy | Who can call AWS APIs |
| Stack policy | Which stack resources CloudFormation can update |

Composer does not replace stack policies. For important stateful resources, stack policies are still valuable.

---

## 15. Infrastructure Composer and DeletionPolicy

`DeletionPolicy` controls what happens to a resource when the stack is deleted or when the resource is removed from the template.

Important values:

| Value | Meaning |
|---|---|
| `Delete` | Delete the resource |
| `Retain` | Keep the resource even if stack is deleted |
| `Snapshot` | Create a snapshot before deletion, where supported |

For stateful resources, `Retain` or `Snapshot` is often safer than the default delete behavior.

Example:

```yaml
OrdersTable:
  Type: AWS::DynamoDB::Table
  DeletionPolicy: Retain
  UpdateReplacePolicy: Retain
  Properties:
    BillingMode: PAY_PER_REQUEST
```

Important distinction:

| Feature | Purpose |
|---|---|
| Stack Policy | Protects resources from stack updates |
| DeletionPolicy | Controls what happens during stack deletion/removal |
| UpdateReplacePolicy | Controls what happens when replacement is required |

---

## 16. Infrastructure Composer and IAM

IAM is one of the biggest areas where generated templates must be reviewed carefully.

Composer can help create resource relationships, but you must verify that the generated or edited permissions are safe.

Bad permission pattern:

```yaml
Action: '*'
Resource: '*'
```

Better pattern:

```yaml
Action:
  - dynamodb:GetItem
  - dynamodb:PutItem
Resource: !GetAtt OrdersTable.Arn
```

Real-world rule:

> Never assume generated IAM is production-safe. Review actions, resources, principals, and trust policies.

---

## 17. Infrastructure Composer and resource dependencies

CloudFormation automatically understands many dependencies through references.

For example:

```yaml
Environment:
  Variables:
    TABLE_NAME: !Ref OrdersTable
```

Because the Lambda function references the DynamoDB table, CloudFormation knows the table must exist before the function can fully use that reference.

Sometimes explicit dependencies are still needed using `DependsOn`, but many dependencies are inferred by references like `!Ref` and `!GetAtt`.

Infrastructure Composer can make relationships easier to see visually, but CloudFormation dependency behavior still matters.

---

## 18. Infrastructure Composer and generated templates

Generated templates should be reviewed for:

- Hardcoded names
- Missing parameters
- Missing outputs
- Overly broad IAM permissions
- Missing tags
- Missing retention policies
- Missing encryption settings
- Missing logging configuration
- Public access settings
- Replacement risk
- Environment-specific values
- Cost-sensitive resources

A generated template is a starting point, not automatically a production-ready template.

---

## 19. Good use cases

Infrastructure Composer is good when:

- You are learning CloudFormation
- You are learning serverless architecture
- You want to visualize an existing template
- You want to explain resource relationships
- You want a starting point for a template
- You are creating a small proof of concept
- You are reviewing how services connect
- You want to reduce manual YAML writing

---

## 20. Weak use cases

Infrastructure Composer is not ideal when:

- You are building a large multi-account platform
- You need reusable infrastructure modules
- You need advanced abstraction and composition
- You need loops and programming logic
- You need strict production governance
- You need complex environment promotion
- You need deep customization

For these cases, CDK, Terraform, or well-structured CloudFormation/SAM templates are usually stronger.

---

## 21. Comparison with CloudFormation Designer

CloudFormation Designer was the older visual template design tool.

Infrastructure Composer is the newer and more modern visual experience.

| Area | CloudFormation Designer | Infrastructure Composer |
|---|---|---|
| Age | Older | Newer |
| Focus | Generic CloudFormation visual design | Modern application and infrastructure composition |
| Serverless experience | Limited | Stronger |
| Console experience | Older | Better modern canvas |
| Local workflow | Limited | Better with VS Code integration |

For new learning, focus on Infrastructure Composer.

---

## 22. Exam-focused summary

For AWS SAA-C03, you do not need deep operational expertise in Infrastructure Composer, but you should know where it fits.

Remember this mapping:

| Requirement | AWS feature/service |
|---|---|
| Repeatable infrastructure deployment | CloudFormation |
| Same stack across accounts and regions | StackSets |
| Visual CloudFormation/SAM template creation | Infrastructure Composer |
| Preview stack update impact | Change Sets |
| Detect manual changes | Drift Detection |
| Protect resources from stack updates | Stack Policies |
| Protect stateful resources from deletion | DeletionPolicy / UpdateReplacePolicy |
| Serverless template abstraction | AWS SAM |
| Code-first IaC | AWS CDK |

Most likely exam angle:

> If the question says visual design, visual composition, or visually creating CloudFormation/SAM templates, think Infrastructure Composer.

But if the question says repeatable deployment, stack updates, rollback, drift, change preview, or multi-account deployment, think CloudFormation features.

---

## 23. Common questions

### Is Infrastructure Composer the same as CloudFormation?

No. CloudFormation is the IaC deployment service. Infrastructure Composer is a visual tool for creating and editing CloudFormation/SAM templates.

### Does Infrastructure Composer replace CloudFormation?

No. It depends on CloudFormation templates and CloudFormation stack deployment.

### Does Infrastructure Composer replace CDK?

No. CDK is better for reusable, code-first, production-grade infrastructure patterns. Composer is better for visualization, learning, and template authoring.

### Can Infrastructure Composer work with existing templates?

Yes. Existing CloudFormation and SAM templates can be loaded and visualized.

### Is Infrastructure Composer only for serverless?

No. It can work with CloudFormation-supported resources, but the experience is especially strong for common serverless services.

### Should production infrastructure be edited directly in the console?

Usually no. Production templates should be stored in Git, reviewed, validated, and deployed through a controlled pipeline.

### Do I still need to learn YAML if I use Composer?

Yes. You need to understand the generated template because production issues are debugged at the CloudFormation/template level, not just at the visual canvas level.

---

## 24. Final takeaways

- AWS Infrastructure Composer is a visual tool for CloudFormation and SAM templates.
- It was formerly called AWS Application Composer.
- It helps you visually create, understand, and edit infrastructure templates.
- It is not a replacement for CloudFormation.
- It is not a replacement for CDK.
- It is most useful for learning, visualization, serverless designs, and template starting points.
- Serious production use still needs Git, review, validation, Change Sets, CI/CD, and CloudFormation knowledge.
- Always review generated templates manually.
- Always pay special attention to IAM, stateful resources, deletion behavior, replacement behavior, and cost.

---

## References

- AWS Infrastructure Composer documentation
- AWS CloudFormation documentation
- AWS Serverless Application Model documentation

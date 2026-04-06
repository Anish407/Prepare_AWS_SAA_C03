



### Steps:

### Create the frontend and backend images and push to ECR
1. Create 2 an Ecr repositories
   <img width="1380" height="694" alt="image" src="https://github.com/user-attachments/assets/4d3deb0d-c41d-4c8f-835f-3bbb8d8aca47" />
   <img width="1181" height="282" alt="image" src="https://github.com/user-attachments/assets/e229d85a-c54f-4a9b-b7a9-89c6a164f0f0" />

2. Copy the ECR url, we will upload the images to this repo
   <img width="810" height="238" alt="image" src="https://github.com/user-attachments/assets/7897fb9b-66ce-4924-acf3-db0a91657aca" />
3. Create an access key to login to aws cli and to configure an aws profile. 
   <img width="1557" height="479" alt="image" src="https://github.com/user-attachments/assets/b1494d9c-5c44-41f3-ac8e-65ccbe59b3d3" />
4. Create an aws profile on your local machine using the below command.
  ```
    aws configure --profile ecslab
  ```
  <img width="1097" height="219" alt="image" src="https://github.com/user-attachments/assets/7c6b7e24-6fca-43d3-8401-e328aaad8e57" />

5. Now run the following command create an image for the frontend app
   ```
   docker build -t myfrontendappimage .

   aws ecr get-login-password --region us-east-1 --profile ecslab | docker login --username AWS --password-stdin 545829658421.dkr.ecr.us-east-1.amazonaws.com

   docker tag frontendlab33:latest 545829658421.dkr.ecr.us-east-1.amazonaws.com/myecr-repo:latest
   docker push 545829658421.dkr.ecr.us-east-1.amazonaws.com/myecr-repo:latest
   ```
  Now tag the backend image and push it to ECR
  ```
  docker tag completeecslab3:latest 545829658421.dkr.ecr.us-east-1.amazonaws.com/be-repo:latest
  docker push 545829658421.dkr.ecr.us-east-1.amazonaws.com/be-repo:latest
  ```
## Step 3 - Create the VPC and subnets

Create a VPC, for example:

- VPC CIDR: `10.0.0.0/16`

Create at least:

- **2 public subnets** in different AZs
- **2 private subnets** in different AZs

Example:

- Public subnet A: `10.0.1.0/24`
- Public subnet B: `10.0.2.0/24`
- Private subnet A: `10.0.11.0/24`
- Private subnet B: `10.0.12.0/24`

<img width="1416" height="675" alt="image" src="https://github.com/user-attachments/assets/bfcd6f7d-e660-46c9-8aa3-bedf4307af6c" />

> we will enable the S3 gateway endpoints manually later.

---

## Step 4 - Create security groups

### CloudFront/ALB security group

Create an ALB security group:

- Inbound: `HTTP 80` from the source you decide for the lab
- Outbound: allow to ECS task security group or all outbound

For a first working lab, keeping the ALB public is simpler.

### ECS task security group

Create a security group for ECS tasks:

- Inbound: `HTTP 80` from the **ALB security group**
- Outbound: allow all outbound for now

### Endpoint security group

Create a security group for interface endpoints:

- Inbound: `HTTPS 443` from the ECS task security group
- Outbound: default

Why this matters:
- Your ECS task talks to ECR API, ECR Docker endpoint, and CloudWatch Logs using **443**.
- If the endpoint SG does not allow the ECS task SG, image pull or log publishing fails.

<img width="1571" height="445" alt="image" src="https://github.com/user-attachments/assets/210b43e0-de3e-4a70-9ad0-82afaa8c120a" />


---

## Step 5 - Create the VPC endpoints

This is the part most people miss.

Create these endpoints:

### Interface endpoints

In the **private subnets**, create:

- `com.amazonaws.us-east-1.ecr.api`
- `com.amazonaws.us-east-1.ecr.dkr`
- `com.amazonaws.us-east-1.logs`

Attach the **endpoint security group**.

> Select the private subnets for the interface endpoints

<img width="1167" height="505" alt="image" src="https://github.com/user-attachments/assets/ca5c8df3-a9ad-4b92-bcd0-ec5c8a7a514c" />


Enable **Private DNS**.

### Gateway endpoint

Create the **S3 gateway endpoint**:

- `com.amazonaws.us-east-1.s3`

Associate it with the **private route table**.

### Why each endpoint exists

- **ecr.api** -> ECS/Fargate talks to the ECR API.
- **ecr.dkr** -> Docker image pull path.
- **logs** -> container logs to CloudWatch Logs.
- **s3 gateway** -> actual image layers are stored in S3.


 <img width="1582" height="458" alt="image" src="https://github.com/user-attachments/assets/74ecfb80-fa36-4d30-a28e-f926159ef31b" />

## Step 6 - Create IAM roles

### A. Task execution role

This role is used by **ECS/Fargate infrastructure**, not by your code.

Use the AWS managed policy:

- `AmazonECSTaskExecutionRolePolicy`
- `AWSAppSyncPushToCloudWatchLogs` - since ECS will create the log group, we need to give it these permissions

This role is responsible for:

- Pulling the image from ECR
- Writing logs to CloudWatch Logs
- principal ```ecs-tasks.amazonaws.com```

  <img width="655" height="323" alt="image" src="https://github.com/user-attachments/assets/bc570c65-bddb-4e60-a4ea-2c1e3e3246d5" />


Name example:
- `ecsTaskExecutionRole`

<img width="1438" height="659" alt="image" src="https://github.com/user-attachments/assets/11396657-2395-4bfc-b194-03f0bebfc0e0" />
<img width="1141" height="456" alt="image" src="https://github.com/user-attachments/assets/d1664398-f01e-49f0-9a18-6d1c21b325cb" />

### B. Task role

We will create the task role while creating the ecs task definition. This role will be used by the application to call different services, In this lab , the api calls S3 to list all its contents.

For this static HTML lab, you do not need any real permissions yet.

Later, when your application calls:
- S3 -> add S3 permissions here
- SSM Parameter Store -> add SSM permissions here
- Secrets Manager -> add secrets permissions here

Name example:
- `ecsAppTaskRole`

## Step 8 - Create the ALB and target group

Create an **Application Load Balancer**.

For the first version of the lab:
- Scheme: **internet-facing**
   <img width="747" height="663" alt="image" src="https://github.com/user-attachments/assets/408a1811-0b26-42c6-a760-9c73296102e5" />
- Subnets: **public subnets**
  <img width="695" height="592" alt="image" src="https://github.com/user-attachments/assets/f1e46665-700d-462e-8c86-6b19d9e57698" />

- Security group: **ALB security group**
  <img width="501" height="217" alt="image" src="https://github.com/user-attachments/assets/ce14f56d-1e01-477b-b328-cb93162c076a" />

- Listener: `HTTP 8080`
  <img width="772" height="535" alt="image" src="https://github.com/user-attachments/assets/a3086b28-f80e-4c7b-ade0-161cb7b2fa7d" />
- On the listener, the default rule now points to the Frontend target group, this means if no rules match then the request is forwarded to the front end app
  <img width="1512" height="665" alt="image" src="https://github.com/user-attachments/assets/abb288f8-063e-4d4e-90fd-606de1b56f68" />
- Create a rule for the front end app, this means the path /fe redirects to the front end app
  <img width="1432" height="684" alt="image" src="https://github.com/user-attachments/assets/a09ae57c-5b2f-425e-9aaf-098eeecbed46" />
  Also select the target group for this rule 
  <img width="1221" height="395" alt="image" src="https://github.com/user-attachments/assets/dea6e4a1-30d3-4480-9a5c-5fdd91465070" />

- Create a rule for the backend app and in the transform we replace the /be/* with a /, so that we dont have to set a base path in our api and the request is forwarded without the /be prefix. 
  <img width="1512" height="626" alt="image" src="https://github.com/user-attachments/assets/817dbf96-9327-4bcb-a280-3318c8dcea3e" />
  
- 

### Target group

Create a target group with:

- Target type: **IP**
- Protocol: HTTP
- Port: 80
- Health check path: `/`
- VPC: your lab VPC

Why IP target type matters:
- ECS Fargate tasks in `awsvpc` mode get their own ENIs and private IPs.
- The ALB registers task IPs, not EC2 instances.

1. Front end Target group
   <img width="1486" height="608" alt="image" src="https://github.com/user-attachments/assets/ab75c807-e83c-4659-bbb8-403d2652feff" />

   <img width="1487" height="612" alt="image" src="https://github.com/user-attachments/assets/dcfa79d9-cc5b-4407-859e-95df90137357" />

2. Backend Target group
   <img width="1347" height="656" alt="image" src="https://github.com/user-attachments/assets/36a05afa-f1f9-48df-ab43-8ab6a1263916" />
   <img width="1052" height="336" alt="image" src="https://github.com/user-attachments/assets/1cd1f0e0-183f-4aa6-acb8-aec64fb9a9be" />
The backend app has a health check endpoint called /health
---

































   

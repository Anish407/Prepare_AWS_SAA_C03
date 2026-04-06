



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














































   

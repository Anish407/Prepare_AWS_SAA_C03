#Lab: 

## Concept: CloudFront Multi-Origin with Route 53, Private EC2 (VPC Origin), and Private S3 (OAC)

### Phase 1:
- Create a Public Hosted Zone in Route 53
- Request an ACM Certificate in us-east-1
- Create a Private S3 Bucket
- Create a CloudFront Distribution with Custom Domain
- Configure Origin Access Control (OAC) for S3

### Phase 2:
- Create a Private EC2 Instance in a VPC
- Configure CloudFront VPC Origin to Private EC2
- Create a Behavior /api/* → Route to Private EC2 (VPC Origin)
- Create a Behavior /myapp/* → Route to S3 (OAC Protected)
- Create a Route 53 Alias Record → CloudFront Distribution
- Enable CloudFront Access Logs

## Steps Phase 1

1. Create an S3 bucket that will be the origin for cloudfront
   <img width="1363" height="687" alt="image" src="https://github.com/user-attachments/assets/8fdef851-78a0-4558-8732-bdfb1b269abe" />
2. Create cloudfront distribution
   <img width="1476" height="727" alt="image" src="https://github.com/user-attachments/assets/e0e58a26-82fa-4cf9-8d76-aaa485692830" />
   <img width="1872" height="728" alt="image" src="https://github.com/user-attachments/assets/bf36bb87-2fcc-4957-8a6f-64366eb099ea" />
3. We can see that cloudfront added the bucket policy to access the private s3 bucket
   <img width="998" height="637" alt="image" src="https://github.com/user-attachments/assets/7857e7f9-2830-46d5-8760-9caa0b1363e2" />
4. To invalidate the cache, we create an invalidation in cloudfront. This will remove the cached contents from the edge locations and the regional cache
   <img width="1292" height="527" alt="image" src="https://github.com/user-attachments/assets/6d816fca-e02c-4221-9d4d-615408ea9251" />
5. Now we can view the html file using the cloudfront url
   <img width="1302" height="325" alt="image" src="https://github.com/user-attachments/assets/43cb5c47-ab21-4e32-af7d-a9b66f060998" />
6. Since we added a path for the origin that matches the folder in which the item is placed in the s3 bucket, we dont need to specify it with the distribution url. The html file is in a folder called private and we added a path for the s3 origin as /private, so we can skip the /private in the url.
If we didnt have /private in the path in the origin settings then we would have to use ```cloudfronturl/private/sample.html``` to access the file.
   <img width="1517" height="382" alt="image" src="https://github.com/user-attachments/assets/315c9423-8e21-4c77-abd1-3c884c311d29" />
7. Now we can try to add the alternate domain name for our distribution. Right now, we use the cloudfront url to access the website.
   <img width="1766" height="687" alt="image" src="https://github.com/user-attachments/assets/9a7fff45-a635-4082-b350-dd3d6b38bd16" />
8. I dont own any domains, but the sandbox environment has a public hosted zone with a registered domain name. So we will try to create a subdomain under that domain and use it with cloudfront to access our sample website.
   <img width="1447" height="330" alt="image" src="https://github.com/user-attachments/assets/df9b9222-7fe4-4b50-8af2-013fd05e9941" />
9. In order to use TLS with the alternate domain name, we need to request a certificate from ACM
    <img width="1548" height="778" alt="image" src="https://github.com/user-attachments/assets/a55e8d8c-cc4e-4d13-9015-3d311a31c7a4" />

   



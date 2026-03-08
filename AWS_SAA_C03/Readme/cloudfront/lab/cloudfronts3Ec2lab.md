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

1. Create an S3 bucket that will be the origin for cloudfront, here I will create clickonce artifacts for a WPF application and store the artifacts in the s3 bucket. We can even store a simple html file also.
   <img width="828" height="382" alt="image" src="https://github.com/user-attachments/assets/dde9a454-676b-4a1d-b0ff-6b53889f3db1" />

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
10. To add an Alias record for the cloudfront distribution in Route53, we need to add an alternate domain name in the cloudfront distribution. Only cloudfront distributions with an alternate domain name can be added as an Alias record in route 53
    <img width="1797" height="698" alt="image" src="https://github.com/user-attachments/assets/ed5ebe65-e3df-4768-b7db-b20e6b8f1ed6" />
11. Inorder to add an alternate domain name in route53, we need to have a certificate with that name, so we create a certificate first for that subdomain.
    <img width="1797" height="603" alt="image" src="https://github.com/user-attachments/assets/21e93899-938f-4ee7-8f32-bae8f6cf37a6" />
12. After the certificate is created , we can see that the status is pending, this is because the certificate has not been validated yet. To complete the validation, we need to add the provided CName record in our hosted zone.
<img width="1872" height="526" alt="image" src="https://github.com/user-attachments/assets/e8239424-8836-4a0f-b5e7-f7f858e03c49" />
13. After adding the records to the hosted zone, we can see that a new Cname record has been added
    <img width="1893" height="662" alt="image" src="https://github.com/user-attachments/assets/7c522ece-5123-4444-a7cb-51bf3562ec58" />
   And now the certificate status has changed to issued.
   <img width="1878" height="469" alt="image" src="https://github.com/user-attachments/assets/eaddd5c1-eff5-4ea3-932f-3e9a03eb99ef" />
14. Now that the certificate has been issued, we can add the alternate domain name in cloud front
    <img width="1877" height="547" alt="image" src="https://github.com/user-attachments/assets/42518196-d035-4613-8ee8-fd9e08041276" />

 15. Now that the alternate domain name has been added, we need to add an ALIAS record for the cloudfront distribution in route53, this is done so that the request can be sent to the cloudfront distribution  
   <img width="1742" height="733" alt="image" src="https://github.com/user-attachments/assets/52510e35-1139-4e61-9015-2cef774cfb56" />
 This will add 2 records in our hosted zone, 1 for Ipv4 and 1 for IPV6
   <img width="1055" height="442" alt="image" src="https://github.com/user-attachments/assets/29a3aa52-13f7-4434-8049-142cff4915be" />
 16. Now since we added the Origin path as /private 
     <img width="635" height="250" alt="image" src="https://github.com/user-attachments/assets/9e759855-4489-49e7-aac8-93dac5d99264" />
   and the clickonce artifacts are present under a folder called /clickonce
    <img width="781" height="377" alt="image" src="https://github.com/user-attachments/assets/5cdc0c60-ce36-4447-9c51-3858c8a99fc8" />
    We can download the application from a url 
     <img width="712" height="115" alt="image" src="https://github.com/user-attachments/assets/b567570f-e98b-4a5f-9f46-b7129a16f9f5" />




using Amazon.S3;
using Amazon.S3.Model;
using AWS_SAA_C03.Handlers.LearnIam.Interfaces;

namespace AWS_SAA_C03.Handlers.LearnIam.Implementation
{
    public class S3Handler(IAmazonS3 s3) : IS3Handler
    {
        public async Task<string> GetS3Object(string bucketName, string folderName, string fileName)
        {
            var bucket = bucketName; // "iam-lab-s3-anish-3498";
            var key = $"{folderName}/{fileName}";  // "private/secret.txt";

            var resp = await s3.GetObjectAsync(bucket, key);
            using var reader = new StreamReader(resp.ResponseStream);
            return await reader.ReadToEndAsync();
        }

        public async Task<List<string>> ListS3Buckets()
        {
            ListObjectsV2Response buckets = await s3.ListObjectsV2Async(new Amazon.S3.Model.ListObjectsV2Request
            {
                BucketName = "iam-lab-s3-anish-3498"
            });
            return buckets.S3Objects.Select(obj => obj.Key).ToList();
        }
    }
}

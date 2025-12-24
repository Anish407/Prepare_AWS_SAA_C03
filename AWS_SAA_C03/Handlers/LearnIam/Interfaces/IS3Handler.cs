

namespace AWS_SAA_C03.Handlers.LearnIam.Interfaces
{
    public interface IS3Handler
    {
        Task<string> GetS3Object(string bucketName, string folderName, string fileName);
        Task<List<string>> ListS3Buckets();
    }
}

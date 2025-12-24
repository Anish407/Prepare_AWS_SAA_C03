using Amazon.S3;
using AWS_SAA_C03.Handlers.LearnIam.Interfaces;

namespace AWS_SAA_C03.Endpoints.LearnIamEndpoints
{
    public static class IAMEndpoints
    {
        extension(WebApplication? app)
        {
            public WebApplication? LearningIamEndpoints()
            {
                    app!.MapGet("/s3/get/{bucketName}/file/{fileName}", async (
                        IS3Handler s3Handler, 
                        string bucketName, 
                        string folderName,
                        string fileName) =>
                    {
                        if (string.IsNullOrWhiteSpace(bucketName))
                            return Results.BadRequest("parameter 'bucket' is required.");

                        if (string.IsNullOrWhiteSpace(fileName))
                            return Results.BadRequest("parameter 'key' is required.");

                        try
                        {
                            var resp = await s3Handler.GetS3Object(bucketName, folderName,fileName);
                            return Results.Text(resp, "text/plain");
                        }
                        catch (Exception ex)
                        {
                            return Results.BadRequest($"Something went wrong, {ex.Message}");
                        }
                    });

                app!.MapGet("List", async (IS3Handler s3Handler) =>
                {
                    return Results.Ok(await s3Handler.ListS3Buckets());
                });

                return app;
            }
        }
    }
}

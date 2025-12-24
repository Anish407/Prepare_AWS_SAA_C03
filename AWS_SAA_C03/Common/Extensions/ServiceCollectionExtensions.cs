using Amazon.S3;

namespace AWS_SAA_C03.Common.Extensions
{
    public static class ServiceCollectionExtensions
    {
        extension (IServiceCollection services)
        {
            public IServiceCollection AddHandlers()
            {
                services.AddScoped<Handlers.LearnIam.Interfaces.IS3Handler, Handlers.LearnIam.Implementation.S3Handler>();
                return services;
            }

            public IServiceCollection AddCommon(IConfiguration configuration)
            {
                services.AddOpenApi();
                services.AddDefaultAWSOptions(configuration.GetAWSOptions());
                services.AddAWSService<IAmazonS3>();
                return services;
            }

        }
    }
}

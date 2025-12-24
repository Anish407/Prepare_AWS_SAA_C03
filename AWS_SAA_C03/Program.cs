using Amazon.S3;
using AWS_SAA_C03.Common.Extensions;
using AWS_SAA_C03.Endpoints.LearnIamEndpoints;
using Scalar.AspNetCore;

var builder = WebApplication.CreateBuilder(args);


builder.Services.AddHandlers();
builder.Services.AddCommon(builder.Configuration);

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.MapScalarApiReference();
}

app.LearningIamEndpoints();

app.Run();

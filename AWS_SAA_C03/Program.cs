using Amazon.S3;
using AWS_SAA_C03.Common.Extensions;
using AWS_SAA_C03.Endpoints.LearnIamEndpoints;
using Microsoft.AspNetCore.Http.HttpResults;
using Scalar.AspNetCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddHealthChecks();
builder.Services.AddHandlers();
builder.Services.AddCommon(builder.Configuration);

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.MapScalarApiReference();
}

app.LearningIamEndpoints();

app.UseHealthChecks("/health");

app.Run();

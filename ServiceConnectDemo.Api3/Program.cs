var builder = WebApplication.CreateBuilder(args);

builder.Services.AddHealthChecks();

var app = builder.Build();

app.MapHealthChecks("/health");

app.MapGet("/", () => Results.Redirect("/chain"));

app.MapGet("/chain", (HttpContext context) =>
{
    return Results.Ok(new ChainResponse(
        Service: "ServiceConnectDemo.Api3",
        Message: "Api3 is the final private service in the call chain.",
        Scheme: context.Request.Scheme,
        Host: context.Request.Host.Value,
        Downstream: null));
});

app.Run();

internal sealed record ChainResponse(
    string Service,
    string Message,
    string Scheme,
    string Host,
    ChainResponse? Downstream);

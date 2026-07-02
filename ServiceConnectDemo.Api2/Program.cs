var builder = WebApplication.CreateBuilder(args);

builder.Services.AddHealthChecks();
builder.Services.AddHttpClient("api3", client =>
{
    var api3BaseUrl = builder.Configuration["Downstream:Api3BaseUrl"]
        ?? "http://localhost:5083";

    client.BaseAddress = new Uri(api3BaseUrl);
});

var app = builder.Build();

app.MapHealthChecks("/health");

app.MapGet("/", () => Results.Redirect("/chain"));

app.MapGet("/chain", async (IHttpClientFactory httpClientFactory, HttpContext context) =>
{
    var response = await httpClientFactory.CreateClient("api3").GetFromJsonAsync<ChainResponse>("/chain");

    return Results.Ok(new ChainResponse(
        Service: "ServiceConnectDemo.Api2",
        Message: "Api2 received an internal request and called Api3.",
        Scheme: context.Request.Scheme,
        Host: context.Request.Host.Value,
        Downstream: response));
});

app.Run();

internal sealed record ChainResponse(
    string Service,
    string Message,
    string Scheme,
    string Host,
    ChainResponse? Downstream);

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddHealthChecks();
builder.Services.AddHttpClient("api2", client =>
{
    var api2BaseUrl = builder.Configuration["Downstream:Api2BaseUrl"]
        ?? "http://localhost:5082";

    client.BaseAddress = new Uri(api2BaseUrl);
});

var app = builder.Build();

app.MapHealthChecks("/health");

app.MapGet("/", () => Results.Redirect("/chain"));

app.MapGet("/chain", async (IHttpClientFactory httpClientFactory, HttpContext context) =>
{
    var response = await httpClientFactory.CreateClient("api2").GetFromJsonAsync<ChainResponse>("/chain");

    return Results.Ok(new ChainResponse(
        Service: "ServiceConnectDemo.Api1",
        Message: "Public API received the request and called Api2.",
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

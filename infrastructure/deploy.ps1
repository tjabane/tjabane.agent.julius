# Mr Krabs - Azure Container Apps infrastructure and image deployment
# Usage: .\infrastructure\deploy.ps1 -ResourceGroup "rg-krabs" -Location "southafricanorth"

param(
    [Parameter(Mandatory)]
    [string]$ResourceGroup,

    [string]$Location = "southafricanorth",

    [string]$AppName = "krabs",

    [string]$AppEnvironment = "dev",

    [bool]$InvestecSandbox = $true,

    [string]$ImageTag = "latest",

    [string]$OtelMode = "disabled",

    [string]$OtelServiceName = "mr-krabs",

    [string]$OtelExporterOtlpEndpoint = "",

    [string]$OtelResourceAttributes = "",

    [string]$OtelTracesSampler = "parentbased_traceidratio",

    [string]$OtelTracesSamplerArg = "1.0"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "`n[1/8] Checking Azure login..." -ForegroundColor Cyan
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Not logged in. Running az login..." -ForegroundColor Yellow
    az login
    $account = az account show | ConvertFrom-Json
}
Write-Host "    Subscription: $($account.name)" -ForegroundColor Green

Write-Host "`n[2/8] Ensuring resource group '$ResourceGroup'..." -ForegroundColor Cyan
az group create --name $ResourceGroup --location $Location --output none
Write-Host "    Ready." -ForegroundColor Green

Write-Host "`n[3/8] Resolving deploying user..." -ForegroundColor Cyan
$deployingUserObjectId = (az ad signed-in-user show --query id -o tsv)
Write-Host "    Object ID: $deployingUserObjectId" -ForegroundColor Green

Write-Host "`n[4/8] Deploying Bicep infrastructure..." -ForegroundColor Cyan
$deployOutput = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file "$PSScriptRoot\main.bicep" `
    --parameters appName=$AppName location=$Location appEnvironment=$AppEnvironment investecSandbox=$($InvestecSandbox.ToString().ToLower()) deployingUserObjectId=$deployingUserObjectId otelMode=$OtelMode otelServiceName=$OtelServiceName otelExporterOtlpEndpoint=$OtelExporterOtlpEndpoint otelResourceAttributes=$OtelResourceAttributes otelTracesSampler=$OtelTracesSampler otelTracesSamplerArg=$OtelTracesSamplerArg `
    --query properties.outputs `
    --output json | ConvertFrom-Json

$keyVaultName     = $deployOutput.keyVaultName.value
$cosmosAccount    = $deployOutput.cosmosAccountName.value
$acsName          = $deployOutput.acsName.value
$containerAppUrl  = $deployOutput.containerAppUrl.value
$acrName          = $deployOutput.acrName.value
$acrLoginServer   = $deployOutput.acrLoginServer.value

Write-Host "    Container App : $containerAppUrl" -ForegroundColor Green
Write-Host "    ACR           : $acrLoginServer" -ForegroundColor Green
Write-Host "    Key Vault     : $keyVaultName" -ForegroundColor Green

Write-Host "`n[5/8] Populating Key Vault secrets..." -ForegroundColor Cyan
$cosmosConn = (az cosmosdb keys list --name $cosmosAccount --resource-group $ResourceGroup --type connection-strings --query "connectionStrings[0].connectionString" -o tsv)
$acsConn    = (az communication list-key --name $acsName --resource-group $ResourceGroup --query "primaryConnectionString" -o tsv)

az keyvault secret set --vault-name $keyVaultName --name "cosmos-connection-string" --value $cosmosConn --output none
az keyvault secret set --vault-name $keyVaultName --name "acs-connection-string" --value $acsConn --output none
Write-Host "    cosmos-connection-string set" -ForegroundColor Green
Write-Host "    acs-connection-string    set" -ForegroundColor Green

$manualSecrets = @(
    @{ Name = "openai-api-key";           Prompt = "OpenAI API key" },
    @{ Name = "investec-client-id";       Prompt = "Investec Client ID" },
    @{ Name = "investec-client-secret";   Prompt = "Investec Client Secret" },
    @{ Name = "investec-api-key";         Prompt = "Investec API key (x-api-key)" },
    @{ Name = "twilio-account-sid";       Prompt = "Twilio Account SID" },
    @{ Name = "twilio-auth-token";        Prompt = "Twilio Auth Token" },
    @{ Name = "twilio-whatsapp-number";   Prompt = "Twilio WhatsApp number (e.g. +1415XXXXXXX)" },
    @{ Name = "email-recipient-address";  Prompt = "Your email address (report recipient)" }
)

foreach ($secret in $manualSecrets) {
    $existing = az keyvault secret show --vault-name $keyVaultName --name $secret.Name --query value -o tsv 2>$null
    if ($existing) {
        Write-Host "    $($secret.Name) already set" -ForegroundColor Green
        continue
    }

    $value = Read-Host -Prompt "    Enter $($secret.Prompt)" -AsSecureString
    $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($value)
    )
    az keyvault secret set --vault-name $keyVaultName --name $secret.Name --value $plain --output none
    Write-Host "    $($secret.Name) set" -ForegroundColor Green
}

Write-Host "`n[6/8] Building and pushing container image with ACR Tasks..." -ForegroundColor Cyan
$imageName = "krabs:$ImageTag"
$image = "$acrLoginServer/$imageName"
az acr build --registry $acrName --image $imageName "$PSScriptRoot\.." --output none
Write-Host "    Built: $image" -ForegroundColor Green

Write-Host "`n[7/8] Applying runtime secrets and container image..." -ForegroundColor Cyan
$deployOutput = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file "$PSScriptRoot\main.bicep" `
    --parameters appName=$AppName location=$Location appEnvironment=$AppEnvironment investecSandbox=$($InvestecSandbox.ToString().ToLower()) deployingUserObjectId=$deployingUserObjectId containerImage=$image configureRuntimeSecrets=true otelMode=$OtelMode otelServiceName=$OtelServiceName otelExporterOtlpEndpoint=$OtelExporterOtlpEndpoint otelResourceAttributes=$OtelResourceAttributes otelTracesSampler=$OtelTracesSampler otelTracesSamplerArg=$OtelTracesSamplerArg `
    --query properties.outputs `
    --output json | ConvertFrom-Json

$containerAppUrl = $deployOutput.containerAppUrl.value
Write-Host "    Runtime configuration applied." -ForegroundColor Green

Write-Host "`n[8/8] Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Container App URL : $containerAppUrl" -ForegroundColor White
Write-Host "  Webhook endpoint  : $containerAppUrl/webhook" -ForegroundColor White
Write-Host "  Legacy alias      : $containerAppUrl/api/webhook" -ForegroundColor White
Write-Host ""
Write-Host "  Next step: configure the webhook URL in your Twilio WhatsApp sandbox." -ForegroundColor Yellow

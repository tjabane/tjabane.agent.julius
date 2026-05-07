# Julius — Azure infrastructure deployment script
# Usage: .\infra\deploy.ps1 -ResourceGroup "rg-julius" -Location "southafricanorth"

param(
    [Parameter(Mandatory)]
    [string]$ResourceGroup,

    [string]$Location = "southafricanorth",

    [string]$AppName = "julius",

    [string]$AppEnvironment = "dev",

    [bool]$InvestecSandbox = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── 1. Login check ────────────────────────────────────────────────────────────
Write-Host "`n[1/6] Checking Azure login..." -ForegroundColor Cyan
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Not logged in. Running az login..." -ForegroundColor Yellow
    az login
    $account = az account show | ConvertFrom-Json
}
Write-Host "    Subscription: $($account.name)" -ForegroundColor Green

# ── 2. Resource group ─────────────────────────────────────────────────────────
Write-Host "`n[2/6] Ensuring resource group '$ResourceGroup'..." -ForegroundColor Cyan
az group create --name $ResourceGroup --location $Location --output none
Write-Host "    Ready." -ForegroundColor Green

# ── 3. Get deploying user object ID ───────────────────────────────────────────
$deployingUserObjectId = (az ad signed-in-user show --query id -o tsv)

# ── 4. Deploy Bicep ───────────────────────────────────────────────────────────
Write-Host "`n[3/6] Deploying Bicep template..." -ForegroundColor Cyan
$deployOutput = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file "$PSScriptRoot\main.bicep" `
    --parameters appName=$AppName location=$Location appEnvironment=$AppEnvironment investecSandbox=$($InvestecSandbox.ToString().ToLower()) deployingUserObjectId=$deployingUserObjectId `
    --query properties.outputs `
    --output json | ConvertFrom-Json

$keyVaultName     = $deployOutput.keyVaultName.value
$cosmosAccount    = $deployOutput.cosmosAccountName.value
$acsName          = $deployOutput.acsName.value
$functionAppUrl   = $deployOutput.functionAppUrl.value

Write-Host "    Function App : $functionAppUrl" -ForegroundColor Green
Write-Host "    Key Vault    : $keyVaultName" -ForegroundColor Green

# ── 5. Populate Key Vault secrets ─────────────────────────────────────────────
Write-Host "`n[4/6] Populating Key Vault secrets..." -ForegroundColor Cyan

# Auto-populate connection strings from deployed resources
$cosmosConn = (az cosmosdb keys list --name $cosmosAccount --resource-group $ResourceGroup --type connection-strings --query "connectionStrings[0].connectionString" -o tsv)
$acsConn    = (az communication list-key --name $acsName --resource-group $ResourceGroup --query "primaryConnectionString" -o tsv)

az keyvault secret set --vault-name $keyVaultName --name "cosmos-connection-string" --value $cosmosConn --output none
az keyvault secret set --vault-name $keyVaultName --name "acs-connection-string"    --value $acsConn    --output none
Write-Host "    cosmos-connection-string  set" -ForegroundColor Green
Write-Host "    acs-connection-string     set" -ForegroundColor Green

# Prompt for secrets that must be provided manually
$manualSecrets = @(
    @{ Name = "openai-api-key";           Prompt = "OpenAI API key" }
    @{ Name = "investec-client-id";      Prompt = "Investec Client ID" }
    @{ Name = "investec-client-secret";  Prompt = "Investec Client Secret" }
    @{ Name = "investec-api-key";        Prompt = "Investec API key (x-api-key)" }
    @{ Name = "twilio-account-sid";      Prompt = "Twilio Account SID" }
    @{ Name = "twilio-auth-token";       Prompt = "Twilio Auth Token" }
    @{ Name = "twilio-whatsapp-number";  Prompt = "Twilio WhatsApp number (e.g. +1415XXXXXXX)" }
    @{ Name = "email-recipient-address"; Prompt = "Your email address (report recipient)" }
)

foreach ($secret in $manualSecrets) {
    $value = Read-Host -Prompt "    Enter $($secret.Prompt)" -AsSecureString
    $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($value)
    )
    az keyvault secret set --vault-name $keyVaultName --name $secret.Name --value $plain --output none
    Write-Host "    $($secret.Name)  set" -ForegroundColor Green
}

# ── 6. Done ───────────────────────────────────────────────────────────────────
Write-Host "`n[5/6] Restarting Function App to pick up Key Vault references..." -ForegroundColor Cyan
$funcAppName = (az functionapp list --resource-group $ResourceGroup --query "[0].name" -o tsv)
az functionapp restart --name $funcAppName --resource-group $ResourceGroup --output none
Write-Host "    Restarted." -ForegroundColor Green

Write-Host "`n[6/6] Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Function App URL : $functionAppUrl" -ForegroundColor White
Write-Host "  Webhook endpoint : $functionAppUrl/api/webhook" -ForegroundColor White
Write-Host ""
Write-Host "  Next step: configure this webhook URL in your Twilio WhatsApp sandbox." -ForegroundColor Yellow

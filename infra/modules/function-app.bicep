param appName string
param location string
param storageAccountName string
param appInsightsConnectionString string
param keyVaultName string
param investecSandbox bool
param emailSenderAddress string

var planName = 'asp-${appName}'
var funcAppName = 'func-${appName}-${uniqueString(resourceGroup().id)}'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-04-01' existing = {
  name: storageAccountName
}

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: planName
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: funcAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.12'
      pythonVersion: '3.12'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        // Non-sensitive config
        {
          name: 'INVESTEC_SANDBOX'
          value: string(investecSandbox)
        }
        {
          name: 'COSMOS_DATABASE'
          value: 'julius'
        }
        {
          name: 'EMAIL_SENDER_ADDRESS'
          value: emailSenderAddress
        }
        // Key Vault references — secrets must be populated post-deploy
        {
          name: 'ANTHROPIC_API_KEY'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=anthropic-api-key)'
        }
        {
          name: 'INVESTEC_CLIENT_ID'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=investec-client-id)'
        }
        {
          name: 'INVESTEC_CLIENT_SECRET'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=investec-client-secret)'
        }
        {
          name: 'INVESTEC_API_KEY'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=investec-api-key)'
        }
        {
          name: 'TWILIO_ACCOUNT_SID'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=twilio-account-sid)'
        }
        {
          name: 'TWILIO_AUTH_TOKEN'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=twilio-auth-token)'
        }
        {
          name: 'TWILIO_WHATSAPP_NUMBER'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=twilio-whatsapp-number)'
        }
        {
          name: 'COSMOS_CONNECTION_STRING'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=cosmos-connection-string)'
        }
        {
          name: 'AZURE_COMMUNICATION_CONNECTION_STRING'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=acs-connection-string)'
        }
        {
          name: 'EMAIL_RECIPIENT_ADDRESS'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=email-recipient-address)'
        }
      ]
    }
  }
}

output url string = 'https://${functionApp.properties.defaultHostName}'
output principalId string = functionApp.identity.principalId
output name string = functionApp.name

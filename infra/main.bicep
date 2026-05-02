@description('Base name used to derive all resource names')
param appName string = 'julius'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Use Investec sandbox API')
param investecSandbox bool = true

@description('Object ID of the deploying user — grants Key Vault Secrets Officer for secret population')
param deployingUserObjectId string = ''

var suffix = uniqueString(resourceGroup().id)

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    name: 'st${appName}${suffix}'
    location: location
  }
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    appName: appName
    location: location
  }
}

module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos'
  params: {
    accountName: 'cosmos-${appName}-${suffix}'
    location: location
  }
}

module communication 'modules/communication.bicep' = {
  name: 'communication'
  params: {
    acsName: 'acs-${appName}-${suffix}'
    emailServiceName: 'email-${appName}-${suffix}'
    dataLocation: 'UnitedStates'
  }
}

module keyvault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    name: 'kv-${appName}-${suffix}'
    location: location
    deployingUserObjectId: deployingUserObjectId
  }
}

module functionApp 'modules/function-app.bicep' = {
  name: 'functionApp'
  params: {
    appName: appName
    location: location
    storageAccountName: storage.outputs.name
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    keyVaultName: keyvault.outputs.name
    investecSandbox: investecSandbox
    emailSenderAddress: communication.outputs.senderAddress
  }
}

module keyvaultRoleAssignment 'modules/keyvault.bicep' = {
  name: 'keyvaultFunctionAccess'
  params: {
    name: keyvault.outputs.name
    location: location
    deployingUserObjectId: deployingUserObjectId
    functionAppPrincipalId: functionApp.outputs.principalId
  }
}

output functionAppUrl string = functionApp.outputs.url
output keyVaultName string = keyvault.outputs.name
output cosmosConnectionStringSecretCmd string = 'az keyvault secret set --vault-name ${keyvault.outputs.name} --name cosmos-connection-string --value "<from cosmos module>"'
output cosmosAccountName string = cosmos.outputs.accountName
output acsName string = communication.outputs.acsName

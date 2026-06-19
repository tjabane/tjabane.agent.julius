@description('Base name used to derive all resource names')
param appName string = 'krabs'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Use Investec sandbox API')
param investecSandbox bool = true

@description('Runtime environment name exposed to the Container App')
param appEnvironment string = 'dev'

@description('Object ID of the deploying user - grants Key Vault Secrets Officer for secret population')
param deployingUserObjectId string = ''

@description('Initial container image. The deploy script updates this to the image built in this repo.')
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Configure runtime Key Vault secret references and secret-backed environment variables.')
param configureRuntimeSecrets bool = false

@description('OpenTelemetry mode: disabled, console, or otlp.')
param otelMode string = 'disabled'

@description('OpenTelemetry service name.')
param otelServiceName string = 'mr-krabs'

@description('Optional OTLP endpoint, for example http://otel-collector:4317.')
param otelExporterOtlpEndpoint string = ''

@description('Additional comma-separated OpenTelemetry resource attributes.')
param otelResourceAttributes string = ''

@description('OpenTelemetry trace sampler.')
param otelTracesSampler string = 'parentbased_traceidratio'

@description('OpenTelemetry trace sampler argument.')
param otelTracesSamplerArg string = '1.0'

var suffix = take(uniqueString(resourceGroup().id), 8)
var safeAppName = replace(appName, '-', '')

// Storage: max 24, lowercase alphanumeric only
var storageAccountName = 'st${take(safeAppName, 14)}${suffix}'

// Key Vault: max 24, alphanumeric + hyphens, no consecutive hyphens
var keyVaultName = 'kv-${take(safeAppName, 11)}-${suffix}'
var runtimeIdentityName = 'id-${appName}-${suffix}'

resource runtimeIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: runtimeIdentityName
  location: location
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    name: storageAccountName
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
    name: keyVaultName
    location: location
    deployingUserObjectId: deployingUserObjectId
    runtimePrincipalId: runtimeIdentity.properties.principalId
  }
}

module containerApp 'modules/container-app.bicep' = {
  name: 'containerApp'
  params: {
    appName: appName
    location: location
    keyVaultName: keyvault.outputs.name
    userAssignedIdentityId: runtimeIdentity.id
    investecSandbox: investecSandbox
    appEnvironment: appEnvironment
    emailSenderAddress: communication.outputs.senderAddress
    containerImage: containerImage
    configureRuntimeSecrets: configureRuntimeSecrets
    otelMode: otelMode
    otelServiceName: otelServiceName
    otelExporterOtlpEndpoint: otelExporterOtlpEndpoint
    otelResourceAttributes: otelResourceAttributes
    otelTracesSampler: otelTracesSampler
    otelTracesSamplerArg: otelTracesSamplerArg
  }
}

output containerAppUrl string = containerApp.outputs.url
output keyVaultName string = keyvault.outputs.name
output cosmosAccountName string = cosmos.outputs.accountName
output acsName string = communication.outputs.acsName
output emailSenderAddress string = communication.outputs.senderAddress
output containerAppName string = containerApp.outputs.name
output containerAppsEnvironmentName string = containerApp.outputs.environmentName
output acrName string = containerApp.outputs.acrName
output acrLoginServer string = containerApp.outputs.acrLoginServer

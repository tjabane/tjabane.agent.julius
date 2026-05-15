param appName string
param location string
param keyVaultName string
param userAssignedIdentityId string
param userAssignedIdentityPrincipalId string
param investecSandbox bool
param appEnvironment string
param emailSenderAddress string
param containerImage string
param configureRuntimeSecrets bool = false
param minReplicas int = 1
param maxReplicas int = 1

var environmentName = 'cae-${appName}-${uniqueString(resourceGroup().id)}'
var containerAppName = 'ca-${appName}-${uniqueString(resourceGroup().id)}'
var acrName = 'acr${replace(take(appName, 12), '-', '')}${take(uniqueString(resourceGroup().id), 8)}'
var keyVaultBaseUrl = 'https://${keyVaultName}${az.environment().suffixes.keyvaultDns}/secrets'
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
}

resource acrPullAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, userAssignedIdentityPrincipalId, acrPullRoleId)
  scope: registry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
    principalId: userAssignedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: registry.properties.loginServer
          identity: userAssignedIdentityId
        }
      ]
      secrets: configureRuntimeSecrets ? [
        {
          name: 'openai-api-key'
          keyVaultUrl: '${keyVaultBaseUrl}/openai-api-key'
          identity: userAssignedIdentityId
        }
        {
          name: 'investec-client-id'
          keyVaultUrl: '${keyVaultBaseUrl}/investec-client-id'
          identity: userAssignedIdentityId
        }
        {
          name: 'investec-client-secret'
          keyVaultUrl: '${keyVaultBaseUrl}/investec-client-secret'
          identity: userAssignedIdentityId
        }
        {
          name: 'investec-api-key'
          keyVaultUrl: '${keyVaultBaseUrl}/investec-api-key'
          identity: userAssignedIdentityId
        }
        {
          name: 'twilio-account-sid'
          keyVaultUrl: '${keyVaultBaseUrl}/twilio-account-sid'
          identity: userAssignedIdentityId
        }
        {
          name: 'twilio-auth-token'
          keyVaultUrl: '${keyVaultBaseUrl}/twilio-auth-token'
          identity: userAssignedIdentityId
        }
        {
          name: 'twilio-whatsapp-number'
          keyVaultUrl: '${keyVaultBaseUrl}/twilio-whatsapp-number'
          identity: userAssignedIdentityId
        }
        {
          name: 'cosmos-connection-string'
          keyVaultUrl: '${keyVaultBaseUrl}/cosmos-connection-string'
          identity: userAssignedIdentityId
        }
        {
          name: 'acs-connection-string'
          keyVaultUrl: '${keyVaultBaseUrl}/acs-connection-string'
          identity: userAssignedIdentityId
        }
        {
          name: 'email-recipient-address'
          keyVaultUrl: '${keyVaultBaseUrl}/email-recipient-address'
          identity: userAssignedIdentityId
        }
      ] : []
    }
    template: {
      containers: [
        {
          name: 'krabs'
          image: containerImage
          env: concat([
            {
              name: 'APP_ENV'
              value: appEnvironment
            }
            {
              name: 'COMMUNICATION_PROVIDER'
              value: 'external'
            }
            {
              name: 'INVESTEC_SANDBOX'
              value: string(investecSandbox)
            }
            {
              name: 'COSMOS_DATABASE'
              value: 'krabs'
            }
            {
              name: 'EMAIL_SENDER_ADDRESS'
              value: emailSenderAddress
            }
            {
              name: 'SCHEDULER_ENABLED'
              value: 'true'
            }
            {
              name: 'SCHEDULER_INTERVAL_SECONDS'
              value: '300'
            }
          ], configureRuntimeSecrets ? [
            {
              name: 'OPENAI_API_KEY'
              secretRef: 'openai-api-key'
            }
            {
              name: 'INVESTEC_CLIENT_ID'
              secretRef: 'investec-client-id'
            }
            {
              name: 'INVESTEC_CLIENT_SECRET'
              secretRef: 'investec-client-secret'
            }
            {
              name: 'INVESTEC_API_KEY'
              secretRef: 'investec-api-key'
            }
            {
              name: 'TWILIO_ACCOUNT_SID'
              secretRef: 'twilio-account-sid'
            }
            {
              name: 'TWILIO_AUTH_TOKEN'
              secretRef: 'twilio-auth-token'
            }
            {
              name: 'TWILIO_WHATSAPP_NUMBER'
              secretRef: 'twilio-whatsapp-number'
            }
            {
              name: 'COSMOS_CONNECTION_STRING'
              secretRef: 'cosmos-connection-string'
            }
            {
              name: 'AZURE_COMMUNICATION_CONNECTION_STRING'
              secretRef: 'acs-connection-string'
            }
            {
              name: 'EMAIL_RECIPIENT_ADDRESS'
              secretRef: 'email-recipient-address'
            }
          ] : [])
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
  dependsOn: [
    acrPullAssignment
  ]
}

output url string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output name string = containerApp.name
output environmentName string = environment.name
output acrName string = registry.name
output acrLoginServer string = registry.properties.loginServer

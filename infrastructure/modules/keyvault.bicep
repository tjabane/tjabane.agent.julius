param name string
param location string
param deployingUserObjectId string = ''
param runtimePrincipalId string = ''

var deployerAccessPolicies = !empty(deployingUserObjectId) ? [
  {
    tenantId: subscription().tenantId
    objectId: deployingUserObjectId
    permissions: {
      secrets: [
        'get'
        'list'
        'set'
        'delete'
      ]
    }
  }
] : []

var runtimeAccessPolicies = !empty(runtimePrincipalId) ? [
  {
    tenantId: subscription().tenantId
    objectId: runtimePrincipalId
    permissions: {
      secrets: [
        'get'
        'list'
      ]
    }
  }
] : []

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: false
    accessPolicies: concat(deployerAccessPolicies, runtimeAccessPolicies)
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

output name string = keyVault.name
output uri string = keyVault.properties.vaultUri

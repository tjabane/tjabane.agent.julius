param acsName string
param emailServiceName string

@allowed(['UnitedStates', 'Europe', 'Asia'])
param dataLocation string = 'UnitedStates'

resource emailService 'Microsoft.Communication/emailServices@2023-04-01' = {
  name: emailServiceName
  location: 'global'
  properties: {
    dataLocation: dataLocation
  }
}

resource domain 'Microsoft.Communication/emailServices/domains@2023-04-01' = {
  parent: emailService
  name: 'AzureManagedDomain'
  location: 'global'
  properties: {
    domainManagement: 'AzureManaged'
  }
}

resource communicationService 'Microsoft.Communication/communicationServices@2023-04-01' = {
  name: acsName
  location: 'global'
  properties: {
    dataLocation: dataLocation
    linkedDomains: [ domain.id ]
  }
}

output acsName string = communicationService.name
output senderAddress string = 'DoNotReply@${domain.properties.mailFromSenderDomain}'

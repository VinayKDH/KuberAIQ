@description('Environment name (dev, staging, prod)')
param environmentName string = 'prod'

@description('Azure region')
param location string = resourceGroup().location

@description('API App Service name')
param apiAppName string = 'vyaparai-api'

@description('Web App Service name')
param webAppName string = 'vyaparai-web'

@description('PostgreSQL admin login')
@secure()
param postgresAdminLogin string

@description('PostgreSQL admin password')
@secure()
param postgresAdminPassword string

@description('PostgreSQL server name (must be globally unique)')
param postgresServerName string = 'vyaparai-pg-${environmentName}'

@description('Storage account name (3-24 lowercase alphanumeric, globally unique)')
param storageAccountName string = 'vyaparai${uniqueString(resourceGroup().id)}'

@description('Key Vault name (3-24 alphanumeric, globally unique)')
param keyVaultName string = 'kv-vyaparai-${environmentName}'

var appServicePlanName = 'asp-vyaparai-${environmentName}'
var postgresDbName = 'vyaparai'
var blobContainerName = 'invoices'

// --- App Service Plan (Linux) ---
resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: environmentName == 'prod' ? 'P1v3' : 'B1'
    tier: environmentName == 'prod' ? 'PremiumV3' : 'Basic'
    capacity: environmentName == 'prod' ? 2 : 1
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// --- Key Vault ---
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
  }
}

// --- Storage Account (Blob) ---
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: environmentName == 'prod' ? 'Standard_GRS' : 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 30
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 30
    }
  }
}

resource invoicesContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: blobContainerName
  properties: {
    publicAccess: 'None'
  }
}

// --- PostgreSQL Flexible Server ---
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: postgresServerName
  location: location
  sku: {
    name: environmentName == 'prod' ? 'Standard_D2s_v3' : 'Standard_B1ms'
    tier: environmentName == 'prod' ? 'GeneralPurpose' : 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    storage: {
      storageSizeGB: environmentName == 'prod' ? 128 : 32
    }
    backup: {
      backupRetentionDays: environmentName == 'prod' ? 35 : 7
      geoRedundantBackup: environmentName == 'prod' ? 'Enabled' : 'Disabled'
    }
    highAvailability: {
      mode: environmentName == 'prod' ? 'ZoneRedundant' : 'Disabled'
    }
  }
}

resource postgresDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  parent: postgresServer
  name: postgresDbName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// --- Application Insights (referenced by App Service settings) ---
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'law-vyaparai-${environmentName}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-vyaparai-${environmentName}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// --- API Web App ---
resource apiApp 'Microsoft.Web/sites@2023-12-01' = {
  name: apiAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${apiAppName}:latest'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'ENVIRONMENT'
          value: environmentName
        }
        {
          name: 'USE_MOCK_LLM'
          value: 'false'
        }
        {
          name: 'USE_MOCK_BLOB'
          value: 'false'
        }
        {
          name: 'USE_MOCK_WHATSAPP'
          value: 'false'
        }
        {
          name: 'USE_MOCK_AUTH'
          value: 'false'
        }
        {
          name: 'AZURE_BLOB_CONTAINER'
          value: blobContainerName
        }
        {
          name: 'DATABASE_URL'
          value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/database-url/)'
        }
        {
          name: 'JWT_SECRET'
          value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/jwt-secret/)'
        }
        {
          name: 'AZURE_BLOB_CONNECTION_STRING'
          value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/blob-connection-string/)'
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/openai-api-key/)'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
      ]
    }
  }
}

// --- Web (frontend) App Service ---
resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: webAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${webAppName}:latest'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'NEXT_PUBLIC_API_URL'
          value: 'https://${apiAppName}.azurewebsites.net'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
      ]
    }
  }
}

// --- Outputs ---
output apiAppUrl string = 'https://${apiApp.properties.defaultHostName}'
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output keyVaultUri string = keyVault.properties.vaultUri
output keyVaultName string = keyVault.name
output storageAccountName string = storageAccount.name
output postgresServerFqdn string = postgresServer.properties.fullyQualifiedDomainName
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output apiManagedIdentityPrincipalId string = apiApp.identity.principalId

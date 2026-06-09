@description('Environment name (dev, staging, prod)')
param environmentName string = 'dev'

@description('Azure region for compute, storage, and networking')
param location string = resourceGroup().location

@description('Azure region for PostgreSQL (may differ when subscription has regional quotas)')
param postgresLocation string = 'centralindia'

@description('Short unique suffix for globally unique resource names')
param nameSuffix string = uniqueString(resourceGroup().id)

@description('PostgreSQL admin login')
@secure()
param postgresAdminLogin string

@description('PostgreSQL admin password')
@secure()
param postgresAdminPassword string

@description('JWT signing secret')
@secure()
param jwtSecret string

@description('Azure OpenAI API key (set via deploy script or CI secret)')
@secure()
param openaiApiKey string

@description('WhatsApp verify token')
param whatsappVerifyToken string = 'kuberaiq-verify'

@description('Google OAuth client ID (Web application)')
param googleClientId string = ''

@description('Google OAuth client secret')
@secure()
param googleClientSecret string = ''

@description('Microsoft Entra tenant ID')
param entraTenantId string = ''

@description('Microsoft Entra application client ID')
param entraClientId string = ''

@description('Microsoft Entra client secret')
@secure()
param entraClientSecret string = ''

@description('Public hostname for the Next.js web app (must be globally unique)')
param webAppHostName string = environmentName == 'prod' ? 'kuberaiq-web-prod' : 'kuberaiq-web-${environmentName}'

@description('Public hostname for the FastAPI app (must be globally unique)')
param apiAppHostName string = environmentName == 'prod' ? 'kuberaiq-api-prod' : 'kuberaiq-api-${environmentName}'

var appServicePlanName = 'asp-kuberaiq-${environmentName}'
var postgresDbName = 'kuberaiq'
var blobContainerName = 'invoices'
var apiAppName = apiAppHostName
var webAppName = webAppHostName
var postgresServerName = 'kuberaiq-pg-${nameSuffix}'
var storageAccountName = 'kuberaiq${nameSuffix}'
var keyVaultName = 'kv-kuberaiq-${take(nameSuffix, 8)}'
var acrName = 'kuberaiq${take(nameSuffix, 10)}'
var databaseUrl = 'postgresql+asyncpg://${postgresAdminLogin}:${postgresAdminPassword}@${postgresServer.properties.fullyQualifiedDomainName}:5432/${postgresDbName}?ssl=require'

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

// --- Container Registry ---
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: environmentName == 'prod' ? 'Standard' : 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
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

resource databaseUrlSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'database-url'
  properties: {
    value: databaseUrl
  }
}

resource jwtSecretKv 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'jwt-secret'
  properties: {
    value: jwtSecret
  }
}

resource blobConnectionSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'blob-connection-string'
  properties: {
    value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
  }
}

resource openaiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'openai-api-key'
  properties: {
    value: openaiApiKey
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
  location: postgresLocation
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
      mode: 'Disabled'
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

resource postgresFirewallAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-12-01-preview' = {
  parent: postgresServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

resource postgresPgcrypto 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-12-01-preview' = {
  parent: postgresServer
  name: 'azure.extensions'
  properties: {
    value: 'pgcrypto'
    source: 'user-override'
  }
}

// --- Monitoring ---
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'law-kuberaiq-${environmentName}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-kuberaiq-${environmentName}'
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
      linuxFxVersion: 'DOCKER|${acr.properties.loginServer}/kuberaiq-api:latest'
      acrUseManagedIdentityCreds: true
      alwaysOn: environmentName != 'dev'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        { name: 'ENVIRONMENT', value: environmentName }
        { name: 'USE_MOCK_LLM', value: environmentName == 'prod' ? 'false' : 'true' }
        { name: 'USE_MOCK_BLOB', value: environmentName == 'prod' ? 'false' : 'true' }
        { name: 'USE_MOCK_WHATSAPP', value: environmentName == 'prod' ? 'false' : 'true' }
        { name: 'USE_MOCK_AUTH', value: environmentName == 'prod' ? 'false' : 'true' }
        { name: 'AZURE_BLOB_CONTAINER', value: blobContainerName }
        { name: 'WEBSITES_PORT', value: '8000' }
        { name: 'DATABASE_URL', value: '@Microsoft.KeyVault(SecretUri=${databaseUrlSecret.properties.secretUriWithVersion})' }
        { name: 'JWT_SECRET', value: '@Microsoft.KeyVault(SecretUri=${jwtSecretKv.properties.secretUriWithVersion})' }
        { name: 'AZURE_BLOB_CONNECTION_STRING', value: '@Microsoft.KeyVault(SecretUri=${blobConnectionSecret.properties.secretUriWithVersion})' }
        { name: 'AZURE_OPENAI_API_KEY', value: '@Microsoft.KeyVault(SecretUri=${openaiKeySecret.properties.secretUriWithVersion})' }
        { name: 'WHATSAPP_VERIFY_TOKEN', value: whatsappVerifyToken }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
        { name: 'CORS_ORIGINS', value: '["https://${webAppName}.azurewebsites.net"]' }
        { name: 'GOOGLE_CLIENT_ID', value: googleClientId }
        { name: 'GOOGLE_CLIENT_SECRET', value: googleClientSecret }
        { name: 'ENTRA_TENANT_ID', value: entraTenantId }
        { name: 'ENTRA_CLIENT_ID', value: entraClientId }
        { name: 'ENTRA_CLIENT_SECRET', value: entraClientSecret }
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
      linuxFxVersion: 'DOCKER|${acr.properties.loginServer}/kuberaiq-web:latest'
      acrUseManagedIdentityCreds: true
      alwaysOn: environmentName != 'dev'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        { name: 'NEXT_PUBLIC_API_URL', value: 'https://${apiAppName}.azurewebsites.net' }
        { name: 'NEXT_PUBLIC_USE_MOCK_AUTH', value: environmentName == 'prod' ? 'false' : 'true' }
        { name: 'NEXT_PUBLIC_GOOGLE_CLIENT_ID', value: googleClientId }
        { name: 'NEXT_PUBLIC_GOOGLE_REDIRECT_URI', value: 'https://${webAppName}.azurewebsites.net/auth/callback' }
        { name: 'NEXT_PUBLIC_ENTRA_CLIENT_ID', value: entraClientId }
        { name: 'NEXT_PUBLIC_ENTRA_TENANT_ID', value: entraTenantId }
        { name: 'NEXT_PUBLIC_ENTRA_REDIRECT_URI', value: 'https://${webAppName}.azurewebsites.net/auth/callback' }
        { name: 'WEBSITES_PORT', value: '3000' }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
      ]
    }
  }
}

// --- RBAC: API → Key Vault Secrets User ---
resource apiKvRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, apiApp.id, 'kv-secrets-user')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: apiApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// --- RBAC: Apps → ACR Pull ---
resource apiAcrRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, apiApp.id, 'acr-pull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: apiApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource webAcrRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, webApp.id, 'acr-pull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: webApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// --- Outputs ---
output apiAppName string = apiApp.name
output webAppName string = webApp.name
output apiAppUrl string = 'https://${apiApp.properties.defaultHostName}'
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output acrLoginServer string = acr.properties.loginServer
output acrName string = acr.name
output keyVaultUri string = keyVault.properties.vaultUri
output keyVaultName string = keyVault.name
output storageAccountName string = storageAccount.name
output postgresServerFqdn string = postgresServer.properties.fullyQualifiedDomainName
output appInsightsConnectionString string = appInsights.properties.ConnectionString

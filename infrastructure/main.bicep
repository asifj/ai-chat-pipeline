// Azure Container Apps Infrastructure (Free Tier Optimized)
// Provisions: Container App Environment, Container App Job, and managed identity

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Unique suffix for resource names')
param uniqueSuffix string = uniqueString(resourceGroup().id)

@description('Container image to deploy')
param containerImage string = 'ghcr.io/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:latest'

@description('Gemini API Key')
@secure()
param geminiApiKey string

@description('Dropbox Refresh Token')
@secure()
param dropboxRefreshToken string

@description('Dropbox App Key')
@secure()
param dropboxAppKey string

@description('Dropbox App Secret')
@secure()
param dropboxAppSecret string

@description('Source directory in Dropbox')
param sourceRoot string = '/AI_logs'

@description('Output directory in Dropbox')
param outputRoot string = '/Obsidian/AI_Chats'

@description('Max files to process per run')
param maxFiles string = '50'

// Container Apps Environment (shared infrastructure)
resource environment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'ai-chat-env-${uniqueSuffix}'
  location: location
  properties: {
    // Free tier: Consumption-only workload profiles
    workloadProfiles: []
    zoneRedundant: false
  }
}

// Container App Job (runs on schedule)
resource containerAppJob 'Microsoft.App/jobs@2023-05-01' = {
  name: 'ai-chat-pipeline-job'
  location: location
  properties: {
    environmentId: environment.id
    configuration: {
      // Manual or scheduled trigger
      triggerType: 'Schedule'
      // Runs every 6 hours
      scheduleTriggerConfig: {
        cronExpression: '0 */6 * * *'
        parallelism: 1
        replicaCompletionCount: 1
      }
      replicaTimeout: 1800 // 30 minutes max runtime
      replicaRetryLimit: 1
      
      // Container registry (GitHub Container Registry - free)
      registries: []
      
      secrets: [
        {
          name: 'gemini-api-key'
          value: geminiApiKey
        }
        {
          name: 'dropbox-refresh-token'
          value: dropboxRefreshToken
        }
        {
          name: 'dropbox-app-key'
          value: dropboxAppKey
        }
        {
          name: 'dropbox-app-secret'
          value: dropboxAppSecret
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'ai-chat-pipeline'
          image: containerImage
          env: [
            {
              name: 'GEMINI_API_KEY'
              secretRef: 'gemini-api-key'
            }
            {
              name: 'DROPBOX_REFRESH_TOKEN'
              secretRef: 'dropbox-refresh-token'
            }
            {
              name: 'DROPBOX_APP_KEY'
              secretRef: 'dropbox-app-key'
            }
            {
              name: 'DROPBOX_APP_SECRET'
              secretRef: 'dropbox-app-secret'
            }
            {
              name: 'SOURCE_ROOT'
              value: sourceRoot
            }
            {
              name: 'OUTPUT_ROOT'
              value: outputRoot
            }
            {
              name: 'MAX_FILES'
              value: maxFiles
            }
          ]
          resources: {
            // Free tier limits: 0.25 CPU, 0.5 GB RAM
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
    }
  }
}

// Outputs for reference
output environmentName string = environment.name
output jobName string = containerAppJob.name
output environmentId string = environment.id

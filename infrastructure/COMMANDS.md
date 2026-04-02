# Azure Commands Cheat Sheet

## Quick Actions

### Deploy Everything
```bash
# Via GitHub Actions (recommended)
git push origin main

# Via Azure CLI
az deployment group create \
  --resource-group ai-chat-pipeline-rg \
  --template-file infrastructure/main.bicep \
  --parameters @infrastructure/parameters.filled.json
```

### Run Job Manually
```bash
az containerapp job start \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg
```

### View Logs (Live)
```bash
az containerapp job logs show \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --follow
```

### Check Job Status
```bash
az containerapp job show \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --query "{name:name,state:properties.provisioningState,schedule:properties.configuration.scheduleTriggerConfig.cronExpression}"
```

### List Executions
```bash
az containerapp job execution list \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --output table
```

### View Specific Execution Logs
```bash
# Get latest execution name
EXECUTION=$(az containerapp job execution list \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --query "[0].name" -o tsv)

# View its logs
az containerapp job logs show \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --execution-name $EXECUTION
```

## Configuration Changes

### Update Schedule
```bash
# Edit main.bicep, change line:
# cronExpression: '0 */12 * * *'  # Every 12 hours

# Redeploy
az deployment group create \
  --resource-group ai-chat-pipeline-rg \
  --template-file infrastructure/main.bicep \
  --parameters containerImage="ghcr.io/YOUR_USER/YOUR_REPO:latest"
```

### Update Environment Variables
```bash
az containerapp job update \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --set-env-vars "MAX_FILES=100"
```

### Update Secrets
```bash
az containerapp job update \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --secrets "gemini-api-key=NEW_KEY_VALUE"
```

### Update Container Image
```bash
az containerapp job update \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --image "ghcr.io/YOUR_USER/YOUR_REPO:v2"
```

## Monitoring

### Check Resource Usage
```bash
az monitor metrics list \
  --resource /subscriptions/SUBSCRIPTION_ID/resourceGroups/ai-chat-pipeline-rg/providers/Microsoft.App/jobs/ai-chat-pipeline-job \
  --metric "WorkingSetBytes" \
  --start-time $(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ') \
  --interval PT5M
```

### View Cost Analysis
```bash
# Open in browser
az cost-management query \
  --scope "/subscriptions/$(az account show --query id -o tsv)" \
  --dataset-filter "{\"and\":[{\"dimensions\":{\"name\":\"ResourceGroupName\",\"operator\":\"In\",\"values\":[\"ai-chat-pipeline-rg\"]}}]}"
```

## Troubleshooting

### Validate Bicep Template
```bash
az bicep build --file infrastructure/main.bicep
```

### Test Deployment (What-If)
```bash
az deployment group what-if \
  --resource-group ai-chat-pipeline-rg \
  --template-file infrastructure/main.bicep \
  --parameters @infrastructure/parameters.filled.json
```

### Check Provider Registration
```bash
az provider show --namespace Microsoft.App --query "registrationState"
```

### Re-register Provider
```bash
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
```

## Cleanup

### Delete Job Only
```bash
az containerapp job delete \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --yes
```

### Delete Everything
```bash
az group delete \
  --name ai-chat-pipeline-rg \
  --yes \
  --no-wait
```

## Authentication

### Login
```bash
az login
```

### Set Subscription
```bash
az account set --subscription "SUBSCRIPTION_NAME_OR_ID"
```

### Create Service Principal (for GitHub Actions)
```bash
az ad sp create-for-rbac \
  --name "github-ai-chat-pipeline" \
  --role contributor \
  --scopes "/subscriptions/$(az account show --query id -o tsv)" \
  --sdk-auth
```

## Aliases (Add to ~/.zshrc or ~/.bashrc)

```bash
alias azjob-status="az containerapp job show --name ai-chat-pipeline-job --resource-group ai-chat-pipeline-rg --query '{name:name,state:properties.provisioningState}'"
alias azjob-start="az containerapp job start --name ai-chat-pipeline-job --resource-group ai-chat-pipeline-rg"
alias azjob-logs="az containerapp job logs show --name ai-chat-pipeline-job --resource-group ai-chat-pipeline-rg --follow"
alias azjob-list="az containerapp job execution list --name ai-chat-pipeline-job --resource-group ai-chat-pipeline-rg --output table"
```

Reload shell: `source ~/.zshrc`

Then use: `azjob-status`, `azjob-start`, `azjob-logs`, `azjob-list`

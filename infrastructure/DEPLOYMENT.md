# Azure Deployment Guide (Free Tier)

This guide walks you through deploying the AI Chat Pipeline to Azure Container Apps using the **free tier**.

## Free Tier Limits

Azure Container Apps free tier includes:
- **180,000 vCPU-seconds** per month
- **360,000 GiB-seconds** of memory per month
- Up to **1,000 job executions** per month

With our configuration (0.25 vCPU, 0.5 GB RAM, ~5 min runtime every 6 hours):
- **4 executions/day** = ~120/month
- **Resource usage**: 5 min × 0.25 vCPU = 75 vCPU-seconds per run
- **Monthly usage**: ~9,000 vCPU-seconds (well within free tier)

## Prerequisites

1. **Azure Account** - [Free account](https://azure.microsoft.com/free/) includes $200 credit
2. **Azure CLI** - Install from [docs.microsoft.com](https://docs.microsoft.com/cli/azure/install-azure-cli)
3. **GitHub Repository** - Your pipeline code
4. **Secrets ready**:
   - Gemini API key
   - Dropbox refresh token, app key, app secret

## Step 1: Azure Setup

### Login to Azure

```bash
az login
az account set --subscription "YOUR_SUBSCRIPTION_NAME_OR_ID"
```

### Create Service Principal for GitHub Actions

```bash
# Get your subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Create service principal
az ad sp create-for-rbac \
  --name "github-ai-chat-pipeline" \
  --role contributor \
  --scopes "/subscriptions/$SUBSCRIPTION_ID" \
  --sdk-auth

# Save the JSON output - you'll need these values:
# - clientId → AZURE_CLIENT_ID
# - clientSecret → AZURE_CLIENT_SECRET  
# - subscriptionId → AZURE_SUBSCRIPTION_ID
# - tenantId → AZURE_TENANT_ID
```

**IMPORTANT**: The `--sdk-auth` flag is deprecated but still works. For newer approach, use OIDC (more complex setup).

### Register Container Apps Provider

```bash
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
```

## Step 2: GitHub Secrets

Go to your GitHub repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `AZURE_CLIENT_ID` | From service principal JSON (clientId) |
| `AZURE_TENANT_ID` | From service principal JSON (tenantId) |
| `AZURE_SUBSCRIPTION_ID` | From service principal JSON (subscriptionId) |
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `DROPBOX_REFRESH_TOKEN` | From tools/get_dropbox_token.py |
| `DROPBOX_APP_KEY` | From tools/get_dropbox_token.py |
| `DROPBOX_APP_SECRET` | From tools/get_dropbox_token.py |

## Step 3: Update Configuration

### Edit `infrastructure/main.bicep`

No changes needed! The file is already configured for free tier.

### Edit `.github/workflows/azure-deploy.yml`

Replace `YOUR_GITHUB_USERNAME/YOUR_REPO_NAME` with your actual values:

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: asifj/ai-chat-pipeline  # ← Update this
```

## Step 4: Deploy

### Option A: Deploy via GitHub Actions (Recommended)

1. Push your code to `main` branch
2. Go to Actions tab → "Deploy to Azure Container Apps"
3. Click "Run workflow"

The workflow will:
1. Build Docker image
2. Push to GitHub Container Registry
3. Create Azure resource group
4. Deploy infrastructure (Container App Environment + Job)

### Option B: Deploy Manually from CLI

```bash
# 1. Build and push container locally (optional)
docker build -t ghcr.io/YOUR_USERNAME/ai-chat-pipeline:latest .
docker push ghcr.io/YOUR_USERNAME/ai-chat-pipeline:latest

# 2. Create resource group
az group create \
  --name ai-chat-pipeline-rg \
  --location eastus

# 3. Deploy infrastructure
# First, copy parameters.local.json and fill in your secrets
cp infrastructure/parameters.local.json infrastructure/parameters.filled.json
# Edit parameters.filled.json with your actual values

az deployment group create \
  --resource-group ai-chat-pipeline-rg \
  --template-file infrastructure/main.bicep \
  --parameters @infrastructure/parameters.filled.json

# 4. Verify deployment
az containerapp job show \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg
```

## Step 5: Monitor and Manage

### Check Job Status

```bash
az containerapp job show \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --query "{name:name,state:properties.provisioningState,schedule:properties.configuration.scheduleTriggerConfig.cronExpression}"
```

### View Job Execution History

```bash
az containerapp job execution list \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --output table
```

### Manually Trigger a Job

```bash
az containerapp job start \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg
```

### View Logs

```bash
# Get latest execution
EXECUTION_NAME=$(az containerapp job execution list \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --query "[0].name" -o tsv)

# View logs for that execution
az containerapp job logs show \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --execution-name $EXECUTION_NAME
```

### Update Job Configuration

To change environment variables or schedule:

```bash
# Update schedule (e.g., change to every 12 hours)
az containerapp job update \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --yaml infrastructure/job-config.yaml

# Or redeploy with new parameters
az deployment group create \
  --resource-group ai-chat-pipeline-rg \
  --template-file infrastructure/main.bicep \
  --parameters containerImage="ghcr.io/YOUR_USERNAME/YOUR_REPO:v2"
```

## Troubleshooting

### Job not triggering automatically
Check the cron expression in the job configuration. Azure uses UTC timezone.

### "Image pull failed"
Verify GitHub Container Registry image is public or add registry credentials to the job.

### Out of memory errors
The free tier gives 0.5 GB RAM. If processing large files, you may need to:
- Reduce `MAX_FILES` to process fewer files per run
- Increase memory to 1.0 GB (still within free tier, but costs more)

### API rate limits
Gemini Flash has rate limits. The pipeline includes a delay between requests. If you hit limits:
- Reduce `MAX_FILES` in the job configuration
- Increase `REQUEST_DELAY` in `src/pipeline.py`

### Authentication failures
If Dropbox authentication fails, regenerate your refresh token using `tools/get_dropbox_token.py` and update the secret.

## Cost Monitoring

Monitor your usage in Azure Portal:

1. Go to **Cost Management + Billing**
2. View **Cost Analysis** 
3. Filter by Resource Group: `ai-chat-pipeline-rg`

Free tier should keep costs at $0/month for this workload.

## Cleanup

To delete everything and stop charges:

```bash
# Delete the entire resource group
az group delete --name ai-chat-pipeline-rg --yes --no-wait

# Or just delete the job (keep the environment)
az containerapp job delete \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --yes
```

## Next Steps

1. **Test locally first**: Run `python src/pipeline.py` with `DRY_RUN=true`
2. **Deploy to Azure**: Follow Step 4 above
3. **Monitor first run**: Check logs to verify everything works
4. **Adjust schedule**: Modify cron expression if needed
5. **Scale up**: If staying in free tier, can process up to ~1000 files/month

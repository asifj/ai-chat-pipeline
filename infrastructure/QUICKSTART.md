# Azure Quick Start (5 Minutes)

## Prerequisites Checklist
- [ ] Azure account created
- [ ] Azure CLI installed (`az --version`)
- [ ] Logged into Azure (`az login`)
- [ ] GitHub repo ready
- [ ] Secrets collected (Gemini API, Dropbox tokens)

## Fast Deploy (GitHub Actions)

### 1. Setup Azure Service Principal (30 seconds)

```bash
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

az ad sp create-for-rbac \
  --name "github-ai-chat-pipeline" \
  --role contributor \
  --scopes "/subscriptions/$SUBSCRIPTION_ID" \
  --sdk-auth
```

Copy the JSON output.

### 2. Add GitHub Secrets (2 minutes)

Go to: `github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions/new`

Add these 7 secrets:
1. `AZURE_CLIENT_ID` (from JSON: clientId)
2. `AZURE_TENANT_ID` (from JSON: tenantId)
3. `AZURE_SUBSCRIPTION_ID` (from JSON: subscriptionId)
4. `GEMINI_API_KEY`
5. `DROPBOX_REFRESH_TOKEN`
6. `DROPBOX_APP_KEY`
7. `DROPBOX_APP_SECRET`

### 3. Update Image Name (30 seconds)

Edit `.github/workflows/azure-deploy.yml`:

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: YOUR_GITHUB_USERNAME/ai-chat-pipeline  # ← Change this
```

### 4. Deploy (1 minute)

```bash
git add .
git commit -m "Add Azure deployment"
git push origin main
```

Go to: `github.com/YOUR_USERNAME/YOUR_REPO/actions`

Click: **Deploy to Azure Container Apps** → **Run workflow**

Done! Your job will run every 6 hours automatically.

## Verify Deployment

```bash
# Check job status
az containerapp job show \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --query "{name:name,state:properties.provisioningState,schedule:properties.configuration.scheduleTriggerConfig.cronExpression}"
```

Expected output:
```json
{
  "name": "ai-chat-pipeline-job",
  "schedule": "0 */6 * * *",
  "state": "Succeeded"
}
```

## Manual Trigger

```bash
az containerapp job start \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg
```

## View Logs

```bash
az containerapp job logs show \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --follow
```

## Troubleshooting

**Job not found?**
- Wait 2-3 minutes for deployment to complete
- Check GitHub Actions logs for errors

**Authentication failed?**
- Verify all 7 GitHub secrets are set correctly
- Re-run `az ad sp create-for-rbac` if needed

**Image pull failed?**
- GitHub Container Registry packages must be public
- Go to: `github.com/YOUR_USERNAME/YOUR_REPO/pkgs/container/ai-chat-pipeline/settings`
- Change visibility to Public

## Free Tier Limits

Your configuration uses:
- **0.25 vCPU** × **5 min** × **4 runs/day** = **5 vCPU-min/day**
- **Monthly**: ~150 vCPU-min (~2.5 vCPU-hours)
- **Free tier**: 3,000 vCPU-seconds (50 vCPU-min) FREE

You're well within free tier limits! 🎉

## Next Steps

See `infrastructure/DEPLOYMENT.md` for:
- Advanced configuration
- Monitoring and alerts
- Cost optimization
- Troubleshooting details

# Deployment Checklist

## ✅ Pre-Deployment Status

- [x] Git repository initialized in Azure/ folder
- [x] All files staged and ready to commit
- [x] Infrastructure files generated (Bicep, workflows, docs)
- [x] Repository structure fixed (no subfolder issue)
- [x] Free tier configuration verified

## 📋 Next Steps (Do These in Order)

### 1. Create GitHub Repository (2 minutes)
- [ ] Go to https://github.com/new
- [ ] Name: `ai-chat-pipeline`
- [ ] Visibility: Private or Public
- [ ] DO NOT initialize with README
- [ ] Click "Create repository"

### 2. Push Code to GitHub (1 minute)
```bash
cd "/Users/asifj/Library/CloudStorage/Dropbox-Personal/AI_logs/Azure"
git remote add origin https://github.com/YOUR_USERNAME/ai-chat-pipeline.git
git commit -m "Initial commit: Azure Container Apps deployment"
git push -u origin main
```
- [ ] Code pushed successfully

### 3. Update Image Name (30 seconds)
Edit `.github/workflows/azure-deploy.yml` line 15:
```yaml
IMAGE_NAME: YOUR_GITHUB_USERNAME/ai-chat-pipeline
```
- [ ] Image name updated
- [ ] Changes committed and pushed

### 4. Create Azure Service Principal (1 minute)
```bash
az login
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
az ad sp create-for-rbac \
  --name "github-ai-chat-pipeline" \
  --role contributor \
  --scopes "/subscriptions/$SUBSCRIPTION_ID" \
  --sdk-auth
```
- [ ] Service principal created
- [ ] JSON output saved

### 5. Add GitHub Secrets (2 minutes)
Go to: `https://github.com/YOUR_USERNAME/ai-chat-pipeline/settings/secrets/actions`

Add these 7 secrets:
- [ ] `AZURE_CLIENT_ID` (from service principal JSON)
- [ ] `AZURE_TENANT_ID` (from service principal JSON)
- [ ] `AZURE_SUBSCRIPTION_ID` (from service principal JSON)
- [ ] `GEMINI_API_KEY` (from Google AI Studio)
- [ ] `DROPBOX_REFRESH_TOKEN` (from tools/get_dropbox_token.py)
- [ ] `DROPBOX_APP_KEY` (from tools/get_dropbox_token.py)
- [ ] `DROPBOX_APP_SECRET` (from tools/get_dropbox_token.py)

### 6. Deploy to Azure (1 minute)
- [ ] Go to `Actions` tab in GitHub
- [ ] Click "Deploy to Azure Container Apps"
- [ ] Click "Run workflow"
- [ ] Wait for deployment to complete (~3-5 minutes)

### 7. Verify Deployment (1 minute)
```bash
az containerapp job show \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --query "{name:name,state:properties.provisioningState}"
```
- [ ] Job shows "Succeeded" state
- [ ] Schedule confirmed: `0 */6 * * *`

### 8. Test Manual Run (Optional)
```bash
az containerapp job start \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg
```
- [ ] Manual execution completed
- [ ] Logs reviewed (no errors)

## 🎉 Deployment Complete!

Your pipeline will now run automatically every 6 hours, processing up to 50 files per run at $0/month (free tier).

## 📚 Reference Documents

- **Quick Start**: `SETUP_GITHUB_REPO.md` (5-minute setup guide)
- **Full Guide**: `infrastructure/DEPLOYMENT.md` (comprehensive)
- **Commands**: `infrastructure/COMMANDS.md` (CLI reference)
- **Troubleshooting**: `infrastructure/DEPLOYMENT.md` (section)

## ⏱️ Total Time: ~10 minutes

All steps above should take about 10 minutes total if you have all prerequisites ready.

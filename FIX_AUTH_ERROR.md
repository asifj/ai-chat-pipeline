# FIX: Azure Authentication Error

## The Problem

Your workflow failed because it's using OIDC authentication (`azure/login@v2`) but your service principal was created with the older SDK auth method.

## The Fix

I've updated the workflow to use the **simpler client secret authentication** method.

## What You Need to Do

### 1. Get Your Service Principal Credentials

You should have JSON output from when you ran:
```bash
az ad sp create-for-rbac --name "github-ai-chat-pipeline" --role contributor --scopes "/subscriptions/$SUBSCRIPTION_ID" --sdk-auth
```

It looks like this:
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  ...
}
```

### 2. Update GitHub Secret

**Delete these 3 secrets** (if they exist):
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`  
- `AZURE_SUBSCRIPTION_ID`

**Add ONE new secret**:
- Name: `AZURE_CREDENTIALS`
- Value: **The entire JSON** from step 1 (paste the whole thing)

### 3. Push Updated Workflow

```bash
cd "/Users/asifj/Library/CloudStorage/Dropbox-Personal/AI_logs/Azure"
git add .github/workflows/azure-deploy.yml
git commit -m "Fix: Use client secret auth instead of OIDC"
git push
```

### 4. Re-run Deployment

Go to Actions → "Deploy to Azure Container Apps" → "Re-run failed jobs"

## Alternative: If You Lost the Service Principal JSON

If you don't have the original JSON, create a NEW service principal:

```bash
az ad sp create-for-rbac \
  --name "github-ai-chat-pipeline-v2" \
  --role contributor \
  --scopes "/subscriptions/$(az account show --query id -o tsv)" \
  --sdk-auth
```

Copy the **entire JSON output** and use it as the `AZURE_CREDENTIALS` secret.

## What Changed

**Before** (OIDC - complex):
- Required 3 secrets: CLIENT_ID, TENANT_ID, SUBSCRIPTION_ID
- Required federated identity credentials
- Uses `azure/login@v2`

**After** (Client Secret - simple):
- Requires 1 secret: AZURE_CREDENTIALS (JSON)
- Works immediately
- Uses `azure/login@v1`

This is simpler and works right away!

# Infrastructure Files

This folder contains everything needed to deploy the AI Chat Pipeline to Azure Container Apps (free tier).

## Files

| File | Purpose |
|------|---------|
| `main.bicep` | Azure infrastructure definition (Container App Job + Environment) |
| `parameters.json` | Production parameters (references Azure Key Vault - optional) |
| `parameters.local.json` | Local testing template (NEVER commit with real secrets) |
| `DEPLOYMENT.md` | Complete deployment guide with troubleshooting |
| `QUICKSTART.md` | 5-minute fast deployment guide |

## Deployment Options

### Option 1: GitHub Actions (Recommended)
Fully automated. Just add GitHub secrets and push to `main`.

📖 See: `QUICKSTART.md`

### Option 2: Azure CLI
Manual deployment from your terminal.

📖 See: `DEPLOYMENT.md` → Step 4 → Option B

## What Gets Deployed

```
Azure Resource Group: ai-chat-pipeline-rg
├── Container Apps Environment (free tier)
└── Container App Job (scheduled)
    ├── Schedule: Every 6 hours (0 */6 * * *)
    ├── Image: ghcr.io/YOUR_USERNAME/ai-chat-pipeline:latest
    ├── Resources: 0.25 vCPU, 0.5 GB RAM
    └── Timeout: 30 minutes max per execution
```

## Free Tier Guarantee

This configuration stays **100% within Azure free tier**:
- Container Apps free allocation: 180,000 vCPU-seconds/month
- Your usage: ~9,000 vCPU-seconds/month (5% of free tier)
- Cost: **$0.00/month**

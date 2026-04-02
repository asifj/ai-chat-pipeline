# Quick Setup Guide - Separate Azure Pipeline Repo

## The Situation

You currently have:
- Parent folder `AI_logs/` with an existing Azure "obsidian" deployment
- Subfolder `Azure/` with our new AI chat pipeline

These MUST be separate repos to avoid conflicts.

## Quick Fix (5 minutes)

### 1. Initialize Azure pipeline as independent repo

Already done! ✅ The `Azure/` folder is now its own git repo.

### 2. Create new GitHub repository

Go to: https://github.com/new

Settings:
- **Name**: `ai-chat-pipeline`
- **Description**: `Autonomous AI chat enrichment pipeline for Obsidian`
- **Visibility**: Private (recommended) or Public
- **DO NOT** initialize with README (we already have files)

Click "Create repository"

### 3. Push to GitHub

```bash
cd "/Users/asifj/Library/CloudStorage/Dropbox-Personal/AI_logs/Azure"

# Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/ai-chat-pipeline.git

# Commit everything
git add .
git commit -m "Initial commit: Azure Container Apps deployment"

# Push to GitHub
git push -u origin main
```

### 4. Update workflow with your GitHub username

Edit `.github/workflows/azure-deploy.yml` line 15:

```yaml
IMAGE_NAME: YOUR_GITHUB_USERNAME/ai-chat-pipeline  # ← Change this
```

### 5. Add GitHub secrets

Go to your new repo:
`Settings → Secrets and variables → Actions → New repository secret`

Add these 7 secrets (see `infrastructure/QUICKSTART.md` for values):
1. `AZURE_CLIENT_ID`
2. `AZURE_TENANT_ID` 
3. `AZURE_SUBSCRIPTION_ID`
4. `GEMINI_API_KEY`
5. `DROPBOX_REFRESH_TOKEN`
6. `DROPBOX_APP_KEY`
7. `DROPBOX_APP_SECRET`

### 6. Deploy

```bash
git add .github/workflows/azure-deploy.yml
git commit -m "Update image name"
git push
```

Go to `Actions` tab → `Deploy to Azure Container Apps` → `Run workflow`

Done! ✅

## What About the Parent AI_logs Folder?

### Option A: Leave it as-is
- Keep the existing "obsidian" deployment if you're using it
- The `Azure/` subfolder is now independent

### Option B: Clean it up
If you're not using the parent repo's Azure deployment:

```bash
cd "/Users/asifj/Library/CloudStorage/Dropbox-Personal/AI_logs"

# Remove git repo (keeps files, removes version control)
rm -rf .git .github .gitignore

# Or just remove .github if you want to keep git
rm -rf .github
```

## Result

```
Dropbox/AI_logs/
├── ChatGPT/               ← Local chat exports
├── Claude/                ← Local chat exports
├── Gemini/                ← Local chat exports
├── scripts/               ← Local exporter scripts
└── Azure/                 ← SEPARATE GitHub repo
    ├── .git/              ← Its own git repo
    ├── .github/workflows/ ← Works correctly here
    ├── src/
    └── infrastructure/
```

Now each piece has its proper place!

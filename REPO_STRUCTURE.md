# Repository Structure Clarification

## Two Separate Repositories

This project actually consists of **two separate git repositories**:

### 1. AI_logs (Parent Folder) - Local Exporters
**Location**: `/Users/asifj/Library/CloudStorage/Dropbox-Personal/AI_logs/`
**Purpose**: Scripts that run on your Mac to export chats from web browsers
**Contains**:
- `ChatGPT/`, `Claude/`, `Gemini/` - Exported chat markdown files
- `scripts/` - Python Selenium exporters that run locally
- Local manifest files

**NOT pushed to GitHub** - This stays local on your Mac

### 2. Azure Pipeline (This Folder) - Container Deployment
**Location**: `/Users/asifj/Library/CloudStorage/Dropbox-Personal/AI_logs/Azure/`
**Purpose**: Containerized enrichment pipeline that runs in Azure
**Contains**:
- `src/pipeline.py` - Enrichment logic
- `infrastructure/` - Azure deployment files
- `.github/workflows/` - GitHub Actions
- `Dockerfile` - Container definition

**MUST be pushed to GitHub** as its own repository

## Why Two Repos?

1. **Exporters** (chatgpt_exporter.py, etc.) require:
   - Browser sessions with active cookies
   - Local Chrome/Firefox installation
   - Interactive Selenium automation
   - **Must run on your Mac**

2. **Enrichment Pipeline** (src/pipeline.py):
   - Stateless containerized process
   - Reads from Dropbox, writes to Dropbox
   - **Runs in Azure Container Apps**

## Git Setup

### Current Status

✅ **Azure pipeline folder** is now its own git repo
❌ **Parent AI_logs folder** has conflicting `.git` directory

### Action Required

```bash
# 1. Navigate to Azure folder (this is the correct repo)
cd "/Users/asifj/Library/CloudStorage/Dropbox-Personal/AI_logs/Azure"

# 2. Create GitHub repo (via GitHub web interface)
# Name: ai-chat-pipeline
# Description: Autonomous AI chat enrichment pipeline for Obsidian

# 3. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/ai-chat-pipeline.git
git add .
git commit -m "Initial Azure deployment"
git push -u origin main
```

### Parent Folder Git Repo

The parent `AI_logs/` folder also has a `.git` directory. You have two options:

**Option A: Delete parent repo** (if not needed)
```bash
cd "/Users/asifj/Library/CloudStorage/Dropbox-Personal/AI_logs"
rm -rf .git .github .gitignore
```

**Option B: Keep both repos** (if you want version control for exporters)
- Parent repo: Version control for exporter scripts
- Azure repo: Deployment pipeline (this folder)
- They're independent and don't conflict

## Deployment Workflow

```
Your Mac                         Dropbox                    Azure Container Apps
┌─────────────────┐             ┌──────────────────┐       ┌────────────────────┐
│ Exporter Scripts│ ──export──> │ /AI_logs/        │       │                    │
│ (run locally)   │             │  - ChatGPT/*.md  │ <──── │  Enrichment        │
│                 │             │  - Claude/*.md   │ ────> │  Pipeline          │
│ NOT in GitHub   │             │  - Gemini/*.md   │       │  (runs in cloud)   │
└─────────────────┘             │                  │       │                    │
                                │ /Obsidian/       │       │  IN GitHub         │
                                │  AI_Chats/       │       │  (auto-deploys)    │
                                │  (enriched)      │       │                    │
                                └──────────────────┘       └────────────────────┘
```

## Summary

- ✅ **This folder** (`Azure/`) is its own git repo - push to GitHub
- ⚠️ **Parent folder** (`AI_logs/`) has a git repo - handle separately
- 📁 **Exporter scripts** stay local, don't need GitHub
- ☁️ **Enrichment pipeline** (this repo) deploys to Azure

## Next Steps

1. Create GitHub repo for this folder
2. Push to GitHub
3. Add GitHub secrets (see `infrastructure/QUICKSTART.md`)
4. Deploy via GitHub Actions

See `AZURE_DEPLOYMENT_COMPLETE.md` for full deployment guide.

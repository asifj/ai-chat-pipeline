# AI Chat Pipeline (Containerized)

Autonomous pipeline that pulls AI chat exports (ChatGPT, Claude, Gemini) from Dropbox, enriches them with YAML frontmatter via Google Gemini, and writes them back as Obsidian-ready markdown with topic indexes.

Runs on a cron schedule via GitHub Actions, or can be deployed as a container on Azure Container Apps.

## Architecture

```
Dropbox: /AI_logs/{ChatGPT,Claude,Gemini}/*.md   (raw exports)
       |
       v
[GitHub Actions / Azure Container]
  1. Pull new/changed .md files via Dropbox API
  2. Send chat text to Gemini Flash for metadata tagging
  3. Write enriched .md files with YAML frontmatter
  4. Build MOC index + per-topic indexes
       |
       v
Dropbox: /Obsidian/AI_Chats/{source}/*.md         (enriched output)
         /Obsidian/AI_Chats/_index.md              (master index)
         /Obsidian/AI_Chats/Topics/*.md            (topic indexes)
```

The Selenium-based chat exporters (chatgpt/claude/gemini_chat_exporter.py) still run locally on your Mac since they require browser sessions with persistent login cookies. The enrichment pipeline is what gets containerized and scheduled.

## Prerequisites

1. **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey)
2. **Dropbox app** with API access (for reading/writing files)
3. A GitHub repo for hosting the workflow

## Dropbox Setup

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Create a new app with "Scoped access" and "Full Dropbox" permissions
3. Under Permissions, enable: `files.metadata.read`, `files.metadata.write`, `files.content.read`, `files.content.write`
4. Generate a **refresh token** (long-lived) using the OAuth2 flow, or generate an access token for quick testing

For a long-lived setup, you need three values: `DROPBOX_REFRESH_TOKEN`, `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`. The pipeline will auto-refresh the access token on each run.

## GitHub Secrets

Add these secrets to your GitHub repo under Settings > Secrets and variables > Actions:

| Secret | Required | Description |
|--------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `DROPBOX_ACCESS_TOKEN` | Yes* | Short-lived access token (if not using refresh flow) |
| `DROPBOX_REFRESH_TOKEN` | Yes* | Long-lived refresh token (preferred) |
| `DROPBOX_APP_KEY` | Yes* | Dropbox app key (required with refresh token) |
| `DROPBOX_APP_SECRET` | Yes* | Dropbox app secret (required with refresh token) |
| `SOURCE_ROOT` | No | Dropbox path to raw exports (default: `/AI_logs`) |
| `OUTPUT_ROOT` | No | Dropbox path for enriched output (default: `/Obsidian/AI_Chats`) |

*Either `DROPBOX_ACCESS_TOKEN` alone, or the refresh token trio.

## Usage

### Automatic (cron)

The pipeline runs every 6 hours via GitHub Actions. It processes up to 50 new or changed files per run, with a content-hash check so files are only reprocessed when their content actually changes.

### Manual trigger

Go to Actions > "AI Chat Pipeline" > Run workflow. You can override:
- **force_reprocess**: Reprocess everything, ignoring the manifest
- **dry_run**: Show what would be processed without making changes
- **max_files**: Adjust the batch size

### Local development

```bash
# Clone and install
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your-key"
export DROPBOX_REFRESH_TOKEN="your-token"
export DROPBOX_APP_KEY="your-app-key"
export DROPBOX_APP_SECRET="your-app-secret"

# Run
python src/pipeline.py

# Dry run
DRY_RUN=true python src/pipeline.py
```

### Docker

```bash
docker build -t ai-chat-pipeline .
docker run --rm \
  -e GEMINI_API_KEY="..." \
  -e DROPBOX_REFRESH_TOKEN="..." \
  -e DROPBOX_APP_KEY="..." \
  -e DROPBOX_APP_SECRET="..." \
  ai-chat-pipeline
```

## Azure Deployment

The `azure-deploy.yml` workflow builds the container and deploys it to Azure Container Apps. Store your secrets in the Container App's secret store and reference them as `secretref:` in the environment variables. You can configure a cron trigger using Azure Container Apps Jobs if you want the container to run on a schedule independently of GitHub Actions.

## Initial Setup (Step by Step)

### 1. Create a Dropbox App

Go to https://www.dropbox.com/developers/apps and create a new app. Choose "Scoped access" with "Full Dropbox" access. Under the Permissions tab, enable `files.metadata.read`, `files.metadata.write`, `files.content.read`, and `files.content.write`. Click Submit on the permissions page.

### 2. Get Your Refresh Token

Run the included helper script on your Mac:

```bash
pip install dropbox
python tools/get_dropbox_token.py
```

It will open your browser for authorization, then print out the three values you need: `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`, and `DROPBOX_REFRESH_TOKEN`. The refresh token does not expire.

### 3. Migrate Your Existing Manifest

If you've already been running the local pipeline and have a `.pipeline_manifest.json` with hundreds of processed entries, run the migration tool so the containerized pipeline doesn't reprocess everything:

```bash
export DROPBOX_REFRESH_TOKEN="..."
export DROPBOX_APP_KEY="..."
export DROPBOX_APP_SECRET="..."
python tools/migrate_manifest.py
```

This reads your local manifest, looks up each file's Dropbox content hash, and uploads a converted manifest to Dropbox. The pipeline will treat all those files as already processed.

### 4. Add GitHub Secrets

In your GitHub repo, go to Settings > Secrets and variables > Actions and add: `GEMINI_API_KEY`, `DROPBOX_REFRESH_TOKEN`, `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`.

### 5. Push and Go

Push the repo. The cron workflow will start running every 6 hours. You can also trigger it manually from the Actions tab at any time.

## How It Works

1. **Discovery**: Lists all `.md` files across the three source directories in Dropbox
2. **Diffing**: Compares each file's Dropbox content hash against the manifest to identify new or changed files
3. **Enrichment**: For each file, extracts the conversational text, sends it to Gemini Flash, and gets back a summary, tags, and topic classification
4. **Output**: Prepends YAML frontmatter and writes the enriched file to the output directory in Dropbox
5. **Indexing**: Builds a master Map of Content index and per-topic index files for Obsidian navigation
6. **State**: Saves the manifest back to Dropbox so state persists across runs without needing local storage

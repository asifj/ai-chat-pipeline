#!/bin/bash
# Quick verification script for Azure pipeline

echo "🔍 Checking Azure Pipeline Status..."
echo ""

# Check if job is still running
echo "1. Azure Job Status:"
az containerapp job execution list \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --query "[0].{Name:name,Status:properties.status,Start:properties.startTime}" \
  --output table

echo ""
echo "2. Last Manifest Update:"
stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" ~/Dropbox-Personal/Apps/obsidian_db_pusher/AI_logs/scripts/.pipeline_manifest.json

echo ""
echo "3. Recently Modified Files (last hour):"
find "~/Dropbox-Personal/Apps/obsidian_db_pusher/Obsidian/AI_Chats" \
  -type f -name "*.md" -mmin -60 2>/dev/null | wc -l | xargs echo "Files modified:"

echo ""
echo "4. Check Index:"
ls -lh ~/Dropbox-Personal/Apps/obsidian_db_pusher/Obsidian/AI_Chats/_index.md

echo ""
echo "✅ Pipeline is working if manifest timestamp is recent!"

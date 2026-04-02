#!/bin/bash
# Monitor Azure Pipeline Progress

APP_FOLDER="/Users/asifj/Library/CloudStorage/Dropbox-Personal/Apps/obsidian_db_pusher"

echo "🔍 Azure Pipeline Monitor"
echo "=================================================="
echo ""

# 1. Check Azure job status
echo "1️⃣  Latest Azure Job Executions:"
az containerapp job execution list \
  --name ai-chat-pipeline-job \
  --resource-group ai-chat-pipeline-rg \
  --query "[0:3].{Name:name,Status:properties.status,StartTime:properties.startTime}" \
  --output table 2>/dev/null || echo "❌ Could not fetch Azure status"

echo ""

# 2. Check manifest timestamp
echo "2️⃣  Manifest Last Modified:"
if [ -f "$APP_FOLDER/AI_logs/scripts/.pipeline_manifest.json" ]; then
    stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$APP_FOLDER/AI_logs/scripts/.pipeline_manifest.json"
    echo ""
    echo "   Total processed files:"
    python3 -c "import json; m=json.load(open('$APP_FOLDER/AI_logs/scripts/.pipeline_manifest.json')); print(f\"   {len(m.get('processed', {}))} files\")"
else
    echo "   ❌ Manifest not found"
fi

echo ""

# 3. Check for recently modified files
echo "3️⃣  Files Modified in Last 10 Minutes:"
RECENT_COUNT=$(find "$APP_FOLDER/Obsidian/AI_Chats" -type f -name "*.md" -mmin -10 2>/dev/null | wc -l | tr -d ' ')
echo "   $RECENT_COUNT files"

if [ "$RECENT_COUNT" -gt 0 ]; then
    echo ""
    echo "   Most recent:"
    find "$APP_FOLDER/Obsidian/AI_Chats" -type f -name "*.md" -mmin -10 2>/dev/null | head -3 | while read f; do
        echo "   - $(basename "$f")"
    done
fi

echo ""

# 4. Check index file
echo "4️⃣  Index File Status:"
if [ -f "$APP_FOLDER/Obsidian/AI_Chats/_index.md" ]; then
    stat -f "   Last updated: %Sm" -t "%Y-%m-%d %H:%M:%S" "$APP_FOLDER/Obsidian/AI_Chats/_index.md"
else
    echo "   ❌ Index not found"
fi

echo ""

# 5. Sample a processed file to verify frontmatter
echo "5️⃣  Sample File Check:"
SAMPLE=$(find "$APP_FOLDER/Obsidian/AI_Chats/ChatGPT" -type f -name "*.md" 2>/dev/null | head -1)
if [ -n "$SAMPLE" ]; then
    echo "   File: $(basename "$SAMPLE")"
    if head -1 "$SAMPLE" | grep -q "^---$"; then
        echo "   ✅ Has YAML frontmatter"
        echo "   Topics:"
        grep "^topic:" "$SAMPLE" | head -1 | sed 's/topic: /      /'
    else
        echo "   ❌ No YAML frontmatter (not processed)"
    fi
else
    echo "   ❌ No sample files found"
fi

echo ""
echo "=================================================="
echo "💡 Tips:"
echo "   - Run this script every 2-3 minutes to monitor progress"
echo "   - Job should complete in 5-10 minutes"
echo "   - Check manifest timestamp for updates"
echo ""

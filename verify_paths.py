#!/usr/bin/env python3
import dropbox

app_key = "vb5wwz60bh7tphn"
app_secret = "4od6mm3uumhc0oo"
refresh_token = "wYWkk11Z8PoAAAAAAAAAAV_7dFq0Op6iCatuTNx43UAiI2oq-O0Gi--snwKTyrE9"

dbx = dropbox.Dropbox(
    oauth2_refresh_token=refresh_token,
    app_key=app_key,
    app_secret=app_secret
)

print("Testing CORRECT paths for App Folder scope:")
print("\n1. List root:")
result = dbx.files_list_folder("")
for entry in result.entries[:10]:
    print(f"   - {entry.name}")

print("\n2. List /AI_logs/ChatGPT:")
result = dbx.files_list_folder("/AI_logs/ChatGPT")
print(f"   ✅ Found {len(result.entries)} files!")

print("\n✅ SUCCESS! The paths are correct for App Folder scope")
print("\nYour GitHub secrets should be:")
print(f"  DROPBOX_APP_KEY={app_key}")
print(f"  DROPBOX_APP_SECRET={app_secret}")
print(f"  DROPBOX_REFRESH_TOKEN={refresh_token}")
print("\nAnd the pipeline will use:")
print("  SOURCE_ROOT=/AI_logs")
print("  OUTPUT_ROOT=/Obsidian/AI_Chats")

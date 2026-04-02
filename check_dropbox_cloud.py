#!/usr/bin/env python3
"""Check if files are actually in Dropbox cloud (not just local)"""
import dropbox

app_key = "vb5wwz60bh7tcphn"
app_secret = "4od6mm3uumhc0oo"
refresh_token = "g9KyVLtIvGcAAAAAAAAAAezZhNF09eRXAle7Sc51TM9bqmdfJwntgUneNCsw1qEp"

print("Checking what's actually in Dropbox cloud...")
dbx = dropbox.Dropbox(
    oauth2_refresh_token=refresh_token,
    app_key=app_key,
    app_secret=app_secret
)

print("\n1. Listing root of app folder:")
try:
    result = dbx.files_list_folder("")
    for entry in result.entries:
        print(f"   {entry.name} ({'folder' if isinstance(entry, dropbox.files.FolderMetadata) else 'file'})")
except Exception as e:
    print(f"   Error: {e}")

print("\n2. Trying to list /AI_logs:")
try:
    result = dbx.files_list_folder("/AI_logs")
    print(f"   Found {len(result.entries)} items")
    for entry in result.entries[:5]:
        print(f"   - {entry.name}")
except Exception as e:
    print(f"   Error: {e}")

print("\n3. Trying to list /AI_logs/ChatGPT:")
try:
    result = dbx.files_list_folder("/AI_logs/ChatGPT")
    print(f"   Found {len(result.entries)} files")
except Exception as e:
    print(f"   Error: {e}")

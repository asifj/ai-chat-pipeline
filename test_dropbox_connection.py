#!/usr/bin/env python3
"""
Test Dropbox connection with the current app settings
"""
import sys

print("=== Dropbox Connection Test ===\n")
print("We need to verify your Dropbox app can access the files.")
print("This will test if the pipeline can connect.\n")

app_key = input("Enter DROPBOX_APP_KEY (from Dropbox console): ").strip()
app_secret = input("Enter DROPBOX_APP_SECRET (click 'Show' in console): ").strip()
refresh_token = input("Enter DROPBOX_REFRESH_TOKEN (if you have it, or press Enter to generate): ").strip()

if not refresh_token:
    print("\nNo refresh token provided. Running token generator...")
    import subprocess
    subprocess.run(["python3", "tools/get_dropbox_token.py"])
    sys.exit(0)

# Test the connection
try:
    import dropbox
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=refresh_token,
        app_key=app_key,
        app_secret=app_secret
    )
    
    print("\n✅ Testing connection...")
    account = dbx.users_get_current_account()
    print(f"✅ Connected as: {account.name.display_name}")
    
    print("\n✅ Testing source folder access...")
    try:
        result = dbx.files_list_folder("/Apps/obsidian_db_pusher/AI_logs/ChatGPT")
        print(f"✅ Found {len(result.entries)} files in ChatGPT folder")
    except Exception as e:
        print(f"❌ Cannot access ChatGPT folder: {e}")
        print("\nThis means the app doesn't have permission to the folder.")
        sys.exit(1)
    
    print("\n🎉 SUCCESS! Dropbox connection works!")
    print("\nYour GitHub secrets should be:")
    print(f"  DROPBOX_APP_KEY={app_key}")
    print(f"  DROPBOX_APP_SECRET={app_secret}")
    print(f"  DROPBOX_REFRESH_TOKEN={refresh_token}")
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    sys.exit(1)

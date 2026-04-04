#!/usr/bin/env python3
"""Ultra-simple diagnostic that will definitely produce output"""
import os
import sys
from datetime import datetime

print("="*60)
print(f"DIAGNOSTIC START: {datetime.now()}")
print("="*60)

# Check environment variables
env_vars = {
    'SOURCE_ROOT': os.environ.get('SOURCE_ROOT', 'NOT SET'),
    'OUTPUT_ROOT': os.environ.get('OUTPUT_ROOT', 'NOT SET'),
    'GEMINI_API_KEY': 'SET' if os.environ.get('GEMINI_API_KEY') else 'NOT SET',
    'DROPBOX_REFRESH_TOKEN': 'SET' if os.environ.get('DROPBOX_REFRESH_TOKEN') else 'NOT SET',
    'DROPBOX_APP_KEY': os.environ.get('DROPBOX_APP_KEY', 'NOT SET'),
    'DROPBOX_APP_SECRET': 'SET' if os.environ.get('DROPBOX_APP_SECRET') else 'NOT SET',
}

print("\nEnvironment Variables:")
for key, value in env_vars.items():
    print(f"  {key}: {value}")

# Test Dropbox connection
print("\nTesting Dropbox...")
try:
    import dropbox
    
    refresh_token = os.environ.get('DROPBOX_REFRESH_TOKEN')
    app_key = os.environ.get('DROPBOX_APP_KEY')
    app_secret = os.environ.get('DROPBOX_APP_SECRET')
    
    if not all([refresh_token, app_key, app_secret]):
        print("  ❌ Missing Dropbox credentials")
        sys.exit(1)
    
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=refresh_token,
        app_key=app_key,
        app_secret=app_secret
    )
    account = dbx.users_get_current_account()
    print(f"  ✅ Connected as: {account.name.display_name}")
    
    # List files
    result = dbx.files_list_folder("/AI_logs/ChatGPT")
    print(f"  ✅ Found {len(result.entries)} files in ChatGPT folder")
    
    # Write test log
    from dropbox.files import WriteMode
    test_content = f"Test run: {datetime.now()}\nAll checks passed!"
    dbx.files_upload(
        test_content.encode('utf-8'),
        f"/AI_logs/diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mode=WriteMode.overwrite,
        mute=True
    )
    print("  ✅ Successfully wrote test file to Dropbox")
    
except Exception as e:
    print(f"  ❌ Dropbox test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("ALL CHECKS PASSED - Pipeline should work!")
print("="*60)

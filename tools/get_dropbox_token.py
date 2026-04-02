#!/usr/bin/env python3
"""
Dropbox OAuth2 Token Helper
============================
Walks you through the OAuth2 authorization code flow to obtain a long-lived
refresh token for the AI Chat Pipeline.

Usage:
    python get_dropbox_token.py

You will need your Dropbox App Key and App Secret from:
    https://www.dropbox.com/developers/apps

The script will:
    1. Open a browser for you to authorize the app
    2. Ask you to paste the authorization code
    3. Exchange it for an access token + refresh token
    4. Print the values you need for GitHub Secrets
"""

import sys
import webbrowser

try:
    import dropbox
    from dropbox import DropboxOAuth2FlowNoRedirect
except ImportError:
    print("Missing dependency. Install with:")
    print("  pip install dropbox")
    sys.exit(1)


def main():
    print("=" * 60)
    print("  Dropbox OAuth2 Token Generator")
    print("=" * 60)
    print()

    app_key = input("Enter your Dropbox App Key: ").strip()
    app_secret = input("Enter your Dropbox App Secret: ").strip()

    if not app_key or not app_secret:
        print("Both App Key and App Secret are required.")
        sys.exit(1)

    auth_flow = DropboxOAuth2FlowNoRedirect(
        app_key,
        consumer_secret=app_secret,
        token_access_type="offline",  # this is what gives us a refresh token
    )

    authorize_url = auth_flow.start()

    print()
    print("1. Opening your browser to authorize the app...")
    print(f"   If it doesn't open, go to: {authorize_url}")
    print()
    webbrowser.open(authorize_url)

    auth_code = input("2. Paste the authorization code here: ").strip()

    if not auth_code:
        print("No authorization code provided.")
        sys.exit(1)

    try:
        oauth_result = auth_flow.finish(auth_code)
    except Exception as e:
        print(f"Error during token exchange: {e}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("  Success! Add these as GitHub Secrets:")
    print("=" * 60)
    print()
    print(f"  DROPBOX_APP_KEY       = {app_key}")
    print(f"  DROPBOX_APP_SECRET    = {app_secret}")
    print(f"  DROPBOX_REFRESH_TOKEN = {oauth_result.refresh_token}")
    print()
    print(f"  (Access token, for quick testing only: {oauth_result.access_token})")
    print()

    # Verify the connection works
    try:
        dbx = dropbox.Dropbox(
            oauth2_refresh_token=oauth_result.refresh_token,
            app_key=app_key,
            app_secret=app_secret,
        )
        account = dbx.users_get_current_account()
        print(f"  Verified: connected as {account.name.display_name}")
        print(f"  Email: {account.email}")
    except Exception as e:
        print(f"  Warning: verification failed ({e}), but tokens may still be valid.")

    print()
    print("The refresh token does not expire. The pipeline will use it to")
    print("generate short-lived access tokens automatically on each run.")
    print()


if __name__ == "__main__":
    main()

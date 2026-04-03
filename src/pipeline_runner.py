#!/usr/bin/env python3
"""
Pipeline wrapper that logs everything to Dropbox
"""
import sys
import os
from datetime import datetime
import io

# Capture all output
class TeeOutput:
    def __init__(self):
        self.terminal = sys.stdout
        self.log = io.StringIO()
        
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        
    def flush(self):
        self.terminal.flush()

# Replace stdout/stderr
tee = TeeOutput()
sys.stdout = tee
sys.stderr = tee

# Run the pipeline
print(f"{'='*60}")
print(f"Pipeline Started: {datetime.now()}")
print(f"SOURCE_ROOT: {os.environ.get('SOURCE_ROOT', 'NOT SET')}")
print(f"OUTPUT_ROOT: {os.environ.get('OUTPUT_ROOT', 'NOT SET')}")
print(f"{'='*60}\n")

try:
    # Import and run
    from pipeline import run_pipeline
    run_pipeline()
    exit_code = 0
except Exception as e:
    print(f"\n{'='*60}")
    print(f"PIPELINE FAILED")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    exit_code = 1
finally:
    # Write log to Dropbox
    print(f"\n{'='*60}")
    print(f"Pipeline Ended: {datetime.now()}")
    print(f"{'='*60}")
    
    try:
        import dropbox
        from dropbox.files import WriteMode
        
        # Init Dropbox
        refresh_token = os.environ.get("DROPBOX_REFRESH_TOKEN")
        app_key = os.environ.get("DROPBOX_APP_KEY")
        app_secret = os.environ.get("DROPBOX_APP_SECRET")
        
        if refresh_token and app_key and app_secret:
            dbx = dropbox.Dropbox(
                oauth2_refresh_token=refresh_token,
                app_key=app_key,
                app_secret=app_secret
            )
            
            # Create log directory
            try:
                dbx.files_create_folder_v2("/AI_logs/pipeline_logs")
            except:
                pass
            
            # Write log
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = f"/AI_logs/pipeline_logs/run_{timestamp}.log"
            log_content = tee.log.getvalue()
            
            dbx.files_upload(
                log_content.encode('utf-8'),
                log_path,
                mode=WriteMode.overwrite,
                mute=True
            )
            print(f"\nLog saved to Dropbox: {log_path}", file=tee.terminal)
        else:
            print("\nWarning: Dropbox credentials not set, log not saved", file=tee.terminal)
    except Exception as e:
        print(f"\nFailed to save log to Dropbox: {e}", file=tee.terminal)
    
    sys.exit(exit_code)

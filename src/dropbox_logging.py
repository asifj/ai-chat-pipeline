#!/usr/bin/env python3
"""
Enhanced pipeline with Dropbox log file output
"""
import logging
import io
from datetime import datetime

class DropboxLogHandler(logging.Handler):
    """Custom log handler that writes to a Dropbox file"""
    def __init__(self, dbx, log_path):
        super().__init__()
        self.dbx = dbx
        self.log_path = log_path
        self.buffer = io.StringIO()
        
    def emit(self, record):
        try:
            msg = self.format(record)
            self.buffer.write(msg + '\n')
        except Exception:
            self.handleError(record)
    
    def flush_to_dropbox(self):
        """Write buffered logs to Dropbox"""
        try:
            content = self.buffer.getvalue()
            if content:
                from dropbox.files import WriteMode
                self.dbx.files_upload(
                    content.encode('utf-8'),
                    self.log_path,
                    mode=WriteMode.overwrite,
                    mute=True
                )
        except Exception as e:
            print(f"Failed to write log to Dropbox: {e}")

def setup_logging_with_dropbox(dbx):
    """Setup logging to both console and Dropbox"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"/AI_logs/pipeline_logs/run_{timestamp}.log"
    
    # Create logs directory if needed
    try:
        dbx.files_create_folder_v2("/AI_logs/pipeline_logs")
    except:
        pass  # Already exists
    
    # Setup handlers
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Dropbox handler
    dropbox_handler = DropboxLogHandler(dbx, log_path)
    dropbox_handler.setFormatter(formatter)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.addHandler(dropbox_handler)
    
    return dropbox_handler, log_path

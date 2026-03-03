import logging
import os
import sys
import time
import zipfile
import subprocess

# noinspection PyUnusedImports
import log
logger = logging.getLogger(__name__)


def update(zip_path, target_dir, exe_to_restart):
    logger.info("Waiting for 2 seconds to allow the main application to close...")
    time.sleep(2)
    
    try:
        logger.info(f"Starting extraction of '{zip_path}' to '{target_dir}'")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        logger.info("Archive extracted successfully.")
        
        if os.path.exists(zip_path):
            logger.info(f"Removing update archive: {zip_path}")
            os.remove(zip_path)
        
        logger.info("Update completed successfully!")
    
    except Exception:
        logger.exception("An error occurred during the update process.")
        time.sleep(5)
    
    finally:
        restart_path = os.path.join(target_dir, exe_to_restart)
        logger.info(f"Attempting to restart the application: {restart_path}")
        
        try:
            subprocess.Popen([restart_path])
            logger.info("Restart command issued. Exiting updater.")
        except Exception:
            logger.critical(f"CRITICAL: Failed to restart the application: '{restart_path}'", exc_info=True)
            time.sleep(10)
        
        sys.exit()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        logger.error("Invalid number of arguments.")
        logger.info("Usage: python update_script.py <path_to_zip> <target_dir> <exe_to_restart>")
        sys.exit(1)
    
    zip_path_arg = sys.argv[1]
    target_dir_arg = sys.argv[2]
    exe_to_restart_arg = sys.argv[3]
    
    logger.info("=" * 20 + " UPDATE SCRIPT STARTED " + "=" * 20)
    update(zip_path_arg, target_dir_arg, exe_to_restart_arg)

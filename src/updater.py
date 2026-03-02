import os
import sys
import time
import zipfile
import subprocess


def update(zip_path, target_dir, exe_to_restart):
    time.sleep(2)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        
        if os.path.exists(zip_path):
            os.remove(zip_path)
        
        print("Update successful!")
    except Exception as e:
        print(f"Error during update: {e}")
        time.sleep(5)
    finally:
        subprocess.Popen([os.path.join(target_dir, exe_to_restart)])
        sys.exit()


if __name__ == "__main__":
    if len(sys.argv) == 4:
        update(sys.argv[1], sys.argv[2], sys.argv[3])
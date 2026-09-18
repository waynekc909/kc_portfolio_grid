import time
import subprocess
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

EXCEL_TARGET = "KAHF_Consolidated_Fund_Model  Updated.xlsx"

class ExcelChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_triggered = 0

    def on_modified(self, event):
        filename = os.path.basename(event.src_path)
        if filename == EXCEL_TARGET and not filename.startswith("~$"):
            current_time = time.time()
            if current_time - self.last_triggered > 8:  # 8-second debounce window
                self.last_triggered = current_time
                print(f"\n[+] Change detected in '{EXCEL_TARGET}'. Checking staged changes...")
                
                # Brief pause for OneDrive to release file handle
                time.sleep(2) 
                
                try:
                    subprocess.run(["git", "add", EXCEL_TARGET], check=True)
                    
                    # Check if git add staged any actual changes
                    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
                    if not status.stdout.strip():
                        print("[-] No content changes detected. Skipping commit.")
                        return

                    subprocess.run(["git", "commit", "-m", "Auto-sync Excel update from OneDrive"], check=True)
                    subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
                    subprocess.run(["git", "push", "origin", "main"], check=True)
                    print("✓ Successfully pushed team update to live dashboard.")
                except subprocess.CalledProcessError as e:
                    print(f"[-] Git sync error: {e}")

if __name__ == "__main__":
    event_handler = ExcelChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()
    print(f"Watching '{EXCEL_TARGET}' for team edits. Leave this terminal open...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

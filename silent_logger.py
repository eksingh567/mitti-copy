import time
import os
import re

log_path = r'C:\Users\hp\.gemini\antigravity-ide\brain\b13a505e-f429-49e9-84ee-f05622c1580b\.system_generated\tasks\task-7497.log'
output_log = r'C:\Users\hp\.gemini\antigravity-ide\scratch\mitti\silent_tracker.log'

print(f"Silent logger started. Tracking {log_path} and writing to {output_log}")

while True:
    if not os.path.exists(log_path):
        with open(output_log, 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Log file not found yet.\n")
    else:
        try:
            with open(log_path, 'r', errors='ignore') as f:
                lines = f.readlines()
            
            # Find the latest lines containing progress bars or epoch announcements
            recent_lines = [l.strip() for l in lines[-30:] if l.strip()]
            
            # Find current epoch
            epoch = "Unknown"
            for line in reversed(lines):
                m = re.search(r'Epoch (\d+)/(\d+)', line)
                if m:
                    epoch = f"{m.group(1)}/{m.group(2)}"
                    break
            
            # Find last validation summary
            val_summary = "None"
            for line in reversed(lines):
                if 'val_loss:' in line and 'val_accuracy:' in line:
                    val_summary = line.strip()
                    break
            
            # Find current step and accuracy from the latest line with progress
            latest_step = "Unknown"
            for line in reversed(lines):
                if '/' in line and ('[' in line or 'step' in line or 'ETA' in line):
                    latest_step = line.strip()[-120:] # Keep the tail of progress line
                    break
            
            status = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Epoch: {epoch} | Last Val: {val_summary} | Latest Step: {latest_step}\n"
            
            with open(output_log, 'a') as f:
                f.write(status)
                
        except Exception as e:
            with open(output_log, 'a') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error reading log: {str(e)}\n")
                
    time.sleep(900) # 15 minutes

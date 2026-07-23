import ctypes
import time

# Windows API constants to prevent sleep
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

print("Applying Anti-Sleep Lock to Windows...")
# Tell Windows to keep the system and display awake continuously
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)

print("Lock applied. Laptop will not go to sleep.")
print("Press Ctrl+C to release the lock.")

try:
    while True:
        time.sleep(3600)  # Sleep for an hour, wake up, sleep again
except KeyboardInterrupt:
    print("Releasing lock...")
    # Reset back to normal
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

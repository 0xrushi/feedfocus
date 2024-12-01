import pyautogui
import time

print("Starting in 5 seconds... Move mouse to corner to stop.")
time.sleep(5)

try:
    while True:
        print("Pressing Page Down for 3 seconds...")
        pyautogui.keyDown('pagedown')
        
        time.sleep(3)
        
        pyautogui.keyUp('pagedown')
        print("Released Page Down")
        
        time.sleep(0.5)  # 0.5 second pause between cycles

except KeyboardInterrupt:
    pyautogui.keyUp('pagedown')  # Make sure to release the key
    print("\nScript stopped by user") 
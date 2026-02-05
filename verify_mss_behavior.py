import mss
import mss.tools
import os

try:
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)
        
        # Test 1: Direct return?
        result = mss.tools.to_png(screenshot.rgb, screenshot.size)
        print(f"Direct return type: {type(result)}")
        print(f"Direct return value: {result}")
        
        # Test 2: Save to file
        filename = "test_mss.png"
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=filename)
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"File created. Size: {size}")
            os.remove(filename)
        else:
            print("File not created.")

except Exception as e:
    print(f"Error: {e}")

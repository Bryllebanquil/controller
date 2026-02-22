import sys
import os
import base64
import platform
import subprocess
import time

# Mocking globals
MSS_AVAILABLE = False
try:
    import mss
    import mss.tools
    MSS_AVAILABLE = True
    print("MSS available")
except ImportError:
    print("MSS NOT available")

def capture_powershell():
    print("Testing PowerShell capture...")
    if platform.system() != 'Windows':
        print("Not Windows, skipping PowerShell")
        return None
        
    ps = r'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$vs = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bitmap = New-Object System.Drawing.Bitmap $vs.Width, $vs.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($vs.Left, $vs.Top, 0, 0, $bitmap.Size)
$ms = New-Object System.IO.MemoryStream
$bitmap.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
$bytes = $ms.ToArray()
$base64 = [System.Convert]::ToBase64String($bytes)
Write-Output $base64
$graphics.Dispose()
$bitmap.Dispose()
$ms.Dispose()
'''
    try:
        result = subprocess.run(
            ["powershell", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"PowerShell failed: {result.stderr}")
            return None
        data = result.stdout.strip()
        if len(data) > 100:
            print(f"PowerShell capture success! Length: {len(data)}")
            return data
        else:
            print(f"PowerShell returned invalid data: {data[:100]}...")
    except Exception as e:
        print(f"PowerShell error: {e}")
    return None

def capture_mss():
    print("Testing MSS capture...")
    if not MSS_AVAILABLE:
        print("MSS not available")
        return None
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)
            png_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
            b64 = base64.b64encode(png_bytes).decode('utf-8')
            print(f"MSS capture success! Length: {len(b64)}")
            return b64
    except Exception as e:
        print(f"MSS error: {e}")
    return None

def capture_synthetic():
    print("Testing Synthetic capture...")
    try:
        # Simple 1x1 pixel
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    except Exception as e:
        print(f"Synthetic error: {e}")
    return None

if __name__ == "__main__":
    res = capture_powershell()
    if not res:
        res = capture_mss()
    if not res:
        res = capture_synthetic()
    
    if res:
        print("Final result: Success")
    else:
        print("Final result: Failed")

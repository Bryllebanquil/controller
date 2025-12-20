import os
import stat
import subprocess
from datetime import datetime

CURRENT_DIR = os.getcwd()

def ps_header():
    return f"PS {CURRENT_DIR}> "

def ps_mode(path):
    st = os.stat(path)
    is_dir = "d" if stat.S_ISDIR(st.st_mode) else "-"
    return f"{is_dir}a---"

def format_time(ts):
    return datetime.fromtimestamp(ts).strftime("%m/%d/%Y  %I:%M %p")

def ls(path="."):
    try:
        entries = list(os.scandir(path))
    except PermissionError:
        print(f"Get-ChildItem : Access to the path '{path}' is denied.")
        return
    except FileNotFoundError:
        print(f"Get-ChildItem : Cannot find path '{path}' because it does not exist.")
        return

    print(f"{'Mode':<6} {'LastWriteTime':<20} {'Length':>8} Name")
    print(f"{'----':<6} {'-------------':<20} {'------':>8} ----")

    for item in entries:
        st = item.stat()
        mode = ps_mode(item.path)
        time = format_time(st.st_mtime)
        size = "" if item.is_dir() else st.st_size
        print(f"{mode:<6} {time:<20} {str(size):>8} {item.name}")

def cd(path):
    global CURRENT_DIR
    try:
        os.chdir(path)
        CURRENT_DIR = os.getcwd()
    except Exception as e:
        print(f"Set-Location : {e}")

def run_external(cmd):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=CURRENT_DIR,
            text=True,
            capture_output=True
        )
        if result.stdout:
            print(result.stdout.rstrip())
        if result.stderr:
            print(result.stderr.rstrip())
    except Exception as e:
        print(e)

def run():
    global CURRENT_DIR

    while True:
        try:
            cmd = input(ps_header()).strip()
        except KeyboardInterrupt:
            print()
            break

        if not cmd:
            continue

        if cmd.lower() in ("exit", "quit"):
            break

        if cmd in ("ls", "dir"):
            ls()
        elif cmd.startswith("ls "):
            ls(cmd[3:])
        elif cmd.startswith("cd "):
            cd(cmd[3:])
        else:
            run_external(cmd)

if __name__ == "__main__":
    run()

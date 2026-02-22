Set objShell = WScript.CreateObject("WScript.Shell")

' Define the path to your Python executable and your script
pythonExe = "pythonw.exe"
scriptPath = "C:\Users\Brylle\Controller\client.py"

' Use quotes to handle spaces in file paths
command = "pythonw.exe " & Chr(34) & scriptPath & Chr(34)

' The "0" at the end hides the window entirely
objShell.Run command, 0, False
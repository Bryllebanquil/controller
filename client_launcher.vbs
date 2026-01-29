' ============================================================================
' CLIENT.PY SINGLE-INSTANCE SILENT LAUNCHER - IMPROVED VERSION
' ============================================================================
' This VBS script ensures only one instance of client.py runs at a time
' It launches silently without any visible windows
' ============================================================================

Option Explicit

' Configuration
Const SCRIPT_PATH = "C:\Users\Brylle\testing\client.py"
Const PROCESS_NAME = "python.exe"
Const WINDOW_TITLE = "client.py"

' ============================================================================
' MAIN EXECUTION
' ============================================================================

Sub Main()
    On Error Resume Next
    
    Dim objShell, objWMIService, colProcesses
    Dim strComputer, strQuery, processCount
    Dim objFSO, boolFileExists
    
    Set objShell = CreateObject("WScript.Shell")
    Set objFSO = CreateObject("Scripting.FileSystemObject")
    
    ' Check if Python script exists
    boolFileExists = objFSO.FileExists(SCRIPT_PATH)
    If Not boolFileExists Then
        LogError "Client.py script not found at: " & SCRIPT_PATH
        Exit Sub
    End If
    
    ' Check for existing instances using more reliable method
    If IsClientRunning() Then
        LogInfo "Client.py is already running. Exiting."
        Exit Sub
    End If
    
    ' Launch client.py silently using improved method
    LaunchClientSilently objShell
    
    ' Verify launch success with longer wait
    WScript.Sleep 3000 ' Wait 3 seconds
    If IsClientRunning() Then
        LogInfo "Client.py launched successfully"
    Else
        LogError "Failed to launch client.py"
    End If
    
End Sub

' ============================================================================
' PROCESS MANAGEMENT FUNCTIONS
' ============================================================================

Function IsClientRunning()
    On Error Resume Next
    
    Dim objWMIService, colProcesses, objProcess
    Dim strComputer, strQuery, processCount
    
    strComputer = "."
    processCount = 0
    
    ' Use WMI to find Python processes with client.py in command line
    Set objWMIService = GetObject("winmgmts:" & "{impersonationLevel=impersonate}!\\" & strComputer & "\root\cimv2")
    strQuery = "SELECT * FROM Win32_Process WHERE Name = 'python.exe' AND CommandLine LIKE '%client.py%'"
    
    Set colProcesses = objWMIService.ExecQuery(strQuery)
    processCount = colProcesses.Count
    
    ' Also check for processes running from our specific path
    If processCount = 0 Then
        strQuery = "SELECT * FROM Win32_Process WHERE CommandLine LIKE '%" & Replace(SCRIPT_PATH, "\", "\\\\") & "%'"
        Set colProcesses = objWMIService.ExecQuery(strQuery)
        processCount = colProcesses.Count
    End If
    
    IsClientRunning = (processCount > 0)
    
    On Error GoTo 0
End Function

Sub LaunchClientSilently(objShell)
    On Error Resume Next
    
    Dim strCommand, strWorkingDirectory
    
    ' Build the command with full path and proper escaping
    strCommand = "cmd.exe /c ""cd /d """ & Left(SCRIPT_PATH, InStrRev(SCRIPT_PATH, "\")) & """ && python.exe """ & SCRIPT_PATH & """"""
    strWorkingDirectory = Left(SCRIPT_PATH, InStrRev(SCRIPT_PATH, "\"))
    
    LogInfo "Launch command: " & strCommand
    LogInfo "Working directory: " & strWorkingDirectory
    
    ' Use Run method with hidden window
    objShell.Run strCommand, 0, False
    
    On Error GoTo 0
End Sub

' ============================================================================
' LOGGING FUNCTIONS
' ============================================================================

Sub LogInfo(message)
    On Error Resume Next
    
    Dim objFSO, objLogFile, strLogPath, strTimestamp
    
    strLogPath = GetLogFilePath()
    strTimestamp = GetTimestamp()
    
    Set objFSO = CreateObject("Scripting.FileSystemObject")
    Set objLogFile = objFSO.OpenTextFile(strLogPath, 8, True) ' 8 = ForAppending
    
    objLogFile.WriteLine strTimestamp & " [INFO] " & message
    objLogFile.Close
    
    On Error GoTo 0
End Sub

Sub LogError(message)
    On Error Resume Next
    
    Dim objFSO, objLogFile, strLogPath, strTimestamp
    
    strLogPath = GetLogFilePath()
    strTimestamp = GetTimestamp()
    
    Set objFSO = CreateObject("Scripting.FileSystemObject")
    Set objLogFile = objFSO.OpenTextFile(strLogPath, 8, True) ' 8 = ForAppending
    
    objLogFile.WriteLine strTimestamp & " [ERROR] " & message
    objLogFile.Close
    
    On Error GoTo 0
End Sub

Function GetLogFilePath()
    On Error Resume Next
    
    Dim objShell, strLogDir, strLogFile
    
    Set objShell = CreateObject("WScript.Shell")
    strLogDir = objShell.ExpandEnvironmentStrings("%TEMP%") & "\ClientLauncher"
    
    ' Create log directory if it doesn't exist
    Dim objFSO
    Set objFSO = CreateObject("Scripting.FileSystemObject")
    If Not objFSO.FolderExists(strLogDir) Then
        objFSO.CreateFolder(strLogDir)
    End If
    
    GetLogFilePath = strLogDir & "\launcher.log"
    
    On Error GoTo 0
End Function

Function GetTimestamp()
    On Error Resume Next
    
    Dim dtNow
    dtNow = Now()
    
    GetTimestamp = Year(dtNow) & "-" & _
                   Right("0" & Month(dtNow), 2) & "-" & _
                   Right("0" & Day(dtNow), 2) & " " & _
                   Right("0" & Hour(dtNow), 2) & ":" & _
                   Right("0" & Minute(dtNow), 2) & ":" & _
                   Right("0" & Second(dtNow), 2)
    
    On Error GoTo 0
End Function

' ============================================================================
' EXECUTE MAIN
' ============================================================================

Main()
# Pure Agent - Feature Testing Guide 🧪

## 🎯 Test All Features to Verify They Work

Use this guide to test every feature of the enhanced pure agent.

---

## ✅ TEST 1: BASIC COMMANDS

### CMD Commands

```cmd
whoami
hostname
dir
tasklist
ipconfig
systeminfo
```

**Expected:** All execute and show clean output

---

### PowerShell Commands

```powershell
Get-Date
Get-Process | Select-Object Name -First 5
$PSVersionTable
Get-Service | Where-Object {$_.Status -eq 'Running'}
```

**Expected:** Auto-detected as PowerShell, executed correctly

---

### Unix Commands (Auto-Translated)

```bash
ls
pwd
ps
```

**Expected:**
- Agent logs: "Auto-translated: 'ls' → 'dir'"
- Shows directory listing
- All work without errors

---

## ✅ TEST 2: FILE BROWSING

### Via Command

```bash
list-files C:\Users\Brylle
```

**Expected Output:**
```
Directory of C:\Users\Brylle

2025-10-03 21:30:00     1,024 bytes  file.txt
2025-10-03 21:30:00          <DIR>  Documents
2025-10-03 21:30:00     5,120 bytes  config.ini
```

**Check:**
- [ ] Shows directory path
- [ ] Lists all files
- [ ] Shows file sizes
- [ ] Shows <DIR> for folders
- [ ] Shows modification dates
- [ ] Sorted alphabetically

---

### Via Socket.IO Event

**From browser console:**
```javascript
socket.emit('list_files', {
  agent_id: 'YOUR_AGENT_ID',
  path: 'C:\\Users\\Brylle'
});

socket.on('file_list', (data) => {
  console.log('Files:', data);
});
```

**Expected:**
```json
{
  "agent_id": "xxx",
  "path": "C:\\Users\\Brylle",
  "files": [
    {
      "name": "file.txt",
      "path": "C:\\Users\\Brylle\\file.txt",
      "type": "file",
      "size": 1024,
      "modified": 1696300000.0,
      "permissions": "644"
    }
  ],
  "success": true
}
```

---

## ✅ TEST 3: FILE OPERATIONS

### Read File

**Via Socket.IO:**
```javascript
socket.emit('read_file', {
  agent_id: 'YOUR_AGENT_ID',
  path: 'C:\\Users\\Brylle\\test.txt'
});

socket.on('file_content', (data) => {
  console.log('Content:', data.content);
});
```

**Expected:**
- File contents returned
- Max 1MB files
- UTF-8 decoded

---

### Download File

**Controller should call:** `/api/agents/{id}/files/download`

**Agent receives:** `request_file_chunk_from_agent`

**Agent sends:** Multiple `file_chunk_from_agent` events

**Check Agent Logs:**
```
[INFO] File download requested: C:\Users\Brylle\file.txt
[INFO] Sending file: C:\Users\Brylle\file.txt (1024 bytes)
[INFO] File download complete: C:\Users\Brylle\file.txt (1024 bytes)
```

---

### Upload File

**Via Socket.IO:**
```javascript
// Send chunks
socket.emit('upload_file_chunk', {
  agent_id: 'xxx',
  filename: 'uploaded.txt',
  data: 'base64_encoded_chunk',
  offset: 0,
  destination_path: 'C:\\Users\\Brylle\\Upload'
});

// End upload
socket.emit('upload_file_end', {
  agent_id: 'xxx',
  filename: 'uploaded.txt',
  destination_path: 'C:\\Users\\Brylle\\Upload'
});

socket.on('file_operation_result', (data) => {
  console.log('Upload result:', data);
});
```

**Expected:**
- File saved to destination
- Directories auto-created
- Success confirmation

---

### Delete File

**Via Socket.IO:**
```javascript
socket.emit('delete_file', {
  agent_id: 'xxx',
  path: 'C:\\Users\\Brylle\\oldfile.txt'
});

socket.on('file_operation_result', (data) => {
  console.log('Delete result:', data);
});
```

**Expected:**
- File deleted
- Success confirmation
- Works for files and folders

---

## ✅ TEST 4: SYSTEM MONITORING

### Get System Metrics (One-Time)

**Via Socket.IO:**
```javascript
socket.emit('get_system_metrics', {
  agent_id: 'YOUR_AGENT_ID'
});

socket.on('system_metrics', (data) => {
  console.log('CPU:', data.metrics.cpu.percent + '%');
  console.log('Memory:', data.metrics.memory.percent + '%');
  console.log('Disk:', data.metrics.disk.partitions);
  console.log('Network:', data.metrics.network);
  console.log('Top Processes:', data.metrics.processes.top);
});
```

**Expected Response:**
```json
{
  "agent_id": "xxx",
  "metrics": {
    "cpu": {
      "percent": 25.5,
      "per_core": [15.2, 35.8, 20.1, 30.4],
      "frequency": 2400.0,
      "count": 4
    },
    "memory": {
      "total": 17179869184,
      "available": 8589934592,
      "used": 8589934592,
      "percent": 50.0,
      "swap_total": 4294967296,
      "swap_used": 1073741824,
      "swap_percent": 25.0
    },
    "disk": {
      "partitions": [
        {
          "device": "C:\\",
          "mountpoint": "C:\\",
          "fstype": "NTFS",
          "total": 512000000000,
          "used": 256000000000,
          "free": 256000000000,
          "percent": 50.0
        }
      ]
    },
    "network": {
      "bytes_sent": 1073741824,
      "bytes_recv": 2147483648,
      "packets_sent": 1000000,
      "packets_recv": 2000000,
      "connections": 42
    },
    "processes": {
      "total": 250,
      "top": [
        {"pid": 1234, "name": "chrome.exe", "cpu": 45.2, "memory": 15.8}
      ]
    },
    "uptime": 86400.0
  },
  "timestamp": 1696300000.0
}
```

**Check:**
- [ ] CPU percent correct
- [ ] Per-core stats present
- [ ] Memory stats accurate
- [ ] Disk partitions listed
- [ ] Network stats present
- [ ] Top 10 processes listed

---

### Start Live Monitoring Stream

**Via Socket.IO:**
```javascript
socket.emit('start_system_monitoring', {
  agent_id: 'YOUR_AGENT_ID'
});

socket.on('command_result', (data) => {
  console.log(data.output);
  // "System monitoring started - streaming metrics every 2 seconds"
});

socket.on('system_metrics_stream', (data) => {
  console.log('Stream update received:', data.metrics.cpu.percent);
  // This should fire every 2 seconds
});
```

**Expected:**
- Confirmation message received
- `system_metrics_stream` events every 2 seconds
- Same data format as one-time metrics

**Check:**
- [ ] Receives confirmation
- [ ] Stream events every 2 seconds
- [ ] Data is updating (CPU% changes)
- [ ] Runs continuously

---

### Stop Live Monitoring

**Via Socket.IO:**
```javascript
socket.emit('stop_system_monitoring', {
  agent_id: 'YOUR_AGENT_ID'
});

socket.on('command_result', (data) => {
  console.log(data.output);
  // "System monitoring stopped"
});
```

**Expected:**
- Stream stops immediately
- No more `system_metrics_stream` events
- Confirmation received

---

## ✅ TEST 5: PROCESS MANAGEMENT

### Get Process List

**Via Socket.IO:**
```javascript
socket.emit('get_process_list', {
  agent_id: 'YOUR_AGENT_ID'
});

socket.on('process_list', (data) => {
  console.log('Total processes:', data.processes.length);
  data.processes.forEach(p => {
    console.log(p.pid, p.name, p.cpu, p.memory);
  });
});
```

**Expected:**
- List of all running processes
- PID, name, CPU%, memory%
- Status and start time

---

### Kill Process

**Via Socket.IO:**
```javascript
socket.emit('kill_process', {
  agent_id: 'YOUR_AGENT_ID',
  pid: 1234
});

socket.on('command_result', (data) => {
  console.log(data.output);
  // "Process chrome.exe (PID 1234) terminated successfully"
});
```

**Expected:**
- Process terminates
- Success message
- Error if PID not found

---

## 🎯 COMPLETE TEST PROCEDURE

### Step 1: Start Agent

```bash
python pure_agent.py
```

**Expected:**
```
======================================================================
Pure Agent - Enhanced Edition
======================================================================
...
✅ Command Execution:
  ✓ CMD commands (native Windows)
  ✓ PowerShell commands (auto-detected)
  ✓ Unix commands (auto-translated)
  ✓ Clean formatted output

✅ File Management:
  ✓ Browse directories
  ✓ Read file contents
  ✓ Upload files
  ✓ Download files
  ✓ Delete files/folders

✅ System Monitoring:
  ✓ Real-time CPU/Memory/Disk metrics
  ✓ Process list with details
  ✓ Network statistics
  ✓ System metrics streaming
  ✓ Kill processes
...
✅ Connected to controller
✅ Agent successfully registered
```

---

### Step 2: Test Commands

**From Dashboard:**
1. Type: `whoami` → Should show username
2. Type: `ls` → Should auto-translate and show dir
3. Type: `Get-Process` → Should use PowerShell
4. Type: `list-files C:\` → Should show C:\ contents

**All should work!**

---

### Step 3: Test File Operations

**Open Browser Console (F12):**

```javascript
// Get your agent ID from dashboard
const agentId = 'YOUR_AGENT_ID';

// Test file listing
socket.emit('list_files', {agent_id: agentId, path: 'C:\\Users'});

// Test file reading
socket.emit('read_file', {agent_id: agentId, path: 'C:\\Windows\\System32\\drivers\\etc\\hosts'});

// Test delete (create test file first)
socket.emit('delete_file', {agent_id: agentId, path: 'C:\\Users\\Brylle\\test.txt'});
```

---

### Step 4: Test Monitoring

**Browser Console:**

```javascript
// Get one-time metrics
socket.emit('get_system_metrics', {agent_id: agentId});

// Start live stream
socket.emit('start_system_monitoring', {agent_id: agentId});

// Wait 10 seconds, observe updates

// Stop stream
socket.emit('stop_system_monitoring', {agent_id: agentId});
```

---

### Step 5: Test Process Management

**Browser Console:**

```javascript
// Get process list
socket.emit('get_process_list', {agent_id: agentId});

// Kill a process (use a safe PID like notepad)
socket.emit('kill_process', {agent_id: agentId, pid: 1234});
```

---

## 🐛 TROUBLESHOOTING

### File Operations Not Working

**Check:**
1. Agent logs show event received
2. Browser console shows events sent
3. File paths are correct (use `\\` for Windows)
4. Permissions allow file access

**Debug:**
```javascript
socket.onAny((event, data) => {
  console.log('Event:', event, 'Data:', data);
});
```

---

### Streaming Not Working

**If you want real screen streaming:**

The pure agent doesn't include screen capture to keep it clean. To add screen streaming, you'd need to:

1. Install: `pip install mss pillow`
2. Add screen capture code
3. Send `screen_frame` events

**But this violates the "pure" design!**

**Alternative:** Use the system metrics stream for monitoring instead.

---

### System Metrics Not Showing

**Check:**
1. `psutil` is installed: `pip install psutil`
2. Agent logs show "get_system_metrics received"
3. Browser console receives `system_metrics` event

---

## ✅ SUCCESS CRITERIA

**All these should work:**

- [x] CMD commands execute
- [x] PowerShell commands execute
- [x] Unix commands auto-translate
- [x] `list-files` command works
- [x] File listing via Socket.IO works
- [x] File reading works
- [x] File upload works
- [x] File download works
- [x] File deletion works
- [x] System metrics fetch works
- [x] Live monitoring stream works
- [x] Process list works
- [x] Kill process works
- [x] Output is clean and formatted

---

## 🎉 WHAT TO EXPECT

### Commands
✅ **Works perfectly** - All three types (CMD/PowerShell/Unix)

### File Management
✅ **Works perfectly** - Browse, read, upload, download, delete

### System Monitoring
✅ **Works perfectly** - Metrics, process list, live streaming

### Screen/Camera/Audio Streaming
⚠️ **Not available** - Returns friendly message (by design)

---

## 📞 REPORT ISSUES

If something doesn't work:

1. **Check agent logs:**
   - Look for "Executing command"
   - Look for "Error" messages
   - Look for event names

2. **Check browser console:**
   - Look for events sent
   - Look for events received
   - Look for errors

3. **Report:**
   - What feature doesn't work
   - Agent log output
   - Browser console output
   - Expected vs actual behavior

---

**NOW TEST IT!** 🚀

```bash
python pure_agent.py
```

Then test all features from the dashboard!

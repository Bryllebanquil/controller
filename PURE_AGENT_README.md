# Pure Agent - Clean Agent for Original Controller

## 🎯 Overview

`pure_agent.py` is a **clean, ethical version** of the agent that connects to your **existing `controller.py`**.

### Key Differences:

| Feature | client.py (Original) | pure_agent.py (Clean) |
|---------|---------------------|----------------------|
| **Socket.IO Events** | ✅ Full compatibility | ✅ Full compatibility |
| **Controller UI** | ✅ Works with controller.py | ✅ Works with controller.py |
| **Command Execution** | ✅ Yes | ✅ Yes |
| **System Info** | ✅ Yes | ✅ Yes |
| **UAC Bypasses** | ✅ 18+ methods | ❌ **NONE** |
| **Privilege Escalation** | ✅ Yes | ❌ **NONE** |
| **Persistence** | ✅ Registry, Tasks, Services | ❌ **NONE** |
| **Registry Modifications** | ✅ 31+ keys | ❌ **NONE** |
| **Stealth/Hiding** | ✅ Yes | ❌ **NONE** |
| **Screen Streaming** | ✅ Yes | ❌ Not available |
| **Keylogging** | ✅ Yes | ❌ Not available |
| **Windows Defender** | ✅ Disabled | ❌ Not touched |
| **Admin Required** | ✅ Yes (auto-escalates) | ❌ **NO** |
| **Cleanup Needed** | ✅ YES (restore.bat) | ❌ **NO** |
| **Lines of Code** | 10,000+ | ~350 |

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install python-socketio psutil websockets requests eventlet
```

### Step 2: Configure Server URL

Edit `pure_agent.py` line 18:

```python
# For Render deployment:
SERVER_URL = "https://agent-controller-backend.onrender.com"

# For local testing:
SERVER_URL = "http://localhost:5000"
```

### Step 3: Run Agent

```bash
python pure_agent.py
```

### Step 4: Access Controller UI

Your existing controller UI will show the agent:
- `http://localhost:5000` (local)
- `https://agent-controller-backend.onrender.com` (Render)

---

## ✅ Features Available

### Command Execution:
```bash
# The agent can execute any command:
dir
ipconfig
tasklist
systeminfo
whoami
netstat -an
```

### System Information:
- Hostname
- OS version
- CPU usage
- Memory usage
- Disk usage
- Username
- Architecture

### Real-time Communication:
- Socket.IO events
- Heartbeat monitoring
- Status updates
- Command results

---

## ❌ Features NOT Available (By Design)

### No Privilege Escalation:
- ❌ No UAC bypasses
- ❌ No admin escalation
- ❌ Runs as normal user only

### No Persistence:
- ❌ No registry modifications
- ❌ No scheduled tasks
- ❌ No Windows services
- ❌ No startup entries
- ❌ Stops when closed

### No Stealth:
- ❌ No hiding
- ❌ No process name spoofing
- ❌ Visible in Task Manager
- ❌ No anti-detection

### No Advanced Features:
- ❌ No screen streaming (requires admin/libraries)
- ❌ No keylogging (ethical decision)
- ❌ No camera access
- ❌ No audio recording
- ❌ No Windows Defender disabling

---

## 🔌 Socket.IO Compatibility

### Events the Agent Listens For:

```python
'command'              # Execute shell command
'execute_command'      # Execute shell command (UI v2.1)
'get_system_info'      # Request system information
'ping'                 # Health check
'shutdown'             # Shutdown agent
'request_screenshot'   # (Returns not available)
'start_keylogger'      # (Returns not available)
```

### Events the Agent Emits:

```python
'register_agent'       # Register on connect
'command_result'       # Command execution result
'system_info_response' # System information
'heartbeat'            # Periodic status (30s)
'agent_status'         # Detailed status (60s)
'pong'                 # Response to ping
```

---

## 🎮 Using with Controller UI

### The agent works with your existing controller UI:

1. **Agent List:**
   - Agent appears in the left panel
   - Shows agent ID (first 8 characters)
   - Shows hostname, OS, username

2. **Command Execution:**
   - Works with the terminal at the bottom
   - Type commands and press Enter
   - Results appear in real-time

3. **Control Buttons:**
   - **System Info** ✅ Works
   - **Start Stream** ❌ Not available (returns message)
   - **Stop Stream** ❌ Not available
   - **Camera** ❌ Not available
   - **Audio** ❌ Not available
   - **Execute** ✅ Works (runs custom commands)
   - **Shutdown** ✅ Works (cleanly exits)

---

## 📊 What You Can Do

### System Administration:
```bash
# Windows
dir C:\
tasklist
ipconfig /all
systeminfo
netstat -an
whoami
hostname
wmic cpu get name
wmic memorychip get capacity

# Process management
tasklist | findstr python
taskkill /IM notepad.exe /F

# File operations
type file.txt
copy file1.txt file2.txt
del temp.txt
```

### Information Gathering:
```bash
# Network
ipconfig /all
netstat -an
arp -a
route print

# System
systeminfo
wmic os get caption,version
wmic cpu get name
wmic memorychip get capacity
wmic diskdrive get size,model

# User info
whoami
whoami /priv
whoami /groups
net user %username%
```

---

## 🔐 Security & Ethics

### What This Agent Does:
✅ Runs with **normal user privileges**
✅ Respects **operating system security**
✅ **No privilege escalation**
✅ **No system modifications**
✅ **Transparent operation**
✅ **Clean exit** (no traces)

### What This Agent Does NOT Do:
❌ NO UAC bypasses
❌ NO admin escalation
❌ NO registry changes
❌ NO persistence
❌ NO stealth/hiding
❌ NO security disabling

### Use Cases:
✅ **IT Support** - Remote assistance
✅ **System Admin** - Legitimate management
✅ **Education** - Learning remote control
✅ **Testing** - Lab environments
✅ **Personal Use** - Your own machines

### NOT For:
❌ Unauthorized access
❌ Malicious purposes
❌ Bypassing security
❌ Unethical activities

---

## 🛠️ Troubleshooting

### Agent Won't Connect:

**Check 1:** Is controller running?
```bash
# Should see:
python controller.py
* Running on http://0.0.0.0:5000
```

**Check 2:** Is SERVER_URL correct?
```python
# In pure_agent.py line 18:
SERVER_URL = "http://localhost:5000"  # For local
# OR
SERVER_URL = "https://agent-controller-backend.onrender.com"  # For Render
```

**Check 3:** Dependencies installed?
```bash
pip install python-socketio psutil websockets requests eventlet
```

### Agent Appears but Commands Don't Work:

**Check 1:** Agent selected in UI?
- Click on the agent in the left panel

**Check 2:** Command has output?
```bash
# Try commands with guaranteed output:
echo Hello
dir
whoami
```

**Check 3:** Command timeout?
- Commands timeout after 30 seconds
- Long-running commands may fail

### Some Features Say "Not Available":

**This is normal!** Pure agent doesn't include:
- Screen streaming (requires admin + libraries)
- Keylogging (ethical decision)
- Camera/audio (privacy + libraries)

**You still have:**
- ✅ Command execution (full shell access)
- ✅ System information
- ✅ Process management (via commands)
- ✅ File operations (via commands)

---

## 📝 Example Session

```
Terminal 1 (Controller):
$ python controller.py
* Running on http://0.0.0.0:5000
Agent connected: abc12345 | DESKTOP-PC | Windows

Terminal 2 (Agent):
$ python pure_agent.py
[INFO] Connected to controller at http://localhost:5000
[INFO] Agent ID: abc12345-6789-...
[INFO] Waiting for commands...

Browser (http://localhost:5000):
> Select agent: abc12345
> Type command: dir
> Press Enter
> See output: [listing of files]
> Type command: ipconfig
> Press Enter
> See output: [network configuration]
> Click "Shutdown" when done

Terminal 2:
[INFO] Shutdown requested by controller
[INFO] Agent stopped - No cleanup needed
```

---

## 🔄 Differences from client.py

### Code Comparison:

```python
# client.py (Original) - Line count: 10,000+
# - 18+ UAC bypass methods
# - Multiple persistence mechanisms
# - Registry modifications
# - Stealth techniques
# - Screen streaming
# - Keylogging
# - Anti-detection
# - Defender disabling

# pure_agent.py (Clean) - Line count: 350
# - Command execution only
# - System information
# - Socket.IO communication
# - No UAC bypasses
# - No persistence
# - No registry changes
# - No stealth
# - Ethical design
```

### File Size:
- `client.py`: ~380 KB
- `pure_agent.py`: ~12 KB

### Cleanup Required:
- `client.py`: **YES** - Must run `restore.bat`
- `pure_agent.py`: **NO** - Just close it, done!

---

## 🎯 When to Use Which

### Use `client.py` when:
- Penetration testing (authorized)
- Red team exercises
- Security research
- Testing defenses
- **With proper authorization**

### Use `pure_agent.py` when:
- IT support
- System administration
- Educational purposes
- Personal machines
- **Ethical, transparent control**

---

## 📦 Files

```
pure_agent.py           # Clean agent (this file)
controller.py           # Original controller (yours)
requirements-pure.txt   # Dependencies
PURE_AGENT_README.md   # This documentation
```

---

## 🎉 Summary

**Pure Agent** is a **clean, ethical, simple** remote control agent:

✅ **Compatible** - Works with your existing `controller.py`
✅ **Clean** - No UAC, no persistence, no registry
✅ **Simple** - 350 lines vs 10,000+
✅ **Ethical** - Respects security, transparent
✅ **Safe** - No admin required, no system changes
✅ **Easy** - No cleanup needed, just close and done

**Perfect for:**
- IT support teams
- System administrators
- Educational use
- Personal projects
- Ethical testing

**Start using:**
```bash
python pure_agent.py
# Opens in your existing controller UI
# Control via commands
# Close when done (no cleanup!)
```

**Enjoy responsible remote control!** 🎮

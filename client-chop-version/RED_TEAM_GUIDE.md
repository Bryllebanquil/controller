# 🔥 Red Team Agent - Usage Guide

## 🎯 Overview

The Red Team Agent is an aggressive, fully automated cybersecurity testing tool designed for authorized penetration testing and red team operations. It implements comprehensive attack techniques including UAC bypasses, persistence mechanisms, stealth features, and advanced post-exploitation capabilities.

## ⚠️ IMPORTANT DISCLAIMER

**This tool is for AUTHORIZED CYBERSECURITY TESTING ONLY**
- Only use on systems you own or have explicit written permission to test
- Intended for red team exercises, penetration testing, and security research
- Misuse may violate laws and regulations
- Users are responsible for compliance with applicable laws

## 🚀 Quick Start

### Standard Deployment
```bash
cd client-chop-version
python main.py
```

### Quick Deployment (Faster, Limited Features)
```bash
python main.py --quick
```

## 🎭 Red Team Capabilities

### 💀 UAC Bypass Techniques (7 Methods)
1. **FodHelper Protocol** - ms-settings protocol hijacking
2. **ComputerDefaults** - ms-settings registry manipulation  
3. **EventVwr** - mscfile registry hijacking
4. **Sdclt** - Folder shell open command hijack
5. **WSReset** - AppX protocol handler abuse
6. **CMLua** - ICMLuaUtil COM interface exploitation
7. **Slui** - exefile shell open command hijack

### 👻 Stealth & Anti-Analysis
- **Process Hiding** - Hide from task manager and process lists
- **Event Log Clearing** - Remove forensic evidence
- **Timestamp Modification** - Blend with system files
- **String Obfuscation** - Evade signature detection
- **Anti-VM Detection** - Detect sandboxes and analysis environments
- **Debugger Detection** - Identify analysis tools

### 🔐 Persistence Mechanisms
- **Registry Run Keys** - Multiple startup locations
- **Startup Folder** - User startup persistence
- **Scheduled Tasks** - System-level task persistence
- **Service Installation** - Windows service persistence
- **WMI Events** - Event-driven persistence
- **COM Hijacking** - Component object model abuse

### 🛡️ Defense Evasion
- **Windows Defender Disable** - Multiple bypass methods
- **Firewall Exception** - Network access assurance
- **Removal Tool Disable** - Prevent cleanup tools
- **Task Manager Disable** - Block system monitoring
- **Registry Editor Disable** - Prevent manual cleanup

### 🔄 Advanced Techniques
- **Process Hollowing** - Code injection into legitimate processes
- **Process Injection** - DLL injection into trusted processes
- **Decoy Processes** - Create legitimate-looking processes

## 📊 Operational Modes

### Full Red Team Mode (Default)
Executes all 10 attack vectors:
1. Privilege Escalation
2. Comprehensive UAC Bypass
3. Stealth Features
4. Persistence Setup
5. Defender Disable
6. Process Hiding
7. Firewall Bypass
8. Startup Configuration
9. Component Initialization
10. Anti-Analysis Measures

### Quick Mode (`--quick` flag)
Executes essential 3 attack vectors:
1. Privilege Escalation
2. Stealth Features  
3. Component Initialization

## 🎯 Attack Flow

```
1. 🚀 System Analysis
   ├── Check current privileges
   ├── Detect OS version
   └── Identify security software

2. 💀 Privilege Escalation
   ├── Admin check
   ├── UAC bypass attempts
   └── Privilege validation

3. 👻 Stealth Activation
   ├── Process hiding
   ├── Log clearing
   └── Timestamp modification

4. 🔐 Persistence Establishment
   ├── Registry entries
   ├── Startup mechanisms
   └── Service installation

5. 🛡️ Defense Neutralization
   ├── Defender disable
   ├── Firewall bypass
   └── Tool disabling

6. 📡 C2 Communication
   ├── Controller connection
   ├── Agent registration
   └── Command channel

7. 🔄 Main Operation Loop
   ├── Command execution
   ├── Data collection
   └── Persistence monitoring
```

## 🔧 Configuration

### Environment Variables
```bash
# Controller settings
export FIXED_SERVER_URL="https://your-c2-server.com"
export CONTROLLER_URL="wss://your-websocket-server.com"

# Email notifications (optional)
export GMAIL_USERNAME="notifications@yourdomain.com"
export GMAIL_APP_PASSWORD="your-app-password"
export EMAIL_RECIPIENT="redteam@yourdomain.com"
```

### Command Line Options
- `--quick` or `-q`: Quick deployment mode
- No arguments: Full red team mode

## 📈 Success Metrics

The agent reports success rates for each operation:
- **Success Rate > 50%**: Fully weaponized status
- **Success Rate < 50%**: Partially weaponized status

### Typical Success Rates by Environment:
- **Undefended Windows 10**: 90-100%
- **Corporate Windows**: 60-80%
- **Hardened Systems**: 30-50%

## 🔍 Monitoring & Logging

### Real-time Status Display
```
🎯 Red Team Progress: [🔥🔥🔥⚫⚫] 3/5 exploits complete...
✅ privilege_escalation: elevation_successful
✅ stealth_features: stealth_features_3_activated
✅ persistence_setup: persistence_comprehensive
❌ defender_disable: defender_failed
⏰ process_hiding: Timed out
```

### Final Status Report
```
🎯 Red Team Success Rate: 8/10 (80.0%)
🚀 STATUS: FULLY WEAPONIZED
👤 Agent ID: a1b2c3d4-e5f6-7890-1234-567890abcdef
🔓 Privilege Level: ADMINISTRATOR
⏱️ Deployment Time: 45.3s
```

## 🛠️ Troubleshooting

### Common Issues

**Privilege Escalation Fails**
- Ensure UAC is not set to "Always notify"
- Try running from different user contexts
- Check for updated security patches

**Persistence Fails**
- Verify write permissions to target locations
- Check if admin privileges were obtained
- Ensure antivirus is not blocking

**Connection Issues**
- Verify controller URL is accessible
- Check firewall rules
- Ensure network connectivity

### Debug Mode
For verbose logging during development:
```python
# In config.py
DEBUG_MODE = True
SILENT_MODE = False
```

## 🎪 Demo Environment Setup

For testing and demonstration:

1. **Virtual Machine**: Windows 10/11 VM
2. **Network**: Isolated lab network
3. **Controller**: Local C2 server
4. **Monitoring**: Process monitor, network analysis

## 🔒 Operational Security

### For Red Team Operations:
- Use dedicated VMs for testing
- Isolated network environments
- Proper documentation of activities
- Coordinate with blue team
- Follow rules of engagement

### For Security Research:
- Academic/research use only
- Responsible disclosure
- Ethical guidelines compliance
- No unauthorized testing

## 📚 Technical Details

### Architecture
- **Modular Design**: 13 specialized modules
- **Multi-threaded**: Parallel execution
- **Asynchronous**: Non-blocking operations
- **Fault Tolerant**: Graceful degradation

### Dependencies
- Standard library (minimal external deps)
- Windows API (pywin32)
- Socket.IO for C2 communication
- Optional: Enhanced features with additional libs

## 🚨 Legal Notice

This software is provided for educational and authorized testing purposes only. The developers assume no liability for misuse. Users must:

1. Obtain proper authorization before use
2. Comply with all applicable laws
3. Use only in controlled environments
4. Document all activities
5. Follow responsible disclosure practices

**Unauthorized use is strictly prohibited and may result in civil and criminal liability.**

---

**Red Team Agent v2.1 - For Authorized Cybersecurity Professionals Only**

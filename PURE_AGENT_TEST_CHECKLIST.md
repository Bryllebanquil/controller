# Pure Agent - Test Checklist ✅

Use this checklist to verify that pure_agent.py is working correctly.

---

## 🎯 PRE-TEST SETUP

- [ ] Python 3.7+ installed
- [ ] Dependencies installed: `pip install python-socketio psutil websockets requests`
- [ ] Browser with JavaScript enabled
- [ ] Internet connection active

---

## ✅ TEST 1: AGENT STARTUP

**Run:**
```bash
python pure_agent.py
```

**✅ Expected Output:**
```
[TIME] ======================================================================
[TIME] Pure Agent - Connects to Original controller.py
[TIME] ======================================================================
[TIME] Agent ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
[TIME] Hostname: DESKTOP-NAME
[TIME] OS: Windows 10.0.26100
[TIME] User: USERNAME
[TIME] Server: https://agent-controller-backend.onrender.com
[TIME] ======================================================================
[TIME] 
[TIME] ✅ Features Available:
[TIME]   ✓ Command execution
[TIME]   ✓ System information
[TIME]   ✓ Process listing (via commands)
[TIME]   ✓ File browsing (via commands)
[TIME]   ✓ Network info (via commands)
[TIME] 
[TIME] ❌ Features NOT Available (No Privilege Escalation):
[TIME]   ✗ Screen streaming
[TIME]   ✗ Camera streaming
[TIME]   ✗ Audio streaming
[TIME]   ✗ Keylogging
[TIME]   ✗ UAC bypasses
[TIME]   ✗ Persistence
[TIME]   ✗ Registry modifications
[TIME] 
[TIME] This is a CLEAN agent - No UAC, No Persistence, No Escalation
[TIME] Compatible with original controller.py Socket.IO events
[TIME] 
[TIME] ======================================================================
[TIME] Connecting to controller at https://agent-controller-backend.onrender.com...
```

**Check:**
- [ ] Agent ID displayed (UUID format)
- [ ] Hostname correct
- [ ] OS version correct
- [ ] Username correct
- [ ] Server URL correct
- [ ] Feature list displayed
- [ ] "Connecting to controller" message shown

---

## ✅ TEST 2: CONNECTION

**✅ Expected Output (continued):**
```
[TIME] ✅ Connected to controller at https://agent-controller-backend.onrender.com
[TIME] Agent ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
[TIME] Agent Type: Pure Agent (No UAC/Persistence)
[TIME] Sending agent_connect event with data: {'agent_id': '...', 'name': '...', ...}
[TIME] ✅ Agent successfully registered with controller!
[TIME] Registration confirmed: {'agent_id': '...', 'status': 'success', 'message': '...'}
[TIME] ✅ Successfully connected!
[TIME] Waiting for commands from controller...
[TIME] The agent will appear in the controller UI
[TIME]
```

**Check:**
- [ ] "✅ Connected to controller" message shown
- [ ] "Sending agent_connect event" message shown
- [ ] "✅ Agent successfully registered" message shown
- [ ] "Registration confirmed" with status: success
- [ ] "Waiting for commands" message shown
- [ ] No error messages
- [ ] Agent stays connected (doesn't disconnect)

---

## ✅ TEST 3: HEARTBEAT

**✅ Expected Output (after 30-60 seconds):**
```
[TIME] ✅ Received pong from controller - Connection alive
[TIME] ✅ Received pong from controller - Connection alive
```

**Check:**
- [ ] "✅ Received pong" messages appear every ~30 seconds
- [ ] No connection errors
- [ ] Agent stays online

---

## ✅ TEST 4: DASHBOARD VISIBILITY

**Open Browser:**
```
https://agent-controller-backend.onrender.com/dashboard
```

**✅ Expected:**
1. Dashboard loads successfully
2. Login screen appears (if not logged in)
3. After login, main dashboard shows
4. Agent list visible on left sidebar

**In Agent List:**
- [ ] Agent appears with name: **Pure-Agent-HOSTNAME**
- [ ] Status indicator shows: **🟢 (green/online)**
- [ ] Platform shows: **Windows 10.0.26100** (or your OS)
- [ ] Username shows correctly
- [ ] CPU percentage displays (e.g., 15%)
- [ ] Memory percentage displays (e.g., 45%)

**If Agent NOT Visible:**
- [ ] Press Ctrl+F5 to hard refresh
- [ ] Check browser console (F12) for errors
- [ ] Verify agent terminal shows "✅ Agent successfully registered"
- [ ] Wait 5 seconds and refresh again

---

## ✅ TEST 5: AGENT SELECTION

**Click on Agent in List:**

**✅ Expected:**
- [ ] Agent card highlights/selects
- [ ] Command panel appears on right side
- [ ] "Command Execution" section visible
- [ ] Input box shows: "Enter command..."
- [ ] Send button visible
- [ ] Output section shows: "No output yet..."

---

## ✅ TEST 6: SIMPLE COMMAND

**Type in Command Box:**
```
whoami
```

**Press Enter or Click Send**

**✅ Expected in Output:**
```
$ whoami
HOSTNAME\USERNAME
```

**Check:**
- [ ] Command echo shows: `$ whoami`
- [ ] Output shows immediately (within 1-2 seconds)
- [ ] Output format is: `HOSTNAME\USERNAME`
- [ ] No error messages
- [ ] "Executing command..." disappears after output shows

**Agent Terminal Shows:**
```
[TIME] 📨 Received 'command' event: whoami (execution_id: exec_...)
[TIME] Executing command: whoami
[TIME] Command completed: 24 characters
[TIME] ✅ Sent command_result for: whoami
```

---

## ✅ TEST 7: PROCESS LIST COMMAND

**Type in Command Box:**
```
tasklist
```

**Press Enter**

**✅ Expected in Output:**
```
$ tasklist

Image Name                     PID Session Name        Session#    Mem Usage
========================= ======== ================ =========== ============
System Idle Process              0 Services                   0          8 K
System                           4 Services                   0      4,856 K
...
(full process list)
```

**Check:**
- [ ] Command executes successfully
- [ ] Full process list displays
- [ ] Output is readable and formatted
- [ ] No truncation or errors
- [ ] Output appears in 2-3 seconds

---

## ✅ TEST 8: NETWORK INFO COMMAND

**Type in Command Box:**
```
ipconfig
```

**Press Enter**

**✅ Expected in Output:**
```
$ ipconfig

Windows IP Configuration

Ethernet adapter Ethernet:
   IPv4 Address. . . . . . . . . . . : 192.168.x.x
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 192.168.x.1
```

**Check:**
- [ ] Network configuration displays
- [ ] IP addresses visible
- [ ] Multiple adapters shown (if available)
- [ ] Output complete and readable

---

## ✅ TEST 9: DIRECTORY LISTING

**Type in Command Box:**
```
dir
```

**Press Enter**

**✅ Expected in Output:**
```
$ dir

 Volume in drive C has no label.
 Directory of C:\Users\USERNAME\...

10/03/2025  09:00 PM    <DIR>          .
10/03/2025  09:00 PM    <DIR>          ..
...
(file and directory listing)
```

**Check:**
- [ ] Directory contents display
- [ ] Files and folders listed
- [ ] Dates and sizes shown
- [ ] Output readable

---

## ✅ TEST 10: SYSTEM INFO COMMAND

**Type in Command Box:**
```
systeminfo
```

**Press Enter**

**✅ Expected in Output:**
```
$ systeminfo

Host Name:                 HOSTNAME
OS Name:                   Microsoft Windows 11
OS Version:                10.0.26100 N/A Build 26100
OS Manufacturer:           Microsoft Corporation
...
(full system information)
```

**Check:**
- [ ] System information displays
- [ ] Hostname correct
- [ ] OS details correct
- [ ] Hardware info shown
- [ ] Output complete (may be long)

---

## ✅ TEST 11: MULTIPLE COMMANDS

**Execute These Commands in Sequence:**

1. `whoami`
2. `hostname`  
3. `echo Hello from Pure Agent`
4. `cd`
5. `date /t`

**Check:**
- [ ] All commands execute successfully
- [ ] Each output displays correctly
- [ ] Output accumulates in terminal (scrollable)
- [ ] No commands interfere with each other
- [ ] Agent stays responsive

---

## ✅ TEST 12: ERROR HANDLING

**Type Invalid Command:**
```
invalid_command_xyz
```

**Press Enter**

**✅ Expected in Output:**
```
$ invalid_command_xyz
'invalid_command_xyz' is not recognized as an internal or external command,
operable program or batch file.
```

**Check:**
- [ ] Error message displays
- [ ] No agent crash
- [ ] Agent stays connected
- [ ] Can send another command after error

---

## ✅ TEST 13: REAL-TIME UPDATES

**Leave Dashboard Open for 2 Minutes**

**Check:**
- [ ] Agent stays online (green indicator)
- [ ] CPU percentage updates every ~60 seconds
- [ ] Memory percentage updates every ~60 seconds
- [ ] No disconnection messages
- [ ] Pong messages continue in agent terminal

---

## ✅ TEST 14: BROWSER CONSOLE

**Open Browser DevTools (F12) → Console Tab**

**✅ Expected Messages:**
```
🔍 SocketProvider: Connected to Neural Control Hub
🔍 SocketProvider: operator_connect event emitted
🔍 SocketProvider: Received event 'agent_list_update': [...]
🔍 SocketProvider: Successfully joined room: operators
🔍 SocketProvider: Command result received: {...}
🔍 SocketProvider: Adding command output: ...
```

**Check:**
- [ ] Connection messages appear
- [ ] `operator_connect` emitted
- [ ] `agent_list_update` received
- [ ] `operators` room joined
- [ ] `command_result` events received
- [ ] No error messages in red

---

## ✅ TEST 15: NETWORK WEBSOCKET

**Open Browser DevTools (F12) → Network Tab**
**Filter: WS (WebSocket)**
**Click on WebSocket Connection**
**Go to Messages Tab**

**✅ Expected Messages:**

**Sent (↑):**
```
{"0":"operator_connect"}
{"0":"execute_command","1":{"agent_id":"xxx","command":"whoami"}}
```

**Received (↓):**
```
{"0":"agent_list_update","1":{...}}
{"0":"command_result","1":{"agent_id":"xxx","output":"...","success":true}}
```

**Check:**
- [ ] WebSocket connection established
- [ ] `operator_connect` sent
- [ ] `agent_list_update` received
- [ ] `execute_command` sent when command typed
- [ ] `command_result` received with output
- [ ] Messages flow in both directions

---

## ✅ TEST 16: AGENT RECONNECTION

**Stop Agent (Ctrl+C in Terminal)**

**✅ Expected:**
```
^C
Shutting down...
Agent stopped - No cleanup needed (no persistence)
No registry entries, no scheduled tasks, no files left behind
```

**Check Dashboard:**
- [ ] Agent changes to offline or disappears
- [ ] Status indicator turns gray/red

**Restart Agent:**
```bash
python pure_agent.py
```

**Check:**
- [ ] Agent reconnects successfully
- [ ] Registers again with controller
- [ ] Appears in dashboard again (may be new agent ID)
- [ ] Can execute commands again

---

## ✅ TEST 17: STRESS TEST

**Execute 5 Commands Rapidly:**
```
whoami
hostname
cd
echo test1
echo test2
```

**Check:**
- [ ] All commands execute
- [ ] All outputs display
- [ ] No commands lost
- [ ] No output mixing
- [ ] Agent stays stable
- [ ] Dashboard responsive

---

## 🎯 TEST SUMMARY

### Minimum Passing Criteria:

**MUST PASS:**
- [x] Test 1: Agent starts without errors
- [x] Test 2: Agent connects and registers
- [x] Test 4: Agent appears in dashboard
- [x] Test 6: Simple command executes and shows output
- [x] Test 13: Agent stays online for 2+ minutes

**SHOULD PASS:**
- [x] Test 3: Heartbeat messages appear
- [x] Test 7-10: Various commands execute correctly
- [x] Test 12: Error handling works
- [x] Test 16: Reconnection works

**OPTIONAL:**
- [x] Test 14-15: Developer tools show correct messages
- [x] Test 17: Handles rapid commands

---

## ✅ IF ALL TESTS PASS

**CONGRATULATIONS! 🎉**

Your pure_agent.py is:
- ✅ Properly configured
- ✅ Successfully connecting
- ✅ Visible in dashboard
- ✅ Executing commands
- ✅ Showing output correctly
- ✅ Maintaining connection
- ✅ Handling errors gracefully

**READY FOR USE!** 🚀

---

## ❌ IF TESTS FAIL

### Quick Fixes:

**Agent doesn't connect:**
- Check internet connection
- Verify SERVER_URL is correct
- Check firewall settings
- Try debug version: `python pure_agent_debug.py`

**Agent doesn't appear in dashboard:**
- Hard refresh browser: Ctrl+F5
- Check browser console (F12)
- Verify agent shows "✅ Agent successfully registered"
- Wait 10 seconds and refresh

**Commands don't show output:**
- Check browser console for errors
- Verify operator_connect was sent
- Check Network → WS → Messages
- Restart agent and dashboard

**See Documentation:**
- `PURE_AGENT_TROUBLESHOOTING.md` - Detailed troubleshooting
- `PURE_AGENT_VERIFICATION_COMPLETE.md` - Implementation verification
- `PURE_AGENT_WORKING_SUMMARY.md` - Complete user guide

---

## 📊 TEST RESULTS

**Date:** ________________  
**Time:** ________________  
**Tester:** ________________

**Results:**
- Tests Passed: ______ / 17
- Tests Failed: ______
- Tests Skipped: ______

**Status:**
- [ ] ✅ ALL PASS - Ready for use
- [ ] ⚠️ PARTIAL - Some issues found
- [ ] ❌ FAIL - Needs troubleshooting

**Notes:**
_______________________________________
_______________________________________
_______________________________________

---

**SAVE THIS CHECKLIST FOR FUTURE REFERENCE** 📋

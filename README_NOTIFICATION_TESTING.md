# Notification Popup Testing Guide

## Overview
This guide explains how to test the notification popup system in the agent-controller dashboard.

## Test Scripts

### 1. Simple Test Script (Quick Test)
**File:** `test_notifications_simple.py`

**Purpose:** Quick 5-notification test to verify basic functionality

**Usage:**
```bash
# Default (localhost:5000)
python3 test_notifications_simple.py

# Custom controller URL
python3 test_notifications_simple.py http://your-controller:5000
```

**What it tests:**
- ✅ Success notification (Camera Stream)
- ⚠️ Warning notification (Already Active)
- ❌ Error notification (File Not Found)
- ℹ️ Info notification (Download Started)
- ✅ Command notification (Executed)

**Duration:** ~30 seconds

---

### 2. Comprehensive Test Script (Full Test)
**File:** `test_notifications.py`

**Purpose:** Complete test suite with 39+ notifications covering all features

**Usage:**
```bash
# Default (localhost:5000)
python3 test_notifications.py

# Custom controller URL
python3 test_notifications.py http://your-controller:5000
```

**What it tests:**

#### Phase 1: Basic Notification Types (12 notifications)
- Success, Warning, Error, Info notifications
- All categories: agent, system, security, command

#### Phase 2: Feature-Specific Tests (27 notifications)
- **Streaming (5 tests):**
  - Screen/Audio/Camera start/stop
  - Already active warnings
  - Stream failures
  
- **File Operations (6 tests):**
  - Upload/Download success
  - File save/delete
  - File not found errors
  
- **Command Execution (5 tests):**
  - Command executed
  - Process list retrieval
  - Directory listing
  - Permission errors
  
- **Security (4 tests):**
  - UAC prompts
  - Privilege escalation
  - Remote control errors
  
- **Connection (3 tests):**
  - Agent connected
  - Connection unstable
  - Connection errors
  
- **WebRTC (4 tests):**
  - WebRTC start/stop
  - Fallback notifications
  - Connection failures

**Duration:** ~3-4 minutes

---

## Prerequisites

### 1. Install Socket.IO Client
```bash
pip install python-socketio[client]
```

### 2. Start the Controller
```bash
cd /workspace
python3 controller.py
```

The controller should be running on `http://localhost:5000`

### 3. Open the Dashboard
Open your browser and navigate to:
```
http://localhost:5000
```

Make sure you're logged in and can see the dashboard.

---

## Running the Tests

### Quick Test (Recommended First)
```bash
cd /workspace
python3 test_notifications_simple.py
```

**Expected Output:**
```
============================================================
🧪 SIMPLE NOTIFICATION TEST
============================================================
Controller: http://localhost:5000
Agent ID: test-a1b2c3d4
============================================================

📡 Connecting to controller...
✅ Connected to controller!
📝 Registering as agent: test-a1b2c3d4

📤 Sending test notifications...

1️⃣ Success notification (Camera Stream)
2️⃣ Warning notification (Already Active)
3️⃣ Error notification (File Not Found)
4️⃣ Info notification (Download Started)
5️⃣ Command notification (Executed)

✅ All test notifications sent!
🔔 Check the dashboard for popup notifications!
⏳ Waiting 5 seconds before disconnecting...

👋 Disconnected from controller

============================================================
✅ TEST COMPLETED!
============================================================
```

### Full Test Suite
```bash
cd /workspace
python3 test_notifications.py
```

**Expected Output:**
- Detailed progress for each notification
- Phase 1: Basic types
- Phase 2: Feature-specific tests
- Final summary with statistics

---

## What to Watch For in the Dashboard

### 1. Notification Bell Icon
- Should show unread count
- Located in the top-right corner

### 2. Popup Notifications
Each notification should appear with:
- **Success (Green):** ✅ Checkmark icon
- **Warning (Yellow):** ⚠️ Warning triangle
- **Error (Red):** 🛡️ Shield icon
- **Info (Blue):** ℹ️ Info icon

### 3. Notification Center
- Click the bell icon to open
- Should list all notifications
- Can filter by category (all/unread/agent/system/security)
- Can mark as read
- Can clear all

### 4. Real-time Updates
- Notifications appear immediately
- No page refresh required
- Multiple notifications queue properly

---

## Troubleshooting

### Problem: Script can't connect
**Solution:**
```bash
# Check if controller is running
curl http://localhost:5000/api/health

# Check controller logs for connection errors
# Verify firewall isn't blocking port 5000
```

### Problem: No popups appear
**Possible causes:**
1. Dashboard not open in browser
2. JavaScript console errors
3. Socket.IO connection issue

**Debug steps:**
```javascript
// Open browser console (F12)
// Check for Socket.IO connection
console.log('Socket connected:', socket.connected);

// Check for notification handler
socket.on('notification', (data) => {
    console.log('Notification received:', data);
});
```

### Problem: Notifications appear but wrong format
**Check:**
1. Notification data structure
2. NotificationCenter component rendering
3. Browser console for errors

---

## Testing Different Scenarios

### Test Success Notifications
```python
sio.emit('agent_notification', {
    'agent_id': 'test-agent',
    'type': 'success',
    'title': 'Your Title',
    'message': 'Your message here',
    'category': 'agent'  # or 'system', 'security', 'command'
})
```

### Test Error Notifications
```python
sio.emit('agent_notification', {
    'agent_id': 'test-agent',
    'type': 'error',
    'title': 'Error Title',
    'message': 'Detailed error message',
    'category': 'system'
})
```

### Test Multiple Quick Notifications
```python
for i in range(10):
    sio.emit('agent_notification', {
        'agent_id': 'test-agent',
        'type': 'info',
        'title': f'Test {i+1}',
        'message': f'Testing notification {i+1}',
        'category': 'agent'
    })
    time.sleep(1)
```

---

## Verification Checklist

After running tests, verify:

- [ ] ✅ Success notifications appear in green
- [ ] ⚠️ Warning notifications appear in yellow
- [ ] ❌ Error notifications appear in red
- [ ] ℹ️ Info notifications appear in blue
- [ ] 🔔 Bell icon shows unread count
- [ ] 📋 Notification center lists all notifications
- [ ] 🔄 Real-time updates work
- [ ] 🗑️ Can clear notifications
- [ ] 📖 Can mark as read
- [ ] 🔍 Can filter by category
- [ ] 📱 Notifications persist across page refresh
- [ ] ⏱️ Timestamps are correct
- [ ] 🎯 Categories match correctly
- [ ] 🖼️ Icons display properly

---

## Expected Behavior

### Notification Lifecycle
1. **Agent sends notification** → `client.py` emits `agent_notification`
2. **Controller receives** → `controller.py` handles via `@socketio.on('agent_notification')`
3. **Controller forwards** → Emits `notification` to operators room
4. **UI receives** → `SocketProvider.tsx` receives via `socket.on('notification')`
5. **Popup appears** → `NotificationCenter.tsx` displays popup
6. **User sees** → 🔔 Popup notification on dashboard!

### Notification Structure
```javascript
{
  id: "uuid-here",
  type: "success" | "warning" | "error" | "info",
  title: "Notification Title",
  message: "Detailed message here",
  timestamp: Date,
  agentId: "agent-id",
  read: false,
  category: "agent" | "system" | "security" | "command"
}
```

---

## Manual Testing

If you want to manually test from `client.py`:

```python
# Add to client.py for testing
def test_notification():
    emit_system_notification(
        'success',
        'Manual Test',
        'This is a manual test notification'
    )

# Call it from any function
test_notification()
```

---

## Performance Notes

- Each notification is ~1-2KB
- Test script sends 39 notifications = ~50-75KB total
- Should handle 100+ notifications/second easily
- Dashboard updates in real-time with no lag

---

## Success Criteria

✅ **Test passes if:**
1. All notifications appear in dashboard
2. Correct colors for each type
3. Proper icons displayed
4. No JavaScript errors in console
5. No Python errors in controller logs
6. Bell icon updates correctly
7. Notification center shows all items

---

## Next Steps After Testing

1. ✅ Verify all notification types work
2. ✅ Test with real agent actions (camera, file ops, etc.)
3. ✅ Check notification persistence
4. ✅ Test multiple simultaneous notifications
5. ✅ Verify cross-browser compatibility
6. ✅ Test notification clearing/marking as read

---

## Additional Resources

- **Notification Flow Diagram:** See main documentation
- **Socket.IO Events:** `controller.py` line 4767
- **UI Component:** `NotificationCenter.tsx`
- **Agent Emission:** `client.py` notification functions

---

## Support

If you encounter issues:
1. Check controller logs: `tail -f controller.log`
2. Check browser console (F12)
3. Verify Socket.IO connection
4. Check network tab for WebSocket frames
5. Ensure all files are saved and controller restarted

---

**Happy Testing! 🎉**

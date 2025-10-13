# Notification System Troubleshooting Guide

## Issue: Notifications Not Appearing in Dashboard

### Current Status
✅ **Backend (Controller)**: Working perfectly
- Notifications are being received from agents
- Notifications are being emitted to the 'operators' room
- All logs show successful emission

❌ **Frontend (Dashboard)**: Not displaying notifications
- Socket.IO is connected
- But notifications aren't showing up

### Root Cause Analysis

The issue is likely one of the following:

#### 1. **Agent ID Format Mismatch**
- **Backend sends**: `agent_id` (snake_case)
- **Frontend expects**: `agentId` (camelCase)

**Fix Applied**: Updated NotificationCenter.tsx to handle both formats:
```typescript
agentId: (notification.agent_id as string) || (notification.agentId as string)
```

#### 2. **Missing Notification Properties**
The notification needs ALL required fields:
- `id` ✅
- `type` ✅
- `title` ✅
- `message` ✅
- `timestamp` ✅
- `category` ✅
- `agentId` (optional) ✅
- `read` ✅

**Fix Applied**: Added explicit parsing with defaults for all fields

#### 3. **Console Logging Added**
Added debug logs to see what's being received:
```typescript
console.log('🔔 NotificationCenter received notification:', notification);
console.log('✅ Parsed notification:', newNotification);
```

### How to Debug

#### Option 1: Use Debug Tool (Recommended)

1. **Deploy the updated controller.py to Render**
2. **Open the debug page**:
   ```
   https://agent-controller-backend.onrender.com/debug.html
   ```
3. **Run the test script**:
   ```bash
   python test_notifications.py
   ```
4. **Watch the debug page** - it will show:
   - Connection status
   - Real-time notifications as they arrive
   - Statistics (success/warning/error counts)
   - Full notification data

#### Option 2: Check Browser Console

1. Open the dashboard: `https://agent-controller-backend.onrender.com/dashboard`
2. Open Browser Console (F12)
3. Run the test script
4. Look for:
   ```
   🔔 NotificationCenter received notification: {...}
   ✅ Parsed notification: {...}
   ```

If you see these logs, notifications ARE being received, but the UI component might not be rendering them.

#### Option 3: Check Socket.IO Connection

In Browser Console:
```javascript
// Check if socket is connected
window.socket = socket;  // Expose socket for debugging

// Listen to ALL events
socket.onAny((event, ...args) => {
    console.log('Event:', event, args);
});

// Check if in operators room
socket.emit('operator_connect');
```

### Verification Steps

1. ✅ **Backend logs show emissions**: `📢 Notification emitted: Camera Stream Started (agent)`
2. ✅ **Operator is in room**: `Operator joined 'operators' room`
3. ❓ **Frontend receives notification**: Check console for `🔔 NotificationCenter received`
4. ❓ **UI updates**: Check if bell icon count increases

### Testing Workflow

```bash
# Terminal 1: Run test script
python test_notifications.py

# Browser 1: Dashboard
https://agent-controller-backend.onrender.com/dashboard
# Open console (F12) and watch for notification logs

# Browser 2: Debug Tool
https://agent-controller-backend.onrender.com/debug.html
# Watch real-time notifications
```

### Expected Behavior

#### In Render Logs:
```
Agent test-agent-5caadda7 connected with SID VZfcD9Y5u7R9cuYdAAAF
📢 Notification emitted: Camera Stream Started (agent)
📢 Agent notification forwarded from test-agent-5caadda7
```

#### In Browser Console:
```
🔔 NotificationCenter received notification: {
  id: "notif_1728677405_abc123",
  type: "success",
  title: "Camera Stream Started",
  message: "Camera streaming started successfully with high quality",
  category: "agent",
  agent_id: "test-agent-5caadda7",
  timestamp: "2025-10-11T21:40:05.123Z",
  read: false
}
✅ Parsed notification: {...}
```

#### In Debug Tool:
- Connection Status: ✅ Connected
- Total Notifications: Incrementing
- Live Notifications: Showing each notification as it arrives

### Quick Fixes to Try

#### Fix 1: Rebuild Frontend
```bash
cd "agent-controller ui v2.1-modified"
npm run build
```

Then deploy the updated `dist` folder.

#### Fix 2: Hard Refresh Dashboard
1. Open dashboard
2. Press `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
3. This clears cached JavaScript

#### Fix 3: Check Socket.IO CORS
Make sure the dashboard URL is in the CORS list in `controller.py`:
```python
cors_allowed_origins = [
    'https://agent-controller-backend.onrender.com',
    # ... other URLs
]
```

#### Fix 4: Verify Operator Connection
In dashboard console:
```javascript
// Check current socket state
console.log('Socket connected:', socket?.connected);
console.log('Socket ID:', socket?.id);

// Manually request agent list (this joins operators room)
socket.emit('get_agent_list');
```

### Common Issues

#### Issue 1: "Socket is undefined"
**Cause**: Socket.IO not initialized
**Fix**: Refresh page, check SocketProvider is wrapping the app

#### Issue 2: Notifications received but not displayed
**Cause**: NotificationCenter component not rendering
**Fix**: Check if NotificationCenter is mounted in the dashboard

#### Issue 3: Old cached code
**Cause**: Browser using old JavaScript
**Fix**: Hard refresh or clear cache

#### Issue 4: CORS error
**Cause**: Frontend domain not in CORS whitelist
**Fix**: Add domain to controller.py CORS list

### Manual Test

You can manually emit a notification from the browser console:

```javascript
// After connecting to socket
socket.emit('agent_notification', {
    agent_id: 'test-manual',
    type: 'success',
    title: 'Manual Test',
    message: 'This is a manual test notification',
    category: 'agent',
    timestamp: new Date().toISOString()
});
```

If this works, the Socket.IO connection is fine, and the issue is in how the agent sends notifications.

### Next Steps

1. **Deploy Updated Code**:
   - Updated `NotificationCenter.tsx` with better parsing
   - Added debug logging
   - Added browser notifications

2. **Access Debug Tool**:
   - `/debug.html` route on your controller URL
   - Real-time visualization of notifications

3. **Check Console Logs**:
   - Browser console (F12)
   - Look for `🔔` emoji logs

4. **Report Findings**:
   - Are notifications appearing in debug tool?
   - Do you see console logs?
   - What's the exact error (if any)?

### Success Indicators

✅ Notifications working if you see:
1. Bell icon count increasing
2. Notifications list populating
3. Console logs showing received notifications
4. Debug tool showing live notifications

❌ Still broken if:
1. No console logs at all
2. Debug tool shows "0 Total Notifications"
3. Bell icon stays at 0
4. No error in console

### Contact Information

If still not working after these steps, provide:
1. Browser console screenshot (F12)
2. Debug tool screenshot
3. Render logs during test
4. Browser network tab (check for failed requests)

# Agent-Controller UI v2.1 - Notification & Features Testing Guide

## Overview
The notification system in agent-controller UI v2.1 is a real-time notification center that displays alerts via:
- **Popup notifications** (toast notifications)
- **Notification Center** (accessible via the Bell icon in the header)
- **Real-time updates** via WebSocket/Socket.IO

---

## How to Access the Notification Center

### 1. Start the Application
```bash
# Make sure your controller backend is running
python controller.py

# Or if using the deployment
# The render.yaml is configured to build and deploy automatically
```

### 2. Access the UI
- Navigate to your controller URL (e.g., `http://localhost:8080` or your deployed URL)
- Look for the **Bell icon** 🔔 in the top-right header
- Click it to open the **Notification Center** panel

---

## How Notifications are Triggered

### Automatic Triggers (Real-time Events)

#### 1. **Agent Connection Notifications**
- **Trigger**: When a new agent connects to the controller
- **Type**: Success notification (green)
- **Category**: Agent
- **Message**: "Agent Connected - Agent {name} ({id}) has connected successfully"

**To Test**:
```bash
# Run a client/agent to connect
python client.py
```

#### 2. **Agent Disconnection Notifications**
- **Trigger**: When an agent disconnects
- **Type**: Warning notification (yellow)
- **Category**: Agent
- **Message**: "Agent Disconnected - Agent {name} ({id}) has disconnected"

**To Test**:
- Connect a client
- Close/stop the client
- Check the notification center

#### 3. **Bulk Action Notifications**
- **Trigger**: When performing bulk actions on multiple agents
- **Type**: Success/Warning/Error based on results
- **Category**: System
- **Messages**:
  - Success: "Bulk Action Completed - {action} successfully executed on all {count} agent(s)"
  - Warning: "Bulk Action Partially Completed - {action} executed on {success}/{total} agent(s)"
  - Error: "Bulk Action Failed - {action} failed on all {count} agent(s)"

**To Test**:
1. Connect multiple agents
2. Select multiple agents in the UI
3. Perform a bulk action (e.g., screenshot, system info)
4. Watch for notifications

---

## Notification System API Endpoints

The following endpoints are available for managing notifications:

### 1. Get All Notifications
```bash
GET /api/notifications?limit=100&category=agent&unread_only=false
```

**Parameters**:
- `limit` (optional): Max number of notifications (default: 100, max: 1000)
- `category` (optional): Filter by category (agent, system, security, command)
- `unread_only` (optional): Only show unread notifications (true/false)

**Test with curl**:
```bash
curl -X GET "http://localhost:8080/api/notifications?limit=50" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

### 2. Mark Notification as Read
```bash
POST /api/notifications/{notification_id}/read
```

### 3. Mark All as Read
```bash
POST /api/notifications/read-all
```

### 4. Delete Notification
```bash
DELETE /api/notifications/{notification_id}
```

### 5. Get Notification Stats
```bash
GET /api/notifications/stats
```

**Response Example**:
```json
{
  "success": true,
  "stats": {
    "total": 25,
    "unread": 5,
    "read": 20,
    "by_category": {
      "agent": 15,
      "system": 8,
      "security": 2
    },
    "by_type": {
      "success": 18,
      "warning": 5,
      "error": 2
    }
  }
}
```

---

## Notification Categories & Types

### Categories
1. **agent**: Agent connection/disconnection events
2. **system**: Bulk actions, system events
3. **security**: Security-related alerts
4. **command**: Command execution results

### Types (Visual Styling)
1. **success**: Green icon (CheckCircle) - Successful operations
2. **warning**: Yellow icon (AlertTriangle) - Warnings
3. **error**: Red icon (Shield) - Errors
4. **info**: Blue icon (Info) - Information

---

## How to Manually Trigger Test Notifications

### Method 1: Use Python to Send Notifications (Backend)

Add this code to trigger test notifications from the backend:

```python
# In controller.py or create a test script
from controller import emit_system_notification, emit_agent_notification, emit_security_notification

# Test system notification
emit_system_notification('info', 'Test System Alert', 'This is a test system notification')

# Test agent notification  
emit_agent_notification('success', 'Test Agent Alert', 'Agent test message', 'agent', 'test-agent-id')

# Test security notification
emit_security_notification('warning', 'Security Test', 'Security alert test', 'test-agent-id')
```

### Method 2: Create a Test Endpoint (Recommended)

Add this to your `controller.py`:

```python
@app.route('/api/test/notification', methods=['POST'])
@require_auth
def test_notification():
    """Trigger a test notification for debugging"""
    try:
        data = request.json or {}
        notif_type = data.get('type', 'info')
        title = data.get('title', 'Test Notification')
        message = data.get('message', 'This is a test notification')
        category = data.get('category', 'system')
        
        notification_id = emit_notification(notif_type, title, message, category)
        
        return jsonify({
            'success': True,
            'notification_id': notification_id,
            'message': 'Test notification sent'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

Then test with:
```bash
curl -X POST "http://localhost:8080/api/test/notification" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "success",
    "title": "Test Alert",
    "message": "This is a test message",
    "category": "system"
  }' \
  --cookie "session=YOUR_SESSION_COOKIE"
```

---

## Features in Agent-Controller UI v2.1

### 1. **Real-time Notification Center**
- Bell icon in header with unread count badge
- Slide-out panel showing all notifications
- Filter by: All, Unread, Agents, System, Security
- Mark as read/delete individual notifications
- Mark all as read

### 2. **Notification Filters**
- **All**: Shows all notifications
- **Unread**: Shows only unread notifications (with count badge)
- **Agents**: Shows only agent-related notifications
- **System**: Shows only system notifications
- **Security**: Shows only security-related notifications

### 3. **Real-time Updates via WebSocket**
- Automatic notification updates via Socket.IO
- No page refresh needed
- Instant popup when new notifications arrive

### 4. **Notification Storage**
- Backend stores last 1000 notifications in memory
- Automatically prunes old notifications
- Thread-safe with locking mechanism

---

## Testing Checklist

### ✅ Basic Functionality
- [ ] Open notification center by clicking bell icon
- [ ] View unread count badge
- [ ] Filter notifications by category
- [ ] Mark individual notification as read
- [ ] Mark all as read
- [ ] Delete individual notification

### ✅ Real-time Features
- [ ] Connect a new agent and watch for notification
- [ ] Disconnect an agent and watch for notification
- [ ] Perform bulk action and check notification
- [ ] Verify notifications appear without refresh

### ✅ API Testing
- [ ] Test GET /api/notifications
- [ ] Test GET /api/notifications/stats
- [ ] Test POST /api/notifications/read-all
- [ ] Test DELETE /api/notifications/{id}

---

## Troubleshooting

### Notifications Not Appearing?

1. **Check WebSocket Connection**
   - Open browser DevTools → Network tab
   - Look for WebSocket connection (ws:// or wss://)
   - Should show "101 Switching Protocols"

2. **Check Browser Console**
   - Look for Socket.IO connection errors
   - Check for JavaScript errors

3. **Check Backend Logs**
   - Look for "📢 Notification emitted" messages
   - Verify Socket.IO is initialized correctly

4. **Verify Authentication**
   - Make sure you're logged in
   - Check session cookie is present

### Test WebSocket Connection

Open browser console and run:
```javascript
// Check if socket is connected
console.log('Socket connected:', socket.connected);

// Listen for notifications
socket.on('notification', (data) => {
  console.log('Notification received:', data);
});
```

---

## Quick Start Testing

### Fastest Way to See Notifications:

1. **Start the controller**:
   ```bash
   python controller.py
   ```

2. **Open the dashboard** in your browser

3. **Connect a test agent**:
   ```bash
   python client.py
   ```

4. **Watch the notification center** - You should see:
   - Bell icon badge increment
   - "Agent Connected" notification appear
   - Real-time update without refresh

5. **Stop the agent** (Ctrl+C) - You should see:
   - "Agent Disconnected" notification

---

## Render.yaml Configuration

Your `render.yaml` is already configured correctly:
```yaml
buildCommand: |
  pip install -r requirements-controller.txt
  cd "agent-controller ui v2.1-modified" && npm install && npm run build && cd ..
```

This ensures:
- Backend dependencies installed
- Frontend built and ready
- Static files served from the build directory

---

## Next Steps

1. **Deploy to Render** (if not already deployed)
2. **Access your deployed URL**
3. **Connect test agents** to see notifications in action
4. **Test all notification filters and features**
5. **Monitor backend logs** for notification emission

---

## Additional Notes

- Notifications are stored in-memory (not persistent)
- Max 1000 notifications stored at a time
- Real-time delivery via Socket.IO
- All notifications are timestamped
- Unread count updates automatically
- Works on mobile and desktop

---

For more information, check:
- `controller.py` lines 272-374 (Notification system)
- `agent-controller ui v2.1-modified/src/components/NotificationCenter.tsx` (UI component)

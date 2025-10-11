# Test Notifications with Real Agent Connections

## ✅ This Works RIGHT NOW (No deployment needed!)

Your Render instance already has the notification system working for **automatic events**. You can test it immediately:

### Step 1: Open Your UI
1. Go to: https://agent-controller-backend.onrender.com
2. Login with your admin password
3. Look for the **Bell icon (🔔)** in the top-right corner

### Step 2: Connect a Test Agent

Run your client to trigger a **real notification**:

```bash
# Make sure your client.py is configured to connect to Render
python client.py
```

**Configuration needed in client.py:**
```python
# Update this line in client.py:
CONTROLLER_URL = "https://agent-controller-backend.onrender.com"
```

### Step 3: Watch the Notifications!

You should see:
- 🟢 **Green "Agent Connected"** notification when client connects
- 🟡 **Yellow "Agent Disconnected"** notification when you stop the client (Ctrl+C)

### Step 4: Test Bulk Actions

1. Connect 2-3 agents
2. In the UI, select multiple agents
3. Perform a bulk action (e.g., "Get System Info" on all)
4. Watch for **system notifications** about the bulk action results

---

## 🎯 What You Can Test NOW

### ✅ Notification Center Features
- Click the bell icon to open notification panel
- See real-time notifications as they arrive
- Filter by: All, Unread, Agents, System, Security
- Click a notification to mark as read
- Click the ❌ to delete notifications
- Click "Mark all as read" at the top

### ✅ Real-time Updates
- Keep the UI open
- Connect/disconnect agents in the terminal
- Watch notifications appear instantly (no refresh needed!)

### ✅ API Endpoints (These work now!)

```bash
# View all notifications
curl "https://agent-controller-backend.onrender.com/api/notifications?limit=50" \
  --cookie "session=YOUR_SESSION"

# View notification stats
curl "https://agent-controller-backend.onrender.com/api/notifications/stats" \
  --cookie "session=YOUR_SESSION"

# Mark all as read
curl -X POST "https://agent-controller-backend.onrender.com/api/notifications/read-all" \
  --cookie "session=YOUR_SESSION"
```

---

## 🔄 After Render Deployment

Once you manually deploy on Render (or wait for auto-deploy), the test endpoint will work:

```bash
python test_notifications.py
# Choose option 2 for full test suite
```

Until then, use real agent connections to test! 🚀

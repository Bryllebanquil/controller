# Test Notifications Using Browser Console

## 🎯 Test Notifications RIGHT NOW (No Deployment Needed!)

You can simulate notifications directly from your browser console while viewing your deployed UI.

## 📝 Steps

### 1. Open Your Deployed UI
Navigate to: `https://agent-controller-backend.onrender.com`

### 2. Login
Use your admin password to login

### 3. Open Browser Console
- **Chrome/Edge**: Press `F12` or `Ctrl+Shift+J` (Windows) / `Cmd+Option+J` (Mac)
- **Firefox**: Press `F12` or `Ctrl+Shift+K` (Windows) / `Cmd+Option+K` (Mac)
- Click the **Console** tab

### 4. Check Socket Connection
In the console, type:
```javascript
// Check if socket is connected
console.log('Socket connected:', socket?.connected);
```

If it shows `true`, you're ready!

### 5. Send Test Notifications

#### Test Success Notification (Green):
```javascript
// Simulate a success notification
if (window.socket) {
  window.socket.emit('notification', {
    id: 'test_' + Date.now(),
    type: 'success',
    title: 'Test Success!',
    message: 'This is a test success notification from browser console',
    category: 'system',
    timestamp: new Date().toISOString(),
    read: false
  });
}
```

#### Test Warning Notification (Yellow):
```javascript
if (window.socket) {
  window.socket.emit('notification', {
    id: 'test_' + Date.now(),
    type: 'warning',
    title: 'Test Warning',
    message: 'This is a test warning notification',
    category: 'security',
    timestamp: new Date().toISOString(),
    read: false
  });
}
```

#### Test Error Notification (Red):
```javascript
if (window.socket) {
  window.socket.emit('notification', {
    id: 'test_' + Date.now(),
    type: 'error',
    title: 'Test Error',
    message: 'This is a test error notification',
    category: 'system',
    timestamp: new Date().toISOString(),
    read: false
  });
}
```

#### Test Info Notification (Blue):
```javascript
if (window.socket) {
  window.socket.emit('notification', {
    id: 'test_' + Date.now(),
    type: 'info',
    title: 'Test Info',
    message: 'This is a test info notification',
    category: 'agent',
    timestamp: new Date().toISOString(),
    read: false
  });
}
```

### 6. Send Multiple Test Notifications
```javascript
// Send a series of test notifications
const notificationTypes = [
  { type: 'success', title: 'Agent Connected', message: 'Agent-001 connected successfully', category: 'agent' },
  { type: 'info', title: 'System Update', message: 'System is running normally', category: 'system' },
  { type: 'warning', title: 'Low Memory', message: 'Agent memory usage is high', category: 'security' },
  { type: 'error', title: 'Connection Failed', message: 'Failed to connect to agent-005', category: 'agent' },
  { type: 'success', title: 'Command Completed', message: 'Screenshot captured successfully', category: 'command' }
];

notificationTypes.forEach((notif, index) => {
  setTimeout(() => {
    if (window.socket) {
      window.socket.emit('notification', {
        id: 'test_' + Date.now() + '_' + index,
        ...notif,
        timestamp: new Date().toISOString(),
        read: false
      });
    }
  }, index * 1000); // 1 second delay between each
});
```

---

## ⚠️ Important Notes

### This is CLIENT-SIDE Only
- These notifications only appear in YOUR browser
- They don't get stored in the backend
- Other users won't see them
- They won't persist after page refresh

### For REAL Testing
Use one of these methods instead:
1. **Connect real agents** (triggers automatic notifications)
2. **Deploy the updated code** to Render (enables test endpoint)
3. **Wait for auto-deployment** from your git push

---

## 🔍 Troubleshooting

### "socket is not defined"
Try accessing it via the window object:
```javascript
console.log(window.socket);
```

If still undefined, check the SocketProvider component is loaded:
```javascript
// Check if React app is loaded
console.log(document.querySelector('#root'));
```

### Socket Not Connected
Wait a few seconds after page load, then check again:
```javascript
setTimeout(() => {
  console.log('Socket connected:', window.socket?.connected);
}, 3000);
```

### Nothing Happens
1. Make sure you're logged in
2. Check for JavaScript errors in console
3. Refresh the page and try again
4. Open the Notification Center (bell icon) to see if notifications appear

---

## 🎯 Best Testing Strategy

**For immediate testing:**
1. Use browser console method (above) for quick UI tests
2. Connect real agents to see actual notifications

**For comprehensive testing:**
1. Manually deploy to Render (5 minutes)
2. Use `python test_notifications.py` script
3. Test all features systematically

---

## 📊 Verify Notifications Appear

After sending test notifications via console:
1. **Check Bell Icon**: Should show unread count badge
2. **Open Notification Center**: Click the bell icon
3. **Check Filters**: Try filtering by category
4. **Mark as Read**: Click a notification
5. **Delete**: Click the ❌ on a notification

All these features should work even with client-side test notifications!

---

## 🚀 Next Steps

Once you verify the UI works with console tests:
1. Deploy the updated controller.py to Render
2. Test with the Python script for backend integration
3. Test with real agent connections for end-to-end flow

Your notification system is fully functional - you're just waiting for the deployment! 🎉

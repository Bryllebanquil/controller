# Reconnection Issue - Analysis & Fix Plan

## 🐛 Problem Identified

When the agent loses connection and reconnects, **commands cannot be executed**.

### Root Cause:

**Event handlers are only registered ONCE after the first connection**, but NOT re-registered on reconnection.

### Current Flow (BROKEN):

```python
# Line 13078-13227: Main connection loop
while True:
    try:
        connection_attempts += 1
        
        # 1. Connect to server
        sio.connect(SERVER_URL, wait_timeout=10)  # Line 13109
        log_message("[OK] Connected to server successfully!")
        
        # 2. Register handlers (ONLY HAPPENS ON FIRST CONNECTION!)
        try:
            register_socketio_handlers()  # Line 13127
            log_message("[OK] Socket.IO event handlers registered successfully")
        except Exception as handler_error:
            log_message(f"[WARN] Failed to register Socket.IO handlers: {handler_error}")
        
        # 3. Wait for events
        sio.wait()  # Line 13214
        
    except socketio.exceptions.ConnectionError:
        # 4. Connection lost - retries
        log_message(f"[WARN] Connection failed. Retrying in 10 seconds...")
        time.sleep(10)
        # LOOP BACK TO LINE 13109 - BUT HANDLERS ARE NOT RE-REGISTERED!
```

### What Happens:

1. **First Connection:**
   - ✅ `sio.connect()` succeeds
   - ✅ `register_socketio_handlers()` is called
   - ✅ Handlers registered: `on_command`, `on_execute_command`, etc.
   - ✅ Commands work

2. **Connection Lost:**
   - ❌ `sio.wait()` throws exception
   - ❌ Loop catches exception
   - ❌ Sleeps 10 seconds
   - ❌ Loops back to `sio.connect()`

3. **Reconnection:**
   - ✅ `sio.connect()` succeeds
   - ✅ `connect()` event fires (agent re-registers)
   - ❌ `register_socketio_handlers()` is called again, BUT...
   - ❌ Socket.IO might not preserve handlers across disconnects
   - ❌ Commands don't work because handlers are lost

---

## 🔧 Solution

### Option 1: Register handlers BEFORE the loop (RECOMMENDED)

Handlers should be registered ONCE before the connection loop starts, so they persist across all reconnections.

```python
# BEFORE the while loop:
log_message("Registering Socket.IO event handlers...")
register_socketio_handlers()
log_message("[OK] Handlers registered (will persist across reconnections)")

# Main connection loop
while True:
    try:
        sio.connect(SERVER_URL, wait_timeout=10)
        log_message("[OK] Connected to server successfully!")
        
        # Handlers are already registered - no need to register again
        
        sio.wait()
    except socketio.exceptions.ConnectionError:
        log_message(f"[WARN] Connection failed. Retrying in 10 seconds...")
        time.sleep(10)
```

**Advantages:**
- ✅ Handlers registered once
- ✅ Persist across all connections
- ✅ Cleaner code
- ✅ No duplicate registrations

---

### Option 2: Register handlers on EVERY connection

Re-register handlers after every successful connection.

```python
while True:
    try:
        sio.connect(SERVER_URL, wait_timeout=10)
        log_message("[OK] Connected to server successfully!")
        
        # Re-register handlers on every connection
        log_message("Re-registering event handlers...")
        register_socketio_handlers()
        log_message("[OK] Handlers registered")
        
        sio.wait()
    except socketio.exceptions.ConnectionError:
        log_message(f"[WARN] Connection failed. Retrying in 10 seconds...")
        time.sleep(10)
```

**Advantages:**
- ✅ Ensures handlers are always fresh
- ✅ Works even if Socket.IO clears handlers

**Disadvantages:**
- ❌ Duplicate registration warnings
- ❌ Less efficient

---

### Option 3: Add disconnect handler to detect and log

Add a disconnect event handler to know when connection is lost.

```python
@sio.event
def disconnect():
    agent_id = get_or_create_agent_id()
    log_message(f"[DISCONNECT] Agent {agent_id} disconnected from controller")
    # Handlers should persist - will reconnect automatically
```

**Advantages:**
- ✅ Better logging
- ✅ Can track connection state
- ✅ Can trigger cleanup actions

---

## ✅ Recommended Fix

**Use Option 1 + Option 3:**

1. Register handlers ONCE before the loop
2. Add disconnect event handler for logging
3. Socket.IO will automatically preserve handlers across reconnections

### Implementation:

```python
# Register handlers ONCE (before connection loop)
log_message("Registering Socket.IO event handlers...")
try:
    register_socketio_handlers()
    log_message("[OK] Socket.IO event handlers registered")
except Exception as e:
    log_message(f"[ERROR] Failed to register handlers: {e}")
    return

# Main connection loop
connection_attempts = 0
while True:
    try:
        connection_attempts += 1
        log_message(f"Connecting to server (attempt {connection_attempts})...")
        
        sio.connect(SERVER_URL, wait_timeout=10)
        log_message("[OK] Connected to server successfully!")
        
        # Reset connection attempts on success
        connection_attempts = 0
        
        # Keep connection alive
        sio.wait()
        
    except socketio.exceptions.ConnectionError:
        log_message(f"[WARN] Connection failed. Retrying in 10 seconds...")
        time.sleep(10)
    except KeyboardInterrupt:
        log_message("\n[INFO] Shutting down...")
        break
    except Exception as e:
        log_message(f"[ERROR] Unexpected error: {e}")
        time.sleep(10)
```

And add to `register_socketio_handlers()`:

```python
@sio.event
def disconnect():
    agent_id = get_or_create_agent_id()
    log_message(f"[DISCONNECT] Agent {agent_id} lost connection to controller")
    log_message("[INFO] Will automatically reconnect...")
```

---

## 🧪 Testing

After fix, test:

1. **Normal connection:** Agent connects and responds to commands ✅
2. **Controller restart:** Stop controller, start it, agent should reconnect and respond ✅
3. **Network loss:** Disconnect network, reconnect, agent should work ✅
4. **Multiple reconnects:** Disconnect/reconnect multiple times ✅

---

## 📊 Expected Behavior After Fix

```
[OK] Socket.IO event handlers registered
Connecting to server (attempt 1)...
[OK] Connected to server successfully!
Connected to controller, registering agent DESKTOP-ABC123

... agent works ...

[DISCONNECT] Agent DESKTOP-ABC123 lost connection to controller
[INFO] Will automatically reconnect...
[WARN] Connection failed. Retrying in 10 seconds...

Connecting to server (attempt 2)...
[OK] Connected to server successfully!
Connected to controller, registering agent DESKTOP-ABC123

... agent works again! ✅
```

---

## ✅ Summary

**Current Issue:** Handlers only registered once, lost on reconnect
**Fix:** Move handler registration BEFORE the connection loop
**Result:** Handlers persist across all reconnections
**Benefit:** Commands work after every reconnection


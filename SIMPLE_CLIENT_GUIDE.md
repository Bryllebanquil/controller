# 🧪 Simple Client - Connection Test Guide

## 📋 Overview

The `simple-client.py` is a minimal version of the full client that only tests the connection to the controller. It's perfect for:

- ✅ **Verifying controller connectivity**
- ✅ **Testing network configuration**
- ✅ **Debugging connection issues**
- ✅ **Quick connection validation**

## 🚀 Quick Start

### **1. Install Dependencies**
```bash
pip install -r requirements-simple-client.txt
```

### **2. Run the Simple Client**
```bash
python3 simple-client.py
```

### **3. Test with Custom URL**
```bash
CONTROLLER_URL=https://your-controller-url.com python3 simple-client.py
```

## 🔍 What It Does

### **Connection Tests:**
1. **HTTP Test** - Verifies basic HTTP connectivity
2. **Socket.IO Test** - Tests real-time communication
3. **Heartbeat Test** - Sends periodic ping messages
4. **Message Test** - Receives and responds to commands

### **Features:**
- ✅ **Minimal dependencies** (only 2 packages)
- ✅ **Clear logging** with timestamps
- ✅ **Connection monitoring** with heartbeat
- ✅ **Graceful error handling**
- ✅ **Connection summary** on exit

## 📊 Expected Output

### **Successful Connection:**
```
🚀 Simple Client - Controller Connection Test
==================================================
Target Controller: https://agent-controller-backend.onrender.com
Agent ID: simple-client-1694567890
==================================================
[10:30:15] INFO: Starting connection tests...
[10:30:15] INFO: Testing HTTP connection to https://agent-controller-backend.onrender.com
[10:30:16] INFO: ✅ HTTP connection successful
[10:30:16] INFO: HTTP connection OK, testing Socket.IO...
[10:30:16] INFO: Testing Socket.IO connection...
[10:30:16] INFO: Connecting to https://agent-controller-backend.onrender.com...
[10:30:17] INFO: ✅ Socket.IO connection established!
[10:30:17] INFO: 📡 Heartbeat received (message #1)
[10:30:27] INFO: 📡 Heartbeat received (message #2)
```

### **Connection Summary:**
```
============================================================
🔍 CONNECTION TEST SUMMARY
============================================================
Controller URL: https://agent-controller-backend.onrender.com
Agent ID: simple-client-1694567890
Connection Status: ✅ Connected
Connection Duration: 45.2 seconds
Messages Received: 4
Last Heartbeat: 2.1s ago
============================================================
```

## 🛠️ Troubleshooting

### **Common Issues:**

#### **1. HTTP Connection Failed**
```
❌ HTTP connection failed: Connection refused
```
**Solution:** Check if the controller URL is correct and accessible

#### **2. Socket.IO Connection Failed**
```
❌ Socket.IO connection error: {'message': 'Invalid namespace'}
```
**Solution:** The controller might not be running or configured properly

#### **3. Missing Dependencies**
```
❌ python-socketio library not available
```
**Solution:** Install dependencies:
```bash
pip install python-socketio requests
```

#### **4. SSL/TLS Issues**
```
❌ SSL: CERTIFICATE_VERIFY_FAILED
```
**Solution:** The client disables SSL verification by default for testing

## 🔧 Configuration

### **Environment Variables:**
- `CONTROLLER_URL` - Controller URL (default: https://agent-controller-backend.onrender.com)
- `CONNECTION_TIMEOUT` - Connection timeout in seconds (default: 30)
- `HEARTBEAT_INTERVAL` - Heartbeat interval in seconds (default: 10)

### **Custom Configuration:**
```python
# Edit simple-client.py to change defaults
CONTROLLER_URL = 'https://your-controller.com'
CONNECTION_TIMEOUT = 60
HEARTBEAT_INTERVAL = 5
```

## 📋 Test Commands

### **Basic Test:**
```bash
python3 simple-client.py
```

### **Test with Custom URL:**
```bash
CONTROLLER_URL=https://localhost:8080 python3 simple-client.py
```

### **Automated Test:**
```bash
python3 test-simple-client.py
```

### **Quick Dependency Check:**
```bash
python3 -c "import socketio, requests; print('✅ Dependencies OK')"
```

## 🎯 Use Cases

### **1. Development Testing**
```bash
# Test local controller
CONTROLLER_URL=http://localhost:8080 python3 simple-client.py
```

### **2. Production Verification**
```bash
# Test deployed controller
CONTROLLER_URL=https://your-production-url.com python3 simple-client.py
```

### **3. Network Debugging**
```bash
# Test with verbose output
python3 simple-client.py 2>&1 | tee connection-test.log
```

### **4. CI/CD Integration**
```bash
# Use in automated tests
python3 test-simple-client.py && echo "Connection test passed"
```

## 📊 Comparison with Full Client

| Feature | Simple Client | Full Client |
|---------|---------------|-------------|
| **Dependencies** | 2 packages | 20+ packages |
| **Size** | ~200 lines | ~10,000+ lines |
| **Features** | Connection only | Full functionality |
| **Installation** | 30 seconds | 5+ minutes |
| **Use Case** | Testing | Production |

## ✅ Success Indicators

The simple client is working correctly when you see:
- ✅ HTTP connection successful
- ✅ Socket.IO connection established
- ✅ Heartbeat messages received
- ✅ Connection summary shows "Connected"

## 🚀 Next Steps

Once the simple client connects successfully:
1. **Install full client dependencies**: `pip install -r requirements-client.txt`
2. **Run the full client**: `python3 client.py`
3. **Access the controller UI**: Open the controller URL in your browser

The simple client is your first step to verify everything is working! 🎉
# Command Execution Testing Guide

This guide helps you test the command execution functionality between the controller, UI, and client.

## Quick Start

### Option 1: Automated Testing
```bash
# Run the automated test script
python3 test-command-execution.py --interactive
```

### Option 2: Manual Testing
```bash
# Terminal 1: Start the controller
python3 controller.py

# Terminal 2: Start the simple client
python3 simple-client.py --interactive

# Terminal 3: Open the web UI
# Navigate to http://localhost:8080 in your browser
```

## Testing Steps

### 1. Start the Controller
```bash
python3 controller.py
```
- Should show "Controller started on http://localhost:8080"
- Should show "Socket.IO server started"

### 2. Start the Simple Client
```bash
python3 simple-client.py --interactive
```
- Should show "✅ Socket.IO connection established!"
- Should show "📝 Agent registration sent"
- Should show "✅ Agent registration confirmed"

### 3. Open the Web UI
- Navigate to `http://localhost:8080`
- Login with your admin password
- Go to the "Agents" tab
- You should see a "Simple-Client" agent in the list

### 4. Test Command Execution
- Select the Simple-Client agent
- Go to the "Commands" tab
- Try these test commands:

#### Windows Commands:
```
dir
Get-Date
Get-Process | Select-Object -First 5
echo "Hello from Windows"
```

#### Linux/Mac Commands:
```
ls
date
ps aux | head -5
echo "Hello from Linux"
```

#### Universal Commands:
```
echo "Hello World"
whoami
pwd
```

## Expected Results

### ✅ Success Indicators:
- Command appears in the output panel
- Command result is displayed
- Status shows `[SUCCESS]` or `[ERROR]`
- Output is properly formatted

### ❌ Failure Indicators:
- No agent appears in the agents list
- Commands don't execute
- No output appears
- Connection errors in console

## Troubleshooting

### No Agent Appears
- Check if simple-client.py is running
- Check controller console for connection logs
- Verify Socket.IO connection is established

### Commands Don't Execute
- Check browser console for JavaScript errors
- Verify agent is selected in the UI
- Check if command panel is visible

### Connection Issues
- Verify controller.py is running on port 8080
- Check firewall settings
- Try different controller URL: `--url http://localhost:8080`

### Command Output Issues
- Check if command syntax is correct
- Verify the command is supported on your platform
- Check simple-client.py console for execution logs

## Advanced Testing

### Interactive Mode
```bash
python3 simple-client.py --interactive
```
- Allows manual command input
- Shows real-time execution results
- Useful for debugging

### Custom Controller URL
```bash
python3 simple-client.py --url https://your-controller.com
```

### Verbose Logging
- Check browser developer console (F12)
- Check controller.py console output
- Check simple-client.py console output

## Test Commands by Platform

### Windows PowerShell Commands:
```powershell
Get-Date
Get-Process | Select-Object -First 3
Get-Service | Where-Object {$_.Status -eq "Running"} | Select-Object -First 3
dir C:\
echo "Windows test successful"
```

### Linux/Mac Bash Commands:
```bash
date
ps aux | head -3
systemctl list-units --type=service --state=running | head -3
ls /
echo "Linux test successful"
```

### Cross-Platform Commands:
```bash
echo "Hello World"
whoami
pwd
python --version
```

## Debugging Tips

1. **Check Connection Status**: Look for "✅ Socket.IO connection established!" in simple-client.py
2. **Verify Agent Registration**: Look for "✅ Agent registration confirmed" in simple-client.py
3. **Monitor Command Flow**: Watch both controller.py and simple-client.py consoles
4. **Check Browser Console**: Press F12 and look for JavaScript errors
5. **Test Network**: Try `curl http://localhost:8080` to verify controller is reachable

## Common Issues and Solutions

### Issue: "Agent not found" error
**Solution**: Restart simple-client.py and wait for registration confirmation

### Issue: Commands execute but no output
**Solution**: Check if the command produces output (try `echo "test"`)

### Issue: Connection timeout
**Solution**: Check if controller.py is running and accessible

### Issue: Permission denied errors
**Solution**: Some commands require elevated privileges, try simpler commands first

## Success Criteria

The command execution is working correctly when:
- ✅ Agent appears in the agents list
- ✅ Commands can be sent from the UI
- ✅ Command results are displayed in the output panel
- ✅ Status indicators show success/error appropriately
- ✅ Multiple commands can be executed in sequence
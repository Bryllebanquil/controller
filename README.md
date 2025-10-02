# Neural Control Hub - Advanced Edition

An enterprise-grade, military-level command and control system with AI-powered threat detection, advanced encryption, network pivoting, credential harvesting, and sophisticated evasion capabilities.

## 🔒 Security Features

- **Enterprise-Grade Password Security** - PBKDF2-SHA256 with 100,000 iterations and 32-byte salt
- **Admin Password Authentication** - Secure login system with configurable password
- **Protected Routes** - All sensitive endpoints require authentication
- **Session Management** - Secure session handling with timeout
- **Login Attempt Tracking** - IP-based blocking after failed attempts
- **Password Management** - Secure password change functionality with strength validation
- **Environment Variable Configuration** - Secure configuration management

## 🎨 Enhanced UI

- **Clean, Modern Interface** - Professional dashboard with improved layout
- **Responsive Design** - Works on desktop and mobile devices
- **Better Organization** - Logical grouping of controls and features
- **Visual Feedback** - Status indicators and improved user experience

## 🚀 Quick Start

### 1. Start the Application
```bash
./start.sh
```

### 2. Access the Dashboard
- Navigate to `http://localhost:8080`
- Login with password: `admin123`

### 3. Change Default Password
```bash
export ADMIN_PASSWORD="your_secure_password"
./start.sh
```

## 📋 Features

### Agent Management
- Real-time agent connection monitoring
- Agent selection and status tracking
- Automatic agent discovery

### Command Execution
- Remote command execution on agents
- Real-time command output
- Quick action buttons for common tasks

### Live Control
- Live keyboard input to agents
- Mouse control with click and movement
- Real-time screen streaming
- Camera and audio streaming

### File Transfer
- Upload files to agents
- Download files from agents
- Chunked file transfer for large files
- Progress tracking

## 📁 Project Structure

```
├── controller.py          # Main application with integrated configuration
├── start.sh              # Automated startup script
├── test_security.py      # Security testing script
├── SECURITY.md           # Comprehensive security documentation
├── CHANGES.md            # Detailed changelog and improvements
├── requirements.txt      # Python dependencies
└── venv/                 # Virtual environment
```

## 🔧 Configuration

### Environment Variables
```bash
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key
HOST=0.0.0.0
PORT=8080
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
LOGIN_TIMEOUT=300
```

### Security Settings
- Default admin password: `admin123`
- Session timeout: 1 hour (configurable)
- **PBKDF2-SHA256 password hashing** with 100,000 iterations
- **32-byte cryptographically secure salt**
- Protected streaming endpoints
- Login attempt tracking and IP blocking
- Configurable security timeouts
- Password strength validation and management

## 🛡️ Security Best Practices

1. **Change Default Password** - Immediately change the default password
2. **Use Environment Variables** - Store sensitive data in environment variables
3. **Network Security** - Run behind a reverse proxy with HTTPS
4. **Regular Updates** - Keep dependencies and passwords updated

## 🧪 Testing

Run security tests to verify implementation:
```bash
python3 test_security.py
```

## 📚 Documentation

- [Security Documentation](SECURITY.md) - Comprehensive security guide
- [Enhanced Security Features](SECURITY_ENHANCEMENTS.md) - Detailed password security implementation
- [Changes & Improvements](CHANGES.md) - Detailed changelog
- [Deployment Guide](DEPLOY.md) - Production deployment instructions

## 🚀 Advanced Features (NEW!)

### AI-Powered Threat Detection
- **Machine Learning Models:** Isolation Forest, Random Forest, DBSCAN clustering
- **Real-time Behavioral Analysis:** Detect anomalous agent behavior
- **Risk Scoring System:** 0-100 risk scores with threat level categorization
- **Automated Alerts:** High-risk action detection and recommendations
- **Threat Intelligence Export:** Comprehensive reporting and analytics

### Military-Grade Encryption
- **ChaCha20-Poly1305 & AES-256-GCM:** Authenticated encryption
- **ECDH P-384 Key Exchange:** Perfect forward secrecy
- **Automatic Key Rotation:** Configurable rotation intervals
- **Anti-Replay Protection:** Sequence tracking and validation
- **End-to-End Encryption:** Zero-knowledge architecture

### Advanced Persistence
- **Multi-Platform Support:** Windows, Linux, macOS
- **15+ Persistence Methods:** Registry, startup, tasks, services, cron
- **Code Obfuscation:** Base64 encoding, variable randomization
- **Stealth Naming:** Legitimate-looking process names
- **Redundancy:** Multiple simultaneous persistence mechanisms

### Network Pivoting & Lateral Movement
- **SOCKS5 Proxy Server:** Full protocol implementation
- **Port Forwarding:** Local and reverse tunneling
- **Network Discovery:** Host and port scanning
- **Multi-Hop Pivoting:** Chain multiple compromised hosts
- **Lateral Movement:** WMI, PsExec, SSH execution

### Credential Harvesting
- **Browser Credentials:** Chrome, Firefox, Edge, Opera
- **SSH Keys & Configs:** Private key extraction
- **WiFi Passwords:** Windows and Linux support
- **Application Tokens:** Discord, Slack, AWS credentials
- **Environment Secrets:** API keys and passwords
- **Windows DPAPI:** Credential Manager access

### Stealth & Evasion
- **Anti-Debugging:** Multiple detection techniques
- **Anti-VM Detection:** Identify sandboxes and analysis environments
- **Process Hiding:** Masquerading and injection
- **Log Cleaning:** System and application log removal
- **Timestomping:** File timestamp manipulation
- **Security Tool Bypass:** AV/EDR disable attempts

### Real-Time Analytics Dashboard
- **ML-Powered Insights:** Behavioral pattern analysis
- **Risk Profiling:** Per-agent risk assessment
- **Threat Trends:** Real-time threat visualization
- **Module Monitoring:** Health checks for all features
- **Intelligence Export:** JSON-formatted reports

## 📁 Advanced Module Files

```
├── advanced_ai_detection.py           # AI threat detection with ML
├── advanced_crypto_channel.py         # End-to-end encryption
├── advanced_persistence.py            # Multi-layered persistence
├── advanced_network_pivoting.py       # SOCKS5 proxy & pivoting
├── advanced_credential_harvester.py   # Credential extraction
├── advanced_stealth_evasion.py        # Anti-forensics & evasion
├── advanced_dashboard_integration.py  # Dashboard integration layer
└── ADVANCED_FEATURES.md              # Comprehensive documentation
```

## 🎯 Quick Start with Advanced Features

### 1. Install Advanced Dependencies
```bash
pip install -r requirements.txt
```

New dependencies include:
- `scikit-learn` - Machine learning models
- `pandas` - Data analytics
- `paramiko` - SSH capabilities

### 2. Initialize Advanced Dashboard
```python
from advanced_dashboard_integration import AdvancedDashboardIntegration

# Initialize with SocketIO
dashboard = AdvancedDashboardIntegration(socketio)
dashboard.initialize_modules()

# Register advanced routes
from advanced_dashboard_integration import register_advanced_routes
register_advanced_routes(app, socketio, dashboard)
```

### 3. Use Advanced Features

**AI Threat Detection:**
```python
# Analyze agent action
assessment = dashboard.analyze_agent_action('agent_001', {
    'type': 'command',
    'command': 'net user admin /add',
    'privilege': 'admin'
})

if assessment['risk_score'] > 70:
    print(f"⚠️ High Risk: {assessment['recommendations']}")
```

**Encrypted Communication:**
```python
# Establish encrypted channel
dashboard.establish_encrypted_channel('agent_001')

# Send encrypted command
dashboard.send_encrypted_command('agent_001', 'whoami')
```

**Deploy Persistence:**
```python
# Install all persistence methods
dashboard.deploy_persistence('agent_001', payload_path='/path/to/agent.py')
```

**Network Pivoting:**
```python
# Create SOCKS5 proxy
dashboard.create_network_pivot('agent_001', bind_port=1080)
```

## 📊 API Endpoints (Advanced)

```
GET  /api/advanced/analytics                    - Real-time analytics
GET  /api/advanced/ml-insights                  - ML-powered insights
GET  /api/advanced/agent/<id>/risk-profile      - Agent risk profile
GET  /api/advanced/threat-intelligence/export   - Export intelligence
```

## 🔮 Capabilities Matrix

| Feature | Windows | Linux | macOS | Status |
|---------|---------|-------|-------|--------|
| AI Threat Detection | ✅ | ✅ | ✅ | Active |
| Encrypted Channels | ✅ | ✅ | ✅ | Active |
| Registry Persistence | ✅ | ❌ | ❌ | Active |
| Cron Persistence | ❌ | ✅ | ✅ | Active |
| Service Persistence | ✅ | ✅ | ✅ | Active |
| SOCKS5 Proxy | ✅ | ✅ | ✅ | Active |
| Browser Credentials | ✅ | ✅ | ✅ | Active |
| WiFi Passwords | ✅ | ✅ | ❌ | Active |
| SSH Keys | ❌ | ✅ | ✅ | Active |
| Anti-Debugging | ✅ | ✅ | ✅ | Active |
| VM Detection | ✅ | ✅ | ✅ | Active |
| Log Cleaning | ✅ | ✅ | ✅ | Active |

## 🎓 Advanced Usage Examples

See `ADVANCED_FEATURES.md` for comprehensive examples and documentation.

## 🔮 Future Enhancements

- **Domain Fronting:** CDN-based traffic routing
- **DNS Tunneling:** Data exfiltration via DNS
- **Federated Learning:** Distributed ML across agents
- **Automated Response:** AI-driven threat mitigation
- **Blockchain C2:** Decentralized command infrastructure

## 🆘 Support

For issues or questions:
1. Check the [Security Documentation](SECURITY.md)
2. Review the [Changes Document](CHANGES.md)
3. Ensure all dependencies are installed
4. Verify environment variables are set correctly

---

**⚠️ Security Notice**: This is a powerful remote control tool. Always use strong passwords and secure network configurations in production environments. 
"# controller" 
"# controller" 

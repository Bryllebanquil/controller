# Neural Control Hub

A secure, advanced command and control interface for managing remote agents with real-time streaming, file transfer, and system control capabilities.

## 🔒 Security Features

- **Admin Password Authentication** - Secure login system with configurable password
- **Protected Routes** - All sensitive endpoints require authentication
- **Session Management** - Secure session handling with timeout
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
├── controller.py          # Main application with security and UI improvements
├── config.py             # Configuration management
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
```

### Security Settings
- Default admin password: `admin123`
- Session timeout: 1 hour
- SHA-256 password hashing
- Protected streaming endpoints

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
- [Changes & Improvements](CHANGES.md) - Detailed changelog
- [Deployment Guide](DEPLOY.md) - Production deployment instructions

## 🔮 Future Enhancements

- Rate limiting and brute force protection
- Two-factor authentication
- API key authentication for agents
- Comprehensive audit logging
- Role-based access control

## 🆘 Support

For issues or questions:
1. Check the [Security Documentation](SECURITY.md)
2. Review the [Changes Document](CHANGES.md)
3. Ensure all dependencies are installed
4. Verify environment variables are set correctly

---

**⚠️ Security Notice**: This is a powerful remote control tool. Always use strong passwords and secure network configurations in production environments. 

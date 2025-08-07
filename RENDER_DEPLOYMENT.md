# Neural Control Hub - Render Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Neural Control Hub to Render with enhanced security features.

## Prerequisites
- Render account (free tier available)
- GitHub repository with the Neural Control Hub code
- Basic understanding of environment variables

## Deployment Steps

### 1. Prepare Your Repository
Ensure your repository contains these files:
```
├── controller.py              # Main application
├── requirements-controller.txt # Dependencies
├── render.yaml               # Render configuration
├── start-render.py           # Deployment startup script
└── README.md                 # Documentation
```

### 2. Deploy to Render

#### Option A: Using render.yaml (Recommended)
1. **Push to GitHub**: Ensure your code is in a GitHub repository
2. **Connect to Render**: 
   - Go to [render.com](https://render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

#### Option B: Manual Deployment
1. **Create Web Service**:
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure as follows:
     - **Name**: `neural-control-hub`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements-controller.txt`
     - **Start Command**: `python start-render.py`

### 3. Configure Environment Variables

#### Critical Security Variables
Set these in the Render dashboard under "Environment":

| Variable | Value | Description |
|----------|-------|-------------|
| `ADMIN_PASSWORD` | `your_secure_password` | **CHANGE THIS** - Admin login password |
| `SECRET_KEY` | `auto-generated` | Flask secret key (auto-generated if not set) |

#### Optional Security Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_TIMEOUT` | `3600` | Session timeout in seconds (1 hour) |
| `MAX_LOGIN_ATTEMPTS` | `5` | Maximum failed login attempts |
| `LOGIN_TIMEOUT` | `300` | Lockout duration in seconds (5 minutes) |
| `HASH_ITERATIONS` | `100000` | PBKDF2 iterations (security level) |
| `SALT_LENGTH` | `32` | Salt length in bytes |

### 4. Security Configuration

#### Required: Change Default Password
1. **In Render Dashboard**:
   - Go to your service → "Environment"
   - Set `ADMIN_PASSWORD` to a strong password
   - Example: `MySecurePassword123!@#`

#### Recommended: Set Secret Key
1. **Generate a secret key**:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```
2. **Set in Render**:
   - Add `SECRET_KEY` environment variable
   - Use the generated value

#### Optional: Adjust Security Settings
```bash
# More restrictive settings
SESSION_TIMEOUT=1800        # 30 minutes
MAX_LOGIN_ATTEMPTS=3        # 3 attempts
LOGIN_TIMEOUT=600          # 10 minutes lockout
HASH_ITERATIONS=150000     # Higher security
```

### 5. Deploy and Test

#### Initial Deployment
1. **Deploy**: Click "Create Blueprint" or "Create Web Service"
2. **Wait**: Render will build and deploy your application
3. **Access**: Use the provided URL (e.g., `https://neural-control-hub.onrender.com`)

#### Testing
1. **Login Test**:
   - Navigate to your Render URL
   - You should be redirected to login page
   - Use your `ADMIN_PASSWORD` to login

2. **Security Test**:
   - Try accessing `/dashboard` directly (should redirect to login)
   - Try wrong password multiple times (should trigger lockout)
   - Test password change functionality

### 6. Post-Deployment Security

#### Change Default Password
1. **Login** to your dashboard
2. **Go to** "Password Management" panel
3. **Change password** using the interface
4. **Update** `ADMIN_PASSWORD` in Render dashboard

#### Monitor Security
1. **Check logs** in Render dashboard
2. **Monitor** failed login attempts
3. **Review** configuration status in dashboard

## Security Features

### 🔐 Password Security
- **PBKDF2-SHA256** with 100,000 iterations
- **32-byte salt** for each password
- **Constant-time comparison** prevents timing attacks
- **Password strength validation**

### 🛡️ Access Control
- **All endpoints protected** with authentication
- **Session timeout** (configurable)
- **IP-based login attempt tracking**
- **Automatic IP blocking** after failed attempts

### 🔒 Session Security
- **Secure session management**
- **Configurable timeouts**
- **IP tracking** for security monitoring
- **Automatic logout** on timeout

## Troubleshooting

### Common Issues

#### Build Failures
```bash
# Check requirements
pip install -r requirements-controller.txt

# Verify Python version
python3 --version  # Should be 3.8+
```

#### Login Issues
1. **Check environment variables** in Render dashboard
2. **Verify password** is set correctly
3. **Clear browser cache** and cookies
4. **Check logs** in Render dashboard

#### Security Issues
1. **Change default password** immediately
2. **Set SECRET_KEY** for production
3. **Review security settings** in dashboard
4. **Monitor failed login attempts**

### Logs and Debugging
1. **Render Logs**: Check service logs in Render dashboard
2. **Application Logs**: View startup messages and errors
3. **Security Logs**: Monitor login attempts and blocks

## Performance Considerations

### Free Tier Limitations
- **512MB RAM** available
- **Shared CPU** resources
- **Sleep after inactivity** (15 minutes)
- **Cold start** delays

### Optimization Tips
1. **Use minimal dependencies** (requirements-controller.txt)
2. **Optimize startup time** with efficient imports
3. **Monitor resource usage** in Render dashboard
4. **Consider paid plans** for production use

## Production Recommendations

### Security Checklist
- [ ] Changed default `ADMIN_PASSWORD`
- [ ] Set `SECRET_KEY` environment variable
- [ ] Configured appropriate timeouts
- [ ] Tested password change functionality
- [ ] Verified all endpoints are protected
- [ ] Monitored failed login attempts

### Monitoring
- **Regular log review**
- **Security event monitoring**
- **Performance monitoring**
- **Uptime monitoring**

### Backup and Recovery
- **Code backup** in GitHub
- **Environment variables** documented
- **Configuration backup** in version control
- **Recovery procedures** documented

## Support

### Render Support
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [Render Status](https://status.render.com)

### Application Support
- Check [SECURITY.md](SECURITY.md) for security documentation
- Check [SECURITY_ENHANCEMENTS.md](SECURITY_ENHANCEMENTS.md) for password security details
- Review [CHANGES.md](CHANGES.md) for recent updates

## Conclusion

Your Neural Control Hub is now deployed with:
- ✅ **Enterprise-grade password security**
- ✅ **Protected endpoints and sessions**
- ✅ **Configurable security settings**
- ✅ **User-friendly management interface**
- ✅ **Production-ready deployment**

**Remember**: Always change the default password and set a secure SECRET_KEY for production use!
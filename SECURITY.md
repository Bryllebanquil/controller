# Neural Control Hub - Security Documentation

## Overview
The Neural Control Hub now includes comprehensive security features to protect against unauthorized access and control.

## Security Features

### 1. Admin Password Authentication
- **Default Password**: `admin123`
- **Configuration**: Set via `ADMIN_PASSWORD` environment variable or in `config.py`
- **Storage**: Password is hashed using SHA-256 before comparison
- **Session Management**: Authenticated sessions are maintained using Flask sessions

### 2. Protected Routes
All sensitive endpoints are now protected with authentication:
- `/dashboard` - Main control interface
- `/stream/<agent_id>` - Video streaming endpoints
- `/camera/<agent_id>` - Camera streaming endpoints
- `/audio/<agent_id>` - Audio streaming endpoints
- All feed endpoints (`/video_feed/`, `/camera_feed/`, `/audio_feed/`)

### 3. Session Management
- Sessions are managed using Flask's built-in session handling
- Secure random secret key generation
- Session timeout configuration available

## Configuration

### Environment Variables
```bash
# Set a strong admin password
export ADMIN_PASSWORD="your_strong_password_here"

# Set a custom secret key (optional, will auto-generate if not set)
export SECRET_KEY="your_secret_key_here"

# Server configuration
export HOST="0.0.0.0"
export PORT="8080"
```

### Configuration File (`config.py`)
```python
# Admin Authentication
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', None)

# Server Configuration
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 8080))
```

## Usage

### First Time Setup
1. Start the server: `python controller.py`
2. Navigate to the application URL
3. You will be redirected to the login page
4. Enter the admin password (default: `admin123`)
5. Access the dashboard

### Changing the Admin Password
1. **Method 1**: Set environment variable
   ```bash
   export ADMIN_PASSWORD="new_secure_password"
   python controller.py
   ```

2. **Method 2**: Edit config.py
   ```python
   ADMIN_PASSWORD = "new_secure_password"
   ```

3. **Method 3**: Use environment variable in production
   ```bash
   ADMIN_PASSWORD=new_secure_password python controller.py
   ```

## Security Best Practices

### 1. Strong Password
- Use a strong, unique password
- Minimum 12 characters
- Include uppercase, lowercase, numbers, and special characters
- Avoid common words or patterns

### 2. Environment Variables
- Store sensitive configuration in environment variables
- Never commit passwords to version control
- Use different passwords for different environments

### 3. Network Security
- Run behind a reverse proxy (nginx, Apache)
- Use HTTPS in production
- Configure firewall rules appropriately
- Consider VPN access for remote administration

### 4. Regular Updates
- Keep the application and dependencies updated
- Monitor for security vulnerabilities
- Regularly rotate passwords

## Production Deployment

### Docker Example
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV ADMIN_PASSWORD=your_secure_password_here
ENV SECRET_KEY=your_secret_key_here

EXPOSE 8080
CMD ["python", "controller.py"]
```

### Docker Compose Example
```yaml
version: '3.8'
services:
  neural-hub:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped
```

## Troubleshooting

### Login Issues
- Ensure the password is correctly set in environment variables
- Check that the config.py file is being read correctly
- Verify that sessions are working (check browser cookies)

### Session Issues
- Clear browser cookies and cache
- Check that the SECRET_KEY is consistent across restarts
- Verify that the session storage is working

### Network Issues
- Check firewall settings
- Verify port configuration
- Ensure the application is accessible from your network

## Security Considerations

### Current Limitations
- Socket.IO authentication is basic (relies on HTTP session)
- No rate limiting on login attempts
- No two-factor authentication
- No audit logging

### Future Enhancements
- Implement proper Socket.IO authentication
- Add rate limiting and brute force protection
- Implement two-factor authentication
- Add comprehensive audit logging
- Implement role-based access control
- Add API key authentication for agents

## Support
For security-related issues or questions, please review this documentation and ensure all security best practices are followed.
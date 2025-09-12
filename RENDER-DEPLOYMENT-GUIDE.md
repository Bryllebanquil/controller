# 🚀 Neural Control Hub - Render Deployment Guide

Complete step-by-step guide to deploy Neural Control Hub on Render with both backend and frontend services.

## 📋 Prerequisites

- **Render Account** (free tier available)
- **GitHub Repository** with your Neural Control Hub code
- **Git** installed locally

## 🏗️ Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Render Cloud                        │
├─────────────────────────────────────────────────────────────┤
│  Backend Service                    Frontend Service       │
│  ┌─────────────────────────┐        ┌─────────────────────┐ │
│  │ neural-control-hub-     │        │ neural-control-hub- │ │
│  │ backend.onrender.com    │◄──────►│ frontend.onrender.  │ │
│  │                         │        │ com                 │ │
│  │ • Python/Flask          │        │ • React/TypeScript  │ │
│  │ • REST API              │        │ • Static Build      │ │
│  │ • WebSocket             │        │ • Vite Preview      │ │
│  │ • Port 10000            │        │ • Port 10000        │ │
│  └─────────────────────────┘        └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Required Files (Already Created)

✅ All necessary files have been created:

```
workspace/
├── render-backend.yaml          # Backend service configuration
├── render-frontend.yaml         # Frontend service configuration
├── start-render-backend.py      # Production backend startup
├── backend-requirements.txt     # Python dependencies
├── build-for-render.sh          # Build script
└── agent-controller ui/
    ├── .env.render              # Production environment
    └── package.json             # Updated for Render
```

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Repository

1. **Push code to GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Verify all files are in your repository**:
   - `controller.py`
   - `start-render-backend.py`
   - `backend-requirements.txt`
   - `render-backend.yaml`
   - `render-frontend.yaml`
   - `agent-controller ui/` directory with all frontend files

### Step 2: Deploy Backend Service

1. **Login to Render**: Go to https://render.com and sign in

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository

3. **Configure Backend Service**:
   ```
   Name: neural-control-hub-backend
   Environment: Python 3
   Region: Oregon (or your preferred region)
   Branch: main
   Root Directory: . (leave empty)
   Build Command: pip install -r backend-requirements.txt
   Start Command: python start-render-backend.py
   ```

4. **Set Environment Variables**:
   ```
   ADMIN_PASSWORD = your-secure-admin-password
   SECRET_KEY = your-secret-key-here
   SESSION_TIMEOUT = 3600
   MAX_LOGIN_ATTEMPTS = 5
   LOGIN_TIMEOUT = 300
   ```

5. **Deploy Backend**:
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Note the backend URL: `https://neural-control-hub-backend.onrender.com`

### Step 3: Deploy Frontend Service

1. **Create Second Web Service**:
   - Click "New +" → "Web Service"
   - Connect the same GitHub repository

2. **Configure Frontend Service**:
   ```
   Name: neural-control-hub-frontend
   Environment: Node
   Region: Oregon (same as backend)
   Branch: main
   Root Directory: agent-controller ui
   Build Command: npm install && npm run build
   Start Command: npm start
   ```

3. **Set Environment Variables**:
   ```
   VITE_API_URL = https://neural-control-hub-backend.onrender.com
   VITE_WS_URL = https://neural-control-hub-backend.onrender.com
   VITE_NODE_ENV = production
   NODE_ENV = production
   ```

4. **Deploy Frontend**:
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Note the frontend URL: `https://neural-control-hub-frontend.onrender.com`

### Step 4: Update CORS Configuration

1. **Update Backend CORS** (if needed):
   - The backend is already configured for `*.onrender.com`
   - If you use custom domains, update the `allowed_origins` in `controller.py`

2. **Redeploy Backend** (if CORS was updated):
   - Go to your backend service in Render
   - Click "Manual Deploy" → "Deploy latest commit"

## 🔧 Configuration Details

### Backend Configuration

**Environment Variables**:
- `ADMIN_PASSWORD`: Secure password for admin access
- `SECRET_KEY`: Flask secret key for sessions
- `SESSION_TIMEOUT`: Session timeout in seconds (default: 3600)
- `MAX_LOGIN_ATTEMPTS`: Maximum failed login attempts (default: 5)
- `LOGIN_TIMEOUT`: Lockout time after failed attempts (default: 300)

**Automatic Variables**:
- `PORT`: Automatically set by Render (10000)
- `HOST`: Set to `0.0.0.0` for Render

### Frontend Configuration

**Environment Variables**:
- `VITE_API_URL`: Backend service URL
- `VITE_WS_URL`: WebSocket URL (same as API URL)
- `VITE_NODE_ENV`: Set to `production`
- `NODE_ENV`: Set to `production`

## 🔒 Security Considerations

### Production Security Checklist

✅ **Strong Admin Password**: Set a secure `ADMIN_PASSWORD`
✅ **Secret Key**: Use a random `SECRET_KEY`
✅ **HTTPS Only**: Render provides automatic HTTPS
✅ **CORS Configuration**: Properly configured for frontend domain
✅ **Session Timeouts**: Configured session timeouts
✅ **Rate Limiting**: Built-in login attempt limiting

### Recommended Security Settings

```bash
# Generate secure passwords
ADMIN_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 64)
```

## 🌐 Access Your Deployment

After successful deployment:

1. **Frontend URL**: `https://neural-control-hub-frontend.onrender.com`
2. **Backend API**: `https://neural-control-hub-backend.onrender.com/api/`
3. **Login**: Use your `ADMIN_PASSWORD`

## 🐛 Troubleshooting

### Common Issues

1. **Build Failed - Backend**:
   ```
   Solution: Check backend-requirements.txt and Python version
   - Ensure all dependencies are compatible
   - Check Render logs for specific errors
   ```

2. **Build Failed - Frontend**:
   ```
   Solution: Check package.json and Node version
   - Verify all dependencies are listed
   - Check build command syntax
   ```

3. **CORS Errors**:
   ```
   Solution: Update CORS configuration
   - Verify frontend URL in allowed_origins
   - Check environment variables
   ```

4. **WebSocket Connection Failed**:
   ```
   Solution: Check WebSocket configuration
   - Verify VITE_WS_URL points to backend
   - Check if backend service is running
   ```

5. **Environment Variables Not Set**:
   ```
   Solution: Check Render dashboard
   - Go to service → Environment
   - Verify all variables are set
   - Redeploy after changes
   ```

### Render-Specific Issues

1. **Free Tier Limitations**:
   - Services sleep after 15 minutes of inactivity
   - Cold starts may take 30-60 seconds
   - Consider upgrading to paid plan for production

2. **Build Timeouts**:
   - Render has build time limits
   - Optimize dependencies if builds are slow

3. **Memory Limits**:
   - Free tier has 512MB RAM limit
   - Monitor memory usage in logs

## 📊 Monitoring & Logs

### Viewing Logs

1. **Backend Logs**:
   - Go to backend service in Render dashboard
   - Click "Logs" tab
   - Monitor for errors and performance

2. **Frontend Logs**:
   - Go to frontend service in Render dashboard
   - Check build logs and runtime logs

### Health Checks

- **Backend**: `GET /api/auth/status`
- **Frontend**: Automatic health check via HTTP response

## 🔄 Updates & Maintenance

### Deploying Updates

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Update features"
   git push origin main
   ```

2. **Auto-Deploy**: Services will automatically redeploy (if enabled)

3. **Manual Deploy**: Use "Manual Deploy" button in Render dashboard

### Environment Updates

1. **Update Environment Variables** in Render dashboard
2. **Redeploy** services after environment changes

## 💰 Cost Considerations

### Free Tier Limits

- **2 Free Services** per account
- **750 hours/month** per service
- **512MB RAM** per service
- **Services sleep** after 15 minutes of inactivity

### Paid Plans

- **Starter Plan**: $7/month per service
- **No sleep**, faster builds, more resources
- **Custom domains** and SSL certificates

## 🎯 Production Optimization

### Performance Tips

1. **Enable Auto-Deploy** for continuous deployment
2. **Use Starter Plan** to avoid service sleeping
3. **Monitor Resource Usage** in Render dashboard
4. **Optimize Bundle Size** for faster frontend loads

### Scaling Considerations

1. **Database**: Add PostgreSQL service if needed
2. **Redis**: Add Redis for session storage
3. **CDN**: Use Render's built-in CDN for static assets
4. **Load Balancing**: Available in higher tier plans

## ✅ Deployment Checklist

Before going live:

- [ ] Backend service deployed and running
- [ ] Frontend service deployed and running
- [ ] Environment variables configured
- [ ] CORS properly configured
- [ ] Admin password set securely
- [ ] WebSocket connection working
- [ ] All API endpoints responding
- [ ] Frontend can authenticate
- [ ] Real-time updates working

## 🆘 Support

If you encounter issues:

1. **Check Render Documentation**: https://render.com/docs
2. **Review Service Logs** in Render dashboard
3. **Check GitHub Repository** for latest updates
4. **Render Support**: Available through dashboard

---

## 🎉 Congratulations!

Your Neural Control Hub is now deployed on Render with:

- ✅ **Scalable Backend** with REST API and WebSocket
- ✅ **Modern Frontend** with React and real-time updates
- ✅ **Production Security** with HTTPS and authentication
- ✅ **Automatic Deployments** from GitHub
- ✅ **Professional URLs** with custom domains available

**Access your deployment at**: `https://neural-control-hub-frontend.onrender.com`
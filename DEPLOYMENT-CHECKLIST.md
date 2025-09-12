# 🚀 Render Deployment Checklist

## Pre-Deployment ✅

- [ ] Code pushed to GitHub repository
- [ ] All required files present:
  - [ ] `controller.py`
  - [ ] `start-render-backend.py` 
  - [ ] `backend-requirements.txt`
  - [ ] `render-backend.yaml`
  - [ ] `render-frontend.yaml`
  - [ ] `agent-controller ui/` directory

## Backend Deployment ✅

- [ ] Create new Web Service in Render
- [ ] Connect GitHub repository
- [ ] Configure service:
  - [ ] Name: `neural-control-hub-backend`
  - [ ] Environment: Python 3
  - [ ] Build Command: `pip install -r backend-requirements.txt`
  - [ ] Start Command: `python start-render-backend.py`
- [ ] Set environment variables:
  - [ ] `ADMIN_PASSWORD` (secure password)
  - [ ] `SECRET_KEY` (random string)
  - [ ] `SESSION_TIMEOUT` (3600)
  - [ ] `MAX_LOGIN_ATTEMPTS` (5)
  - [ ] `LOGIN_TIMEOUT` (300)
- [ ] Deploy and verify service is running
- [ ] Note backend URL: `https://neural-control-hub-backend.onrender.com`

## Frontend Deployment ✅

- [ ] Create second Web Service in Render
- [ ] Connect same GitHub repository
- [ ] Configure service:
  - [ ] Name: `neural-control-hub-frontend`
  - [ ] Environment: Node
  - [ ] Root Directory: `agent-controller ui`
  - [ ] Build Command: `npm install && npm run build`
  - [ ] Start Command: `npm start`
- [ ] Set environment variables:
  - [ ] `VITE_API_URL` (backend URL)
  - [ ] `VITE_WS_URL` (backend URL)
  - [ ] `VITE_NODE_ENV` (production)
  - [ ] `NODE_ENV` (production)
- [ ] Deploy and verify service is running
- [ ] Note frontend URL: `https://neural-control-hub-frontend.onrender.com`

## Post-Deployment Testing ✅

- [ ] Frontend loads successfully
- [ ] Login page appears
- [ ] Can authenticate with admin password
- [ ] Dashboard loads with proper data
- [ ] WebSocket connection established
- [ ] API endpoints responding
- [ ] Real-time updates working
- [ ] No CORS errors in browser console

## Security Verification ✅

- [ ] Strong admin password set
- [ ] HTTPS enabled (automatic on Render)
- [ ] Session timeouts working
- [ ] Rate limiting active
- [ ] No sensitive data in logs

## Production Ready ✅

- [ ] Services not sleeping (consider Starter plan)
- [ ] Monitoring set up
- [ ] Backup plan in place
- [ ] Documentation updated
- [ ] Team access configured

## Environment Variables Reference

### Backend
```
ADMIN_PASSWORD=your-secure-password
SECRET_KEY=your-secret-key
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
LOGIN_TIMEOUT=300
```

### Frontend
```
VITE_API_URL=https://neural-control-hub-backend.onrender.com
VITE_WS_URL=https://neural-control-hub-backend.onrender.com
VITE_NODE_ENV=production
NODE_ENV=production
```

## Quick Commands

### Generate Secure Passwords
```bash
# Admin password
openssl rand -base64 32

# Secret key
openssl rand -base64 64
```

### Local Testing Before Deploy
```bash
# Test backend locally
python3 start-render-backend.py

# Test frontend build
cd "agent-controller ui"
npm run build
npm run preview
```

## Troubleshooting Quick Fixes

### Backend Won't Start
- Check Python version (should be 3.8+)
- Verify all dependencies in requirements.txt
- Check environment variables are set

### Frontend Won't Build
- Verify Node.js version (should be 18+)
- Check package.json syntax
- Ensure all dependencies are listed

### CORS Errors
- Verify frontend URL in backend CORS config
- Check environment variables match
- Redeploy backend after CORS changes

### WebSocket Issues
- Ensure VITE_WS_URL matches backend URL
- Check backend service is running
- Verify no firewall blocking WebSocket

---

**🎯 Goal**: Both services running on Render with full functionality

**📱 Access**: https://neural-control-hub-frontend.onrender.com
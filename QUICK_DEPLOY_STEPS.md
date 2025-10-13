# ⚡ Quick Deploy Steps - Modified UI to Render

## 🎯 Fastest Path to Testing on Render

### Option: Create Separate Test Service (5 minutes)

```bash
# 1. Build locally to verify (2 min)
cd "agent-controller ui v2.1-modified"
npm install && npm run build
cd ..

# 2. Commit and push (1 min)
git add "agent-controller ui v2.1-modified/" render-test-modified.yaml
git commit -m "Add UI v2.1-modified for testing"
git push origin main

# 3. Deploy on Render (2 min)
```
Then in Render Dashboard:
- Click "New +" → "Blueprint"
- Select repo → Blueprint: `render-test-modified.yaml`
- Set `ADMIN_PASSWORD` env var
- Click "Apply"

**Done!** Test at: `https://agent-controller-backend-test.onrender.com`

---

## 🎬 Even Faster: Use the Script

```bash
chmod +x deploy-modified-to-render.sh
./deploy-modified-to-render.sh
```

Follow the prompts, choose Option 1.

---

## ✅ What You'll See

1. **First Visit:** Login screen with password field
2. **After Login:** "Connecting..." spinner
3. **Then:** Full dashboard with:
   - Process Manager in Commands tab
   - Network Performance in Monitoring tab
   - Mobile-responsive navigation

---

## 🔄 Side-by-Side URLs

- **Production (v2.1):** Your current URL
- **Test (v2.1-modified):** `agent-controller-backend-test.onrender.com`

Compare them! Both run simultaneously.

---

## 📝 One-Line Checklist

- [ ] Build works locally
- [ ] Commit and push
- [ ] Create Render Blueprint
- [ ] Set ADMIN_PASSWORD
- [ ] Test at new URL

**That's it!** 🚀

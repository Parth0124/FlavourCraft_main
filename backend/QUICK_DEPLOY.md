# Quick Deployment Guide - TL;DR

Get your FlavourCraft backend deployed in 15 minutes!

## 🚀 Quick Start (3 Steps)

### Step 1: Set Up Accounts (5 mins)

1. **MongoDB Atlas** (FREE)
   - Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
   - Create free cluster (512MB)
   - Get connection string: `mongodb+srv://...`
   - **Important**: Add `0.0.0.0/0` to IP Access List

2. **Cloudinary** (FREE)
   - Go to [cloudinary.com](https://cloudinary.com)
   - Sign up for free account (25GB)
   - Copy: Cloud Name, API Key, API Secret

3. **OpenAI** (Pay-as-you-go)
   - Go to [platform.openai.com](https://platform.openai.com)
   - Add payment method ($5-15/month usage)
   - Create API key

4. **Docker Hub** (FREE)
   - Go to [hub.docker.com](https://hub.docker.com)
   - Create account
   - Create access token: Settings → Security → New Access Token

5. **Render.com** (FREE)
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

---

### Step 2: Configure GitHub (3 mins)

1. **Add Secrets** to GitHub repo:
   - Go to: Settings → Secrets and variables → Actions
   - Click: New repository secret

   ```
   DOCKER_USERNAME=your-docker-hub-username
   DOCKER_PASSWORD=dckr_pat_your-access-token
   ```

   *(We'll add RENDER secrets after creating the service)*

---

### Step 3: Deploy on Render (7 mins)

1. **Create Web Service**:
   - Go to [render.com/dashboard](https://render.com/dashboard)
   - Click: **New +** → **Web Service**
   - Connect: Your GitHub repository
   - Select: **FlavourCraft** repo

2. **Configure**:
   ```
   Name: flavourcraft-backend
   Region: Oregon
   Branch: main
   Root Directory: backend
   Environment: Docker
   Plan: Free
   ```

3. **Add Environment Variables** (in Render dashboard):

   Click **Environment** and add these:

   **Required Secrets**:
   ```bash
   MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/FlavourCraft
   JWT_SECRET_KEY=your-super-secure-secret-key-here
   OPENAI_API_KEY=sk-your-openai-api-key
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret
   CORS_ORIGINS=https://your-frontend-url.com
   ```

   **Optional** (use defaults):
   ```bash
   ENVIRONMENT=production
   PROMETHEUS_ENABLED=false
   ENABLE_DRIFT_DETECTION=false
   ```

4. **Deploy**:
   - Click: **Create Web Service**
   - Wait 3-5 minutes for build
   - Your app will be live at: `https://flavourcraft-backend-xxxx.onrender.com`

5. **Test**:
   ```bash
   curl https://your-app.onrender.com/health
   ```

---

### Step 4: Enable Auto-Deploy (2 mins)

1. **Get Render Deploy Hook**:
   - In Render dashboard → Your service → **Settings**
   - Copy **Deploy Hook URL**

2. **Add to GitHub Secrets**:
   ```
   RENDER_DEPLOY_HOOK_URL=https://api.render.com/deploy/srv-xxx?key=yyy
   RENDER_APP_URL=https://your-app.onrender.com
   ```

3. **Push to trigger CI/CD**:
   ```bash
   git add .
   git commit -m "Enable auto-deployment"
   git push origin main
   ```

   Now every push to `main` will auto-deploy!

---

## ✅ Verification Checklist

```bash
# 1. Health check
curl https://your-app.onrender.com/health

# 2. API docs
https://your-app.onrender.com/docs

# 3. Test authentication
curl -X POST https://your-app.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"Test123!"}'
```

---

## 🔧 Generate JWT Secret Key

```bash
# On Mac/Linux:
openssl rand -hex 32

# Or use Python:
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📊 What You Get (Free Tier)

| Service | What's Free |
|---------|-------------|
| **Render** | 750 hours/month (enough for 24/7) |
| **MongoDB** | 512MB storage |
| **Cloudinary** | 25GB bandwidth/month |
| **Docker Hub** | 1 private repository |
| **GitHub Actions** | 2000 CI/CD minutes/month |

**Total Cost**: $0/month + OpenAI usage (~$5-15/month)

---

## ⚠️ Important Notes

1. **Render Free Tier Limitation**:
   - Service spins down after 15 minutes of inactivity
   - First request after spin-down takes 30-60 seconds
   - **Solution**: Use [cron-job.org](https://cron-job.org) to ping `/health` every 14 minutes

2. **MongoDB Atlas IP Whitelist**:
   - Add `0.0.0.0/0` to allow connections from anywhere
   - Or add Render's specific IPs

3. **CORS Configuration**:
   - Update `CORS_ORIGINS` with your actual frontend URL
   - Separate multiple URLs with commas: `https://app1.com,https://app2.com`

4. **API Keys Security**:
   - Never commit `.env` to Git
   - Use GitHub Secrets for CI/CD
   - Use Render Environment Variables for production

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Build fails | Check logs in Render dashboard |
| Database connection fails | Verify MONGODB_URI and IP whitelist |
| CORS errors | Update CORS_ORIGINS environment variable |
| 503 errors | Check `/health` endpoint, verify database |
| Slow first request | Normal for free tier spin-up |

---

## 📱 Update Frontend

After deployment, update your frontend with the backend URL:

```javascript
// In your frontend .env
VITE_API_URL=https://your-app.onrender.com
# or
REACT_APP_API_URL=https://your-app.onrender.com
```

---

## 🎉 You're Done!

Your backend is now:
- ✅ Deployed on Render (FREE)
- ✅ Auto-deploys on every push
- ✅ Has health monitoring
- ✅ Uses cloud database and storage
- ✅ Secured with JWT authentication

**Next Steps**:
- Test all API endpoints
- Deploy your frontend
- Set up monitoring alerts
- Configure custom domain (optional)

---

## 📚 Need More Details?

See the full deployment guide: [DEPLOYMENT.md](./DEPLOYMENT.md)

---

**Questions?** Check the [Troubleshooting section](./DEPLOYMENT.md#troubleshooting) in DEPLOYMENT.md

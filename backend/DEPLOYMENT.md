# FlavourCraft Backend - Deployment Guide

Complete guide for deploying the FlavourCraft backend to production with CI/CD automation.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment (Render.com - FREE)](#production-deployment-rendercom---free)
4. [GitHub Actions CI/CD Setup](#github-actions-cicd-setup)
5. [Environment Variables](#environment-variables)
6. [Docker Hub Setup](#docker-hub-setup)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

- [x] MongoDB Atlas account (FREE tier - 512MB)
- [x] Cloudinary account (FREE tier - 25GB storage)
- [x] OpenAI API key (pay-as-you-go)
- [x] GitHub account
- [x] Docker Hub account (FREE - 1 private repo)
- [x] Render.com account (FREE tier - 750 hours/month)

---

## Local Development Setup

### 1. Clone and Install

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 3. Run Locally

```bash
# Single service
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or with Docker Compose (includes MLOps stack)
docker-compose up --build
```

### 4. Test the API

```bash
curl http://localhost:8000/health
```

---

## Production Deployment (Render.com - FREE)

Render.com offers a generous free tier perfect for this project:
- ✅ 750 hours/month (enough for continuous operation)
- ✅ Automatic SSL certificates
- ✅ Auto-deploys from GitHub
- ⚠️ Spins down after 15 minutes of inactivity (restarts on request)

### Step 1: Prepare Your Repository

```bash
# Ensure all deployment files are committed
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub (recommended)
3. Verify your email

### Step 3: Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Select the **FlavourCraft** repository
4. Configure the service:

   ```
   Name: flavourcraft-backend
   Region: Oregon (or closest to your users)
   Branch: main
   Root Directory: backend
   Environment: Docker
   Plan: Free
   ```

5. **Auto-Deploy**: Enable (deploys on every push to main)

### Step 4: Set Environment Variables

In the Render dashboard, go to **Environment** and add these variables:

#### Required Secrets
```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/FlavourCraft
JWT_SECRET_KEY=your-super-secure-secret-key-here
OPENAI_API_KEY=sk-your-openai-api-key-here
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-key
CLOUDINARY_API_SECRET=your-cloudinary-secret
CORS_ORIGINS=https://your-frontend-domain.com
```

#### Optional Configuration
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
PROMETHEUS_ENABLED=false
ENABLE_DRIFT_DETECTION=false
```

💡 **Tip**: Generate a secure JWT secret with:
```bash
openssl rand -hex 32
```

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will automatically:
   - Pull your code from GitHub
   - Build the Docker image
   - Deploy the container
   - Assign a public URL: `https://flavourcraft-backend.onrender.com`

3. Monitor deployment in the **Logs** tab

### Step 6: Verify Deployment

```bash
# Check health endpoint
curl https://your-app.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-11-27T...",
  "environment": "production",
  "checks": {
    "database": {"status": "connected", "healthy": true},
    "disk": {...},
    "memory": {...}
  }
}
```

---

## GitHub Actions CI/CD Setup

Automate testing and deployment on every push to main.

### Step 1: Create GitHub Secrets

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**

Add these secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `DOCKER_USERNAME` | Your Docker Hub username | `yourusername` |
| `DOCKER_PASSWORD` | Docker Hub access token | `dckr_pat_...` |
| `RENDER_DEPLOY_HOOK_URL` | Render deploy webhook | `https://api.render.com/deploy/srv-xxx` |
| `RENDER_APP_URL` | Your Render app URL | `https://your-app.onrender.com` |

### Step 2: Get Render Deploy Hook

1. In Render dashboard → Your service → **Settings**
2. Scroll to **Deploy Hook**
3. Copy the URL (format: `https://api.render.com/deploy/srv-xxxxx?key=yyyy`)
4. Add to GitHub secrets as `RENDER_DEPLOY_HOOK_URL`

### Step 3: Create Docker Hub Access Token

1. Go to [Docker Hub](https://hub.docker.com)
2. **Account Settings** → **Security** → **New Access Token**
3. Name: `github-actions`
4. Permissions: Read, Write, Delete
5. Copy the token and add to GitHub secrets

### Step 4: Enable GitHub Actions

The workflow file is already created at `.github/workflows/deploy.yml`

It will automatically:
1. ✅ Run code quality checks (Black, Flake8, isort)
2. ✅ Run tests
3. ✅ Build Docker image
4. ✅ Push to Docker Hub
5. ✅ Trigger Render deployment
6. ✅ Run health check

### Step 5: Test the Pipeline

```bash
# Make a change and push
git add .
git commit -m "Test CI/CD pipeline"
git push origin main
```

Go to **Actions** tab in GitHub to see the workflow running.

---

## Environment Variables

### Complete Environment Variables List

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MONGODB_URI` | ✅ Yes | - | MongoDB Atlas connection string |
| `JWT_SECRET_KEY` | ✅ Yes | - | Secret key for JWT tokens |
| `OPENAI_API_KEY` | ✅ Yes | - | OpenAI API key |
| `CLOUDINARY_CLOUD_NAME` | ✅ Yes | - | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | ✅ Yes | - | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | ✅ Yes | - | Cloudinary API secret |
| `CORS_ORIGINS` | ✅ Yes | - | Frontend URL(s), comma-separated |
| `ENVIRONMENT` | No | `development` | `development` or `production` |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `720` | Token expiry (12 hours) |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model to use |
| `USE_LOCAL_MODELS` | No | `true` | Use CLIP locally |
| `PROMETHEUS_ENABLED` | No | `true` | Enable metrics (disable for free tier) |

---

## Docker Hub Setup

### 1. Create Repository

```bash
# Login to Docker Hub
docker login

# Tag your image
docker tag flavourcraft-backend yourusername/flavourcraft-backend:latest

# Push to Docker Hub
docker push yourusername/flavourcraft-backend:latest
```

### 2. Update GitHub Workflow

The workflow automatically pushes to Docker Hub on every commit to main.

---

## Monitoring & Health Checks

### Health Check Endpoint

```bash
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-27T12:00:00Z",
  "environment": "production",
  "checks": {
    "database": {
      "status": "connected",
      "healthy": true
    },
    "disk": {
      "healthy": true,
      "total_gb": 50,
      "free_gb": 30,
      "percent_used": 40
    },
    "memory": {
      "healthy": true,
      "total_gb": 4,
      "available_gb": 2,
      "percent_used": 50
    }
  }
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "degraded",
  "checks": {
    "database": {"healthy": false}
  }
}
```

### Metrics Endpoint

```bash
GET /metrics
```

Returns Prometheus-formatted metrics.

### Render Monitoring

1. **Logs**: Real-time logs in Render dashboard
2. **Metrics**: CPU, Memory, Disk usage
3. **Health Checks**: Automatic health pings
4. **Alerts**: Email notifications on failures

---

## Troubleshooting

### Issue: Service Spins Down (Free Tier)

**Problem**: First request after inactivity takes 30-60 seconds

**Solutions**:
1. Upgrade to paid plan ($7/month for 24/7 uptime)
2. Use a ping service to keep it alive:
   - [cron-job.org](https://cron-job.org) - Ping `/health` every 14 minutes
   - [UptimeRobot](https://uptimerobot.com) - Free monitoring

### Issue: Docker Build Fails

**Check**:
```bash
# Build locally to debug
cd backend
docker build -t flavourcraft-backend .

# Check build logs
docker logs <container-id>
```

**Common fixes**:
- Ensure `requirements.txt` has all dependencies
- Verify Dockerfile syntax
- Check Docker Hub credentials

### Issue: Health Check Fails

**Debug**:
```bash
# Check database connection
curl https://your-app.onrender.com/health

# Check logs in Render dashboard
# Look for: "Database connected" message
```

**Common causes**:
- MongoDB Atlas IP whitelist (use 0.0.0.0/0 for all IPs)
- Wrong `MONGODB_URI` format
- Database credentials expired

### Issue: CORS Errors

**Fix**:
```bash
# Ensure CORS_ORIGINS includes your frontend URL
CORS_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
```

### Issue: CI/CD Pipeline Fails

**Check**:
1. GitHub Secrets are set correctly
2. Docker Hub credentials are valid
3. Render deploy hook URL is correct

**Debug**:
```bash
# Go to Actions tab in GitHub
# Click on failed workflow
# Check step-by-step logs
```

### Issue: Out of Memory

**Render Free Tier**: 512MB RAM

**Solutions**:
1. Disable MLOps features for production:
   ```bash
   PROMETHEUS_ENABLED=false
   ENABLE_DRIFT_DETECTION=false
   ```

2. Reduce number of workers:
   ```bash
   # In Dockerfile, use:
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
   ```

3. Optimize CLIP model loading (it's loaded on-demand)

### Issue: API is Slow

**Render Free Tier**: Shared CPU

**Optimizations**:
1. Enable Cloudinary for image processing (offload CPU)
2. Use MongoDB indexes (already configured)
3. Cache OpenAI responses (implement if needed)
4. Upgrade to Render Starter plan for better performance

---

## Cost Breakdown (Free Tier)

| Service | Free Tier | Cost After Free Tier |
|---------|-----------|----------------------|
| **Render** | 750 hours/month | $7/month (starter) |
| **MongoDB Atlas** | 512MB storage | $0.08/GB/month |
| **Cloudinary** | 25GB bandwidth | $0.10/GB |
| **OpenAI** | No free tier | ~$0.0015 per request |
| **Docker Hub** | 1 private repo | $5/month (pro) |
| **GitHub Actions** | 2000 minutes | $0.008/minute |

**Total Free**: $0/month (excluding OpenAI usage)
**Estimated OpenAI Cost**: $5-15/month (depends on usage)

---

## Alternative Deployment Options

### Option 2: Fly.io (Free Tier)

**Advantages**:
- More generous free tier
- Doesn't spin down
- Better for production

**Setup**:
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy
fly launch --dockerfile backend/Dockerfile
```

### Option 3: Railway (Limited Free)

- $5 free credit per month
- Simple deployment
- Good for testing

### Option 4: AWS ECS (Production)

- Best for scale
- More complex setup
- Use Fargate for serverless

---

## Support & Resources

- **Render Docs**: https://render.com/docs
- **Docker Docs**: https://docs.docker.com
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **GitHub Actions**: https://docs.github.com/en/actions

---

## Summary Checklist

- [ ] MongoDB Atlas account created and connection string obtained
- [ ] Cloudinary account created and credentials obtained
- [ ] OpenAI API key obtained
- [ ] Docker Hub account created and access token generated
- [ ] GitHub repository set up with secrets
- [ ] Render account created and service configured
- [ ] Environment variables set in Render dashboard
- [ ] GitHub Actions workflow tested
- [ ] Health check verified
- [ ] Frontend updated with backend URL

**You're all set! Your backend is now deployed with automated CI/CD!** 🚀

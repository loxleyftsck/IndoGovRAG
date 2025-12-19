# 🚀 IndoGovRAG Deployment Guide

**Version:** 1.0  
**Last Updated:** 2024-12-19  
**Target:** Production Deployment

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure:

- [ ] All tests passing (`11/11` ✅)
- [ ] Environment variables configured
- [ ] API keys secured (`.env` not committed)
- [ ] Docker builds successfully
- [ ] Local testing complete
- [ ] Documentation up-to-date

---

## 🐳 Local Deployment (Docker)

### **1. Prerequisites**

```bash
# Required
- Docker Desktop installed
- Docker Compose installed
- Git repository cloned
```

### **2. Environment Setup**

```bash
# Create .env file
cp .env.example .env

# Edit .env and add your Gemini API key
GEMINI_API_KEY=your-key-here
ENVIRONMENT=production
```

### **3. Build & Run**

```bash
# Build Docker image
docker build -t indogovrag:latest .

# Or use Docker Compose
docker-compose up -d

# Check status
docker ps

# View logs
docker logs indogovrag-api -f
```

### **4. Test Deployment**

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs

# Test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Apa itu KTP elektronik?"}'
```

---

## ☁️ Cloud Deployment - Fly.io (100% FREE)

### **Option 1: Fly.io (Recommended)** ⭐

**Free Tier:** 3 VMs (256MB RAM), 160GB transfer

**Steps:**

```bash
# 1. Install Fly CLI
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Mac/Linux
curl -L https://fly.io/install.sh | sh

# 2. Login
fly auth login

# 3. Initialize app
fly launch
# Choose: 
# - App name: indogovrag
# - Region: Singapore (sin)
# - Don't deploy yet

# 4. Set secrets
fly secrets set GEMINI_API_KEY=your-key-here

# 5. Deploy
fly deploy

# 6. Check status
fly status

# 7. Open app
fly open
```

**Custom Domain (Optional):**
```bash
fly certs add yourdomain.com
# Follow DNS instructions
```

---

### **Option 2: Railway (Alternative)**

**Free Tier:** $5 credit/month (renews)

**Steps:**

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize
railway init

# 4. Add environment variables
railway variables set GEMINI_API_KEY=your-key-here

# 5. Deploy
railway up

# 6. Get URL
railway open
```

---

### **Option 3: Render (Alternative)**

**Free Tier:** 750h/month

**Steps:**

1. Go to https://render.com
2. Connect GitHub repository
3. Create new Web Service
4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `GEMINI_API_KEY`
6. Deploy

---

## 🌐 CDN Setup (Cloudflare) - FREE

**Benefits:** Unlimited bandwidth, global caching, DDoS protection

**Steps:**

1. **Sign up:** https://cloudflare.com
2. **Add site:** Enter your domain
3. **Update nameservers:** (provided by Cloudflare)
4. **Configure DNS:**
   - Add A record pointing to Fly.io IP
   - Enable proxy (orange cloud)
5. **SSL/TLS:**
   - Set to "Full (strict)"
6. **Cache Rules:**
   - Cache static assets
   - Cache API responses (optional, 5min TTL)

**Result:** Global CDN, FREE forever ✅

---

## 📊 Monitoring & Logging

### **Fly.io Built-in Monitoring**

```bash
# View metrics
fly dashboard

# View logs
fly logs

# SSH into instance
fly ssh console
```

### **Custom Monitoring (Optional)**

Create simple dashboard using Streamlit:

```python
# monitoring/dashboard.py
import streamlit as st
import requests

st.title("IndoGovRAG Monitoring")

# Health check
response = requests.get("https://your-app.fly.dev/health")
st.metric("Status", "Healthy" if response.ok else "Down")

# Metrics
metrics = requests.get("https://your-app.fly.dev/metrics").json()
st.metric("Total Queries", metrics["total_queries"])
st.metric("Avg Latency", f"{metrics['avg_latency_ms']}ms")
```

---

## 🔒 Security Checklist

Before going live:

- [ ] API keys in environment variables (not code)
- [ ] `.env` in `.gitignore`
- [ ] HTTPS enabled (Fly.io/Cloudflare auto)
- [ ] Rate limiting configured
- [ ] CORS configured properly
- [ ] Input validation enabled
- [ ] Error messages don't leak sensitive info
- [ ] PII detection active
- [ ] Logs don't contain secrets

---

## 🚨 Troubleshooting

### **Issue: Docker build fails**

```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache -t indogovrag:latest .
```

### **Issue: API returns 500 errors**

```bash
# Check logs
docker logs indogovrag-api

# Common causes:
# 1. GEMINI_API_KEY not set
# 2. ChromaDB not initialized
# 3. Missing dependencies

# Fix: Rebuild with verbose logging
docker-compose up
```

### **Issue: Out of memory**

```bash
# Increase Docker memory
# Docker Desktop > Settings > Resources > Memory: 4GB

# Or optimize Python
# Add to Dockerfile:
ENV PYTHONOPTIMIZE=2
```

### **Issue: Fly.io deployment fails**

```bash
# Check logs
fly logs

# Common fixes:
fly secrets list  # Verify secrets set
fly scale memory 512  # Increase memory if needed
fly deploy --strategy immediate  # Force deploy
```

---

## 📈 Scaling Guide

### **When to Scale:**

Monitor these metrics:
- Response time > 500ms
- Error rate > 1%
- Memory usage > 80%
- Free tier limit reached

### **Scaling Options:**

**Vertical Scaling (Fly.io):**
```bash
# Increase memory
fly scale memory 512  # 512MB (paid)

# Increase CPU
fly scale vm shared-cpu-2x  # (paid)
```

**Horizontal Scaling:**
```bash
# Add more instances
fly scale count 3  # 3 instances (paid after free tier)
```

**Caching (Stay Free):**
- Implement embedding cache (Week 5)
- Implement query cache (Week 5)
- Use Cloudflare caching
- Result: 5-10x capacity, still FREE

---

## 💰 Cost Optimization

### **Stay Within Free Tier:**

1. **Cache aggressively:** 80% cache hit rate
2. **Optimize queries:** Reduce LLM calls
3. **Batch processing:** Handle multiple queries efficiently
4. **Monitor usage:** Track Gemini token usage
5. **Use Cloudflare:** Reduce origin requests

### **If Scaling Beyond Free:**

| Queries/Month | Strategy | Cost |
|---------------|----------|------|
| 0-10k | Free tier only | $0 |
| 10k-100k | Free + caching | $0-5 |
| 100k-1M | Multi-platform + CDN | $5-20 |
| 1M+ | Consider sponsors/monetization | $20-100 |

---

## 🔄 Rollback Procedure

If deployment fails:

```bash
# Fly.io rollback
fly releases  # List releases
fly deploy --image <previous-version>

# Railway rollback
railway rollback

# Docker local
docker-compose down
docker-compose up -d --build
```

---

## ✅ Post-Deployment Validation

After deployment, verify:

```bash
# 1. Health check
curl https://your-app.fly.dev/health

# 2. API functionality
curl -X POST https://your-app.fly.dev/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Test query"}'

# 3. Performance
# Should be < 500ms response time

# 4. Error handling
curl https://your-app.fly.dev/query
# Should return 400/422 (not 500)

# 5. Documentation
open https://your-app.fly.dev/docs
# Swagger UI should load
```

---

## 📱 Quick Reference

### **Useful Commands:**

```bash
# Local Development
docker-compose up -d        # Start
docker-compose logs -f      # View logs
docker-compose down         # Stop

# Fly.io
fly deploy                  # Deploy
fly logs                    # View logs
fly ssh console             # SSH
fly status                  # Check status
fly dashboard               # Web dashboard

# Railway
railway up                  # Deploy
railway logs                # View logs
railway open                # Open app
```

### **Important URLs:**

- **Local:** http://localhost:8000
- **Fly.io:** https://your-app.fly.dev
- **Railway:** https://your-app.railway.app
- **Docs:** /docs
- **Health:** /health

---

## 🎯 Success Criteria

Deployment is successful when:

- ✅ Health endpoint returns 200
- ✅ Query endpoint works
- ✅ Response time < 500ms
- ✅ No errors in logs
- ✅ Swagger docs accessible
- ✅ Cost: $0 (free tier)

---

## 📚 Additional Resources

- **Docker:** https://docs.docker.com
- **Fly.io:** https://fly.io/docs
- **Railway:** https://docs.railway.app
- **FastAPI:** https://fastapi.tiangolo.com
- **Cloudflare:** https://developers.cloudflare.com

---

**Deployment Guide Version:** 1.0  
**Maintained By:** Development Team  
**Last Tested:** 2024-12-19

---

**Need Help?** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or create an issue on GitHub.

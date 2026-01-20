# 🚀 Deploy Finance Companion to Render.com (FREE)

## Why Render.com?
- ✅ Free tier for web services (backend)
- ✅ Free PostgreSQL database (90 days, renewable)
- ✅ Free static site hosting (frontend)
- ✅ Auto-deploy from GitHub
- ✅ Custom subdomains (yourapp.onrender.com)

---

## 📋 Step-by-Step Deployment

### Step 1: Push Code to GitHub

```bash
# Make sure all changes are committed
git add .
git commit -m "Add deployment configuration for Render"
git push origin main
```

### Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Click **"Get Started for Free"**
3. Sign up with **GitHub** (recommended - easier deployment)

### Step 3: Deploy PostgreSQL Database

1. In Render Dashboard, click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name:** `finance-companion-db`
   - **Database:** `finance_companion`
   - **User:** `finance_user`
   - **Region:** Choose closest to you
   - **Plan:** **Free**
3. Click **"Create Database"**
4. ⏳ Wait for it to be ready (1-2 minutes)
5. **Copy the "Internal Database URL"** - you'll need this!

### Step 4: Deploy FastAPI Backend

1. Click **"New +"** → **"Web Service"**
2. Connect your **GitHub repository**
3. Configure:
   - **Name:** `finance-companion-api`
   - **Region:** Same as database
   - **Branch:** `main`
   - **Root Directory:** (leave empty)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** **Free**

4. Add **Environment Variables** (click "Advanced"):
   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | (paste Internal Database URL from Step 3) |
   | `SECRET_KEY` | (generate: `openssl rand -hex 32` or any random string) |
   | `PYTHON_VERSION` | `3.11.0` |
   | `finance_companion_key` | (your OpenRouter API key, optional) |

5. Click **"Create Web Service"**
6. ⏳ Wait for deployment (3-5 minutes)
7. **Copy your API URL:** `https://finance-companion-api.onrender.com`

### Step 5: Update Frontend API URL

Before deploying frontend, update the API URL:

**Option A: Create `.env.production` in frontend folder:**
```bash
# frontend/.env.production
VITE_API_URL=https://finance-companion-api.onrender.com
```

**Option B: Set during build (we'll do this in Render)**

### Step 6: Deploy React Frontend

1. Click **"New +"** → **"Static Site"**
2. Connect the **same GitHub repository**
3. Configure:
   - **Name:** `finance-companion-web`
   - **Branch:** `main`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`

4. Add **Environment Variable**:
   | Key | Value |
   |-----|-------|
   | `VITE_API_URL` | `https://finance-companion-api.onrender.com` |

5. Click **"Create Static Site"**
6. ⏳ Wait for deployment (2-3 minutes)

### Step 7: Update Backend CORS (Important!)

After frontend is deployed, add the frontend URL to backend:

1. Go to your **finance-companion-api** service in Render
2. Click **"Environment"**
3. Add new variable:
   | Key | Value |
   |-----|-------|
   | `FRONTEND_URL` | `https://finance-companion-web.onrender.com` |
4. Click **"Save Changes"** (triggers redeploy)

---

## 🎉 Your URLs

After deployment, you'll have:

| Service | URL |
|---------|-----|
| **Frontend (for resume!)** | `https://finance-companion-web.onrender.com` |
| **Backend API** | `https://finance-companion-api.onrender.com` |
| **API Docs** | `https://finance-companion-api.onrender.com/docs` |

---

## ⚠️ Important Notes

### Free Tier Limitations
1. **Spin-down:** Free services sleep after 15 mins of inactivity. First request takes ~30 seconds to wake up.
2. **Database:** Free PostgreSQL expires after 90 days. Create a new one and update `DATABASE_URL`.
3. **Build minutes:** 500 free build minutes/month (plenty for personal projects).

### Keep App Awake (Optional)
Use a free service like [UptimeRobot](https://uptimerobot.com) to ping your API every 14 minutes:
- Add monitor: `https://finance-companion-api.onrender.com/health`
- Interval: 14 minutes

### Voice Feature Note
⚠️ Whisper model requires significant memory. On free tier, voice transcription may be slow or fail. Consider:
- Using `tiny` model instead of `small` (set `WHISPER_MODEL=tiny`)
- Or disabling voice feature for production

---

## 🔧 Troubleshooting

### "Application Error" on backend
- Check **Logs** in Render dashboard
- Verify `DATABASE_URL` is correct
- Ensure all environment variables are set

### Frontend shows "Network Error"
- Check browser console (F12)
- Verify `VITE_API_URL` matches your backend URL
- Check CORS - `FRONTEND_URL` must be set in backend

### Database connection failed
- Make sure you're using **Internal Database URL** (not External)
- The URL should start with `postgres://` or `postgresql://`

---

## 📝 For Your Resume

Add this to your resume:

**Finance Companion** | [Live Demo](https://finance-companion-web.onrender.com) | [GitHub](https://github.com/yourusername/Finance_companion)
- Full-stack personal finance app with voice-enabled expense tracking
- Built with FastAPI, React, PostgreSQL, and OpenAI Whisper
- Features: AI-powered insights, budget goals, spending analytics

---

## 🔄 Auto-Deployment

Render automatically redeploys when you push to GitHub:
```bash
git add .
git commit -m "Update feature"
git push origin main
# Render auto-deploys in ~3 minutes!
```

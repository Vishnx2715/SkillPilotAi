# Skill Pilot AI - Render Deployment Guide

## Prerequisites

1. GitHub account
2. Render account (free tier works)
3. xAI Grok API key (get from https://console.x.ai)

## Quick Deploy (Automated)

### Option 1: Using render.yaml (Recommended)

1. **Push to GitHub**
   ```bash
   cd skill-pilot-ai
   git init
   git add .
   git commit -m "Initial commit - Skill Pilot AI v3.0"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/skill-pilot-ai.git
   git push -u origin main
   ```

2. **Deploy on Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml` and create all services
   - Wait 10-15 minutes for initial deployment

3. **Configure Environment Variables**
   - Go to `skillpilot-backend` service
   - Click "Environment" tab
   - Add: `XAI_API_KEY` = your Grok API key
   - Services will auto-redeploy

4. **Update CORS**
   - Once frontend deploys, copy its URL (e.g., `https://skillpilot-frontend.onrender.com`)
   - Go to backend service → Environment
   - Update `BACKEND_CORS_ORIGINS` to include frontend URL
   - Save (auto-redeploys)

### Option 2: Manual Setup

#### Step 1: Deploy PostgreSQL Database

1. Dashboard → "New +" → "PostgreSQL"
2. Name: `skillpilot-db`
3. Database: `skillpilot`
4. Plan: Free
5. Region: Oregon (or closest)
6. Click "Create Database"
7. Wait for deployment (~2-3 minutes)
8. Copy the **Internal Database URL** from the database dashboard

#### Step 2: Deploy Backend

1. Dashboard → "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `skillpilot-backend`
   - **Region**: Oregon
   - **Branch**: main
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Free

4. Add Environment Variables:
   - `DATABASE_URL` = (paste Internal Database URL from Step 1)
   - `SECRET_KEY` = (generate random 32+ char string, or use Render's "Generate")
   - `ENVIRONMENT` = `production`
   - `XAI_API_KEY` = (your Grok API key from https://console.x.ai)
   - `XAI_MODEL` = `grok-2-1212`
   - `BACKEND_CORS_ORIGINS` = `http://localhost:3000` (update after frontend deploys)
   - `MAX_FILE_SIZE_MB` = `5`
   - `UPLOAD_DIR` = `/tmp/uploads`

5. Click "Create Web Service"
6. Wait 5-10 minutes for first deployment
7. Copy the backend URL (e.g., `https://skillpilot-backend.onrender.com`)

#### Step 3: Deploy Frontend

1. Dashboard → "New +" → "Static Site"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `skillpilot-frontend`
   - **Branch**: main
   - **Root Directory**: `frontend`
   - **Build Command**: 
     ```bash
     npm install && npm run build
     ```
   - **Publish Directory**: `dist`

4. Add Environment Variable:
   - `VITE_API_URL` = (paste backend URL from Step 2)

5. Click "Create Static Site"
6. Wait 5-8 minutes for deployment
7. Copy the frontend URL

#### Step 4: Update CORS

1. Go to backend service
2. Environment tab
3. Update `BACKEND_CORS_ORIGINS`:
   ```
   https://your-frontend-url.onrender.com,http://localhost:3000
   ```
4. Save (triggers auto-redeploy)

## Verify Deployment

1. Visit your frontend URL
2. Backend health check: `https://your-backend.onrender.com/api/v1/health`
3. Try registering a new account
4. Login and test features

## Post-Deployment

### Database Seeding

The database is automatically seeded on first startup with:
- Demo admin account: `admin@skillpilot.ai` / `admin123`
- Demo mentors and students
- Skills, career roles, assessments
- Sample coding problems
- College courses and assignments

### Cold Start Warning

Free tier services sleep after 15 minutes of inactivity. First request after sleep takes 30-60 seconds.

### Environment Variables Reference

**Backend (Required)**
- `DATABASE_URL` - PostgreSQL connection string (auto-provided by Render)
- `SECRET_KEY` - JWT signing key (auto-generate)
- `XAI_API_KEY` - xAI Grok API key (get from https://console.x.ai)
- `ENVIRONMENT` - Set to `production`
- `BACKEND_CORS_ORIGINS` - Comma-separated allowed origins

**Backend (Optional)**
- `XAI_MODEL` - Default: `grok-2-1212`
- `MAX_FILE_SIZE_MB` - Default: `5`
- `UPLOAD_DIR` - Default: `/tmp/uploads`
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Default: `120`

**Frontend (Required)**
- `VITE_API_URL` - Backend URL (e.g., `https://skillpilot-backend.onrender.com`)

## Monitoring

- **Logs**: Each service has a "Logs" tab in Render dashboard
- **Metrics**: "Metrics" tab shows CPU/memory/response times
- **Health**: Backend exposes `/api/v1/health` endpoint

## Troubleshooting

### Backend won't start
1. Check Logs tab for Python errors
2. Verify `DATABASE_URL` is set correctly
3. Ensure all required packages in `requirements.txt`

### Frontend shows "Network Error"
1. Check `VITE_API_URL` matches backend URL
2. Verify CORS settings in backend include frontend URL
3. Check backend is running and healthy

### Database connection errors
1. Verify database is running (check database service)
2. Copy fresh Internal Database URL from database dashboard
3. Update `DATABASE_URL` in backend environment variables

### AI features not working
1. Verify `XAI_API_KEY` is set correctly
2. Check Grok API quota: https://console.x.ai
3. Review logs for API error messages

## Scaling

Free tier limits:
- 750 hours/month per service (auto-sleep after 15min idle)
- 100GB bandwidth/month
- PostgreSQL: 256MB storage, 97 hours/month

To upgrade:
- Backend: Switch to Starter plan ($7/month) for always-on
- Database: Upgrade for more storage/connections
- Frontend: Free tier is usually sufficient

## Local Development After Deploy

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your local settings
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
# Update .env.local with VITE_API_URL=http://localhost:8000
npm run dev
```

## Support

- GitHub Issues: https://github.com/YOUR_USERNAME/skill-pilot-ai/issues
- Render Docs: https://render.com/docs
- xAI Docs: https://docs.x.ai

---

**Security Note**: Never commit `.env` files with real credentials. Use Render's environment variable UI.

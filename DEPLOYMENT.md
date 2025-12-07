# Smart Cotton System - Deployment Guide

## Frontend Deployment (Vercel)

### Prerequisites

- GitHub account
- Vercel account (sign up at vercel.com)

### Steps to Deploy Frontend

1. **Push your code to GitHub** (if not already done):

   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Import to Vercel**:

   - Go to https://vercel.com/new
   - Import your GitHub repository
   - Select the `frontend/smart-cotton` directory as the root directory
   - Framework Preset: Next.js (auto-detected)

3. **Configure Environment Variables** in Vercel:

   - Go to Project Settings → Environment Variables
   - Add:
     ```
     NEXT_PUBLIC_API_URL = https://your-backend-app.onrender.com
     ```

4. **Deploy**:

   - Click "Deploy"
   - Vercel will automatically build and deploy your frontend

5. **Update Domain** (after backend is deployed):
   - After backend deployment, update `NEXT_PUBLIC_API_URL` with actual Render URL
   - Redeploy if needed

---

## Backend Deployment (Render)

### Prerequisites

- GitHub account
- Render account (sign up at render.com)

### Steps to Deploy Backend

1. **Push your code to GitHub** (if not already done):

   ```bash
   git add .
   git commit -m "Add Render configuration"
   git push origin main
   ```

2. **Create PostgreSQL Database** on Render:

   - Go to https://dashboard.render.com/
   - Click "New +" → "PostgreSQL"
   - Name: `smart-cotton-db`
   - Plan: Free
   - Click "Create Database"
   - Copy the "Internal Database URL" for later

3. **Create Web Service** on Render:

   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `smart-cotton-backend`
     - **Region**: Oregon (US West)
     - **Branch**: `main` or your branch name
     - **Root Directory**: `smart_cotton_system`
     - **Runtime**: Python 3
     - **Build Command**: `./build.sh`
     - **Start Command**: `gunicorn config.wsgi:application`
     - **Plan**: Free

4. **Add Environment Variables** in Render:

   ```
   PYTHON_VERSION = 3.11.0
   DEBUG = False
   SECRET_KEY = (generate a strong random key)
   ALLOWED_HOSTS = your-app.onrender.com
   DATABASE_URL = (paste Internal Database URL from step 2)
   CORS_ALLOWED_ORIGINS = https://your-frontend.vercel.app,http://localhost:3000
   CSRF_TRUSTED_ORIGINS = https://your-frontend.vercel.app,https://your-app.onrender.com
   ROBOFLOW_API_KEY = your-roboflow-api-key
   GEMINI_API_KEY = your-gemini-api-key
   ```

5. **Deploy**:

   - Click "Create Web Service"
   - Render will automatically build and deploy

6. **After First Deploy**:
   - Copy your Render backend URL (e.g., `https://smart-cotton-backend.onrender.com`)
   - Go back to Vercel
   - Update `NEXT_PUBLIC_API_URL` environment variable with this URL
   - Redeploy frontend

---

## Post-Deployment

### Update CORS Settings

After both deployments, update your backend's environment variables:

- `CORS_ALLOWED_ORIGINS` - add your Vercel frontend URL
- `CSRF_TRUSTED_ORIGINS` - add both Vercel and Render URLs

### Test Your Deployment

1. Visit your Vercel frontend URL
2. Check that API calls work
3. Test all major features

### Monitoring

- **Vercel**: Check deployment logs at https://vercel.com/dashboard
- **Render**: Check service logs at https://dashboard.render.com/

---

## Important Notes

### Free Tier Limitations

- **Render Free Tier**:

  - Service spins down after 15 minutes of inactivity
  - First request after spin-down takes ~30 seconds
  - 750 hours/month free

- **Vercel Free Tier**:
  - 100 GB bandwidth/month
  - Unlimited deployments

### Security

- Never commit `.env` files
- Use strong SECRET_KEY (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- Keep API keys secure

### Troubleshooting

- Check Render logs for backend errors
- Check Vercel deployment logs for frontend errors
- Verify environment variables are set correctly
- Ensure CORS origins match exactly (including https://)

---

## Quick Commands

### Generate Django Secret Key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Local Testing Before Deploy:

```bash
# Backend
cd smart_cotton_system
python manage.py collectstatic --noinput
gunicorn config.wsgi:application

# Frontend
cd frontend/smart-cotton
npm run build
npm start
```

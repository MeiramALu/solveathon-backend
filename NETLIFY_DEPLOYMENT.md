# Netlify Deployment Guide for Smart Cotton System

## Quick Start

### 1. Install Netlify CLI (Optional)
```bash
npm install -g netlify-cli
```

### 2. Deploy via Netlify UI

#### Step 1: Push Code to Git
```bash
git add .
git commit -m "Add Netlify configuration"
git push origin main
```

#### Step 2: Connect to Netlify
1. Go to https://app.netlify.com/
2. Click "Add new site" → "Import an existing project"
3. Connect your Git provider (GitHub/GitLab/Bitbucket)
4. Select your repository

#### Step 3: Configure Build Settings
- **Base directory**: `frontend/smart-cotton`
- **Build command**: `npm run build`
- **Publish directory**: `frontend/smart-cotton/.next`
- **Framework**: Next.js

#### Step 4: Environment Variables
Add these in Site settings → Environment variables:
```
NEXT_PUBLIC_API_URL=https://your-backend-app.onrender.com
```

#### Step 5: Deploy
Click "Deploy site" and wait for the build to complete.

---

## Alternative: Deploy via CLI

### From the frontend/smart-cotton directory:

```bash
cd frontend/smart-cotton

# Login to Netlify
netlify login

# Initialize (first time only)
netlify init

# Deploy to production
netlify deploy --prod
```

---

## Important Notes

### 1. Next.js on Netlify
Netlify requires the `@netlify/plugin-nextjs` plugin for proper Next.js support. This is configured in `netlify.toml`.

### 2. Update Backend CORS Settings
After deploying, update your backend's CORS settings to allow your Netlify domain:

In `smart_cotton_system/config/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    'https://your-site-name.netlify.app',
    'http://localhost:3000',
]

CSRF_TRUSTED_ORIGINS = [
    'https://your-site-name.netlify.app',
]
```

### 3. Custom Domain (Optional)
- Go to Site settings → Domain management
- Add your custom domain
- Update DNS records as instructed

---

## Troubleshooting

### Build Failures
- Check Node.js version (should be 18+)
- Verify all dependencies are in `package.json`
- Check build logs in Netlify dashboard

### API Connection Issues
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check backend CORS settings
- Ensure backend is running and accessible

### 404 Errors
- The `netlify.toml` redirects should handle this
- Make sure publish directory is set to `.next`

---

## Deploy Backend to Render

Your backend is already configured for Render. Follow the steps in `DEPLOYMENT.md` to deploy the Django backend.

---

## Full Deployment Flow

1. Deploy backend to Render (follow `DEPLOYMENT.md`)
2. Get the Render URL (e.g., `https://smart-cotton-backend.onrender.com`)
3. Add the URL to Netlify environment variables as `NEXT_PUBLIC_API_URL`
4. Deploy frontend to Netlify
5. Update backend CORS settings with your Netlify URL
6. Test the full application

---

## Continuous Deployment

Netlify automatically redeploys when you push to your Git repository. You can configure:
- Deploy previews for pull requests
- Branch deploys
- Deploy hooks for external triggers

Configure these in: Site settings → Build & deploy

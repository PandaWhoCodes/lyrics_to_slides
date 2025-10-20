# Deployment Checklist for Render

## Before Deploying

- [x] Remove unused service account keys
- [x] Update .gitignore for production
- [x] Create render.yaml configuration
- [x] Update README with deployment instructions

## Deployment Steps

### 1. Prepare Repository

```bash
# Check current status
git status

# Add all changes
git add .

# Commit
git commit -m "feat: prepare for Render deployment"

# Push to GitHub
git push origin main
```

### 2. Create Render Account

1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

### 3. Deploy via Blueprint

1. Click **"New +"** → **"Blueprint"**
2. Connect your `lyrics_to_slides` repository
3. Render will auto-detect `render.yaml`
4. Review the services:
   - `lyrics-to-slides-api` (Backend)
   - `lyrics-to-slides-frontend` (Frontend)
5. Click **"Apply"** to deploy both services

### 4. Configure Environment Variables

**Backend Service:**
1. Go to Dashboard → `lyrics-to-slides-api`
2. Navigate to "Environment" tab
3. Add secret environment variable:
   - Key: `XAI_API_KEY`
   - Value: `your-xai-api-key-here` (get from your xAI dashboard)
4. Click "Save Changes"
5. Wait for automatic redeploy

**Frontend Service:**
1. Go to Dashboard → `lyrics-to-slides-frontend`
2. Navigate to "Environment" tab
3. Add environment variable:
   - Key: `VITE_API_URL`
   - Value: `https://lyrics-to-slides-api.onrender.com` (use your actual backend URL)
4. Click "Save Changes"
5. Trigger manual deploy

### 5. Verify Deployment

1. **Backend Health Check:**
   - Visit: `https://your-api.onrender.com/`
   - Should return: `{"message": "Lyrics to Slides API"}`

2. **Frontend:**
   - Visit: `https://your-frontend.onrender.com/`
   - Should load the UI

3. **Test Full Flow:**
   - Enter a song name
   - Click search
   - Select result
   - Generate presentation
   - Download should work

## Post-Deployment

### Monitor Logs

**Backend Logs:**
```
Dashboard → lyrics-to-slides-api → Logs
```
Watch for:
- Playwright installation success
- API requests
- Any errors

**Frontend Logs:**
```
Dashboard → lyrics-to-slides-frontend → Logs
```
Watch for:
- Build success
- Static file serving

### Common Issues

**Issue: Playwright browsers not found**
- Solution: Ensure build command includes `playwright install chromium`
- Check in render.yaml: `buildCommand: "pip install -r requirements.txt && playwright install chromium"`

**Issue: CORS errors**
- Solution: Update CORS origins in `backend/main.py`
- Add your frontend URL to `allow_origins`

**Issue: API calls fail**
- Solution: Verify `VITE_API_URL` is set correctly in frontend
- Check backend URL in Render dashboard

**Issue: Grok API errors**
- Solution: Verify `XAI_API_KEY` is set correctly
- Check xAI API quota/limits

## Performance Optimization

### For Free Tier

Render free tier services spin down after 15 minutes of inactivity:
- First request after spin-down takes ~30 seconds
- Subsequent requests are fast

### Upgrade Considerations

Consider upgrading if:
- You need faster cold starts
- You have high traffic
- You need custom domains

## Security Notes

- API keys are stored as secret environment variables
- Never commit API keys to git
- `.gitignore` prevents accidental commits
- Service account keys removed (not needed)

## Maintenance

### Update Deployment

```bash
# Make changes locally
git add .
git commit -m "feat: your changes"
git push origin main

# Render auto-deploys on push
```

### Manual Redeploy

In Render Dashboard:
1. Go to your service
2. Click "Manual Deploy"
3. Select branch
4. Click "Deploy"

## Monitoring

### Check Service Status

```bash
# Backend health
curl https://your-api.onrender.com/

# Test search endpoint
curl -X POST https://your-api.onrender.com/api/search \
  -H "Content-Type: application/json" \
  -d '{"song_name":"test"}'
```

### View Metrics

In Render Dashboard:
- CPU usage
- Memory usage
- Request counts
- Error rates

## Rollback

If deployment fails:
1. Go to Render Dashboard
2. Navigate to service
3. Click "Deploys" tab
4. Find previous working deploy
5. Click "Rollback"

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- GitHub Issues: Your repository issues page

# Deployment Guide

## Fly.io Deployment

### Prerequisites

1. Install Fly.io CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Sign up and login:
```bash
fly auth signup  # or fly auth login
```

### First Time Deployment

1. **Clone the repository**:
```bash
git clone <your-repo-url>
cd lyrics_to_slides
```

2. **Launch the app** (creates app on Fly.io):
```bash
fly launch --no-deploy
```
- Choose your app name (or use default: `lyrics-to-slides`)
- Choose your region (closest to your users)
- Don't deploy yet - we need to set secrets first

3. **Set environment variables**:
```bash
fly secrets set XAI_API_KEY="your_xai_api_key_here"
fly secrets set GOOGLE_API_KEY="your_google_api_key_here"
fly secrets set GOOGLE_SEARCH_ENGINE_ID="your_search_engine_id_here"
```

4. **Create persistent volume** (for temporary file storage):
```bash
fly volumes create lyrics_data --size 1 --region <your-region>
```

5. **Deploy the application**:
```bash
fly deploy
```

6. **Open your app**:
```bash
fly open
```

### Updating the App

After making changes:

```bash
git pull  # or make your changes
fly deploy
```

### Monitoring

- **View logs**: `fly logs`
- **Check status**: `fly status`
- **Scale resources**: `fly scale memory 4096` (if needed)
- **SSH into machine**: `fly ssh console`

### Configuration

The app is configured in fly.toml:

- **Region**: Set in `primary_region` (e.g., "lax", "iad", "fra")
- **Resources**: 2 CPUs, 2GB RAM (adjustable in `[vm]` section)
- **Auto-scaling**: Machines auto-stop when idle, restart on request
- **Health checks**: HTTP GET to `/health` every 10s

### Cost Estimate

- **Free tier**: Includes 3 shared-cpu-1x machines with 256MB RAM
- **This app**: Uses 2 CPUs + 2GB RAM = ~$10-15/month
- **Auto-stop**: Reduces costs when not in use (billed by running time)

### Troubleshooting

**Build fails - Playwright installation:**
```bash
# Check build logs
fly logs
# May need to increase build timeout or use larger builder
```

**App crashes on start:**
```bash
# Check if secrets are set
fly secrets list
# View detailed logs
fly logs --tail
```

**Out of memory:**
```bash
# Increase memory
fly scale memory 4096
```

**Slow cold starts:**
```bash
# Keep at least 1 machine running
fly scale count 1
```

### Alternative: Ubuntu VPS Deployment

If Fly.io costs are too high, you can deploy on a traditional VPS:

1. **Clone repo on server**:
```bash
git clone <your-repo-url>
cd lyrics_to_slides
```

2. **Run installer**:
```bash
chmod +x install.sh
./install.sh
```

3. **Create .env file**:
```bash
nano .env
# Add your API keys
```

4. **Start the app**:
```bash
./start.sh
```

5. **Optional: Set up as systemd service** for auto-restart.

### Recommended VPS Providers

- **DigitalOcean**: $6/month droplet
- **Linode**: $5/month nanode
- **Vultr**: $6/month instance
- **AWS EC2**: t2.micro free tier (1 year)
- **Hetzner**: €4.5/month CX11

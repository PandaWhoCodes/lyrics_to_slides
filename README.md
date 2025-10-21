# Lyrics to Slides 🎵→📊

An AI-powered web app that converts song lyrics into beautiful PowerPoint presentations. Uses Grok AI for intelligent lyrics extraction and grouping by verse/chorus structure.

## 🎥 Demo Video

Watch the app in action: [Demo Video](https://drive.google.com/file/d/1Q62mHQlNHw-YvQxKk0YLRSWcywXLeTkC/view?usp=sharing)

## ✨ Features

- 🎨 **Sleek Apple-inspired UI** - Clean, modern design
- 🤖 **AI-Powered** - Grok intelligently extracts titles and groups lyrics
- 🔍 **Smart Search** - Google Custom Search finds the best lyrics sources
- 🎭 **Multi-Song Support** - Add multiple songs to one presentation
- 📑 **Title Slides** - Each song starts with its title and artist
- 🧠 **Intelligent Grouping** - Keeps verses and choruses together naturally
- 🧹 **Auto-Cleanup** - Generated files are automatically deleted after download
- 🌐 **JavaScript Rendering** - Playwright handles dynamic websites

## 🚀 Quick Start

### Local Development

```bash
./start.sh
```

Then open [http://localhost:5173](http://localhost:5173)

### Manual Setup

**Backend:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cd backend && python main.py
```

**Frontend:**
```bash
npm install
npm run dev
```

## 📦 Deployment to Render

### Prerequisites
- GitHub repository with this code
- Render account ([render.com](https://render.com))
- xAI API key

### Deploy Steps

1. **Push to GitHub:**
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

2. **Create Render Services:**

Go to [render.com](https://render.com) and create a **Blueprint** from `render.yaml`:

- Connect your GitHub repository
- Render will auto-detect `render.yaml`
- Click "Apply" to create both services

3. **Set Environment Variables:**

In the Render Dashboard, go to your **API service** and add:
- `XAI_API_KEY` = `your-xai-api-key-here`

The Google API keys are already configured in `render.yaml`

4. **Update Frontend API URL:**

After backend deploys, update the frontend environment variable:
- Go to frontend service settings
- Add `VITE_API_URL` = `https://your-backend-url.onrender.com`
- Trigger a manual deploy

### Architecture on Render

```
Frontend (Static Site) → Backend API (Python)
     ↓                        ↓
  Vite Build            FastAPI + Playwright
                             ↓
                    xAI Grok + Google Search
```

## 🎯 How to Use

1. **Enter Songs** - Type song names (e.g., "Thunder by Imagine Dragons")
2. **Search** - Click search to find lyrics via Google
3. **Select** - Choose the Genius.com or lyrics site result
4. **Configure** - Set lines per slide (or let AI decide)
5. **Generate** - Download your PPTX presentation!

## 🏗️ Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **Playwright** - Headless browser for JavaScript rendering
- **BeautifulSoup** - HTML parsing
- **xAI Grok** - AI-powered lyrics extraction and grouping
- **python-pptx** - PowerPoint generation
- **Google Custom Search API** - Finding lyrics sources

### Frontend
- **React** - UI framework
- **Vite** - Fast build tool
- **Axios** - HTTP client
- **CSS3** - Apple-inspired styling

## 📁 Project Structure

```
lyrics_to_slides/
├── backend/
│   ├── main.py              # FastAPI server & routes
│   ├── search_service.py    # Google Custom Search
│   ├── lyrics_service.py    # Playwright + Grok extraction
│   └── pptx_service.py      # PowerPoint generation
├── src/
│   ├── App.jsx              # Main React component
│   ├── App.css              # Styling
│   ├── config.js            # API configuration
│   └── main.jsx             # Entry point
├── render.yaml              # Render deployment config
├── requirements.txt         # Python dependencies
├── package.json             # Node dependencies
└── start.sh                 # Local dev script
```

## 🔐 Environment Variables

### Required
- `XAI_API_KEY` - Your xAI Grok API key

### Optional
- `VITE_API_URL` - Backend URL (auto-detected locally)

### Pre-configured
- `GOOGLE_API_KEY` - Google Custom Search API key
- `GOOGLE_SEARCH_ENGINE_ID` - Custom search engine ID

## 🎨 Features Deep Dive

### AI-Powered Title Extraction
Grok analyzes webpage content to extract the actual song title and artist, no URL parsing needed.

### Intelligent Lyric Grouping
Instead of blindly splitting every N lines, Grok:
- Identifies verse/chorus/bridge structure
- Keeps logical sections together
- Won't split mid-chorus or mid-verse
- Respects natural song flow

### Smart Scraping
- **Playwright** renders JavaScript-heavy sites
- **BeautifulSoup** extracts content with site-specific selectors
- **Grok** cleans and structures the output

### Auto-Cleanup
Generated PPTX files are automatically deleted from the server 2 seconds after download.

## 🐛 Troubleshooting

**Spotify/Smule URLs don't work:**
- These require authentication
- Use the Google Search feature to find Genius.com or other lyrics sites

**Playwright timeout:**
- Some sites have anti-bot protection
- Try a different search result (Genius.com works best)

**Deployment issues:**
- Check Render logs for errors
- Ensure Playwright browsers are installed: `playwright install chromium`
- Verify environment variables are set

## 📝 License

MIT

## 🤝 Contributing

Pull requests welcome! This project uses:
- Black for Python formatting
- ESLint for JavaScript
- Conventional commits

## 🙏 Credits

Built with:
- [xAI Grok](https://x.ai) - AI-powered extraction
- [Genius](https://genius.com) - Lyrics source
- [Playwright](https://playwright.dev) - Browser automation
- [FastAPI](https://fastapi.tiangolo.com) - Backend framework
- [React](https://react.dev) - Frontend framework
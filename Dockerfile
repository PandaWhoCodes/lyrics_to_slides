# Multi-stage build for lyrics-to-slides application
FROM node:18-alpine AS frontend-builder

# Build frontend
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build && npm prune --production

# Python backend with Playwright
FROM python:3.11-slim

# Install only essential runtime dependencies for Playwright
# Remove build tools and unnecessary packages after installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    libglib2.0-0 \
    libgdk-pixbuf-2.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# Install Playwright Chromium browser only
RUN playwright install chromium --with-deps || playwright install chromium \
    && rm -rf /root/.cache/ms-playwright/*/.git \
    && rm -rf /root/.cache/pip

# Copy backend code
COPY backend/ ./backend/
COPY reference_template.pptx ./backend/

# Copy frontend build from builder stage (only dist folder)
COPY --from=frontend-builder /app/dist ./dist

# Create directory for generated files
RUN mkdir -p /data

# Remove unnecessary files to reduce size
RUN find /usr/local/lib/python3.11 -type d -name tests -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.11 -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true \
    && rm -rf /tmp/* /var/tmp/*

# Change working directory to backend
WORKDIR /app/backend

# Expose port
EXPOSE 8080

# Set environment variable for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Start the application (now running from /app/backend directory like start.sh)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

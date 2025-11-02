# Multi-stage build for lyrics-to-slides application
FROM node:18-slim AS frontend-builder

# Build frontend
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Python backend with Playwright
FROM python:3.11-slim

# Install system dependencies for Playwright and PPT generation
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
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
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and Chromium
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy backend code
COPY backend/ ./backend/
COPY reference_template.pptx ./

# Copy frontend build from builder stage
COPY --from=frontend-builder /app/dist ./dist

# Create directory for generated files
RUN mkdir -p /data

# Expose port
EXPOSE 8080

# Set environment variable for production
ENV PYTHONUNBUFFERED=1

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Start the application
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]

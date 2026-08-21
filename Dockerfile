FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files and test suite
COPY app/ ./app/
COPY static/ ./static/
COPY tests/ ./tests/
COPY pytest.ini .

# Environment variables
ENV PORT=3000
ENV DB_PATH=/app/data/ausgabenplaner.db
ENV TZ=Europe/Berlin
ENV APP_TIMEZONE=Europe/Berlin

# Expose container port
EXPOSE 3000

# Create volume mount point for Synology NAS persistence
VOLUME ["/app/data"]

# Run server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]

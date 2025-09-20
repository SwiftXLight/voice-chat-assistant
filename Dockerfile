# Multi-stage build for production deployment
FROM node:18-alpine AS frontend-builder

# Build frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# Python backend
FROM python:3.11-slim AS backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy backend dependency files
COPY backend/pyproject.toml ./
COPY backend/poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy backend source
COPY backend/ ./

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./static

# Create startup script
RUN echo '#!/bin/bash\n\
if [ "$ENVIRONMENT" = "production" ]; then\n\
    exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2\n\
else\n\
    exec uvicorn main:app --host 0.0.0.0 --port $PORT --reload\n\
fi' > /app/start.sh && chmod +x /app/start.sh

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/ || exit 1

# Start application
CMD ["/app/start.sh"]

# Multi-stage build for production deployment
FROM node:18-alpine AS frontend-builder

# Build frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
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
    && poetry install --only=main --no-interaction --no-ansi --no-root

# Copy backend source
COPY backend/ ./

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./static

# Debug: List contents to verify static files exist
RUN ls -la ./static/ || echo "Static directory not found"

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Environment: $ENVIRONMENT"\n\
echo "Port: $PORT"\n\
echo "Static directory contents:"\n\
ls -la /app/static/ || echo "No static directory"\n\
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

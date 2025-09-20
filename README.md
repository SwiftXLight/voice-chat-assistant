# Voice Chat App

A React application that records voice, converts it to text using OpenAI Whisper, and gets responses from ChatGPT.

## Project Structure

```
voice-chat-app/
├── frontend/          # React + Vite + TypeScript
├── backend/           # FastAPI + OpenAI integration
└── README.md
```

## Setup

### 🚀 **Quick Start with Docker (Recommended)**

#### **One-Command Start:**
```bash
./start.sh
```

That's it! The script will:
- ✅ Check if `.env` exists (creates it if needed)
- ✅ Verify Docker is running
- ✅ Start both frontend and backend containers
- ✅ Show you the URLs to access

#### **Available Docker Commands:**
```bash
./start.sh           # Start the application
./start.sh stop      # Stop all services
./start.sh logs      # View container logs
./start.sh restart   # Restart all services
```

#### **First Time Docker Setup:**
1. **Run the script:**
   ```bash
   ./start.sh
   ```

2. **Add your OpenAI API key:**
   - Edit the `.env` file that gets created
   - Add your `OPENAI_API_KEY=your_key_here`

3. **Run again:**
   ```bash
   ./start.sh
   ```

4. **Access your app:**
   - **Frontend:** http://localhost:3000
   - **Backend API:** http://localhost:8000

---

### 🛠️ **Local Development Setup**

For local development without Docker:

#### **Prerequisites:**
- Python 3.11+
- Node.js 18+
- Poetry (Python package manager)

#### **Backend Setup:**
```bash
# Navigate to backend directory
cd backend

# Install Poetry if not installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Start backend server
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### **Frontend Setup:**
```bash
# Navigate to frontend directory (in a new terminal)
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### **Environment Variables:**
Create a `.env` file in the root directory:
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
VITE_API_URL=http://localhost:8000
```

#### **Alternative Backend Start Methods:**
```bash
# Method 1: Using Poetry (Recommended)
cd backend
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Method 2: Using Python directly
cd backend
poetry shell  # Activate virtual environment
python main.py

# Method 3: Using traditional venv (if you prefer)
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt  # You'll need to generate this from pyproject.toml
python main.py
```

### 🐛 **Development & Debugging:**

#### **Backend Debugging:**
```bash
# Run with full debugging support
cd backend
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

#### **Frontend Debugging:**
```bash
# Run with development tools
cd frontend
npm run dev
```

#### **Running Tests:**
```bash
# Backend tests
cd backend
poetry run pytest tests/ -v

# Frontend tests (if available)
cd frontend
npm run test
```

### 📁 **Project Structure:**
```
voice-chat-app/
├── backend/           # FastAPI + OpenAI integration
├── frontend/          # React + Vite + TypeScript  
├── .env              # Environment variables (your API key)
├── .env.example      # Environment template
├── docker-compose.yml # Docker containers
├── start.sh          # Main startup script
└── README.md
```

## Features

- 🎤 Voice recording using WebRTC/MediaRecorder
- 🗣️ Speech-to-text using OpenAI Whisper
- 🤖 AI responses using ChatGPT
- 📱 Single-page React interface

## Tech Stack

- **Frontend**: React, Vite, TypeScript
- **Backend**: FastAPI, Python
- **AI**: OpenAI Whisper, ChatGPT
- **Audio**: WebRTC, MediaRecorder API
- **Containerization**: Docker, Docker Compose
- **Development**: VS Code/Cursor integration with debugging support

## Docker Files

- `backend/Dockerfile` - Production backend container
- `backend/Dockerfile.dev` - Development backend with debugger
- `frontend/Dockerfile` - Frontend development container
- `docker-compose.yml` - Production multi-container setup
- `docker-compose.dev.yml` - Development with debugging support
- `.vscode/launch.json` - Cursor/VS Code run configurations

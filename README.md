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

### 🚀 **Super Simple Startup**

#### **One-Command Start:**
```bash
./start.sh
```

That's it! The script will:
- ✅ Check if `.env` exists (creates it if needed)
- ✅ Verify Docker is running
- ✅ Start both frontend and backend containers
- ✅ Show you the URLs to access

#### **Available Commands:**
```bash
./start.sh           # Start the application
./start.sh stop      # Stop all services
./start.sh logs      # View container logs
./start.sh restart   # Restart all services
```

#### **First Time Setup:**
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

### 🐛 **For Debugging:**
```bash
# Run backend locally with full debugging support
cd backend && source venv/bin/activate && python main.py
```
This gives you full Python debugging capabilities with breakpoints, etc.

### 🛠️ **Manual Setup (if needed):**
```bash
# Backend - the code will automatically find the .env file in the root directory
cd backend && source venv/bin/activate && python main.py

# Frontend (in another terminal)
cd frontend && npm run dev
```

**Note:** The backend automatically loads the `.env` file from the root directory, so you don't need a separate backend `.env` file.

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

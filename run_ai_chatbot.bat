@echo off
echo Starting AI Chatbot (Migrated)...

:: Set Python to use UTF-8 for console output
set PYTHONIOENCODING=utf-8

:: Start Backend
echo Starting Backend on port 9010...
start "AI Chatbot Backend" cmd /k "cd backend && python -m pip install -r requirements.txt && python -m uvicorn main:app --reload --host 0.0.0.0 --port 9010"

:: Start Frontend
echo Starting Frontend...
start "AI Chatbot Frontend" cmd /k "cd frontend && npm install && npm run dev"

echo Both services are starting in new windows.

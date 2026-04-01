#!/bin/bash

# Start both backend and frontend for development

echo "Starting First Move development environment..."

# Start frontend in background first
echo "Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 3

# Start backend in foreground (so logs are visible)
echo "Starting backend server..."
cd ../backend
PYTHONPATH=/Users/jojowang/Documents/UChi/FinMatrix/FirstMove/first-move/backend python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --log-level debug

# When backend stops, stop frontend
echo "Stopping frontend..."
kill $FRONTEND_PID
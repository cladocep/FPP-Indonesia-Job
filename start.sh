#!/bin/bash

# Start FastAPI backend in background
echo "Starting backend..."
uvicorn backend.app.main:app --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to initialize
sleep 2

# Start Streamlit frontend
echo "Starting Streamlit frontend..."
streamlit run frontend/streamlit/app.py

# When Streamlit exits, kill the backend too
kill $BACKEND_PID


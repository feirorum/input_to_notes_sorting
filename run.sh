#!/bin/bash

# Semantic Sorting Lab - Run Script
# Starts both backend and frontend servers

echo "🧪 Starting Semantic Sorting Lab..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if backend dependencies are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Backend dependencies not installed. Installing..."
    cd backend
    pip install -r requirements.txt
    cd ..
fi

echo "✅ Dependencies OK"
echo ""

# Start backend server
echo "🚀 Starting backend server on http://localhost:8000"
cd backend
python3 main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
done

# Start frontend server
echo "🌐 Starting frontend server on http://localhost:8080"
cd frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✨ Semantic Sorting Lab is running!"
echo ""
echo "   Frontend: http://localhost:8080"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Open browser (optional)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8080
elif command -v open &> /dev/null; then
    open http://localhost:8080
fi

# Wait for user interrupt
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '✅ Stopped'; exit 0" INT

# Keep script running
wait

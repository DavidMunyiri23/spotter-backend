#!/bin/bash
echo "Starting FMCSA HOS Tracker Backend..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt
echo

# Run migrations
echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate
echo

# Start server
echo "Starting Django development server..."
echo "Backend will be available at: http://localhost:8000/api/"
echo "Admin interface at: http://localhost:8000/admin/"
echo
python manage.py runserver
@echo off
cd /d "%~dp0"
echo Starting FMCSA HOS Tracker Backend...
echo Current directory: %CD%
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
echo.

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt
echo.

REM Run migrations
echo Running migrations...
python manage.py makemigrations
python manage.py migrate
echo.

REM Start server
echo Starting Django development server...
echo Backend will be available at: http://localhost:8000/api/
echo Admin interface at: http://localhost:8000/admin/
echo.
python manage.py runserver
#!/bin/bash

# Deployment script for Product Capability Matching System
# This script automates the deployment process on the server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT/.."

print_info "Starting deployment..."
print_info "Project root: $(pwd)"

# Step 1: Pull latest code
print_info "Step 1: Pulling latest code..."
git fetch origin main || git fetch origin main
git checkout main
git pull origin main

# Step 2: Activate virtual environment
print_info "Step 2: Activating virtual environment..."
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found!"
    exit 1
fi
source venv/bin/activate

# Step 3: Install/update Python dependencies
print_info "Step 3: Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Step 4: Build frontend
print_info "Step 4: Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Step 5: Run database migrations
print_info "Step 5: Running database migrations..."
cd backend
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py migrate --noinput

# Step 6: Collect static files
print_info "Step 6: Collecting static files..."
python manage.py collectstatic --noinput
cd ..

# Step 7: Restart Gunicorn service
print_info "Step 7: Restarting Gunicorn service..."
sudo systemctl restart prod-answer

# Wait for service to start
sleep 3

# Check if service is running
if sudo systemctl is-active --quiet prod-answer; then
    print_info "Gunicorn service started successfully"
else
    print_error "Failed to start Gunicorn service"
    sudo systemctl status prod-answer
    exit 1
fi

# Step 8: Reload nginx
print_info "Step 8: Reloading nginx..."
sudo systemctl reload nginx

print_info "Deployment completed successfully!"
print_info "Application is now running at: http://103.40.14.59"

#!/bin/bash

# TravelMate Production Build Script
echo "🚀 TravelMate Build Script"
echo "=========================="

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Collect static files with verbose output
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear -v 3

echo "✅ Build complete!"
#!/bin/bash

# TravelMate Production Deployment Script
echo "🚀 TravelMate Production Deployment Script"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv_new" ]; then
    echo "❌ Virtual environment not found. Please run the setup first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv_new/bin/activate

# Install production dependencies
echo "📥 Installing production dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --settings=TravelMate.settings_production --noinput clear

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --settings=TravelMate.settings_production

# Test production settings
echo "🧪 Testing production configuration..."
python manage.py check --settings=TravelMate.settings_production

echo "✅ Production setup complete!"
echo ""
echo "🌐 To run in production mode locally:"
echo "   python manage.py runserver --settings=TravelMate.settings_production"
echo ""
echo "🚀 To deploy to Railway:"
echo "   1. Push your code to GitHub"
echo "   2. Connect to Railway.app"
echo "   3. Add environment variables"
echo "   4. Deploy!"
echo ""
echo "📖 See deploy.md for detailed deployment instructions"

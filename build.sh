#!/bin/bash

# TravelMate Production Build Script
echo "🚀 TravelMate Build Script"
echo "=========================="

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Running database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Create superuser if it doesn't exist (optional)
echo "👤 Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

# Collect static files with verbose output
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "✅ Build complete!"
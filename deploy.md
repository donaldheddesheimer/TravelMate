# TravelMate Production Deployment Guide

## 🚀 Quick Deploy Options

### Option 1: Railway (Recommended - Free & Easy)

1. **Sign up** at [railway.app](https://railway.app)
2. **Connect your GitHub** repository
3. **Deploy** - Railway will automatically detect Django and deploy
4. **Add environment variables** in Railway dashboard:
   ```
   SECRET_KEY=your-secret-key-here
   OWM_API_KEY=your-openweathermap-key
   GEOCODE_API_KEY=your-geocode-key
   OPENROUTER_API_KEY=your-openrouter-key
   GOOGLE_API_KEY=your-google-key
   ```
5. **Your app will be live** at `https://your-app-name.railway.app`

### Option 2: Render (Free Tier Available)

1. **Sign up** at [render.com](https://render.com)
2. **Create new Web Service**
3. **Connect your GitHub** repository
4. **Configure**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn TravelMate.wsgi:application --bind 0.0.0.0:$PORT`
5. **Add environment variables** in Render dashboard
6. **Deploy**

### Option 3: Heroku (Paid but Reliable)

1. **Install Heroku CLI**
2. **Login**: `heroku login`
3. **Create app**: `heroku create your-app-name`
4. **Add PostgreSQL**: `heroku addons:create heroku-postgresql:hobby-dev`
5. **Set environment variables**:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set OWM_API_KEY=your-openweathermap-key
   heroku config:set GEOCODE_API_KEY=your-geocode-key
   heroku config:set OPENROUTER_API_KEY=your-openrouter-key
   heroku config:set GOOGLE_API_KEY=your-google-key
   ```
6. **Deploy**: `git push heroku main`

## 🔧 Local Production Testing

Test your production setup locally:

```bash
# Install production dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --settings=TravelMate.settings_production

# Run with production settings
python manage.py runserver --settings=TravelMate.settings_production
```

## 📋 Pre-Deployment Checklist

- [ ] All API keys are set in environment variables
- [ ] DEBUG = False in production settings
- [ ] SECRET_KEY is secure and unique
- [ ] ALLOWED_HOSTS includes your domain
- [ ] Static files are configured
- [ ] Database is set up (PostgreSQL recommended)
- [ ] Environment variables are configured on hosting platform

## 🛡️ Security Notes

- Never commit `.env` files to version control
- Use strong, unique SECRET_KEY
- Enable HTTPS in production
- Keep DEBUG = False in production
- Use environment variables for all sensitive data

## 📊 Monitoring

After deployment, monitor your app:
- Check logs for errors
- Monitor API usage limits
- Set up uptime monitoring
- Configure error tracking (Sentry recommended)

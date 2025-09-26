# 🧳 TravelMate

<div align="center">

![TravelMate Logo](<img width="2834" height="1292" alt="image" src="https://github.com/user-attachments/assets/892e5eef-fbc6-40f0-b6cc-a3696fe07f8d" />
)

**Your Smart Travel Planning Companion**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-🌐%20Visit%20App-ff4c24?style=for-the-badge)](https://travelmate-jv1d.onrender.com/)
[![Django](https://img.shields.io/badge/Django-4.2.24-092E20?style=for-the-badge&logo=django)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

A comprehensive travel planning and management web application built with Django. TravelMate helps users organize trips, get weather forecasts, generate packing lists, discover travel tips, and interact with an AI-powered travel assistant.

**🌐 [Try TravelMate Live](https://travelmate-jv1d.onrender.com/)**

</div>

---

## 🌟 Features

<table>
<tr>
<td width="50%">

### 🎯 Core Functionality
- **✈️ Trip Management**: Create, edit, and organize travel itineraries with destinations and dates
- **🔐 User Authentication**: Secure user registration, login, and profile management  
- **📊 Dashboard**: Centralized overview of all travel-related information

### 🚀 Smart Travel Tools
- **🌤️ Weather Integration**: Real-time weather forecasts for trip destinations using OpenWeatherMap API
- **🧳 AI-Powered Packing Lists**: Automatically generate customized packing lists based on destination, weather, and trip duration
- **💡 Travel Tips**: Get personalized travel advice and recommendations
- **🤖 AI Chat Assistant**: Interactive chatbot for travel-related questions and planning assistance

</td>
<td width="50%">

### 💻 User Experience
- **📱 Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **🎨 Modern UI**: Clean, intuitive interface with smooth animations and transitions
- **🌙 Dark Theme**: Elegant dark mode design with orange accent colors
- **⚡ Fast Performance**: Optimized loading times and smooth interactions

### 🛡️ Security & Reliability
- **🔒 Secure Authentication**: Protected user accounts and data
- **☁️ Cloud Deployment**: Reliable hosting on Render platform
- **📈 Scalable Architecture**: Built to handle growing user base

</td>
</tr>
</table>

## 🛠️ Tech Stack

<div align="center">

| Category | Technologies |
|----------|-------------|
| **Backend** | ![Django](https://img.shields.io/badge/Django-4.2.24-092E20?style=flat-square&logo=django) ![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python) ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=postgresql) |
| **Frontend** | ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3) ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5) ![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?style=flat-square&logo=bootstrap) |
| **APIs** | ![OpenWeatherMap](https://img.shields.io/badge/OpenWeatherMap-orange?style=flat-square) ![OpenRouter](https://img.shields.io/badge/OpenRouter-AI-blue?style=flat-square) ![Google](https://img.shields.io/badge/Google_APIs-4285F4?style=flat-square&logo=google) |
| **Deployment** | ![Render](https://img.shields.io/badge/Render-000000?style=flat-square) ![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=flat-square&logo=gunicorn) ![WhiteNoise](https://img.shields.io/badge/WhiteNoise-static-green?style=flat-square) |

</div>

### 🏗️ Architecture Details
- **Framework**: Django 4.2.24
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Django's built-in user authentication system
- **API Framework**: Django REST Framework

### Frontend
- **Styling**: Custom CSS with modern design patterns
- **Forms**: Django Crispy Forms with Bootstrap 4
- **Responsive**: Mobile-first responsive design
- **Animations**: CSS animations and transitions

### External APIs
- **Weather Data**: OpenWeatherMap API
- **AI Services**: OpenRouter API with Google Gemini 2.5 Flash
- **Maps/Geocoding**: Google Maps API (optional)

### Deployment
- **Platform**: Render.com
- **Web Server**: Gunicorn
- **Static Files**: WhiteNoise for static file serving

## 🚀 Quick Start

### 🌐 Try the Live App
**No installation needed!** Visit **[https://travelmate-jv1d.onrender.com/](https://travelmate-jv1d.onrender.com/)** to start planning your travels immediately.

### 💻 Local Development Setup

<details>
<summary><b>📋 Prerequisites</b></summary>

- Python 3.8+ 
- pip (Python package manager)
- Git
- API keys (see [API Keys section](#-api-keys-required))

</details>

**1️⃣ Clone & Setup**
```bash
git clone https://github.com/yourusername/TravelMate.git
cd TravelMate
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**2️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

**3️⃣ Environment Configuration**
Create a `.env` file in the project root:
```env
SECRET_KEY=your-django-secret-key
OWM_API_KEY=your-openweathermap-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
GOOGLE_API_KEY=your-google-api-key (optional)
GEOCODE_API_KEY=your-geocoding-api-key (optional)
```

**4️⃣ Database Setup**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

**5️⃣ Launch Application**
```bash
python manage.py runserver
```
🎉 **Access your local TravelMate at:** `http://localhost:8000`

---

```
TravelMate/
├── TravelMate/           # Main project settings
│   ├── settings.py       # Django settings
│   ├── urls.py          # Main URL routing
│   └── wsgi.py          # WSGI configuration
├── accounts/            # User authentication app
├── api/                 # API endpoints and services
│   └── services/        # External API integrations
├── chatbot/             # AI chat functionality
├── home/                # Homepage and main views
├── packing/             # Packing list management
├── tips/                # Travel tips functionality
├── trips/               # Trip management
├── weather/             # Weather forecast features
├── static/              # Static files (CSS, JS, images)
│   └── css/
│       └── styles.css   # Main stylesheet
├── templates/           # HTML templates
│   ├── base.html        # Base template
│   └── [app folders]/   # App-specific templates
├── requirements.txt     # Python dependencies
├── build.sh            # Build script for deployment
└── manage.py           # Django management script
```

## 🔑 API Keys Required

<div align="center">

| Service | Status | Purpose | Get Your Key |
|---------|--------|---------|--------------|
| **OpenWeatherMap** | `Required` | Weather forecasts & location data | [Get API Key](https://openweathermap.org/api) |
| **OpenRouter** | `Required` | AI chat assistant & smart recommendations | [Get API Key](https://openrouter.ai/) |
| **Google Maps** | `Optional` | Enhanced location services & geocoding | [Get API Key](https://developers.google.com/maps) |

</div>

> 💡 **Tip:** The app will work with just OpenWeatherMap and OpenRouter keys. Google Maps integration provides enhanced location features but isn't required for core functionality.

## Deployment

### Render.com Deployment

1. **Connect Repository**
   - Link your GitHub repository to Render
   - Set build command: `./build.sh`
   - Set start command: `gunicorn TravelMate.wsgi:application --bind 0.0.0.0:$PORT`

2. **Environment Variables**
   Add all required API keys and settings in Render's environment section

3. **Database**
   - For production, add a PostgreSQL database service
   - The app will automatically use the `DATABASE_URL` environment variable

## Usage

### Getting Started
1. **Create Account**: Register a new user account
2. **Plan Trip**: Create your first trip with destination and dates
3. **Explore Features**: 
   - Check weather forecasts
   - Generate packing lists
   - Get travel tips
   - Chat with AI assistant

### Key Features

**Trip Planning**
- Add destinations with start/end dates
- Organize multiple trips
- View trip dashboard

**Smart Packing**
- AI-generated packing lists based on destination and weather
- Customizable item categories
- Check off items as you pack

**Weather Integration**
- 5-day weather forecasts
- Location-based weather data
- Weather-aware packing suggestions

**AI Assistant**
- Ask questions about destinations
- Get travel recommendations
- Planning assistance

## 🤝 Contributing

We welcome contributions to TravelMate! Here's how you can help:

<div align="center">

[![Contributors Welcome](https://img.shields.io/badge/Contributors-Welcome-brightgreen?style=for-the-badge)](CONTRIBUTING.md)

</div>

### 🛠️ Development Process

1. **🍴 Fork** the repository
2. **🌿 Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **💾 Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **📤 Push** to the branch (`git push origin feature/amazing-feature`)
5. **🔄 Open** a Pull Request

### 🐛 Bug Reports & Feature Requests
- Found a bug? [Open an issue](https://github.com/yourusername/TravelMate/issues)
- Have an idea? [Request a feature](https://github.com/yourusername/TravelMate/issues/new?template=feature_request.md)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

```
MIT License - Feel free to use, modify, and distribute as you wish!
```

---

## 📞 Support & Contact

<div align="center">

| Channel | Purpose | Link |
|---------|---------|------|
| 🐛 **Issues** | Bug reports & feature requests | [GitHub Issues](https://github.com/yourusername/TravelMate/issues) |
| 💬 **Discussions** | General questions & community chat | [GitHub Discussions](https://github.com/yourusername/TravelMate/discussions) |
| 📧 **Email** | Direct contact & partnerships | [donaldheddes@gmail.com](mailto:donaldheddesheimer@gmail.com) |

**Response Time:** We aim to respond within 24-48 hours ⏰

</div>

---

### 🎉 Recent Updates
- ✅ AI-powered packing list generation
- ✅ Weather integration with forecasts
- ✅ Responsive dark theme design
- ✅ Real-time chat assistance

---

<div align="center">

## ⭐ Show Your Support

If TravelMate helps you plan better trips, please consider giving us a star!

[![GitHub stars](https://img.shields.io/github/stars/yourusername/TravelMate?style=social)](https://github.com/yourusername/TravelMate/stargazers)

**Built with ❤️ for travelers who love to plan ahead**

---

*Happy travels! ✈️🌍*

</div>

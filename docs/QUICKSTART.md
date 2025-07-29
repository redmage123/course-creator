# 🚀 Course Creator Platform - Quick Start

Get the Course Creator Platform running in **under 10 minutes**!

## ⚡ Prerequisites (2 minutes)

**Install Docker & Git:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y git docker.io docker-compose
sudo usermod -aG docker $USER && newgrp docker

# macOS
brew install git docker docker-compose

# Windows: Install Docker Desktop and Git for Windows
```

**Get API Keys:**
- [Anthropic Claude API Key](https://console.anthropic.com/) (Required)
- [OpenAI API Key](https://platform.openai.com/) (Optional)

## 🏃‍♂️ Installation (5 minutes)

### 1. Clone & Configure
```bash
git clone https://github.com/your-org/course-creator.git
cd course-creator
cp .env.example .env
```

### 2. Add Your API Keys
Edit `.env` file:
```bash
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  # Optional
```

### 3. Deploy Everything
```bash
./app-control.sh docker-start
```

**Wait 2-3 minutes for all services to start.**

### 4. Create Admin User
```bash
python create-admin.py
```

## 🎯 Access Your Platform

Open these URLs in your browser:

- **🏠 Platform Home**: http://localhost:3000
- **👨‍🏫 Instructor Dashboard**: http://localhost:3000/instructor-dashboard.html  
- **👨‍🎓 Student Dashboard**: http://localhost:3000/student-dashboard.html
- **🔧 Admin Panel**: http://localhost:3000/admin.html
- **💻 Interactive Labs**: http://localhost:3000/lab.html

## 🎓 Create Your First Course (2 minutes)

1. **Go to Instructor Dashboard**: http://localhost:3000/instructor-dashboard.html
2. **Click "Create New Course"**
3. **Upload a PDF/PowerPoint** (drag & drop)
4. **Let AI generate your course** (30 seconds)
5. **Customize and publish!**

## 🧪 Try Interactive Labs

1. **Go to Lab Environment**: http://localhost:3000/lab.html
2. **Select an IDE** (VS Code, Vim, Nano)
3. **Choose a language** (Python, JavaScript, Java, C++)
4. **Start coding!**

## ✅ Verify Everything Works

```bash
# Check all services are healthy
./app-control.sh docker-status

# Test the APIs
curl http://localhost:8000/health  # Should return {"status": "healthy"}
curl http://localhost:3000         # Should return HTML page
```

## 🆘 Quick Troubleshooting

**Services won't start?**
```bash
docker --version  # Check Docker is installed
./app-control.sh docker-logs  # Check error logs
```

**Can't access web interface?**
```bash
curl http://localhost:3000  # Test if frontend responds
./app-control.sh docker-restart  # Restart everything
```

**Lab containers won't work?**
```bash
sudo chmod 666 /var/run/docker.sock  # Fix Docker permissions
```

## 🔧 Optional: CI/CD Pipeline

Want automated testing and deployment?

```bash
# Install Jenkins & SonarQube
./jenkins/jenkins-setup.sh
./sonarqube/setup-sonarqube.sh

# Access tools
# Jenkins: http://localhost:8080 (admin/admin)
# SonarQube: http://localhost:9000 (admin/admin)
```

## 📚 What's Next?

- **📖 Full Documentation**: Check `docs/RUNBOOK.md`
- **🔧 Configuration**: See `docs/ci-cd-pipeline.md`
- **🐛 Issues**: Create issues in the repository
- **💡 Features**: Explore content export, analytics, multi-user support

## 🎉 You're Ready!

Your Course Creator Platform is now running with:
- ✅ AI-powered course generation
- ✅ Interactive multi-IDE lab environments  
- ✅ Student and instructor dashboards
- ✅ Content management and export
- ✅ Analytics and monitoring

**Happy teaching and learning! 🚀**

---

*Need help? Check the full runbook at `docs/RUNBOOK.md` or create an issue in the repository.*
# Course Creator Platform

A comprehensive web-based platform for creating, managing, and delivering interactive programming courses with hands-on lab environments.

## 🚀 Features

### For Instructors
- **Course Management**: Create, edit, and organize courses with rich content
- **Student Management**: Track enrollments, progress, and performance
- **Lab Environment Creation**: Build interactive coding environments
- **Content Generation**: AI-powered course content creation
- **Real-time Analytics**: Monitor student engagement and completion rates

### For Students
- **Interactive Learning**: Access courses with integrated lab environments
- **Progress Tracking**: Monitor learning progress and achievements
- **Hands-on Practice**: Code directly in browser-based terminals
- **Secure Environment**: Sandboxed lab environments for safe experimentation

### For Administrators
- **User Management**: Manage instructor and student accounts
- **Platform Analytics**: System-wide usage and performance metrics
- **Content Moderation**: Review and approve course content

## 🏗️ Architecture

The platform is built using a modern microservices architecture:

```
course-creator/
├── frontend/                   # Client-side application
│   ├── admin.html             # Admin dashboard
│   ├── instructor-dashboard.html  # Instructor interface
│   ├── student-dashboard.html     # Student interface
│   ├── lab.html              # Interactive lab environment
│   ├── css/                  # Stylesheets
│   └── js/                   # JavaScript modules
├── services/                  # Backend microservices
│   ├── user-management/       # Authentication & user data
│   ├── course-management/     # Course CRUD operations
│   ├── course-generator/      # AI content generation
│   └── content-storage/       # File and content storage
├── api/                      # API gateway and routes
├── infrastructure/           # Deployment configurations
├── monitoring/              # Observability stack
└── docs/                   # Documentation
```

## 🛠️ Technology Stack

### Frontend
- **HTML5/CSS3/JavaScript** - Core web technologies
- **Bootstrap 5** - UI framework
- **Font Awesome** - Icon library
- **Marked.js** - Markdown rendering
- **Xterm.js** - Terminal emulation

### Backend
- **Python 3.8+** - Core language
- **FastAPI** - Web framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Primary database
- **Redis** - Caching and sessions
- **JWT** - Authentication tokens

### Infrastructure
- **Docker** - Containerization
- **Kubernetes** - Container orchestration
- **Nginx** - Reverse proxy
- **Prometheus/Grafana** - Monitoring
- **GitHub Actions** - CI/CD

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+
- Docker (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd course-creator
   ```

2. **Set up the database**
   ```bash
   # Install PostgreSQL and start the service
   sudo apt-get install postgresql postgresql-contrib
   sudo systemctl start postgresql
   
   # Create database
   sudo -u postgres createdb course_creator
   
   # Run migrations
   python setup-database.py
   ```

3. **Start backend services**
   ```bash
   # Start all services
   python start-platform.py
   
   # Or start individual services
   cd services/user-management && python run.py
   cd services/course-management && python run.py
   cd services/course-generator && python run.py
   cd services/content-storage && python run.py
   ```

4. **Serve frontend**
   ```bash
   # Using Python's built-in server
   cd frontend
   python -m http.server 8080
   
   # Or using Node.js
   npx http-server frontend -p 8080
   ```

5. **Access the application**
   - Frontend: http://localhost:8080
   - Admin Dashboard: http://localhost:8080/admin.html
   - Instructor Dashboard: http://localhost:8080/instructor-dashboard.html
   - Student Dashboard: http://localhost:8080/student-dashboard.html
   - API Documentation: http://localhost:8001/docs

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📖 Usage Guide

### Creating Your First Course

1. **Access Instructor Dashboard**
   - Navigate to `/instructor-dashboard.html`
   - Log in with instructor credentials

2. **Generate Course Content**
   - Click "Generate New Course"
   - Enter course title and topics
   - Wait for AI-powered content generation

3. **Customize Course**
   - Edit generated modules and lessons
   - Add exercises and quizzes
   - Configure lab environments

4. **Publish Course**
   - Review content and settings
   - Publish for student enrollment

### Managing Students

1. **Enrollment Management**
   - View enrolled students
   - Track progress and performance
   - Send notifications and updates

2. **Lab Environment**
   - Create interactive coding exercises
   - Monitor student activity
   - Provide real-time assistance

### Student Experience

1. **Course Access**
   - Browse available courses
   - Enroll in courses
   - Track learning progress

2. **Lab Environment**
   - Access browser-based coding environment
   - Complete hands-on exercises
   - Submit assignments

## 🔧 Configuration

### Environment Variables

Create `.env` files for each service:

**User Management Service**
```env
DATABASE_URL=postgresql://user:password@localhost/course_creator
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secret-key
```

**Course Management Service**
```env
DATABASE_URL=postgresql://user:password@localhost/course_creator
USER_SERVICE_URL=http://localhost:8001
```

**Course Generator Service**
```env
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key
DATABASE_URL=postgresql://user:password@localhost/course_creator
```

### Frontend Configuration

Update `frontend/js/config.js`:

```javascript
const CONFIG = {
    BASE_URL: 'http://localhost:8001',
    WEBSOCKET_URL: 'ws://localhost:8001',
    ENDPOINTS: {
        USER_SERVICE: 'http://localhost:8001',
        COURSE_SERVICE: 'http://localhost:8002',
        CONTENT_SERVICE: 'http://localhost:8004'
    }
};
```

## 📚 API Documentation

### Authentication
```http
POST /api/auth/login
POST /api/auth/register
GET /api/auth/profile
PUT /api/auth/profile
```

### Course Management
```http
GET /api/courses
POST /api/courses
GET /api/courses/{id}
PUT /api/courses/{id}
DELETE /api/courses/{id}
```

### User Management
```http
GET /api/users
POST /api/users
GET /api/users/{id}
PUT /api/users/{id}
DELETE /api/users/{id}
```

### Content Generation
```http
POST /api/generate/course
POST /api/generate/module
POST /api/generate/exercise
```

For complete API documentation, visit: `http://localhost:8001/docs`

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/e2e/

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Service interaction testing
- **End-to-End Tests**: Full workflow testing
- **Performance Tests**: Load and stress testing

## 🚀 Deployment

### Production Deployment

1. **Kubernetes Deployment**
   ```bash
   kubectl apply -f infrastructure/kubernetes/
   ```

2. **Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Manual Deployment**
   ```bash
   # Set production environment
   export ENVIRONMENT=production
   
   # Start services with production config
   python start-platform.py --env production
   ```

### Environment Setup

- **Development**: Local development with hot reloading
- **Staging**: Production-like environment for testing
- **Production**: Optimized for performance and security

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- Secure session management

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF tokens

### Infrastructure Security
- HTTPS enforcement
- Security headers
- Rate limiting
- DDoS protection

## 📊 Monitoring

### Observability Stack
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Jaeger**: Distributed tracing
- **ELK Stack**: Centralized logging

### Key Metrics
- User engagement
- Course completion rates
- System performance
- Error rates

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make changes and test**
4. **Submit pull request**

### Code Standards
- Follow PEP 8 for Python code
- Use ESLint for JavaScript
- Write comprehensive tests
- Document all public APIs

### Before Submitting PR
- [ ] All tests pass
- [ ] Code is properly formatted
- [ ] Documentation is updated
- [ ] No security vulnerabilities

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Documentation**: Check `/docs` directory
- **API Docs**: Visit `/docs` endpoint on any service
- **Issues**: Create GitHub issue for bugs
- **Discussions**: Use GitHub discussions for questions

### Troubleshooting

**Common Issues:**

1. **Services won't start**
   - Check port availability
   - Verify database connection
   - Review logs for errors

2. **Frontend can't connect to backend**
   - Verify CORS configuration
   - Check service URLs in config
   - Ensure all services are running

3. **Database connection errors**
   - Verify PostgreSQL is running
   - Check database credentials
   - Ensure database exists

**Useful Commands:**
```bash
# Check service status
python start-platform.py --status

# View service logs
tail -f logs/*.log

# Reset database
python setup-database.py --reset

# Run health checks
curl http://localhost:8001/health
```

## 🎯 Roadmap

### Current Release (v1.0)
- ✅ Core course management
- ✅ User authentication
- ✅ Basic lab environments
- ✅ Content generation

### Next Release (v1.1)
- 🔄 Advanced analytics
- 🔄 Mobile responsiveness
- 🔄 Video content support
- 🔄 Enhanced lab environments

### Future Releases
- 📋 Real-time collaboration
- 📋 Advanced AI features
- 📋 Payment integration
- 📋 Mobile application

## 🏆 Acknowledgments

- **FastAPI**: Modern Python web framework
- **Anthropic**: AI-powered content generation
- **Bootstrap**: UI framework
- **PostgreSQL**: Reliable database system
- **Docker**: Containerization platform

---

**Project Status**: Active Development  
**Version**: 1.0.0  
**Last Updated**: 2025-07-12

For more detailed documentation, visit the `/docs` directory or access the live documentation at `/docs` endpoint when services are running.
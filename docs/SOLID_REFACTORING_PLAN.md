# SOLID Refactoring Plan for Course Creator Platform

## Executive Summary

This document outlines a comprehensive refactoring strategy to apply SOLID principles across the entire Course Creator Platform codebase. The goal is to improve code maintainability, testability, and extensibility while minimizing disruption to existing functionality.

**Scope**: ~50+ JS files, ~30+ HTML files, ~40+ CSS files, 9 Python microservices
**Estimated Impact**: 200+ test files will need updates
**Approach**: Incremental refactoring with continuous testing

---

## Current State Assessment

### ✅ Already Good (Python Services)
All 9 microservices follow Clean Architecture:
- **course-management**
- **organization-management**
- **user-management**
- **content-management**
- **course-generator**
- **knowledge-graph-service**
- **metadata-service**
- **nlp-preprocessing**
- **analytics**

These services already implement:
- Domain/Application/Infrastructure separation
- Dependency Inversion (DI containers)
- Single Responsibility (mostly)
- Custom exceptions instead of generic handlers

### ❌ Needs Refactoring

#### **HIGH PRIORITY**

1. **Frontend JavaScript** - Critical violations
2. **Python main.py files** - Mixed concerns
3. **Data Access Objects** - Some business logic leakage

#### **MEDIUM PRIORITY**

4. **HTML Templates** - Inline JavaScript
5. **CSS Architecture** - No modularity

#### **LOW PRIORITY**

6. **Test Files** - Update after code refactoring

---

## Detailed Refactoring Strategy

## 1. Frontend JavaScript Refactoring (HIGH PRIORITY)

### Current Violations

**File: `/home/bbrelin/course-creator/frontend/js/org-admin-main.js` (578 lines)**

#### Problems Identified:
1. **Global Namespace Pollution**
   ```javascript
   // Current - violates encapsulation
   window.OrgAdmin = { ... }
   window.showCreateProjectModal = () => ...
   window.logout = () => ...
   ```

2. **Direct DOM Manipulation + Business Logic**
   ```javascript
   // Current - mixed concerns
   window.submitGenerateCourse = async (event) => {
       event.preventDefault();
       const title = document.getElementById('generateCourseTitle').value;
       const response = await fetch('https://localhost:8004/courses', { ... });
       // 60 lines of mixed DOM + API + business logic
   }
   ```

3. **No Dependency Injection**
   ```javascript
   // Current - tight coupling
   import { metadataClient } from './metadata-client.js';
   import * as Projects from './modules/org-admin-projects.js';
   // Direct imports = cannot mock in tests
   ```

4. **Inline Event Handlers**
   ```javascript
   // Current - HTML/JS coupling
   window.showCreateProjectModal = () => { ... }
   // Called from: <button onclick="showCreateProjectModal()">
   ```

### Proposed Solution: Modern MVC/Service Architecture

#### **Step 1: Create Service Layer (Dependency Inversion)**

**File: `/frontend/js/services/CourseService.js`**
```javascript
/**
 * Course Management Service
 *
 * BUSINESS PURPOSE:
 * Encapsulates all course-related API operations following Single Responsibility.
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only handles course API communication
 * - Open/Closed: Extensible through configuration, not modification
 * - Dependency Inversion: Depends on ApiClient abstraction
 */
export class CourseService {
    constructor(apiClient, authService) {
        this._apiClient = apiClient;  // DI: injected dependency
        this._authService = authService;
    }

    async createCourse(courseData) {
        const token = await this._authService.getToken();
        return this._apiClient.post('/courses', courseData, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
    }

    async updateCourse(courseId, courseData) {
        const token = await this._authService.getToken();
        return this._apiClient.put(`/courses/${courseId}`, courseData, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
    }

    async getCourse(courseId) {
        return this._apiClient.get(`/courses/${courseId}`);
    }
}
```

#### **Step 2: Create Controller Layer (Single Responsibility)**

**File: `/frontend/js/controllers/CourseController.js`**
```javascript
/**
 * Course Controller
 *
 * BUSINESS PURPOSE:
 * Coordinates user interactions with course management features.
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only coordinates between view and service
 * - Dependency Inversion: Depends on abstractions (service interface)
 */
export class CourseController {
    constructor(courseService, notificationService, modalService) {
        this._courseService = courseService;
        this._notificationService = notificationService;
        this._modalService = modalService;
    }

    async handleCreateCourse(formData) {
        try {
            this._modalService.showLoadingState('generateCourseModal');

            const course = await this._courseService.createCourse({
                title: formData.get('title'),
                description: formData.get('description'),
                category: formData.get('category'),
                difficulty_level: formData.get('difficulty')
            });

            this._notificationService.showSuccess('Course created successfully!');
            this._modalService.close('generateCourseModal');

            // Dispatch event for other components to react
            window.dispatchEvent(new CustomEvent('course:created', {
                detail: { course }
            }));

        } catch (error) {
            this._notificationService.showError(`Failed to create course: ${error.message}`);
        } finally {
            this._modalService.hideLoadingState('generateCourseModal');
        }
    }
}
```

#### **Step 3: Create View Bindings (Separation of Concerns)**

**File: `/frontend/js/views/CourseFormView.js`**
```javascript
/**
 * Course Form View
 *
 * BUSINESS PURPOSE:
 * Manages DOM interactions for course forms.
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only handles DOM updates and events
 * - Open/Closed: Can add new form fields without changing core logic
 */
export class CourseFormView {
    constructor(formElement, controller) {
        this._form = formElement;
        this._controller = controller;
        this._bindEvents();
    }

    _bindEvents() {
        // Remove onclick from HTML, use event delegation
        this._form.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(this._form);
            this._controller.handleCreateCourse(formData);
        });
    }

    showValidationError(field, message) {
        const errorElement = this._form.querySelector(`#${field}-error`);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }

    clearValidationErrors() {
        this._form.querySelectorAll('.error-message').forEach(el => {
            el.style.display = 'none';
        });
    }
}
```

#### **Step 4: Create Dependency Injection Container**

**File: `/frontend/js/core/Container.js`**
```javascript
/**
 * Dependency Injection Container
 *
 * BUSINESS PURPOSE:
 * Manages application dependencies and lifecycle.
 *
 * SOLID PRINCIPLES:
 * - Dependency Inversion: Entire app depends on this abstraction
 * - Single Responsibility: Only manages dependency creation
 * - Open/Closed: Can register new services without changing code
 */
export class Container {
    constructor() {
        this._services = new Map();
        this._singletons = new Map();
    }

    register(name, factory, singleton = false) {
        this._services.set(name, { factory, singleton });
        return this;
    }

    get(name) {
        const service = this._services.get(name);
        if (!service) {
            throw new Error(`Service '${name}' not registered`);
        }

        if (service.singleton) {
            if (!this._singletons.has(name)) {
                this._singletons.set(name, service.factory(this));
            }
            return this._singletons.get(name);
        }

        return service.factory(this);
    }
}
```

#### **Step 5: Application Bootstrap (Dependency Setup)**

**File: `/frontend/js/org-admin-app.js`**
```javascript
/**
 * Organization Admin Application Bootstrap
 *
 * BUSINESS PURPOSE:
 * Initializes and wires up all application dependencies.
 *
 * SOLID PRINCIPLES:
 * - Dependency Inversion: All dependencies injected through container
 * - Single Responsibility: Only handles app initialization
 */
import { Container } from './core/Container.js';
import { ApiClient } from './core/ApiClient.js';
import { AuthService } from './services/AuthService.js';
import { CourseService } from './services/CourseService.js';
import { CourseController } from './controllers/CourseController.js';
import { CourseFormView } from './views/CourseFormView.js';
import { NotificationService } from './services/NotificationService.js';
import { ModalService } from './services/ModalService.js';

const container = new Container();

// Register core services (singletons)
container.register('apiClient', () => new ApiClient({
    baseURL: 'https://localhost:8004',
    timeout: 30000
}), true);

container.register('authService', (c) => new AuthService(
    c.get('apiClient')
), true);

container.register('notificationService', () => new NotificationService(), true);
container.register('modalService', () => new ModalService(), true);

// Register domain services
container.register('courseService', (c) => new CourseService(
    c.get('apiClient'),
    c.get('authService')
), true);

// Register controllers
container.register('courseController', (c) => new CourseController(
    c.get('courseService'),
    c.get('notificationService'),
    c.get('modalService')
));

// Initialize views
document.addEventListener('DOMContentLoaded', () => {
    const courseForm = document.getElementById('generateCourseForm');
    if (courseForm) {
        new CourseFormView(courseForm, container.get('courseController'));
    }
});

// Export container for testing
export { container };
```

### Refactoring Checklist for JavaScript

- [ ] **Extract Services** (20 files)
  - [ ] `CourseService.js`
  - [ ] `ProjectService.js`
  - [ ] `TrackService.js`
  - [ ] `InstructorService.js`
  - [ ] `StudentService.js`
  - [ ] `SettingsService.js`
  - [ ] `AnalyticsService.js`
  - [ ] `FileService.js`
  - [ ] `AIAssistantService.js`
  - [ ] `TargetRoleService.js`
  - [ ] `NotificationService.js`
  - [ ] `ModalService.js`
  - [ ] `ValidationService.js`
  - [ ] `AuthService.js`
  - [ ] `ApiClient.js` (base HTTP client)

- [ ] **Extract Controllers** (10 files)
  - [ ] `CourseController.js`
  - [ ] `ProjectController.js`
  - [ ] `TrackController.js`
  - [ ] `InstructorController.js`
  - [ ] `StudentController.js`
  - [ ] `SettingsController.js`
  - [ ] `AnalyticsController.js`

- [ ] **Extract Views** (10 files)
  - [ ] `CourseFormView.js`
  - [ ] `ProjectListView.js`
  - [ ] `TrackListView.js`
  - [ ] `TabNavigationView.js`
  - [ ] `StatsCardView.js`

- [ ] **Create Infrastructure** (5 files)
  - [ ] `Container.js` (DI container)
  - [ ] `EventBus.js` (pub/sub for decoupling)
  - [ ] `Router.js` (client-side routing)
  - [ ] `Validator.js` (form validation)
  - [ ] `Formatter.js` (date/currency/etc.)

- [ ] **Update Main Entry Point**
  - [ ] Refactor `org-admin-main.js` to bootstrap
  - [ ] Remove global namespace pollution
  - [ ] Remove inline event handlers

---

## 2. Python main.py Refactoring (HIGH PRIORITY)

### Current Violations

**File: `/services/course-management/main.py` (1750 lines)**

#### Problems Identified:

1. **Mixed Concerns**
   ```python
   # Current - everything in one file
   def create_app(config: DictConfig) -> FastAPI:
       # CORS middleware setup
       # Authentication middleware
       # Exception handlers
       # 50+ endpoint definitions
       # Helper functions
       # Configuration
       # Lifecycle management
   ```

2. **God Object Pattern**
   ```python
   # Current - main.py knows about everything
   from course_management.domain.entities.course import Course
   from course_management.domain.entities.enrollment import Enrollment
   from course_management.domain.entities.feedback import CourseFeedback
   from course_management.application.services.spreadsheet_parser import SpreadsheetParser
   # ... 30+ more imports
   ```

3. **Global State**
   ```python
   # Current - module-level globals
   container: Optional[Container] = None
   current_config: Optional[DictConfig] = None
   course_instances_store = {}  # In-memory state!
   ```

### Proposed Solution: Modular Application Factory

#### **Step 1: Extract Middleware Configuration**

**File: `/services/course-management/middleware/__init__.py`**
```python
"""
Middleware Configuration Module

BUSINESS PURPOSE:
Centralizes all middleware configuration following Single Responsibility.

SOLID PRINCIPLES:
- Single Responsibility: Only configures middleware
- Open/Closed: Add new middleware without modifying existing code
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from omegaconf import DictConfig
from typing import List

def configure_cors(app: FastAPI, allowed_origins: List[str] = None) -> None:
    """
    Configure CORS middleware for cross-origin requests.

    BUSINESS CONTEXT:
    Enables frontend applications to communicate with backend services
    across different domains while maintaining security controls.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def configure_authentication(app: FastAPI, config: DictConfig) -> None:
    """
    Configure authentication middleware for request validation.

    BUSINESS CONTEXT:
    Ensures all requests are authenticated and authorized before
    reaching endpoint handlers.
    """
    from auth.organization_middleware import OrganizationAuthorizationMiddleware
    app.add_middleware(OrganizationAuthorizationMiddleware, config=config)

def configure_all_middleware(app: FastAPI, config: DictConfig) -> None:
    """
    Configure all middleware layers in correct order.

    BUSINESS CONTEXT:
    Middleware order matters - authentication before CORS ensures
    security checks happen before cross-origin handling.
    """
    configure_authentication(app, config)
    configure_cors(app, config.get('cors', {}).get('allowed_origins'))
```

#### **Step 2: Extract Exception Handlers**

**File: `/services/course-management/error_handlers/__init__.py`**
```python
"""
Exception Handler Configuration

BUSINESS PURPOSE:
Centralizes exception handling following Single Responsibility.

SOLID PRINCIPLES:
- Single Responsibility: Only handles error responses
- Open/Closed: Add new exception types without modifying core logic
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from exceptions import (
    CourseManagementException,
    ValidationException,
    CourseNotFoundException,
    # ... other exceptions
)
from typing import Dict, Type

# Exception type to HTTP status code mapping (Open/Closed Principle)
EXCEPTION_STATUS_MAPPING: Dict[Type[CourseManagementException], int] = {
    ValidationException: 400,
    CourseNotFoundException: 404,
    # ... other mappings
}

def configure_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with FastAPI app.

    BUSINESS CONTEXT:
    Consistent error handling across all endpoints ensures
    clients receive structured error responses.
    """

    @app.exception_handler(CourseManagementException)
    async def course_management_exception_handler(
        request: Request,
        exc: CourseManagementException
    ):
        """Handle custom course management exceptions."""
        status_code = next(
            (code for exc_type, code in EXCEPTION_STATUS_MAPPING.items()
             if isinstance(exc, exc_type)),
            500  # Default status code
        )

        response_data = exc.to_dict()
        response_data["path"] = str(request.url)

        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
```

#### **Step 3: Extract API Routers**

**File: `/services/course-management/api/course_endpoints.py`**
```python
"""
Course Management API Endpoints

BUSINESS PURPOSE:
Handles all course-related HTTP endpoints.

SOLID PRINCIPLES:
- Single Responsibility: Only course endpoints
- Dependency Inversion: Depends on service interfaces
- Interface Segregation: Separate routers for different domains
"""
from fastapi import APIRouter, Depends, HTTPException
from course_management.domain.interfaces.course_service import ICourseService
from course_management.api.dependencies import get_course_service
from course_management.api.schemas import CourseCreateRequest, CourseResponse
from typing import List

router = APIRouter(prefix="/courses", tags=["courses"])

@router.post("", response_model=CourseResponse)
async def create_course(
    request: CourseCreateRequest,
    course_service: ICourseService = Depends(get_course_service)
):
    """
    Create a new course in the educational platform.

    BUSINESS WORKFLOW:
    1. Validate instructor permissions
    2. Create course entity in draft state
    3. Initialize course metadata
    4. Set up analytics tracking
    """
    # Implementation...

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    course_service: ICourseService = Depends(get_course_service)
):
    """Get course by ID"""
    # Implementation...

@router.get("", response_model=List[CourseResponse])
async def list_courses(
    instructor_id: str = None,
    published_only: bool = True,
    course_service: ICourseService = Depends(get_course_service)
):
    """List courses with optional filters"""
    # Implementation...
```

#### **Step 4: Create Dependency Injection Module**

**File: `/services/course-management/api/dependencies.py`**
```python
"""
FastAPI Dependency Injection

BUSINESS PURPOSE:
Provides dependency injection for endpoint handlers.

SOLID PRINCIPLES:
- Dependency Inversion: Endpoints depend on interfaces
- Single Responsibility: Only provides dependencies
"""
from fastapi import Depends, HTTPException
from course_management.infrastructure.container import Container
from course_management.domain.interfaces.course_service import ICourseService
from typing import Optional

# Module-level container (initialized at startup)
_container: Optional[Container] = None

def set_container(container: Container) -> None:
    """Set the global container instance."""
    global _container
    _container = container

def get_course_service() -> ICourseService:
    """Dependency injection for course service."""
    if not _container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return _container.get_course_service()
```

#### **Step 5: Refactored Application Factory**

**File: `/services/course-management/main.py` (NEW - 200 lines vs 1750)**
```python
"""
Course Management Service - Main Entry Point

BUSINESS PURPOSE:
Initializes and runs the course management microservice.

SOLID PRINCIPLES:
- Single Responsibility: Only bootstraps the application
- Open/Closed: Add features by importing new routers
- Dependency Inversion: All dependencies injected via container
"""
from fastapi import FastAPI
from omegaconf import DictConfig
import uvicorn
import hydra

from course_management.infrastructure.container import Container
from course_management.middleware import configure_all_middleware
from course_management.error_handlers import configure_exception_handlers
from course_management.api import dependencies
from course_management.api.routers import (
    course_router,
    enrollment_router,
    feedback_router,
    bulk_enrollment_router,
    project_router,
    instance_router
)

def create_app(config: DictConfig) -> FastAPI:
    """
    Application factory for Course Management Service.

    BUSINESS CONTEXT:
    Creates a fully configured FastAPI application with all
    necessary routes, middleware, and error handlers.

    SOLID PRINCIPLES:
    - Open/Closed: Add features by registering new routers
    - Dependency Inversion: Services injected via container
    """
    app = FastAPI(
        title="Course Management Service",
        description="Microservice for managing courses, enrollments, and feedback",
        version="3.4.0"
    )

    # Configure middleware (authentication, CORS, etc.)
    configure_all_middleware(app, config)

    # Configure exception handlers
    configure_exception_handlers(app)

    # Register API routers (Open/Closed: add new routers here)
    app.include_router(course_router)
    app.include_router(enrollment_router)
    app.include_router(feedback_router)
    app.include_router(bulk_enrollment_router)
    app.include_router(project_router)
    app.include_router(instance_router)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "course-management"}

    # Lifecycle events
    @app.on_event("startup")
    async def startup():
        container = Container(config)
        await container.initialize()
        dependencies.set_container(container)

    @app.on_event("shutdown")
    async def shutdown():
        # Cleanup handled by container
        pass

    return app

@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """Main entry point using Hydra configuration."""
    app = create_app(cfg)

    uvicorn.run(
        app,
        host=cfg.server.host,
        port=cfg.server.port,
        ssl_keyfile="/app/ssl/nginx-selfsigned.key",
        ssl_certfile="/app/ssl/nginx-selfsigned.crt"
    )

if __name__ == "__main__":
    main()
```

### Refactoring Checklist for Python Services

**For each of 9 microservices:**

- [ ] **Extract API Routers** (5-8 routers per service)
  - [ ] Group endpoints by domain (courses, enrollments, feedback, etc.)
  - [ ] Move to `/api/routers/` directory
  - [ ] Use APIRouter with prefixes and tags

- [ ] **Extract Middleware Configuration**
  - [ ] Create `/middleware/__init__.py`
  - [ ] Separate CORS, auth, logging, error handling

- [ ] **Extract Exception Handlers**
  - [ ] Create `/error_handlers/__init__.py`
  - [ ] Centralize exception-to-status-code mapping

- [ ] **Extract Dependencies**
  - [ ] Create `/api/dependencies.py`
  - [ ] Move all `Depends()` functions here

- [ ] **Extract Lifecycle Management**
  - [ ] Create `/lifecycle.py`
  - [ ] Move startup/shutdown logic

- [ ] **Simplify main.py**
  - [ ] Reduce to ~200 lines
  - [ ] Only bootstrap, no business logic
  - [ ] Import and register routers

---

## 3. HTML Templates Refactoring (MEDIUM PRIORITY)

### Current Violations

**File: `/frontend/html/org-admin-dashboard.html`**

#### Problems:
1. Inline CSS (`<style>` tags)
2. Inline JavaScript (onclick handlers)
3. Mixed concerns (structure + style + behavior)

### Proposed Solution

#### **Step 1: Remove Inline CSS**

**Before:**
```html
<head>
    <style>
        .org-admin-container { display: flex; }
        .sidebar { width: 280px; }
        /* 100+ lines of CSS */
    </style>
</head>
```

**After:**
```html
<head>
    <link rel="stylesheet" href="../css/components/org-admin-layout.css">
    <link rel="stylesheet" href="../css/components/org-admin-sidebar.css">
    <link rel="stylesheet" href="../css/components/org-admin-tabs.css">
</head>
```

#### **Step 2: Remove Inline Event Handlers**

**Before:**
```html
<button onclick="showCreateProjectModal()">Create Project</button>
<button onclick="window.OrgAdmin.Projects.showCreate()">Add</button>
```

**After:**
```html
<button data-action="create-project" class="btn btn-primary">Create Project</button>
<button data-controller="projects" data-action="create" class="btn btn-primary">Add</button>
```

**JavaScript Event Delegation:**
```javascript
// In org-admin-app.js
document.addEventListener('click', (e) => {
    const button = e.target.closest('[data-action]');
    if (!button) return;

    const action = button.dataset.action;
    const controller = button.dataset.controller;

    // Route to appropriate controller
    if (controller && action) {
        const ctrl = container.get(`${controller}Controller`);
        ctrl[action]();
    }
});
```

#### **Step 3: Extract Reusable Components**

**Before: Inline modal in HTML**
```html
<div id="createProjectModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">...</div>
        <div class="modal-body">...</div>
        <div class="modal-footer">...</div>
    </div>
</div>
<!-- Repeat 10+ times for different modals -->
```

**After: Template-based components**
```html
<!-- Define modal template once -->
<template id="modal-template">
    <div class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title"></h3>
                <button class="modal-close" data-action="close-modal">&times;</button>
            </div>
            <div class="modal-body"></div>
            <div class="modal-footer"></div>
        </div>
    </div>
</template>

<!-- Use JavaScript to create modals dynamically -->
```

### Refactoring Checklist for HTML

- [ ] **Remove All Inline CSS** (30 files)
  - [ ] Extract to component-specific CSS files
  - [ ] Link external stylesheets

- [ ] **Remove All Inline onclick** (30 files)
  - [ ] Use data-action attributes
  - [ ] Implement event delegation in JS

- [ ] **Create Template System**
  - [ ] Modal template
  - [ ] Card template
  - [ ] Table template
  - [ ] Form template

- [ ] **Separate Concerns**
  - [ ] HTML = structure only
  - [ ] CSS = styling only
  - [ ] JS = behavior only

---

## 4. CSS Architecture Refactoring (MEDIUM PRIORITY)

### Current Violations

**File: `/frontend/css/components/rbac-dashboard.css` (1384 lines)**

#### Problems:
1. No scoping - global namespace pollution
2. Mixed concerns (layout + components + responsive)
3. Specificity wars (.nav-tab vs .nav-tab.active)
4. No clear component boundaries

### Proposed Solution: BEM + CSS Modules

#### **Step 1: Adopt BEM Naming Convention**

**Before: Generic class names**
```css
.card { ... }
.header { ... }
.button { ... }
```

**After: BEM (Block Element Modifier)**
```css
/* Block: org-admin-dashboard */
.org-admin-dashboard { ... }

/* Element: org-admin-dashboard__header */
.org-admin-dashboard__header { ... }

/* Modifier: org-admin-dashboard__header--sticky */
.org-admin-dashboard__header--sticky { ... }

/* Block: project-card */
.project-card { ... }
.project-card__title { ... }
.project-card__actions { ... }
.project-card--featured { ... }
```

#### **Step 2: Split Into Component Files**

**Current: One giant file**
```
/frontend/css/components/rbac-dashboard.css (1384 lines)
```

**After: Modular component files**
```
/frontend/css/components/
├── org-admin-dashboard.css         (100 lines - layout)
├── org-admin-header.css            (50 lines)
├── org-admin-sidebar.css           (80 lines)
├── org-admin-tabs.css              (60 lines)
├── stat-card.css                   (40 lines)
├── project-card.css                (60 lines)
├── track-card.css                  (60 lines)
├── member-card.css                 (60 lines)
├── modal.css                       (100 lines)
├── button.css                      (80 lines)
├── form.css                        (120 lines)
├── table.css                       (80 lines)
├── notification.css                (60 lines)
└── utilities.css                   (80 lines)
```

**Import in main CSS:**
```css
/* /frontend/css/main.css */
@import './components/org-admin-dashboard.css';
@import './components/org-admin-header.css';
@import './components/project-card.css';
/* ... */
```

#### **Step 3: Create CSS Custom Properties (CSS Variables)**

**File: `/frontend/css/variables.css`**
```css
/**
 * CSS Design Tokens
 *
 * BUSINESS PURPOSE:
 * Centralizes all design decisions for consistent theming.
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only defines design tokens
 * - Open/Closed: Add new tokens without changing components
 */
:root {
    /* Colors */
    --color-primary: #667eea;
    --color-secondary: #764ba2;
    --color-success: #48bb78;
    --color-danger: #e53e3e;
    --color-warning: #ed8936;
    --color-info: #4299e1;

    --color-text-primary: #2d3748;
    --color-text-secondary: #718096;
    --color-text-muted: #a0aec0;

    --color-bg-primary: #ffffff;
    --color-bg-secondary: #f7fafc;
    --color-border: #e2e8f0;

    /* Spacing */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;

    /* Typography */
    --font-family-base: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    --font-size-xs: 0.75rem;
    --font-size-sm: 0.875rem;
    --font-size-base: 1rem;
    --font-size-lg: 1.125rem;
    --font-size-xl: 1.25rem;
    --font-size-2xl: 1.5rem;

    /* Border Radius */
    --radius-sm: 0.25rem;
    --radius-md: 0.5rem;
    --radius-lg: 1rem;

    /* Shadows */
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);
}
```

**Use in components:**
```css
.project-card {
    background: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    box-shadow: var(--shadow-sm);
}

.project-card__title {
    color: var(--color-text-primary);
    font-size: var(--font-size-xl);
    margin-bottom: var(--spacing-md);
}
```

#### **Step 4: Extract Utilities**

**File: `/frontend/css/utilities.css`**
```css
/**
 * Utility Classes
 *
 * BUSINESS PURPOSE:
 * Provides reusable utility classes following functional CSS principles.
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Each class does one thing
 * - Open/Closed: Add new utilities without modifying existing
 */

/* Display */
.u-flex { display: flex; }
.u-inline-flex { display: inline-flex; }
.u-grid { display: grid; }
.u-block { display: block; }
.u-inline { display: inline; }
.u-hidden { display: none; }

/* Flexbox */
.u-flex-col { flex-direction: column; }
.u-flex-wrap { flex-wrap: wrap; }
.u-items-center { align-items: center; }
.u-justify-center { justify-content: center; }
.u-justify-between { justify-content: space-between; }

/* Spacing */
.u-m-0 { margin: 0; }
.u-m-sm { margin: var(--spacing-sm); }
.u-m-md { margin: var(--spacing-md); }
.u-p-0 { padding: 0; }
.u-p-sm { padding: var(--spacing-sm); }
.u-p-md { padding: var(--spacing-md); }

/* Typography */
.u-text-primary { color: var(--color-text-primary); }
.u-text-secondary { color: var(--color-text-secondary); }
.u-text-center { text-align: center; }
.u-font-bold { font-weight: 700; }
```

### Refactoring Checklist for CSS

- [ ] **Split Giant Files** (40 files)
  - [ ] Identify component boundaries
  - [ ] Extract to separate files
  - [ ] Use @import in main CSS

- [ ] **Adopt BEM Naming**
  - [ ] Rename all classes to BEM format
  - [ ] Update HTML references
  - [ ] Document naming convention

- [ ] **Create Design Tokens**
  - [ ] Extract all magic numbers to variables
  - [ ] Define color palette
  - [ ] Define spacing scale
  - [ ] Define typography scale

- [ ] **Extract Utilities**
  - [ ] Create utilities.css
  - [ ] Replace one-off styles with utilities
  - [ ] Document utility classes

- [ ] **Reduce Specificity**
  - [ ] Remove unnecessary nesting
  - [ ] Use single class selectors
  - [ ] Avoid !important

---

## 5. Data Access Objects (HIGH PRIORITY - Minor Fixes)

### Current State: Mostly Good

**File: `/services/user-management/data_access/user_dao.py` (1137 lines)**

The DAO is actually well-structured! Only minor improvements needed.

### Minor Improvements

#### **Issue 1: Method Length**

Some methods are 50+ lines. Extract query builders.

**Before:**
```python
async def create_user(self, user_data: Dict[str, Any]) -> str:
    try:
        async with self.db_pool.acquire() as conn:
            if 'user_id' in user_data and user_data['user_id']:
                # 30 lines of custom ID logic
            else:
                # 30 lines of auto-generated ID logic
            # More processing...
```

**After:**
```python
async def create_user(self, user_data: Dict[str, Any]) -> str:
    try:
        async with self.db_pool.acquire() as conn:
            if 'user_id' in user_data and user_data['user_id']:
                return await self._create_user_with_custom_id(conn, user_data)
            else:
                return await self._create_user_with_auto_id(conn, user_data)
```

#### **Issue 2: Query Builder Pattern**

Extract SQL queries to separate query builder class.

**File: `/services/user-management/data_access/queries/user_queries.py`**
```python
"""
SQL Query Builder for User Operations

BUSINESS PURPOSE:
Centralizes all SQL queries for maintainability.

SOLID PRINCIPLES:
- Single Responsibility: Only builds SQL queries
- Open/Closed: Add new queries without modifying DAO
"""
class UserQueries:
    @staticmethod
    def insert_user() -> str:
        return """
            INSERT INTO course_creator.users (
                email, username, full_name, hashed_password, role,
                organization, status, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, email, username, full_name, role, organization,
                      status, created_at, updated_at
        """

    @staticmethod
    def insert_user_with_id() -> str:
        return """
            INSERT INTO course_creator.users (
                id, email, username, full_name, hashed_password, role,
                organization, status, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, email, username, full_name, role, organization,
                      status, created_at, updated_at
        """

    @staticmethod
    def select_user_by_email() -> str:
        return """
            SELECT id, email, username, full_name, hashed_password, role,
                   organization, status, created_at, updated_at, last_login
            FROM course_creator.users
            WHERE email = $1
        """
```

### Refactoring Checklist for DAOs

For each service:

- [ ] **Extract Query Builders**
  - [ ] Create `/data_access/queries/` directory
  - [ ] Move SQL strings to query builder classes
  - [ ] One class per entity

- [ ] **Extract Long Methods**
  - [ ] Methods > 50 lines = split
  - [ ] Private helper methods for sub-operations

- [ ] **Remove Business Logic**
  - [ ] Move validation to domain layer
  - [ ] Move calculations to domain layer
  - [ ] DAO only does CRUD

---

## 6. Test Updates (LOW PRIORITY - After Refactoring)

### Impact Analysis

**Estimated Test Files Requiring Updates: 200+**

- **Frontend JavaScript Tests**: 50+ files
  - Need to use DI container in tests
  - Mock services instead of global functions

- **Python Unit Tests**: 100+ files
  - Update imports (router paths)
  - Mock new service layer

- **E2E Tests**: 50+ files
  - Update selectors (data-action attributes)
  - Update event handling

### Test Refactoring Strategy

#### **Step 1: Update JavaScript Tests**

**Before: Testing global functions**
```javascript
describe('OrgAdmin', () => {
    it('should create project', async () => {
        global.window.OrgAdmin = {
            Projects: {
                submit: jest.fn()
            }
        };
        // Test...
    });
});
```

**After: Testing with DI**
```javascript
describe('ProjectController', () => {
    let controller;
    let mockProjectService;
    let mockNotificationService;

    beforeEach(() => {
        mockProjectService = {
            createProject: jest.fn()
        };
        mockNotificationService = {
            showSuccess: jest.fn()
        };
        controller = new ProjectController(
            mockProjectService,
            mockNotificationService
        );
    });

    it('should create project', async () => {
        const projectData = { name: 'Test' };
        mockProjectService.createProject.mockResolvedValue({ id: '123' });

        await controller.handleCreateProject(projectData);

        expect(mockProjectService.createProject).toHaveBeenCalledWith(projectData);
        expect(mockNotificationService.showSuccess).toHaveBeenCalled();
    });
});
```

#### **Step 2: Update Python Tests**

**Before: Importing from main.py**
```python
from services.course_management.main import create_course

def test_create_course():
    # Test...
```

**After: Importing from routers**
```python
from services.course_management.api.routers.course_router import create_course

def test_create_course():
    # Test...
```

### Test Update Checklist

- [ ] **JavaScript Unit Tests** (50 files)
  - [ ] Update to use DI container
  - [ ] Mock service dependencies
  - [ ] Remove global window mocks

- [ ] **Python Unit Tests** (100 files)
  - [ ] Update import paths
  - [ ] Update mocks for new structure

- [ ] **E2E Tests** (50 files)
  - [ ] Update selectors (data-action)
  - [ ] Update event expectations

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Goal: Set up infrastructure without breaking existing code**

- [ ] Create JavaScript DI container
- [ ] Create service layer interfaces
- [ ] Extract query builders from DAOs
- [ ] Extract CSS variables
- [ ] Document new patterns

**Risk: None** (new code coexists with old)

### Phase 2: Backend Refactoring (Week 3-4)
**Goal: Refactor Python services**

- [ ] Extract API routers (1 service)
- [ ] Extract middleware configuration (1 service)
- [ ] Extract exception handlers (1 service)
- [ ] Test thoroughly
- [ ] Repeat for remaining 8 services

**Risk: Medium** (changes service structure)

### Phase 3: Frontend Services (Week 5-6)
**Goal: Create service layer**

- [ ] Extract CourseService
- [ ] Extract ProjectService
- [ ] Extract all other services
- [ ] Update tests

**Risk: Medium** (changes how services are called)

### Phase 4: Frontend Controllers (Week 7-8)
**Goal: Create controller layer**

- [ ] Extract controllers
- [ ] Update views to use controllers
- [ ] Remove global functions
- [ ] Update tests

**Risk: High** (changes event handling)

### Phase 5: Frontend Views (Week 9-10)
**Goal: Separate DOM manipulation**

- [ ] Extract view classes
- [ ] Remove inline onclick handlers
- [ ] Implement event delegation
- [ ] Update tests

**Risk: High** (changes HTML/JS interaction)

### Phase 6: CSS Refactoring (Week 11-12)
**Goal: Modular CSS**

- [ ] Split CSS into components
- [ ] Adopt BEM naming
- [ ] Extract utilities
- [ ] Update HTML classes

**Risk: Medium** (visual regressions)

### Phase 7: HTML Cleanup (Week 13-14)
**Goal: Pure semantic HTML**

- [ ] Remove inline CSS
- [ ] Remove inline JavaScript
- [ ] Create template system
- [ ] Final testing

**Risk: Low** (mostly organizational)

---

## Testing Strategy

### Continuous Testing
**Run after EVERY refactoring step**

```bash
# Backend tests
pytest tests/unit/ tests/integration/

# Frontend tests
npm run test:unit
npm run test:integration

# E2E tests
pytest tests/e2e/

# Visual regression tests
npm run test:visual
```

### Acceptance Criteria

**Before considering a component "refactored":**

- [ ] All existing tests pass
- [ ] Code coverage maintained or improved
- [ ] No visual regressions
- [ ] Performance maintained or improved
- [ ] Documentation updated
- [ ] Code review approved

---

## Rollback Strategy

### If Refactoring Fails

**We can rollback because:**

1. **Git Branches**: Each phase in separate branch
2. **Feature Flags**: New code behind flags
3. **Parallel Implementation**: Old and new code coexist
4. **Incremental Deployment**: One service at a time

**Rollback Steps:**

```bash
# If frontend refactoring fails
git checkout main
git revert <commit-hash>

# If backend refactoring fails
git checkout main
git revert <commit-hash>
docker-compose up -d --build
```

---

## Success Metrics

### Code Quality Metrics

- **Cyclomatic Complexity**: Reduce by 30%
- **Lines per File**: Average < 300 lines
- **Test Coverage**: Maintain > 80%
- **Code Duplication**: Reduce by 50%

### SOLID Compliance Metrics

- **Single Responsibility**: 90% of classes have one reason to change
- **Dependency Inversion**: 95% of classes depend on interfaces
- **Open/Closed**: 80% of features added without modifying existing code

### Performance Metrics

- **Load Time**: Maintain < 2 seconds
- **Test Execution**: Maintain < 5 minutes
- **Build Time**: Maintain < 3 minutes

---

## Conclusion

This refactoring will transform the Course Creator Platform from a monolithic codebase to a modular, maintainable, and testable architecture following SOLID principles. The incremental approach minimizes risk while delivering continuous improvements.

**Total Estimated Effort**: 14 weeks (1 developer)
**Risk Level**: Medium (mitigated by incremental approach)
**Expected ROI**: 50% reduction in bug fix time, 30% faster feature development

**Next Steps**:
1. Review and approve this plan
2. Create GitHub issues for each phase
3. Start with Phase 1 (Foundation)
4. Weekly progress reviews

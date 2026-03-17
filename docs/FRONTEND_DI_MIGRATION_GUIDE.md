# Frontend Dependency Injection Migration Guide

## Overview

This guide documents the migration from global `window` namespace pollution to a clean dependency injection (DI) architecture using the Container pattern.

**Current State:**
- **702 window.* usages** across **65 files**
- **32 files** declaring window globals
- Tight coupling, hard to test, namespace collisions

**Target State:**
- Zero global namespace pollution
- All dependencies injected through Container
- Easy to test with mock services
- Clear dependency declarations
- SOLID principles applied

## Architecture

### Files Created

1. **`/frontend/js/core/Container.js`** - DI Container implementation
   - Singleton and transient service support
   - Circular dependency detection
   - Service lifecycle management
   - Hierarchical containers for scoped dependencies

2. **`/frontend/js/core/bootstrap.js`** - Application initialization
   - Service registration
   - Infrastructure setup
   - Application startup

### Container Usage

```javascript
// OLD - Global namespace pollution
window.MyService = class MyService {
    doSomething() { ... }
};

// NEW - Service registration in bootstrap.js
container.register('myService', () => new MyService(), true); // singleton

// NEW - Service consumption
import { container } from './core/bootstrap.js';
const myService = container.get('myService');
myService.doSomething();
```

## Migration Strategy

### Phase 1: Infrastructure (COMPLETED ✓)

**Files Created:**
- ✓ `/frontend/js/core/Container.js` (360 lines, comprehensive)
- ✓ `/frontend/js/core/bootstrap.js` (500+ lines, service registration)

**Services Registered:**
- ✓ `config` - Application configuration
- ✓ `httpClient` - HTTP communication
- ✓ `authService` - Authentication
- ✓ `sessionManager` - Session management
- ✓ `notificationService` - User notifications
- ✓ `projectService` - Project management
- ✓ `courseService` - Course management
- ✓ `trackService` - Track management
- ✓ `dashboardController` - Dashboard initialization

### Phase 2: High-Priority Files (TODO)

**Priority 1 - Most Polluted (47-29 occurrences):**
1. `modules/app.js` - 47 window.* uses
2. `modules/onboarding-system.js` - 29 uses

**Priority 2 - Moderate Pollution (24-19 occurrences):**
3. `modules/navigation.js` - 26 uses
4. `modules/instructor-tab-handlers.js` - 24 uses
5. `modules/instructor-dashboard.js` - 19 uses

**Priority 3 - Lower Pollution (16-12 occurrences):**
6. `modules/org-admin-core.js` - 16 uses
7. `components/dashboard-navigation.js` - 16 uses
8. `modules/student-file-manager.js` - 15 uses
9. `components/course-manager.js` - 14 uses
10. `modules/org-admin-projects.js` - 12 uses

### Phase 3: Remaining Files (TODO)

- 55 additional files with 8 or fewer window.* uses each
- Less urgent but should be migrated for consistency

## Migration Pattern

### Step 1: Identify Window Globals

```javascript
// BEFORE - in my-feature.js
window.MyFeature = {
    init: function() { ... },
    doSomething: function() { ... }
};
```

### Step 2: Convert to ES6 Module

```javascript
// AFTER - in my-feature.js
/**
 * My Feature Module
 *
 * BUSINESS CONTEXT: What this feature does
 *
 * DEPENDENCIES:
 * - authService: For user authentication
 * - httpClient: For API calls
 */
export class MyFeature {
    constructor(authService, httpClient) {
        this.authService = authService;
        this.httpClient = httpClient;
    }

    init() {
        // Implementation
    }

    doSomething() {
        // Implementation
    }
}
```

### Step 3: Register in Bootstrap

```javascript
// In bootstrap.js - registerApplicationServices()
container.register('myFeature', (c) => {
    const authService = c.get('authService');
    const httpClient = c.get('httpClient');
    return new MyFeature(authService, httpClient);
}, true); // true = singleton, false = transient
```

### Step 4: Update Consumers

```javascript
// BEFORE - in consumer.js
window.MyFeature.doSomething();

// AFTER - in consumer.js
import { container } from './core/bootstrap.js';
const myFeature = container.get('myFeature');
myFeature.doSomething();
```

### Step 5: Update HTML Script Tags

```html
<!-- BEFORE -->
<script src="/js/my-feature.js"></script>
<script>
    window.MyFeature.init();
</script>

<!-- AFTER -->
<script type="module">
    import { initializeApp } from '/js/core/bootstrap.js';
    const container = initializeApp();
    const myFeature = container.get('myFeature');
    myFeature.init();
</script>
```

## Common Patterns

### Pattern 1: Service with Dependencies

```javascript
// Service depends on other services
container.register('userService', (c) => {
    const httpClient = c.get('httpClient');
    const authService = c.get('authService');
    const notificationService = c.get('notificationService');

    return {
        getProfile: async (userId) => {
            try {
                const token = authService.getToken();
                return await httpClient.get(`/api/users/${userId}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
            } catch (error) {
                notificationService.error('Failed to load profile');
                throw error;
            }
        }
    };
}, true);
```

### Pattern 2: UI Controller (Transient)

```javascript
// UI controllers should be transient (new instance each time)
container.register('modalController', (c) => {
    const notificationService = c.get('notificationService');

    return {
        open: (modalId) => {
            const modal = document.getElementById(modalId);
            modal.style.display = 'block';
        },
        close: (modalId) => {
            const modal = document.getElementById(modalId);
            modal.style.display = 'none';
        },
        confirm: async (message) => {
            return new Promise((resolve) => {
                // Show confirmation modal
                // Resolve with true/false based on user choice
            });
        }
    };
}, false); // false = transient (new instance each time)
```

### Pattern 3: Factory Pattern

```javascript
// When you need to create multiple instances programmatically
container.register('formValidatorFactory', (c) => {
    const notificationService = c.get('notificationService');

    // Return a factory function
    return (formElement) => {
        return {
            validate: () => {
                // Validation logic
                const isValid = true; // ... actual validation
                if (!isValid) {
                    notificationService.error('Form validation failed');
                }
                return isValid;
            },
            reset: () => {
                formElement.reset();
            }
        };
    };
}, true); // singleton factory function

// Usage:
const factory = container.get('formValidatorFactory');
const validator = factory(document.getElementById('myForm'));
validator.validate();
```

## Testing Benefits

### Before (Hard to Test):

```javascript
// my-feature.js
window.MyFeature = {
    loadData: function() {
        // Hard-coded API call - can't mock!
        return fetch('https://api.example.com/data');
    }
};

// test.js - IMPOSSIBLE TO TEST WITHOUT HITTING REAL API
test('should load data', () => {
    const result = window.MyFeature.loadData();
    // Can't mock fetch easily, hits real API
});
```

### After (Easy to Test):

```javascript
// my-feature.js
export class MyFeature {
    constructor(httpClient) {
        this.httpClient = httpClient; // Injected!
    }

    loadData() {
        return this.httpClient.get('/data');
    }
}

// test.js - EASY TO TEST WITH MOCK
test('should load data', async () => {
    // Create mock httpClient
    const mockHttpClient = {
        get: jest.fn().mockResolvedValue({ data: 'test' })
    };

    // Inject mock
    const myFeature = new MyFeature(mockHttpClient);

    // Test
    const result = await myFeature.loadData();
    expect(mockHttpClient.get).toHaveBeenCalledWith('/data');
    expect(result).toEqual({ data: 'test' });
});
```

## File-by-File Migration Checklist

### High Priority (Complete These First)

- [ ] `modules/app.js` (47 uses) - Main application controller
- [ ] `modules/onboarding-system.js` (29 uses) - Onboarding flow
- [ ] `modules/navigation.js` (26 uses) - Navigation management
- [ ] `modules/instructor-tab-handlers.js` (24 uses) - Instructor UI
- [ ] `modules/instructor-dashboard.js` (19 uses) - Dashboard
- [ ] `modules/org-admin-core.js` (16 uses) - Organization admin
- [ ] `components/dashboard-navigation.js` (16 uses) - Navigation component

### Medium Priority

- [ ] `modules/student-file-manager.js` (15 uses)
- [ ] `components/course-manager.js` (14 uses)
- [ ] `modules/org-admin-projects.js` (12 uses)
- [ ] `modules/navigation-manager.js` (12 uses)
- [ ] `modules/auth.js` (12 uses)
- [ ] `modules/config-manager.js` (8 uses)
- [ ] `components/component-loader.js` (8 uses)
- [ ] `modules/asset-cache.js` (7 uses)

### Lower Priority (55 files)

See full list in grep output: `grep -r "window\." frontend/js/**/*.js`

## Services To Register

Based on existing codebase analysis, these services should be registered:

### Core Services (Already Registered ✓)
- ✓ config
- ✓ httpClient
- ✓ authService
- ✓ sessionManager
- ✓ notificationService

### Application Services (Already Registered ✓)
- ✓ projectService
- ✓ courseService
- ✓ trackService

### Application Services (TODO)
- [ ] studentService
- [ ] instructorService
- [ ] quizService
- [ ] labService
- [ ] analyticsService
- [ ] feedbackService
- [ ] fileUploadService
- [ ] videoService
- [ ] aiAssistantService

### UI Controllers (TODO)
- [ ] dashboardController (basic version registered)
- [ ] modalController
- [ ] tabController
- [ ] formController
- [ ] navigationController

## Breaking Changes

### For HTML Pages

**Before:**
```html
<script src="/js/my-feature.js"></script>
<script>
    MyFeature.init();
</script>
```

**After:**
```html
<script type="module">
    import { initializeApp } from '/js/core/bootstrap.js';
    const container = initializeApp();
    const myFeature = container.get('myFeature');
    myFeature.init();
</script>
```

### For Inline Event Handlers

**Before:**
```html
<button onclick="window.MyFeature.doSomething()">Click</button>
```

**After:**
```html
<button data-action="my-feature.doSomething">Click</button>

<script type="module">
    import { initializeApp } from '/js/core/bootstrap.js';
    const container = initializeApp();

    // Event delegation
    document.addEventListener('click', (event) => {
        const action = event.target.dataset.action;
        if (action === 'my-feature.doSomething') {
            const myFeature = container.get('myFeature');
            myFeature.doSomething();
        }
    });
</script>
```

## Progress Tracking

**Total Files:** 65 files with window.* usage
**Total Occurrences:** 702
**Completed:** 0 files (0%)
**In Progress:** Bootstrap infrastructure (Container + Service Registration)
**TODO:** 65 files

## Next Steps

1. **Complete Phase 2**: Migrate high-priority files (top 10)
2. **Update HTML pages**: Update script tags to use `type="module"`
3. **Extract inline handlers**: Remove onclick/onchange attributes
4. **Test thoroughly**: Ensure all features work with new architecture
5. **Update documentation**: Document new patterns in CLAUDE.md
6. **Complete remaining files**: Migrate remaining 55 files

## Rollout Strategy

### Option 1: Big Bang (Not Recommended)
- Migrate all files at once
- High risk, hard to debug if issues arise

### Option 2: Incremental (Recommended)
1. Start with one dashboard page (e.g., instructor-dashboard.html)
2. Migrate all JS files used by that page
3. Test thoroughly
4. Move to next page
5. Repeat until all pages migrated

### Option 3: Service-by-Service
1. Migrate all auth-related files first
2. Then navigation files
3. Then dashboard files
4. etc.

**Recommended: Option 2 (Incremental by Page)**

## Success Metrics

- Zero `window.*` assignments in production code (except bootstrap)
- All services testable with mocks
- No global namespace collisions
- Faster test execution (due to mockability)
- Clearer dependency graphs
- Easier onboarding for new developers

## Resources

- **Container Implementation**: `/frontend/js/core/Container.js`
- **Bootstrap File**: `/frontend/js/core/bootstrap.js`
- **SOLID Refactoring Plan**: `/docs/SOLID_REFACTORING_PLAN.md`
- **This Guide**: `/docs/FRONTEND_DI_MIGRATION_GUIDE.md`

---

**Status:** Infrastructure Complete ✓ | Migration In Progress 🔄 | **Next:** Migrate high-priority files

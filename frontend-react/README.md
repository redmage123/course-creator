# Course Creator Platform - React Frontend

**Version**: 1.2.0 (Phase 4 Complete!)
**Status**: Development
**Migration Phase**: Dashboard & Navigation (Complete routing & protection)

## 🎉 Phase 1: Foundation - COMPLETE!
## 🎉 Phase 2: Component Library - COMPLETE!
## 🎉 Phase 3: Authentication Pages - COMPLETE!
## 🎉 Phase 4: Dashboard & Navigation - COMPLETE!

This is the React rewrite of the Course Creator Platform frontend. The migration from vanilla JavaScript to React + TypeScript is currently in progress.

## 🎯 Business Model

**B2B Corporate IT Training Platform**

This platform serves corporate and personal IT trainers who deliver graduate-level AI/IT training programs. Our customers are:

- **Corporate Trainers** - IT professionals who train employees in AI, ML, and software development
- **Personal Trainers** - Independent IT consultants offering specialized tech training
- **Organizations** - Companies purchasing training programs for employee development

**Key Characteristics:**
- **Trainer-Directed Learning** - Instructors enroll students and assign courses
- **No Self-Service Course Selection** - Students don't browse or choose courses; they're assigned by trainers
- **Enterprise Focus** - Bulk student enrollment, compliance tracking, and organizational analytics
- **AI-Focused Content** - Graduate-level AI, machine learning, and modern IT training

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server (HTTPS on port 3002)
npm run dev

# Build for production
npm run build

# Run tests (601 tests, all passing!)
npm test

# Lint and format
npm run lint
npm run format
```

## 📦 Technology Stack

- **React** 19.1.1 - UI framework
- **TypeScript** 5.9.3 - Type safety
- **Vite** 7.1.7 - Build tool & dev server
- **Redux Toolkit** 2.10.1 - State management
- **React Router** 7.9.5 - Client-side routing
- **React Query** 5.90.6 - Server state management
- **Axios** 1.13.2 - HTTP client
- **Vitest** + **React Testing Library** - Testing

## ✅ Completed

### Phase 1: Foundation (COMPLETE)
- ✅ Vite build system with HMR
- ✅ HTTPS development server (port 3002)
- ✅ Redux Toolkit store (auth, user, ui slices)
- ✅ Axios API client with interceptors
- ✅ Authentication service & useAuth hook
- ✅ React Router setup
- ✅ Tami design system CSS
- ✅ TypeScript configuration

### Phase 2: Component Library (COMPLETE - 10 components)
- ✅ **Button** - 5 variants, 3 sizes, loading states, icons (52 tests)
- ✅ **Input** - 4 validation states, 3 sizes, labels, icons, error prop (61 tests)
- ✅ **Card** - 4 variants, header/body/footer, padding options (42 tests)
- ✅ **Modal** - Portal rendering, focus trap, ESC handling (36 tests)
- ✅ **Spinner** - 3 sizes, 3 colors, accessibility (20 tests)
- ✅ **Toast** - 4 variants, auto-dismiss, 6 positions, ESC key (36 tests)
- ✅ **Select** - Search/filter, multi-select, keyboard nav (52 tests)
- ✅ **Textarea** - Auto-resize, character count, validation states (48 tests)
- ✅ **Checkbox** - Indeterminate state, 3 sizes, keyboard nav, ReactNode labels (44 tests)
- ✅ **Heading** - 6 semantic levels, display variant, visual overrides (46 tests)

### Phase 3: Authentication Pages (COMPLETE - 4 pages + layout)
- ✅ **LoginPage** - Email/password validation, remember me, error handling (24 tests)
- ✅ **RegistrationPage** - Full validation, terms acceptance, GDPR compliance (29 tests)
- ✅ **ForgotPasswordPage** - Email validation, success state, retry flow (16 tests)
- ✅ **ResetPasswordPage** - Token validation, password strength, auto-redirect (18 tests)
- ✅ **AuthLayout** - Shared auth page layout with gradient background (15 tests)

### Phase 4: Dashboard & Navigation (COMPLETE - 9 components)
- ✅ **Navbar** - Role-based nav, user menu, mobile responsive, logout (27 tests)
- ✅ **DashboardLayout** - Reusable template, optional sidebar, navbar integration (19 tests)
- ✅ **ProtectedRoute** - Auth guard, role-based access control, redirects (16 tests)
- ✅ **StudentDashboard** - Assigned courses, training progress, lab access (B2B model)
- ✅ **InstructorDashboard** - Corporate trainer tools, student enrollment, content generation
- ✅ **OrgAdminDashboard** - Trainer management, bulk student enrollment, compliance tracking
- ✅ **SiteAdminDashboard** - Platform admin, multi-org management, system config
- ✅ **NotFoundPage** - 404 error page with context-aware navigation
- ✅ **Complete Routing** - 30+ protected routes aligned with B2B corporate training model

**Test Coverage**: 601 tests, 100% passing ✅

## 📁 Project Structure

```
src/
├── components/
│   ├── atoms/               # ✅ 10 atomic components (Button, Input, Card, Modal, Spinner, Toast, Select, Textarea, Checkbox, Heading)
│   ├── organisms/           # ✅ Navbar with role-based navigation
│   ├── templates/           # ✅ DashboardLayout
│   └── routing/             # ✅ ProtectedRoute wrapper
├── features/
│   ├── auth/                # ✅ Authentication feature
│   │   ├── components/      # ✅ AuthLayout component
│   │   └── pages/           # ✅ Login, Register, ForgotPassword, ResetPassword pages
│   └── dashboard/           # ✅ Dashboard feature
│       └── pages/           # ✅ Student, Instructor, OrgAdmin, SiteAdmin dashboards
├── pages/                   # ✅ Top-level pages (Homepage, NotFoundPage)
├── hooks/                   # ✅ Custom React hooks (useAuth, useRedux)
├── services/                # ✅ API clients (apiClient, authService)
├── store/                   # ✅ Redux (auth/user/ui slices)
├── styles/                  # ✅ Global styles (Tami CSS)
├── App.tsx                  # ✅ Root component with comprehensive routing (30+ routes)
└── main.tsx                 # ✅ Entry point
```

## 🧪 Testing

All components have comprehensive test coverage:

```bash
# Run all tests
npm test

# Run specific component tests
npm test -- Button.test.tsx
npm test -- Input.test.tsx
npm test -- Card.test.tsx
npm test -- Modal.test.tsx
npm test -- Spinner.test.tsx
npm test -- Toast.test.tsx
npm test -- Select.test.tsx
npm test -- Textarea.test.tsx
npm test -- Checkbox.test.tsx
npm test -- Heading.test.tsx

# Run auth page tests
npm test -- LoginPage.test.tsx
npm test -- RegistrationPage.test.tsx
npm test -- ForgotPasswordPage.test.tsx
npm test -- ResetPasswordPage.test.tsx
npm test -- AuthLayout.test.tsx

# Run dashboard & navigation tests
npm test -- Navbar.test.tsx
npm test -- DashboardLayout.test.tsx
npm test -- ProtectedRoute.test.tsx

# Run with coverage
npm run test:coverage
```

## 🚦 Migration Status

### ✅ Phase 1: Foundation (COMPLETE - Week 1-2)
### ✅ Phase 2: Component Library (COMPLETE - Week 3-4)
### ✅ Phase 3: Authentication Pages (COMPLETE - Week 5)
### ✅ Phase 4: Dashboard & Navigation (COMPLETE - Week 6)
### ⏳ Phase 5: Course Management Pages (Next - Week 7-8)
### ⏳ Phase 6-9: Advanced Features & Deployment (Pending - Week 9-14)

See `/docs/REACT_MIGRATION_STRATEGY.md` for full timeline.

## 🎨 Component Design

All components follow Tami design system:
- Platform blue (#2563eb) for primary actions
- 8px border radius
- Consistent spacing and typography
- WCAG 2.1 AA+ accessibility
- TypeScript with full type safety
- CSS Modules for scoped styling

## 🔗 Links

- Migration Strategy: `../docs/REACT_MIGRATION_STRATEGY.md`
- Vanilla JS Frontend: `../frontend/`
- Development Guide: `../CLAUDE.md`

---

**Last Updated**: 2025-11-05
**Next Milestone**: Phase 5 - Course Management Pages (Course Catalog, Course Details, Enrollment)

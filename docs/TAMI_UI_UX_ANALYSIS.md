# Tami UI/UX Design Analysis Report
## Comprehensive Study for Course Creator Platform Enhancement

**Date**: 2025-10-15
**Analyzed Website**: https://trytami.com
**Purpose**: Identify design patterns and UI/UX elements to enhance Course Creator Platform dashboards and wizards

---

## Executive Summary

Tami employs a clean, professional design system built on modern web standards with a focus on clarity, accessibility, and systematic implementation. Their design philosophy emphasizes:

- **Simplicity over complexity**: Clean layouts with generous whitespace
- **Consistency**: Systematic use of design tokens (colors, spacing, typography)
- **Professional aesthetics**: Deep purple primary with orange accents creates sophisticated yet approachable feel
- **Progressive disclosure**: Information revealed contextually through dropdown menus and card-based layouts
- **Responsive-first**: Mobile and desktop experiences equally polished

**Key Takeaway**: Tami's design succeeds by balancing visual appeal with functional clarity—perfect inspiration for our multi-tenant educational platform.

---

## 1. Visual Design Elements

### 1.1 Color Scheme & Palette

**Primary Colors:**
```css
--color-primary: #3E215B;        /* Deep purple - headers, navigation, primary actions */
--color-secondary: #F38120;      /* Vibrant orange - CTAs, highlights, accents */
--color-background: #FFFFFF;     /* Clean white background */
--color-text: #030712;           /* Near-black for optimal readability */
```

**Color Usage Philosophy:**
- Purple establishes brand authority and professionalism (education-appropriate)
- Orange provides energetic contrast for calls-to-action
- High contrast ratios (purple on white, orange on white) ensure accessibility (WCAG AA+ compliance)
- Neutral backgrounds let content breathe

**Recommendations for Course Creator:**
```css
/* Adapt Tami's approach with our educational context */
--cc-primary: #3E215B;           /* Adopt for org admin dashboard headers */
--cc-accent: #F38120;            /* Use for "Create Project", "Add Track" buttons */
--cc-success: #10B981;           /* Keep our existing success green */
--cc-danger: #EF4444;            /* Keep our existing danger red */
--cc-neutral-50: #F9FAFB;        /* Light gray backgrounds for cards */
--cc-neutral-900: #030712;       /* Dark text on light backgrounds */
```

**Priority**: ⭐⭐⭐⭐⭐ **HIGH - Quick Win**
**Implementation**: Update CSS variables in `/home/bbrelin/course-creator/frontend/css/components/rbac-dashboard.css`

---

### 1.2 Typography

**Font Stack:**
```css
font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
             "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

**Font Weights:**
- **100-300**: Light weights (rarely used, only for large hero text)
- **400**: Regular body text
- **500-600**: Medium weights for emphasized text, subheadings
- **700-900**: Bold weights for headings, navigation

**Type Scale (observed):**
```css
/* Headings */
--text-4xl: 36px;     /* H1 - Page titles */
--text-3xl: 30px;     /* H2 - Section headers */
--text-2xl: 24px;     /* H3 - Subsection headers */
--text-xl: 20px;      /* H4 - Card titles */

/* Body */
--text-base: 15px;    /* Standard body text */
--text-sm: 13px;      /* Small text, labels */
--text-xs: 11px;      /* Fine print, captions */
```

**Line Heights:**
- Body text: 1.5 (22.5px at 15px font size) for comfortable reading
- Headings: 1.2-1.3 for tighter, more impactful headlines

**Recommendations for Course Creator:**
1. **Replace current font stack** with Inter (already using system fonts, Inter is a upgrade)
2. **Establish clear type scale** across all dashboards (currently inconsistent)
3. **Use font weights strategically**:
   - 400 for body text
   - 600 for form labels, sidebar navigation
   - 700 for page headers, modal titles
   - 800+ sparingly for hero sections only

**Priority**: ⭐⭐⭐⭐ **HIGH - Major Impact**
**Implementation**:
```css
/* Add to /frontend/css/components/header-footer.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-size-xs: 0.6875rem;   /* 11px */
  --font-size-sm: 0.8125rem;   /* 13px */
  --font-size-base: 0.9375rem; /* 15px */
  --font-size-lg: 1rem;        /* 16px */
  --font-size-xl: 1.25rem;     /* 20px */
  --font-size-2xl: 1.5rem;     /* 24px */
  --font-size-3xl: 1.875rem;   /* 30px */
  --font-size-4xl: 2.25rem;    /* 36px */
}

body {
  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  line-height: 1.5;
}
```

---

### 1.3 Spacing & Layout Patterns

**Spacing System (8px base unit):**
```css
--spacing-1: 8px;
--spacing-2: 16px;   /* Most common - navigation, card padding */
--spacing-3: 24px;   /* Dropdown menus, modal content */
--spacing-4: 32px;
--spacing-5: 40px;   /* Navigation horizontal padding */
--spacing-6: 48px;
--spacing-8: 64px;
--spacing-10: 80px;
```

**Layout Patterns Observed:**

1. **Navigation Bar**:
   - Horizontal padding: 40px
   - Vertical padding: 16px
   - Sticky positioning (stays at top on scroll)
   - Full-width with max-width container

2. **Dropdown Menus**:
   - Padding: 24px
   - Border radius: 8px
   - Box shadow for depth perception
   - Generous spacing between menu items

3. **Card-Based Layouts**:
   - Consistent padding: 24px
   - Border radius: 8px
   - White background with subtle shadows
   - Equal spacing between cards (16-24px gaps)

4. **Content Sections**:
   - Vertical section padding: 64px+ for visual breathing room
   - Horizontal padding: 40px (desktop), 16px (mobile)
   - Max-width containers (~1200px) to prevent line length issues

**Whitespace Philosophy:**
- **Generous vertical spacing** between major sections (64px+)
- **Comfortable padding** inside containers (24px minimum)
- **Breathing room** around interactive elements (buttons, inputs)
- **Grid gaps** consistent at 16-24px

**Recommendations for Course Creator:**

Our current dashboards feel cramped. Apply Tami's spacing system:

```css
/* Update /frontend/css/components/rbac-dashboard.css */
:root {
  --space-xs: 0.5rem;   /* 8px */
  --space-sm: 1rem;     /* 16px */
  --space-md: 1.5rem;   /* 24px */
  --space-lg: 2rem;     /* 32px */
  --space-xl: 2.5rem;   /* 40px */
  --space-2xl: 3rem;    /* 48px */
  --space-3xl: 4rem;    /* 64px */
}

.dashboard-container {
  padding: var(--space-xl);        /* 40px breathing room */
  max-width: 1200px;               /* Prevent overly wide content */
  margin: 0 auto;                  /* Center content */
}

.dashboard-card {
  padding: var(--space-md);        /* 24px consistent card padding */
  border-radius: 8px;              /* Tami's border radius */
  margin-bottom: var(--space-md);  /* Vertical rhythm */
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-sm);            /* 16px grid gap */
}
```

**Priority**: ⭐⭐⭐⭐⭐ **CRITICAL - Immediate Impact**
**Effort**: Low (CSS variables update)

---

## 2. Component Design

### 2.1 Button Styles & Interactions

**Button Hierarchy:**

1. **Primary CTA** (Request a Demo, Get Started):
   ```css
   .btn-primary {
     background-color: #F38120;  /* Orange */
     color: #FFFFFF;
     padding: 12px 24px;
     border-radius: 8px;
     font-weight: 600;
     font-size: 15px;
     border: none;
     transition: background-color 200ms ease;
   }

   .btn-primary:hover {
     background-color: #D86F1A;  /* Darker orange on hover */
     cursor: pointer;
   }
   ```

2. **Secondary Actions**:
   ```css
   .btn-secondary {
     background-color: transparent;
     color: #3E215B;
     border: 2px solid #3E215B;
     padding: 12px 24px;
     border-radius: 8px;
     font-weight: 600;
     transition: all 200ms ease;
   }

   .btn-secondary:hover {
     background-color: #3E215B;
     color: #FFFFFF;
   }
   ```

3. **Text Links/Ghost Buttons**:
   ```css
   .btn-ghost {
     background: none;
     border: none;
     color: #3E215B;
     font-weight: 500;
     text-decoration: underline;
     padding: 8px 16px;
   }
   ```

**Button Sizing:**
- **Default**: 12px vertical, 24px horizontal padding
- **Large**: 16px vertical, 32px horizontal padding
- **Small**: 8px vertical, 16px horizontal padding

**Interaction States:**
- **Hover**: Background color darkens slightly (200ms transition)
- **Active/Pressed**: Slight scale transform or darker background
- **Disabled**: 50% opacity, no pointer events
- **Focus**: Visible outline (accessibility requirement)

**Recommendations for Course Creator:**

Replace all button styles across dashboards:

```css
/* Add to /frontend/css/components/rbac-dashboard.css */

/* Primary actions: Create Project, Add Track, Save Settings */
.btn-primary,
.create-project-btn,
.add-track-btn,
.save-settings-btn {
  background-color: #F38120;
  color: #FFFFFF;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 15px;
  border: none;
  transition: all 200ms ease;
  cursor: pointer;
}

.btn-primary:hover {
  background-color: #D86F1A;
  transform: translateY(-1px);  /* Subtle lift effect */
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Secondary actions: Cancel, View Details, Filter */
.btn-secondary,
.cancel-btn,
.filter-btn {
  background-color: transparent;
  color: #3E215B;
  border: 2px solid #3E215B;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 15px;
  transition: all 200ms ease;
  cursor: pointer;
}

.btn-secondary:hover {
  background-color: #3E215B;
  color: #FFFFFF;
}

/* Destructive actions: Delete, Remove, Archive */
.btn-danger,
.delete-btn {
  background-color: #EF4444;
  color: #FFFFFF;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 15px;
  border: none;
  transition: all 200ms ease;
  cursor: pointer;
}

.btn-danger:hover {
  background-color: #DC2626;
}

/* Disabled state - all buttons */
.btn-primary:disabled,
.btn-secondary:disabled,
.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

/* Focus state for accessibility */
.btn-primary:focus,
.btn-secondary:focus,
.btn-danger:focus {
  outline: 3px solid rgba(62, 33, 91, 0.3);
  outline-offset: 2px;
}
```

**Priority**: ⭐⭐⭐⭐⭐ **CRITICAL - Consistent UX**
**Pages to Update**:
- `/frontend/html/org-admin-dashboard.html`
- `/frontend/html/site-admin-dashboard.html`
- All modal dialogs (create project, add track, etc.)

---

### 2.2 Form Design & Input Fields

**Form Field Anatomy:**

```html
<!-- Tami-style form field structure -->
<div class="form-field">
  <label for="project-name" class="form-label">Project Name</label>
  <input
    type="text"
    id="project-name"
    class="form-input"
    placeholder="Enter project name"
  />
  <span class="form-hint">This will be visible to all instructors</span>
</div>
```

**Input Field Styling:**
```css
.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #374151;  /* Darker gray for labels */
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #E5E7EB;  /* Light gray border */
  border-radius: 8px;
  font-size: 15px;
  font-family: 'Inter', sans-serif;
  transition: all 200ms ease;
}

.form-input:focus {
  outline: none;
  border-color: #3E215B;  /* Purple border on focus */
  box-shadow: 0 0 0 3px rgba(62, 33, 91, 0.1);  /* Subtle purple glow */
}

.form-input::placeholder {
  color: #9CA3AF;  /* Medium gray placeholder */
  font-weight: 400;
}

.form-hint {
  display: block;
  font-size: 13px;
  color: #6B7280;
  margin-top: 6px;
}

.form-error {
  color: #EF4444;
  font-size: 13px;
  margin-top: 6px;
}
```

**Input States:**
- **Default**: Light gray border (#E5E7EB)
- **Focus**: Purple border with subtle shadow glow
- **Error**: Red border with error message below
- **Disabled**: Gray background, reduced opacity
- **Success**: Green border (for validated fields)

**Select Dropdowns:**
```css
.form-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #E5E7EB;
  border-radius: 8px;
  font-size: 15px;
  background-color: #FFFFFF;
  background-image: url('data:image/svg+xml;utf8,<svg>...</svg>');  /* Custom dropdown arrow */
  background-repeat: no-repeat;
  background-position: right 12px center;
  appearance: none;
}
```

**Checkbox & Radio Styling:**
```css
.form-checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid #E5E7EB;
  border-radius: 4px;
  accent-color: #3E215B;  /* Purple checkmark */
}

.form-checkbox:checked {
  background-color: #3E215B;
  border-color: #3E215B;
}
```

**Recommendations for Course Creator:**

Our forms need visual consistency. Apply these patterns to:

1. **Project Creation Wizard** (`/frontend/html/org-admin-dashboard.html`)
2. **Track Creation Forms**
3. **User Registration Forms**
4. **Settings Pages**

```css
/* Add to /frontend/css/components/rbac-dashboard.css */

.form-container {
  max-width: 600px;  /* Prevent overly wide forms */
  margin: 0 auto;
}

.form-field {
  margin-bottom: 24px;  /* Consistent vertical spacing */
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.form-label.required::after {
  content: " *";
  color: #EF4444;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #E5E7EB;
  border-radius: 8px;
  font-size: 15px;
  font-family: 'Inter', sans-serif;
  transition: all 200ms ease;
  background-color: #FFFFFF;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3E215B;
  box-shadow: 0 0 0 3px rgba(62, 33, 91, 0.1);
}

.form-input.error,
.form-select.error {
  border-color: #EF4444;
}

.form-hint {
  display: block;
  font-size: 13px;
  color: #6B7280;
  margin-top: 6px;
  font-style: italic;
}

.form-error {
  display: block;
  color: #EF4444;
  font-size: 13px;
  margin-top: 6px;
  font-weight: 500;
}

.form-success {
  display: block;
  color: #10B981;
  font-size: 13px;
  margin-top: 6px;
}

/* Checkbox/Radio groups */
.form-checkbox-group,
.form-radio-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-checkbox-item,
.form-radio-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-checkbox,
.form-radio {
  width: 20px;
  height: 20px;
  accent-color: #3E215B;
}
```

**Priority**: ⭐⭐⭐⭐⭐ **CRITICAL - User Input Quality**
**Impact**: Reduces form errors, improves user confidence

---

### 2.3 Navigation Patterns

**Header Navigation Structure:**

```html
<nav class="navbar">
  <div class="navbar-container">
    <!-- Logo/Brand -->
    <div class="navbar-brand">
      <img src="logo.svg" alt="Tami" />
    </div>

    <!-- Primary Navigation -->
    <ul class="navbar-menu">
      <li class="navbar-item has-dropdown">
        <a href="#" class="navbar-link">Solutions</a>
        <div class="navbar-dropdown">
          <!-- Dropdown content -->
        </div>
      </li>
      <li class="navbar-item">
        <a href="#" class="navbar-link">Pricing</a>
      </li>
      <!-- More items -->
    </ul>

    <!-- CTA Buttons -->
    <div class="navbar-actions">
      <a href="#" class="btn-secondary">Sign In</a>
      <a href="#" class="btn-primary">Request a Demo</a>
    </div>
  </div>
</nav>
```

**Navigation Styling:**
```css
.navbar {
  position: sticky;
  top: 0;
  z-index: 1000;
  background-color: #FFFFFF;
  border-bottom: 1px solid #E5E7EB;
  padding: 16px 40px;
}

.navbar-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.navbar-menu {
  display: flex;
  gap: 32px;  /* Generous spacing between nav items */
  list-style: none;
  margin: 0;
  padding: 0;
}

.navbar-link {
  font-size: 15px;
  font-weight: 500;
  color: #374151;
  text-decoration: none;
  transition: color 200ms ease;
}

.navbar-link:hover {
  color: #3E215B;  /* Purple on hover */
}

/* Dropdown menus */
.navbar-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  background: #FFFFFF;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  padding: 24px;
  min-width: 300px;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: all 200ms ease;
}

.navbar-item:hover .navbar-dropdown {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}
```

**Dropdown Menu Content:**
- **Descriptive items**: Not just links, but mini-cards with titles and descriptions
- **Icon support**: Small icons next to menu items for visual cues
- **Organized sections**: Grouped related items with subtle dividers

**Mobile Navigation:**
- **Hamburger menu**: Collapses to mobile menu at 667px breakpoint
- **Full-screen overlay**: Mobile menu takes over entire screen
- **Touch-friendly**: Larger touch targets (minimum 44px height)

**Recommendations for Course Creator:**

Our navigation needs modernization:

**Current Issues:**
- Sidebar navigation feels dated
- No sticky header on dashboards
- Inconsistent active states
- Poor mobile experience

**Proposed Updates:**

```css
/* Modernize sidebar navigation - /frontend/css/components/rbac-dashboard.css */

.dashboard-sidebar {
  width: 260px;
  background-color: #FFFFFF;
  border-right: 1px solid #E5E7EB;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  padding: 24px 0;
}

.sidebar-nav {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar-nav-item {
  margin-bottom: 4px;  /* Tight vertical spacing */
}

.sidebar-nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  color: #6B7280;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  transition: all 200ms ease;
  border-left: 3px solid transparent;
}

.sidebar-nav-link:hover {
  background-color: #F9FAFB;
  color: #3E215B;
}

.sidebar-nav-link.active {
  background-color: #F3F4F6;
  color: #3E215B;
  border-left-color: #F38120;  /* Orange accent for active state */
  font-weight: 600;
}

.sidebar-nav-icon {
  width: 20px;
  height: 20px;
  color: currentColor;
}

/* Collapsible sections */
.sidebar-section {
  margin-bottom: 24px;
}

.sidebar-section-title {
  padding: 8px 24px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #9CA3AF;
}
```

**Priority**: ⭐⭐⭐⭐ **HIGH - Navigation Clarity**
**Implementation**: Update all dashboard HTML templates

---

### 2.4 Card & Container Designs

**Card Anatomy:**

```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Project Statistics</h3>
    <button class="card-action">
      <svg><!-- Action icon --></svg>
    </button>
  </div>
  <div class="card-body">
    <!-- Card content -->
  </div>
  <div class="card-footer">
    <!-- Optional footer actions -->
  </div>
</div>
```

**Card Styling:**
```css
.card {
  background: #FFFFFF;
  border-radius: 8px;
  border: 1px solid #E5E7EB;
  overflow: hidden;
  transition: all 200ms ease;
}

.card:hover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);  /* Subtle lift on hover */
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #E5E7EB;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.card-body {
  padding: 24px;
}

.card-footer {
  padding: 16px 24px;
  background-color: #F9FAFB;
  border-top: 1px solid #E5E7EB;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
```

**Card Variations:**

1. **Stat Cards**:
   ```css
   .stat-card {
     background: linear-gradient(135deg, #3E215B 0%, #6D28D9 100%);
     color: #FFFFFF;
     padding: 24px;
     border-radius: 8px;
   }

   .stat-value {
     font-size: 36px;
     font-weight: 700;
     margin-bottom: 8px;
   }

   .stat-label {
     font-size: 14px;
     opacity: 0.9;
   }
   ```

2. **Feature Cards** (Pricing page):
   ```css
   .feature-card {
     background: #FFFFFF;
     border: 2px solid #E5E7EB;
     border-radius: 12px;
     padding: 32px;
     text-align: center;
   }

   .feature-card.featured {
     border-color: #F38120;
     box-shadow: 0 20px 40px rgba(243, 129, 32, 0.15);
   }
   ```

3. **Interactive Cards** (Clickable):
   ```css
   .card-clickable {
     cursor: pointer;
     transition: all 200ms ease;
   }

   .card-clickable:hover {
     border-color: #3E215B;
     box-shadow: 0 10px 30px rgba(62, 33, 91, 0.15);
   }
   ```

**Container Patterns:**

```css
/* Page container */
.page-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px;
}

/* Content sections */
.content-section {
  margin-bottom: 64px;  /* Large vertical spacing */
}

.section-header {
  margin-bottom: 32px;
}

.section-title {
  font-size: 30px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 12px;
}

.section-description {
  font-size: 16px;
  color: #6B7280;
  max-width: 600px;
}
```

**Recommendations for Course Creator:**

Replace dashboard card styles:

```css
/* Update all dashboard cards */
.dashboard-card,
.stats-card,
.project-card,
.track-card {
  background: #FFFFFF;
  border-radius: 8px;
  border: 1px solid #E5E7EB;
  overflow: hidden;
  transition: all 200ms ease;
}

.dashboard-card:hover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

/* Stats overview cards */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: linear-gradient(135deg, #3E215B 0%, #6D28D9 100%);
  color: #FFFFFF;
  padding: 24px;
  border-radius: 8px;
}

.stat-card-value {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stat-card-label {
  font-size: 14px;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Project/Track cards in grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.project-card,
.track-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 24px;
  cursor: pointer;
  transition: all 200ms ease;
}

.project-card:hover,
.track-card:hover {
  border-color: #3E215B;
  box-shadow: 0 10px 30px rgba(62, 33, 91, 0.12);
  transform: translateY(-4px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 8px 0;
}

.card-meta {
  font-size: 13px;
  color: #6B7280;
}

.card-body {
  margin-bottom: 16px;
}

.card-description {
  font-size: 14px;
  color: #4B5563;
  line-height: 1.6;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #F3F4F6;
}

.card-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.card-tag {
  display: inline-block;
  padding: 4px 12px;
  background-color: #F3F4F6;
  color: #6B7280;
  font-size: 12px;
  font-weight: 500;
  border-radius: 12px;
}

.card-tag.status-active {
  background-color: #D1FAE5;
  color: #065F46;
}

.card-tag.status-draft {
  background-color: #FEF3C7;
  color: #92400E;
}
```

**Priority**: ⭐⭐⭐⭐⭐ **CRITICAL - Visual Consistency**
**Files to Update**:
- `/frontend/css/components/rbac-dashboard.css`
- `/frontend/html/org-admin-dashboard.html`
- All project/track listing pages

---

### 2.5 Modal & Dialog Patterns

**Modal Structure:**

```html
<div class="modal-overlay">
  <div class="modal">
    <div class="modal-header">
      <h2 class="modal-title">Create New Project</h2>
      <button class="modal-close" aria-label="Close">
        <svg><!-- Close icon --></svg>
      </button>
    </div>
    <div class="modal-body">
      <!-- Form content -->
    </div>
    <div class="modal-footer">
      <button class="btn-secondary">Cancel</button>
      <button class="btn-primary">Create Project</button>
    </div>
  </div>
</div>
```

**Modal Styling:**
```css
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  animation: fadeIn 200ms ease;
}

.modal {
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  animation: slideUp 300ms ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #E5E7EB;
}

.modal-title {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  color: #6B7280;
  transition: color 200ms ease;
}

.modal-close:hover {
  color: #111827;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  max-height: calc(90vh - 160px);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #E5E7EB;
  background-color: #F9FAFB;
}
```

**Dialog Variants:**

1. **Confirmation Dialog**:
   ```css
   .dialog-confirm {
     max-width: 400px;
     text-align: center;
   }

   .dialog-icon {
     width: 48px;
     height: 48px;
     margin: 0 auto 16px;
     color: #F38120;
   }
   ```

2. **Alert/Warning Dialog**:
   ```css
   .dialog-warning {
     border-top: 4px solid #EF4444;
   }

   .dialog-warning .modal-title {
     color: #EF4444;
   }
   ```

**Recommendations for Course Creator:**

Update modal system across all wizards:

```css
/* Unified modal system - /frontend/css/components/rbac-dashboard.css */

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);  /* Modern blur effect */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  opacity: 0;
  visibility: hidden;
  transition: all 300ms ease;
}

.modal-overlay.active {
  opacity: 1;
  visibility: visible;
}

.modal {
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
  max-width: 700px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  transform: translateY(20px) scale(0.95);
  transition: transform 300ms ease;
}

.modal-overlay.active .modal {
  transform: translateY(0) scale(1);
}

/* Wizard-specific modals */
.wizard-modal {
  max-width: 900px;  /* Wider for multi-step forms */
}

.wizard-steps {
  display: flex;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid #E5E7EB;
  background-color: #F9FAFB;
}

.wizard-step {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  position: relative;
}

.wizard-step::after {
  content: '';
  position: absolute;
  top: 50%;
  right: -50%;
  width: 100%;
  height: 2px;
  background-color: #E5E7EB;
  z-index: -1;
}

.wizard-step:last-child::after {
  display: none;
}

.wizard-step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #E5E7EB;
  color: #6B7280;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.wizard-step.active .wizard-step-number {
  background-color: #3E215B;
  color: #FFFFFF;
}

.wizard-step.completed .wizard-step-number {
  background-color: #10B981;
  color: #FFFFFF;
}

.wizard-step-label {
  font-size: 14px;
  font-weight: 500;
  color: #6B7280;
}

.wizard-step.active .wizard-step-label {
  color: #3E215B;
}
```

**Priority**: ⭐⭐⭐⭐ **HIGH - Wizard UX**
**Impact**: Project creation wizard will feel more modern and guided

---

## 3. User Experience Patterns

### 3.1 Information Architecture & Flow

**Hierarchical Structure:**

Tami uses clear visual hierarchy to guide users:

1. **Homepage Flow**:
   - Hero section with clear value proposition
   - Solution overview (what we offer)
   - Feature highlights (how it works)
   - Pricing transparency (how to get it)
   - CTA repetition (multiple entry points)

2. **Navigation Flow**:
   - Logical grouping: Solutions → Pricing → Resources → Company
   - Dropdown menus reveal detailed options without overwhelming top nav
   - Persistent header keeps navigation accessible

3. **Page Structure Pattern**:
   ```
   ┌─────────────────────────────────┐
   │  Hero / Page Title              │
   │  (Clear H1, supporting copy)    │
   ├─────────────────────────────────┤
   │  Key Message / Subheading       │
   ├─────────────────────────────────┤
   │  Content Section 1              │
   │  (Visual + Text)                │
   ├─────────────────────────────────┤
   │  Content Section 2              │
   │  (Text + Visual - alternating)  │
   ├─────────────────────────────────┤
   │  Social Proof / Testimonials    │
   ├─────────────────────────────────┤
   │  CTA Section                    │
   └─────────────────────────────────┘
   ```

**Recommendations for Course Creator:**

Apply to our dashboards:

1. **Org Admin Dashboard Structure**:
   ```
   ┌──────────────────────────────────────┐
   │  Header: Welcome, [Org Admin Name]   │  ← Personalization
   ├──────────────────────────────────────┤
   │  Quick Stats (4 stat cards)          │  ← At-a-glance metrics
   ├──────────────────────────────────────┤
   │  Primary Actions                     │  ← Create Project, Add Track (prominent)
   ├──────────────────────────────────────┤
   │  Recent Projects (card grid)         │  ← Quick access to work
   ├──────────────────────────────────────┤
   │  Activity Feed                       │  ← What's happening
   └──────────────────────────────────────┘
   ```

2. **Project Creation Wizard Flow**:
   ```
   Step 1: Project Basics
   ↓
   Step 2: Audience & Tracks
   ↓
   Step 3: Instructors Assignment
   ↓
   Step 4: Review & Create
   ```
   - Each step visible in progress indicator
   - "Save Draft" option at every step
   - Clear "Next" and "Back" navigation

**Priority**: ⭐⭐⭐⭐ **HIGH - User Orientation**

---

### 3.2 Call-to-Action Placements

**CTA Strategy Observed:**

1. **Repetition**: "Request a Demo" appears multiple times:
   - Header navigation (always visible)
   - Hero section (primary focus)
   - End of pricing page (after information)
   - Footer (last chance)

2. **Hierarchy**:
   - Primary CTA: Orange button, prominent placement
   - Secondary CTA: Outlined button, less visually dominant
   - Tertiary CTA: Text links within content

3. **Context-Aware**:
   - Different CTAs based on page context
   - Pricing page emphasizes "Get Started" vs homepage's "Request Demo"

**Recommendations for Course Creator:**

**Org Admin Dashboard CTAs:**

```html
<!-- Primary action area -->
<div class="dashboard-actions">
  <button class="btn-primary btn-large">
    <svg class="btn-icon"><!-- Plus icon --></svg>
    Create New Project
  </button>
  <button class="btn-secondary">
    <svg class="btn-icon"><!-- Users icon --></svg>
    Invite Instructors
  </button>
  <button class="btn-secondary">
    <svg class="btn-icon"><!-- Settings icon --></svg>
    Organization Settings
  </button>
</div>
```

**Positioning Rules:**
- **Above the fold**: Primary action visible without scrolling
- **Contextual**: Show "Create Track" when viewing project details
- **Persistent**: Keep create buttons accessible in sticky header or sidebar
- **Clear hierarchy**: One primary action per view

**Priority**: ⭐⭐⭐⭐⭐ **CRITICAL - Conversion Optimization**

---

### 3.3 Progressive Disclosure Techniques

**How Tami Does It:**

1. **Navigation Dropdowns**: Don't show all options upfront, reveal on hover
2. **Pricing Tiers**: Expand to show full feature lists
3. **Content Sections**: Key information first, details available on click/scroll

**Progressive Disclosure Pattern:**
```
Initial State → Hover/Click → Expanded State
   Simple    →   Trigger   →   Detailed
```

**Recommendations for Course Creator:**

**Project Cards with Progressive Disclosure:**

```html
<div class="project-card">
  <!-- Always visible -->
  <div class="card-preview">
    <h3 class="project-title">Frontend Development</h3>
    <p class="project-meta">12 tracks • 45 students • Active</p>
    <p class="project-description">
      Comprehensive frontend development curriculum...
    </p>
  </div>

  <!-- Revealed on hover or click -->
  <div class="card-details">
    <div class="project-stats">
      <div class="stat-item">
        <span class="stat-label">Completion Rate</span>
        <span class="stat-value">78%</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Avg. Score</span>
        <span class="stat-value">85%</span>
      </div>
    </div>
    <div class="project-actions">
      <button class="btn-small btn-secondary">View Details</button>
      <button class="btn-small btn-secondary">Edit</button>
    </div>
  </div>
</div>
```

```css
.card-details {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: all 300ms ease;
}

.project-card:hover .card-details {
  max-height: 200px;
  opacity: 1;
  margin-top: 16px;
}
```

**Benefits**:
- Reduces cognitive load
- Keeps interface clean
- Provides details on demand

**Priority**: ⭐⭐⭐ **MEDIUM - Enhanced UX**

---

### 3.4 Loading States & Feedback

**Tami's Approach** (inferred from modern web standards):

1. **Skeleton Screens**: Show content structure while loading
2. **Progress Indicators**: Clear feedback for actions
3. **Optimistic UI**: Update immediately, sync in background
4. **Error Handling**: Clear, actionable error messages

**Recommendations for Course Creator:**

**Loading States:**

```html
<!-- Skeleton loader for cards -->
<div class="card-skeleton">
  <div class="skeleton-header"></div>
  <div class="skeleton-text"></div>
  <div class="skeleton-text short"></div>
  <div class="skeleton-footer"></div>
</div>
```

```css
.skeleton-header,
.skeleton-text,
.skeleton-footer {
  background: linear-gradient(
    90deg,
    #F3F4F6 0%,
    #E5E7EB 50%,
    #F3F4F6 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-header {
  height: 24px;
  width: 60%;
  margin-bottom: 12px;
}

.skeleton-text {
  height: 16px;
  width: 100%;
  margin-bottom: 8px;
}

.skeleton-text.short {
  width: 70%;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```

**Button Loading States:**

```html
<button class="btn-primary" data-loading="true">
  <span class="btn-spinner"></span>
  <span class="btn-text">Creating Project...</span>
</button>
```

```css
.btn-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #FFFFFF;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

button[data-loading="true"] {
  pointer-events: none;
  opacity: 0.7;
}
```

**Toast Notifications:**

```html
<div class="toast toast-success">
  <svg class="toast-icon"><!-- Checkmark --></svg>
  <div class="toast-content">
    <p class="toast-title">Project Created Successfully</p>
    <p class="toast-message">Frontend Development is now live</p>
  </div>
  <button class="toast-close">×</button>
</div>
```

```css
.toast {
  position: fixed;
  top: 24px;
  right: 24px;
  background: #FFFFFF;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 320px;
  max-width: 400px;
  animation: slideInRight 300ms ease;
  z-index: 10000;
}

.toast-success {
  border-left: 4px solid #10B981;
}

.toast-error {
  border-left: 4px solid #EF4444;
}

.toast-warning {
  border-left: 4px solid #F59E0B;
}

@keyframes slideInRight {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
```

**Priority**: ⭐⭐⭐⭐ **HIGH - User Confidence**
**Implementation**: Add to all async operations (create, update, delete)

---

### 3.5 Error Handling & Validation

**Best Practices from Tami's Design:**

1. **Inline Validation**: Show errors next to form fields
2. **Clear Messaging**: Explain what went wrong and how to fix it
3. **Visual Indicators**: Red borders, icons, error text
4. **Prevent Errors**: Disable submit until form is valid

**Recommendations for Course Creator:**

**Form Validation Pattern:**

```html
<div class="form-field" data-valid="false">
  <label for="project-name" class="form-label required">
    Project Name
  </label>
  <div class="input-wrapper">
    <input
      type="text"
      id="project-name"
      class="form-input error"
      value=""
      aria-describedby="project-name-error"
    />
    <svg class="input-icon error-icon"><!-- X icon --></svg>
  </div>
  <span id="project-name-error" class="form-error">
    Project name is required and must be at least 3 characters
  </span>
</div>

<div class="form-field" data-valid="true">
  <label for="project-desc" class="form-label">
    Description
  </label>
  <div class="input-wrapper">
    <textarea
      id="project-desc"
      class="form-input success"
      aria-describedby="project-desc-success"
    >A comprehensive course</textarea>
    <svg class="input-icon success-icon"><!-- Checkmark --></svg>
  </div>
  <span id="project-desc-success" class="form-success">
    Looks good!
  </span>
</div>
```

```css
.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  pointer-events: none;
}

.error-icon {
  color: #EF4444;
}

.success-icon {
  color: #10B981;
}

.form-input.error {
  border-color: #EF4444;
  padding-right: 40px;  /* Make room for icon */
}

.form-input.success {
  border-color: #10B981;
  padding-right: 40px;
}

.form-error {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #EF4444;
  font-size: 13px;
  margin-top: 6px;
}

.form-error::before {
  content: '⚠';
  font-size: 14px;
}

.form-success {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #10B981;
  font-size: 13px;
  margin-top: 6px;
}

.form-success::before {
  content: '✓';
  font-size: 14px;
}
```

**Error Page Design:**

```html
<div class="error-container">
  <div class="error-icon-large">
    <svg><!-- Error illustration --></svg>
  </div>
  <h1 class="error-title">Oops! Something went wrong</h1>
  <p class="error-message">
    We couldn't load the project details. This might be a temporary issue.
  </p>
  <div class="error-actions">
    <button class="btn-primary" onclick="location.reload()">
      Try Again
    </button>
    <a href="/dashboard" class="btn-secondary">
      Go to Dashboard
    </a>
  </div>
  <details class="error-details">
    <summary>Technical Details</summary>
    <pre class="error-stack">Error: Failed to fetch project ID 123...</pre>
  </details>
</div>
```

**Priority**: ⭐⭐⭐⭐⭐ **CRITICAL - Data Integrity**

---

## 4. Unique & Innovative Features

### 4.1 Standout Design Patterns

**Observed Innovations:**

1. **Descriptive Navigation Menus**:
   - Not just "Solutions" but mini-cards explaining each solution
   - Helps users understand options without clicking through
   - Reduces cognitive load and decision paralysis

2. **Credits-Based Pricing Transparency**:
   - Complex pricing made simple through visual explanation
   - "1 Credit = 1 Learner Training" clear formula
   - Builds trust through transparency

3. **Skill-Based Organization**:
   - Navigation organized by skills (Development, Design, Business)
   - Aligns with how users think about learning
   - More intuitive than generic categories

**Recommendations for Course Creator:**

**Descriptive Sidebar Navigation:**

```html
<nav class="dashboard-sidebar">
  <div class="sidebar-section">
    <h4 class="sidebar-section-title">Content Management</h4>
    <ul class="sidebar-nav">
      <li class="sidebar-nav-item">
        <a href="#projects" class="sidebar-nav-link">
          <svg class="sidebar-nav-icon"><!-- Projects icon --></svg>
          <div class="sidebar-nav-content">
            <span class="sidebar-nav-label">Projects</span>
            <span class="sidebar-nav-desc">Manage learning paths</span>
          </div>
        </a>
      </li>
      <li class="sidebar-nav-item">
        <a href="#tracks" class="sidebar-nav-link active">
          <svg class="sidebar-nav-icon"><!-- Tracks icon --></svg>
          <div class="sidebar-nav-content">
            <span class="sidebar-nav-label">Tracks</span>
            <span class="sidebar-nav-desc">Course sequences</span>
          </div>
        </a>
      </li>
    </ul>
  </div>
</nav>
```

```css
.sidebar-nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 6px;
  transition: all 200ms ease;
}

.sidebar-nav-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-nav-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.sidebar-nav-desc {
  font-size: 12px;
  color: #9CA3AF;
}

.sidebar-nav-link.active .sidebar-nav-label {
  color: #3E215B;
  font-weight: 600;
}
```

**Priority**: ⭐⭐⭐ **MEDIUM - Enhanced Navigation**

---

### 4.2 Animations & Transitions

**Observed Patterns:**

1. **Smooth Transitions**: 200ms for most interactions
2. **Hover Effects**: Subtle lifts, color changes
3. **Page Entry**: Fade-in and slide-up for modals
4. **Loading States**: Shimmer animations for skeletons

**Animation Principles:**

```css
/* Standard timing functions */
:root {
  --transition-fast: 100ms;
  --transition-normal: 200ms;
  --transition-slow: 300ms;
  --ease-out: cubic-bezier(0.22, 0.61, 0.36, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
}

/* Hover animations */
.interactive-element {
  transition: all var(--transition-normal) var(--ease-out);
}

.interactive-element:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

/* Page transitions */
.page-enter {
  animation: fadeInUp var(--transition-slow) var(--ease-out);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Focus animations */
.form-input:focus {
  transition:
    border-color var(--transition-fast) var(--ease-out),
    box-shadow var(--transition-fast) var(--ease-out);
}
```

**Recommendations for Course Creator:**

Add subtle animations to dashboards:

```css
/* Card entry animations */
.card-grid .card {
  animation: fadeInUp 400ms ease-out backwards;
}

.card-grid .card:nth-child(1) { animation-delay: 0ms; }
.card-grid .card:nth-child(2) { animation-delay: 50ms; }
.card-grid .card:nth-child(3) { animation-delay: 100ms; }
.card-grid .card:nth-child(4) { animation-delay: 150ms; }

/* Button click feedback */
.btn:active {
  transform: scale(0.98);
}

/* Wizard step transitions */
.wizard-step-content {
  animation: fadeInRight 300ms ease-out;
}

@keyframes fadeInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
```

**Priority**: ⭐⭐ **LOW - Polish** (implement after core UX improvements)

---

### 4.3 Accessibility Considerations

**Tami's Accessibility Features** (modern standards):

1. **Semantic HTML**: Proper heading hierarchy, landmarks
2. **Focus States**: Visible focus indicators on all interactive elements
3. **Color Contrast**: WCAG AA+ compliance
4. **Keyboard Navigation**: All functions accessible via keyboard
5. **ARIA Labels**: Descriptive labels for screen readers

**Recommendations for Course Creator:**

**Accessibility Checklist:**

```html
<!-- Proper heading hierarchy -->
<h1>Organization Dashboard</h1>
  <h2>Projects</h2>
    <h3>Frontend Development</h3>
  <h2>Recent Activity</h2>

<!-- ARIA labels for icons -->
<button aria-label="Close modal" class="modal-close">
  <svg aria-hidden="true"><!-- X icon --></svg>
</button>

<!-- Skip to content link -->
<a href="#main-content" class="skip-link">
  Skip to main content
</a>

<!-- Focus visible -->
<style>
  .skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: #3E215B;
    color: #FFFFFF;
    padding: 8px 16px;
    z-index: 100;
  }

  .skip-link:focus {
    top: 0;
  }
</style>

<!-- Keyboard navigation indicators -->
<nav aria-label="Main navigation">
  <ul>
    <li><a href="#projects" tabindex="0">Projects</a></li>
    <li><a href="#tracks" tabindex="0">Tracks</a></li>
  </ul>
</nav>
```

**Focus Management:**

```css
/* Visible focus states */
*:focus-visible {
  outline: 3px solid #3E215B;
  outline-offset: 2px;
}

/* Remove focus outline for mouse users */
*:focus:not(:focus-visible) {
  outline: none;
}

/* Enhanced button focus */
.btn:focus-visible {
  outline: 3px solid rgba(62, 33, 91, 0.5);
  outline-offset: 2px;
}
```

**Priority**: ⭐⭐⭐⭐⭐ **CRITICAL - Legal Compliance**
**Note**: We already have accessibility CSS, but should enhance with Tami patterns

---

## 5. Applicability to Course Creator Platform

### 5.1 Org Admin Dashboard Adaptations

**Recommended Updates:**

1. **Color Scheme** (⭐⭐⭐⭐⭐ CRITICAL):
   ```css
   /* Replace current colors with Tami-inspired palette */
   :root {
     --primary: #3E215B;        /* Deep purple for authority */
     --accent: #F38120;         /* Orange for CTAs */
     --success: #10B981;
     --danger: #EF4444;
     --warning: #F59E0B;
     --gray-50: #F9FAFB;
     --gray-100: #F3F4F6;
     --gray-200: #E5E7EB;
     --gray-900: #111827;
   }
   ```

2. **Typography** (⭐⭐⭐⭐ HIGH):
   - Switch to Inter font
   - Establish clear type scale
   - Consistent font weights

3. **Spacing System** (⭐⭐⭐⭐⭐ CRITICAL):
   - 8px base unit
   - Generous padding (24px cards, 40px containers)
   - Vertical rhythm (64px section spacing)

4. **Card Redesign** (⭐⭐⭐⭐⭐ CRITICAL):
   - Consistent border radius (8px)
   - Hover effects (lift + shadow)
   - Clear visual hierarchy

5. **Button Consistency** (⭐⭐⭐⭐⭐ CRITICAL):
   - Primary: Orange background
   - Secondary: Purple outline
   - Danger: Red background
   - Consistent sizing and padding

**Implementation Files:**
- `/home/bbrelin/course-creator/frontend/css/components/rbac-dashboard.css`
- `/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html`

---

### 5.2 Project Creation Wizard Enhancements

**Apply Tami Patterns:**

1. **Wizard Progress Indicator** (⭐⭐⭐⭐⭐ CRITICAL):
   ```html
   <div class="wizard-progress">
     <div class="wizard-step completed">
       <div class="step-number">1</div>
       <div class="step-label">Project Basics</div>
     </div>
     <div class="wizard-step active">
       <div class="step-number">2</div>
       <div class="step-label">Tracks & Audiences</div>
     </div>
     <div class="wizard-step">
       <div class="step-number">3</div>
       <div class="step-label">Review</div>
     </div>
   </div>
   ```

2. **Form Validation** (⭐⭐⭐⭐⭐ CRITICAL):
   - Inline error messages
   - Success indicators
   - Icon feedback (checkmark/X)

3. **Progressive Disclosure** (⭐⭐⭐⭐ HIGH):
   - Show only current step
   - Expandable sections for advanced options
   - Collapsible help text

4. **Save Draft Functionality** (⭐⭐⭐ MEDIUM):
   - Auto-save indicator
   - Manual "Save Draft" button
   - Resume from saved state

**Implementation Files:**
- `/home/bbrelin/course-creator/frontend/js/modules/org-admin-projects.js`
- `/home/bbrelin/course-creator/frontend/css/components/rbac-dashboard.css`

---

### 5.3 Multi-Step Wizard Improvements

**Current Issues:**
- Steps not clearly indicated
- No save draft option
- Poor validation feedback
- Confusing navigation

**Tami-Inspired Solutions:**

1. **Clear Step Indicators** (⭐⭐⭐⭐⭐ CRITICAL):
   ```css
   .wizard-steps {
     display: flex;
     justify-content: space-between;
     padding: 24px;
     background: #F9FAFB;
     border-bottom: 1px solid #E5E7EB;
   }

   .wizard-step {
     flex: 1;
     text-align: center;
     position: relative;
   }

   .wizard-step::after {
     content: '';
     position: absolute;
     top: 16px;
     left: 50%;
     width: 100%;
     height: 2px;
     background: #E5E7EB;
     z-index: 0;
   }

   .wizard-step:last-child::after {
     display: none;
   }

   .wizard-step.completed::after {
     background: #10B981;
   }

   .step-circle {
     width: 40px;
     height: 40px;
     border-radius: 50%;
     background: #E5E7EB;
     color: #6B7280;
     display: inline-flex;
     align-items: center;
     justify-content: center;
     font-weight: 600;
     position: relative;
     z-index: 1;
   }

   .wizard-step.completed .step-circle {
     background: #10B981;
     color: #FFFFFF;
   }

   .wizard-step.active .step-circle {
     background: #3E215B;
     color: #FFFFFF;
     box-shadow: 0 0 0 4px rgba(62, 33, 91, 0.1);
   }
   ```

2. **Navigation Controls** (⭐⭐⭐⭐⭐ CRITICAL):
   ```html
   <div class="wizard-footer">
     <button class="btn-secondary" id="prev-step">
       <svg>← Back</svg>
     </button>
     <div class="wizard-footer-center">
       <button class="btn-ghost" id="save-draft">
         Save Draft
       </button>
     </div>
     <button class="btn-primary" id="next-step">
       Next →
     </button>
   </div>
   ```

3. **Step Validation** (⭐⭐⭐⭐⭐ CRITICAL):
   - Disable "Next" until current step is valid
   - Show validation errors inline
   - Highlight incomplete required fields

**Priority**: ⭐⭐⭐⭐⭐ **CRITICAL**
**Impact**: Major improvement to project creation UX

---

### 5.4 Color Scheme Enhancements

**Current Palette** (needs consistency):
- Inconsistent primary colors
- Low contrast in some areas
- No systematic color tokens

**Tami-Inspired Palette:**

```css
:root {
  /* Brand Colors */
  --color-primary-50: #F5F3FF;
  --color-primary-100: #EDE9FE;
  --color-primary-200: #DDD6FE;
  --color-primary-300: #C4B5FD;
  --color-primary-400: #A78BFA;
  --color-primary-500: #8B5CF6;
  --color-primary-600: #3E215B;   /* Primary purple */
  --color-primary-700: #6D28D9;
  --color-primary-800: #5B21B6;
  --color-primary-900: #4C1D95;

  /* Accent Colors */
  --color-accent-50: #FFF7ED;
  --color-accent-100: #FFEDD5;
  --color-accent-200: #FED7AA;
  --color-accent-300: #FDBA74;
  --color-accent-400: #FB923C;
  --color-accent-500: #F38120;    /* Orange accent */
  --color-accent-600: #EA580C;
  --color-accent-700: #C2410C;
  --color-accent-800: #9A3412;
  --color-accent-900: #7C2D12;

  /* Semantic Colors */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-danger: #EF4444;
  --color-info: #3B82F6;

  /* Neutral Colors */
  --color-gray-50: #F9FAFB;
  --color-gray-100: #F3F4F6;
  --color-gray-200: #E5E7EB;
  --color-gray-300: #D1D5DB;
  --color-gray-400: #9CA3AF;
  --color-gray-500: #6B7280;
  --color-gray-600: #4B5563;
  --color-gray-700: #374151;
  --color-gray-800: #1F2937;
  --color-gray-900: #111827;

  /* Background & Text */
  --color-background: #FFFFFF;
  --color-text-primary: #111827;
  --color-text-secondary: #6B7280;
  --color-text-tertiary: #9CA3AF;
}
```

**Usage Examples:**

```css
/* Dashboard cards */
.dashboard-card {
  background: var(--color-background);
  border: 1px solid var(--color-gray-200);
  color: var(--color-text-primary);
}

/* Primary button */
.btn-primary {
  background: var(--color-accent-500);
  color: var(--color-background);
}

.btn-primary:hover {
  background: var(--color-accent-600);
}

/* Success states */
.status-active {
  background: var(--color-success);
  color: var(--color-background);
}

/* Sidebar navigation */
.sidebar {
  background: var(--color-gray-50);
  border-right: 1px solid var(--color-gray-200);
}

.sidebar-link.active {
  background: var(--color-primary-50);
  color: var(--color-primary-600);
  border-left: 3px solid var(--color-accent-500);
}
```

**Priority**: ⭐⭐⭐⭐⭐ **CRITICAL - Foundation**
**Impact**: Consistent visual language across entire platform

---

### 5.5 Typography for Readability

**Current Issues:**
- Inconsistent font sizes
- Poor hierarchy
- Hard to scan content

**Tami Solution:**

```css
:root {
  /* Font Family */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;

  /* Font Sizes */
  --text-xs: 0.6875rem;    /* 11px */
  --text-sm: 0.8125rem;    /* 13px */
  --text-base: 0.9375rem;  /* 15px */
  --text-lg: 1rem;         /* 16px */
  --text-xl: 1.25rem;      /* 20px */
  --text-2xl: 1.5rem;      /* 24px */
  --text-3xl: 1.875rem;    /* 30px */
  --text-4xl: 2.25rem;     /* 36px */

  /* Font Weights */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  --font-extrabold: 800;

  /* Line Heights */
  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;
}

/* Application */
body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  color: var(--color-text-primary);
}

h1 {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  color: var(--color-gray-900);
}

h2 {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
}

h3 {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-snug);
}

.text-small {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.text-tiny {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Code blocks */
code, pre {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}
```

**Priority**: ⭐⭐⭐⭐ **HIGH**
**Impact**: Significantly improved readability and content hierarchy

---

## 6. Implementation Recommendations

### 6.1 Quick Wins (Implement First)

**Priority 1: CSS Variables & Color System** (1-2 hours)
- Add Tami color palette to `/frontend/css/components/rbac-dashboard.css`
- Update all component colors to use CSS variables
- Test across all dashboards

```bash
# File to update
/home/bbrelin/course-creator/frontend/css/components/rbac-dashboard.css
```

**Priority 2: Button Standardization** (2-3 hours)
- Create unified button system
- Update all buttons across dashboards
- Add hover/focus states

```bash
# Files to update
/home/bbrelin/course-creator/frontend/css/components/rbac-dashboard.css
/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html
```

**Priority 3: Form Input Styling** (2-3 hours)
- Standardize input field design
- Add focus states and validation styles
- Update all forms

```bash
# Files to update
/home/bbrelin/course-creator/frontend/css/components/rbac-dashboard.css
# All modal/wizard HTML files
```

**Priority 4: Spacing System** (1-2 hours)
- Implement 8px base spacing
- Update card padding to 24px
- Add generous vertical spacing (64px sections)

**Priority 5: Typography** (2-3 hours)
- Import Inter font
- Create type scale
- Update heading hierarchy

**Total Quick Wins Effort**: ~10-15 hours
**Impact**: Immediately modernized, consistent UI

---

### 6.2 Major Redesigns (Plan Carefully)

**Phase 1: Dashboard Overhaul** (1-2 weeks)
- Restructure org admin dashboard layout
- Implement card grid system
- Add stats overview section
- Modernize sidebar navigation

**Phase 2: Wizard Improvements** (1-2 weeks)
- Redesign project creation wizard
- Add progress indicators
- Implement save draft functionality
- Enhanced validation and error handling

**Phase 3: Component Library** (2-3 weeks)
- Build reusable component system
- Document design patterns
- Create style guide
- Implement across all dashboards

**Total Major Redesign Effort**: ~4-7 weeks
**Impact**: Professional, scalable design system

---

### 6.3 Code Examples for Immediate Use

**Complete Button System:**

```css
/* /home/bbrelin/course-creator/frontend/css/components/rbac-dashboard.css */

/* ============================================
   BUTTON SYSTEM - Tami-Inspired
   ============================================ */

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 8px;
  font-family: 'Inter', sans-serif;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 200ms cubic-bezier(0.22, 0.61, 0.36, 1);
  border: none;
  white-space: nowrap;
}

/* Primary Button - Orange CTA */
.btn-primary {
  background-color: #F38120;
  color: #FFFFFF;
}

.btn-primary:hover {
  background-color: #D86F1A;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(243, 129, 32, 0.3);
}

.btn-primary:active {
  transform: translateY(0);
}

/* Secondary Button - Purple Outline */
.btn-secondary {
  background-color: transparent;
  color: #3E215B;
  border: 2px solid #3E215B;
}

.btn-secondary:hover {
  background-color: #3E215B;
  color: #FFFFFF;
}

/* Danger Button - Red */
.btn-danger {
  background-color: #EF4444;
  color: #FFFFFF;
}

.btn-danger:hover {
  background-color: #DC2626;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

/* Success Button - Green */
.btn-success {
  background-color: #10B981;
  color: #FFFFFF;
}

.btn-success:hover {
  background-color: #059669;
}

/* Ghost Button - Text Only */
.btn-ghost {
  background: none;
  color: #3E215B;
  padding: 8px 16px;
}

.btn-ghost:hover {
  background-color: rgba(62, 33, 91, 0.05);
}

/* Button Sizes */
.btn-small {
  padding: 8px 16px;
  font-size: 13px;
}

.btn-large {
  padding: 16px 32px;
  font-size: 16px;
}

/* Button States */
.btn:disabled,
.btn[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.btn:focus-visible {
  outline: 3px solid rgba(62, 33, 91, 0.3);
  outline-offset: 2px;
}

/* Loading State */
.btn[data-loading="true"] {
  pointer-events: none;
  opacity: 0.7;
  position: relative;
}

.btn[data-loading="true"]::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #FFFFFF;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Button Icon */
.btn-icon {
  width: 20px;
  height: 20px;
}
```

**Complete Form System:**

```css
/* ============================================
   FORM SYSTEM - Tami-Inspired
   ============================================ */

.form-container {
  max-width: 600px;
  margin: 0 auto;
}

.form-field {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.form-label.required::after {
  content: " *";
  color: #EF4444;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #E5E7EB;
  border-radius: 8px;
  font-family: 'Inter', sans-serif;
  font-size: 15px;
  color: #111827;
  background-color: #FFFFFF;
  transition: all 200ms ease;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3E215B;
  box-shadow: 0 0 0 3px rgba(62, 33, 91, 0.1);
}

.form-input::placeholder {
  color: #9CA3AF;
}

.form-input.error {
  border-color: #EF4444;
}

.form-input.success {
  border-color: #10B981;
}

.form-textarea {
  min-height: 100px;
  resize: vertical;
}

.form-hint {
  display: block;
  font-size: 13px;
  color: #6B7280;
  margin-top: 6px;
  font-style: italic;
}

.form-error {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #EF4444;
  font-size: 13px;
  margin-top: 6px;
  font-weight: 500;
}

.form-error::before {
  content: '⚠';
}

.form-success {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #10B981;
  font-size: 13px;
  margin-top: 6px;
}

.form-success::before {
  content: '✓';
}

/* Checkbox & Radio */
.form-checkbox,
.form-radio {
  width: 20px;
  height: 20px;
  accent-color: #3E215B;
}

.form-checkbox-group,
.form-radio-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-checkbox-item,
.form-radio-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-checkbox-label,
.form-radio-label {
  font-size: 14px;
  color: #374151;
  cursor: pointer;
}
```

**Complete Card System:**

```css
/* ============================================
   CARD SYSTEM - Tami-Inspired
   ============================================ */

.card {
  background: #FFFFFF;
  border-radius: 8px;
  border: 1px solid #E5E7EB;
  overflow: hidden;
  transition: all 200ms ease;
}

.card:hover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #E5E7EB;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.card-action {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: #6B7280;
  transition: color 200ms ease;
}

.card-action:hover {
  color: #111827;
}

.card-body {
  padding: 24px;
}

.card-footer {
  padding: 16px 24px;
  background-color: #F9FAFB;
  border-top: 1px solid #E5E7EB;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* Stat Cards */
.stat-card {
  background: linear-gradient(135deg, #3E215B 0%, #6D28D9 100%);
  color: #FFFFFF;
  padding: 24px;
  border-radius: 8px;
  border: none;
}

.stat-card-value {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stat-card-label {
  font-size: 14px;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Interactive Cards */
.card-clickable {
  cursor: pointer;
}

.card-clickable:hover {
  border-color: #3E215B;
  box-shadow: 0 10px 30px rgba(62, 33, 91, 0.15);
  transform: translateY(-4px);
}

/* Card Grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}
```

---

### 6.4 Prioritized Implementation Roadmap

**Week 1-2: Foundation** (Quick Wins)
- [ ] Day 1-2: Implement CSS color variables
- [ ] Day 3-4: Standardize all buttons
- [ ] Day 5-6: Update form inputs
- [ ] Day 7-8: Apply spacing system
- [ ] Day 9-10: Implement typography system

**Week 3-4: Dashboard Redesign**
- [ ] Day 1-3: Org admin dashboard layout
- [ ] Day 4-6: Sidebar navigation update
- [ ] Day 7-8: Card system implementation
- [ ] Day 9-10: Testing and refinement

**Week 5-6: Wizard Enhancement**
- [ ] Day 1-3: Progress indicator component
- [ ] Day 4-6: Step-by-step validation
- [ ] Day 7-8: Save draft functionality
- [ ] Day 9-10: Error handling improvements

**Week 7-8: Polish & Consistency**
- [ ] Day 1-3: Loading states and animations
- [ ] Day 4-6: Toast notifications system
- [ ] Day 7-8: Accessibility audit and fixes
- [ ] Day 9-10: Cross-browser testing

**Total Timeline**: 8 weeks for complete implementation
**Quick Wins Timeline**: 2 weeks for 80% visual improvement

---

## 7. Conclusion & Next Steps

### 7.1 Key Takeaways

Tami's design succeeds through:

1. **Systematic Approach**: Everything uses design tokens (colors, spacing, typography)
2. **Consistency**: Same patterns repeated across entire site
3. **Clarity**: Visual hierarchy makes information easy to scan
4. **Professional Polish**: Subtle animations, generous whitespace, high contrast
5. **User-Centered**: Progressive disclosure, clear CTAs, helpful validation

### 7.2 Immediate Actions for Course Creator

**Start Here (This Week):**

1. **Implement CSS Variables** (2 hours):
   ```bash
   # Edit this file
   /home/bbrelin/course-creator/frontend/css/components/rbac-dashboard.css

   # Add Tami color palette and spacing system
   ```

2. **Standardize Buttons** (3 hours):
   ```bash
   # Update all buttons across dashboards
   # Use provided button system CSS
   ```

3. **Update Form Inputs** (3 hours):
   ```bash
   # Apply new form styling
   # Add validation states
   ```

4. **Test Visual Changes** (2 hours):
   ```bash
   # View all dashboards
   # Verify consistency
   # Check accessibility
   ```

**Next Week:**
- Dashboard layout restructuring
- Card grid implementation
- Sidebar navigation update

### 7.3 Measurement & Success Criteria

**Before Implementation:**
- Current design feels dated
- Inconsistent spacing and colors
- Poor visual hierarchy
- Confusing wizards

**After Implementation (Success Metrics):**
- ✅ Consistent color palette used throughout
- ✅ All buttons follow same design system
- ✅ Forms have clear validation feedback
- ✅ Generous whitespace improves readability
- ✅ Card grids provide organized layout
- ✅ Wizards have clear progress indicators
- ✅ Professional, modern appearance
- ✅ WCAG AA+ accessibility compliance

**User Feedback Goals:**
- "The interface feels modern and professional"
- "I can easily find what I need"
- "Creating projects is intuitive"
- "The design builds trust"

---

## Appendix: Additional Resources

### A. Files to Modify (Complete List)

**CSS Files:**
```
/home/bbrelin/course-creator/frontend/css/components/rbac-dashboard.css
/home/bbrelin/course-creator/frontend/css/components/header-footer.css
/home/bbrelin/course-creator/frontend/css/accessibility.css
```

**HTML Files:**
```
/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html
/home/bbrelin/course-creator/frontend/html/site-admin-dashboard.html
/home/bbrelin/course-creator/frontend/html/organization-registration.html
```

**JavaScript Files:**
```
/home/bbrelin/course-creator/frontend/js/modules/org-admin-core.js
/home/bbrelin/course-creator/frontend/js/modules/org-admin-projects.js
/home/bbrelin/course-creator/frontend/js/modules/org-admin-tracks.js
```

### B. Design Token Reference

```css
/* Complete Design Token System */
:root {
  /* Colors */
  --color-primary: #3E215B;
  --color-accent: #F38120;
  --color-success: #10B981;
  --color-danger: #EF4444;
  --color-warning: #F59E0B;
  --color-info: #3B82F6;

  /* Spacing (8px base) */
  --space-1: 0.5rem;   /* 8px */
  --space-2: 1rem;     /* 16px */
  --space-3: 1.5rem;   /* 24px */
  --space-4: 2rem;     /* 32px */
  --space-5: 2.5rem;   /* 40px */
  --space-6: 3rem;     /* 48px */
  --space-8: 4rem;     /* 64px */

  /* Typography */
  --font-sans: 'Inter', sans-serif;
  --text-xs: 0.6875rem;    /* 11px */
  --text-sm: 0.8125rem;    /* 13px */
  --text-base: 0.9375rem;  /* 15px */
  --text-lg: 1rem;         /* 16px */
  --text-xl: 1.25rem;      /* 20px */
  --text-2xl: 1.5rem;      /* 24px */
  --text-3xl: 1.875rem;    /* 30px */
  --text-4xl: 2.25rem;     /* 36px */

  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.15);
  --shadow-xl: 0 25px 50px rgba(0, 0, 0, 0.25);

  /* Transitions */
  --transition-fast: 100ms;
  --transition-normal: 200ms;
  --transition-slow: 300ms;
  --ease-out: cubic-bezier(0.22, 0.61, 0.36, 1);
}
```

### C. Component Checklist

Before submitting any UI work, verify:

- [ ] Uses CSS variables for all colors
- [ ] Follows 8px spacing system
- [ ] Typography uses defined scale
- [ ] Buttons follow standard patterns
- [ ] Forms have validation states
- [ ] Cards have consistent styling
- [ ] Hover states implemented
- [ ] Focus states visible (accessibility)
- [ ] Loading states included
- [ ] Error handling present
- [ ] Responsive design verified
- [ ] Cross-browser tested

---

**End of Report**

**Next Action**: Review this report with user, prioritize quick wins, begin CSS variable implementation.

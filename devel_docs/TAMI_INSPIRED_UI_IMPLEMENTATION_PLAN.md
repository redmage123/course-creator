# Tami-Inspired UI Enhancement Implementation Plan

**Date**: 2025-10-17
**Approach**: Test-Driven Development (TDD) + Parallel Agent Execution
**Goal**: Modernize Course Creator Platform UI using Tami design principles as inspiration

---

## 🎯 Executive Summary

This plan integrates Tami's design principles into the Course Creator Platform without copying their code. We'll use TDD methodology to ensure visual regression protection while modernizing our UI/UX systematically.

### Key Objectives

1. **Establish Design System Foundation** - CSS variables, typography, spacing
2. **Modernize Component Library** - Buttons, forms, cards, modals
3. **Enhance Dashboard UX** - Better hierarchy, clearer CTAs, improved navigation
4. **Implement Wizard Improvements** - Progress indicators, validation, save states
5. **Maintain Accessibility** - WCAG 2.1 AA+ compliance throughout

---

## 📋 Three-Phase Approach

### Phase 1: Foundation & Quick Wins (Week 1-2)
**Goal**: Establish design system and modernize 80% of visual appearance
**Effort**: 10-15 hours
**Impact**: Immediate professional appearance

### Phase 2: Component Enhancement (Week 3-4)
**Goal**: Rebuild core components with modern patterns
**Effort**: 2-3 weeks
**Impact**: Consistent, scalable component library

### Phase 3: Advanced UX Patterns (Week 5-8)
**Goal**: Implement sophisticated interactions and animations
**Effort**: 3-4 weeks
**Impact**: Best-in-class user experience

---

## 🔴 RED Phase: Test Suite Creation

Before making ANY visual changes, we create comprehensive visual regression tests.

### Test Strategy

**1. Visual Snapshot Tests** (Selenium + Screenshot Comparison)
```python
# tests/visual/test_tami_ui_baseline.py
class TestTamiUIBaseline:
    """Baseline visual regression tests before Tami UI integration"""

    def test_org_admin_dashboard_baseline(self):
        """Capture baseline of org admin dashboard"""
        # Navigate to dashboard
        # Take full-page screenshot
        # Save as baseline for comparison

    def test_button_states_baseline(self):
        """Capture all button states (default, hover, active, disabled)"""

    def test_form_inputs_baseline(self):
        """Capture all form input states"""

    def test_card_grid_baseline(self):
        """Capture card layouts"""

    def test_wizard_flow_baseline(self):
        """Capture project creation wizard steps"""
```

**2. CSS Token Tests**
```python
# tests/unit/css/test_design_tokens.py
class TestDesignTokens:
    """Verify CSS variables are properly defined"""

    def test_color_palette_defined(self):
        """All Tami-inspired colors in CSS variables"""

    def test_spacing_system_8px_base(self):
        """Spacing follows 8px base unit system"""

    def test_typography_scale_complete(self):
        """All font sizes defined in scale"""
```

**3. Accessibility Tests**
```python
# tests/accessibility/test_tami_ui_accessibility.py
class TestTamiUIAccessibility:
    """Ensure Tami patterns maintain WCAG AA+ compliance"""

    def test_color_contrast_ratios(self):
        """Purple/Orange meet WCAG AA contrast requirements"""

    def test_focus_states_visible(self):
        """All interactive elements have visible focus"""

    def test_button_touch_targets(self):
        """Buttons meet 44px minimum touch target"""
```

**4. Component API Tests**
```javascript
// tests/unit/frontend/test_tami_components.test.js
describe('Tami-Inspired Components', () => {
    describe('Button Component', () => {
        it('should support primary, secondary, danger variants', () => {});
        it('should handle loading state', () => {});
        it('should support small, default, large sizes', () => {});
    });

    describe('Form Input Component', () => {
        it('should show error state with red border', () => {});
        it('should show success state with green border', () => {});
        it('should display validation message', () => {});
    });
});
```

### RED Phase Tasks (Parallel Execution)

**Task Group 1: Visual Baseline Capture**
- Task 1: Dashboard baseline screenshots (org admin, site admin, instructor, student)
- Task 2: Component baseline screenshots (buttons, forms, cards, modals)
- Task 3: Navigation baseline screenshots (sidebar, header, breadcrumbs)

**Task Group 2: Test Infrastructure**
- Task 4: Visual regression test framework setup
- Task 5: CSS token extraction utility
- Task 6: Accessibility audit baseline

**Expected Output**: 60-80 failing tests (no Tami patterns implemented yet)

---

## 🟢 GREEN Phase: Implementation by Priority

### PHASE 1: Foundation & Quick Wins (CRITICAL - Week 1-2)

#### 1.1 Design Token System (Day 1-2)

**File**: `/frontend/css/base/variables.css`

**TDD Approach**:
```javascript
// Test FIRST
describe('CSS Design Tokens', () => {
    it('should define Tami color palette', () => {
        expect(getCSSVariable('--color-primary')).toBe('#3E215B');
        expect(getCSSVariable('--color-accent')).toBe('#F38120');
    });

    it('should define 8px spacing system', () => {
        expect(getCSSVariable('--space-1')).toBe('0.5rem'); // 8px
        expect(getCSSVariable('--space-2')).toBe('1rem');   // 16px
    });
});
```

**Implementation** (make tests pass):
```css
:root {
    /* Tami-Inspired Brand Colors */
    --color-primary: #3E215B;        /* Deep purple */
    --color-accent: #F38120;         /* Vibrant orange */
    --color-success: #10B981;
    --color-danger: #EF4444;
    --color-warning: #F59E0B;

    /* Neutral Palette */
    --color-gray-50: #F9FAFB;
    --color-gray-100: #F3F4F6;
    --color-gray-200: #E5E7EB;
    --color-gray-300: #D1D5DB;
    --color-gray-500: #6B7280;
    --color-gray-900: #111827;

    /* Spacing (8px base unit) */
    --space-1: 0.5rem;   /* 8px */
    --space-2: 1rem;     /* 16px */
    --space-3: 1.5rem;   /* 24px */
    --space-4: 2rem;     /* 32px */
    --space-5: 2.5rem;   /* 40px */
    --space-8: 4rem;     /* 64px */

    /* Typography */
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --text-xs: 0.6875rem;    /* 11px */
    --text-sm: 0.8125rem;    /* 13px */
    --text-base: 0.9375rem;  /* 15px */
    --text-xl: 1.25rem;      /* 20px */
    --text-2xl: 1.5rem;      /* 24px */
    --text-3xl: 1.875rem;    /* 30px */
    --text-4xl: 2.25rem;     /* 36px */

    /* Border Radius */
    --radius-md: 8px;
    --radius-lg: 12px;

    /* Shadows */
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.15);

    /* Transitions */
    --transition-normal: 200ms;
    --ease-out: cubic-bezier(0.22, 0.61, 0.36, 1);
}
```

**Priority**: ⭐⭐⭐⭐⭐ CRITICAL (Foundation for everything)

---

#### 1.2 Typography System (Day 3-4)

**File**: `/frontend/css/utilities/typography.css`

**TDD Test**:
```javascript
it('should load Inter font', () => {
    expect(document.fonts.check('15px Inter')).toBe(true);
});

it('should apply consistent heading hierarchy', () => {
    const h1 = document.querySelector('h1');
    expect(getComputedStyle(h1).fontSize).toBe('36px');
    expect(getComputedStyle(h1).fontWeight).toBe('700');
});
```

**Implementation**:
```css
/* Import Inter font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

body {
    font-family: var(--font-sans);
    font-size: var(--text-base);
    line-height: 1.5;
    color: var(--color-gray-900);
}

h1 {
    font-size: var(--text-4xl);
    font-weight: 700;
    line-height: 1.2;
    color: var(--color-gray-900);
    margin-bottom: var(--space-3);
}

h2 {
    font-size: var(--text-3xl);
    font-weight: 700;
    line-height: 1.3;
    margin-bottom: var(--space-2);
}

h3 {
    font-size: var(--text-2xl);
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: var(--space-2);
}
```

**Priority**: ⭐⭐⭐⭐ HIGH

---

#### 1.3 Button Component System (Day 5-6)

**File**: `/frontend/css/components/buttons.css`

**TDD Test Suite**:
```python
# tests/e2e/test_tami_buttons.py
class TestTamiButtons:
    def test_primary_button_orange_background(self):
        """Primary buttons use Tami orange (#F38120)"""
        btn = self.driver.find_element(By.CSS_SELECTOR, '.btn-primary')
        bg_color = btn.value_of_css_property('background-color')
        assert bg_color == 'rgb(243, 129, 32)'  # #F38120

    def test_secondary_button_purple_outline(self):
        """Secondary buttons have purple outline"""
        btn = self.driver.find_element(By.CSS_SELECTOR, '.btn-secondary')
        border_color = btn.value_of_css_property('border-color')
        assert border_color == 'rgb(62, 33, 91)'  # #3E215B

    def test_button_hover_lift_effect(self):
        """Buttons lift on hover"""
        btn = self.driver.find_element(By.CSS_SELECTOR, '.btn-primary')
        ActionChains(self.driver).move_to_element(btn).perform()
        time.sleep(0.3)  # Wait for transition
        transform = btn.value_of_css_property('transform')
        assert 'translateY(-1px)' in transform

    def test_button_loading_state(self):
        """Buttons show spinner when loading"""
        btn = self.driver.find_element(By.CSS_SELECTOR, '.btn-primary[data-loading="true"]')
        spinner = btn.find_element(By.CSS_SELECTOR, '::after')
        assert spinner is not None

    def test_disabled_button_not_clickable(self):
        """Disabled buttons ignore clicks"""
        btn = self.driver.find_element(By.CSS_SELECTOR, '.btn-primary:disabled')
        assert btn.get_attribute('disabled') == 'true'
        assert 'not-allowed' in btn.value_of_css_property('cursor')
```

**Implementation**:
```css
/* Tami-Inspired Button System */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 24px;
    border-radius: var(--radius-md);
    font-family: var(--font-sans);
    font-size: var(--text-base);
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-normal) var(--ease-out);
    border: none;
}

/* Primary - Orange CTA (Tami pattern) */
.btn-primary {
    background-color: var(--color-accent);
    color: #FFFFFF;
}

.btn-primary:hover {
    background-color: #D86F1A;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(243, 129, 32, 0.3);
}

/* Secondary - Purple Outline (Tami pattern) */
.btn-secondary {
    background-color: transparent;
    color: var(--color-primary);
    border: 2px solid var(--color-primary);
}

.btn-secondary:hover {
    background-color: var(--color-primary);
    color: #FFFFFF;
}

/* Danger - Keep existing red */
.btn-danger {
    background-color: var(--color-danger);
    color: #FFFFFF;
}

/* States */
.btn:disabled {
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
```

**HTML Updates Required**:
```html
<!-- Before -->
<button class="create-project-btn">Create Project</button>

<!-- After (Tami-inspired) -->
<button class="btn btn-primary">
    <svg class="btn-icon"><!-- Icon --></svg>
    Create Project
</button>
```

**Priority**: ⭐⭐⭐⭐⭐ CRITICAL

---

#### 1.4 Form Input System (Day 7-8)

**File**: `/frontend/css/components/forms.css`

**TDD Test Suite**:
```python
class TestTamiFormInputs:
    def test_input_purple_focus_border(self):
        """Inputs show purple border on focus"""
        input_field = self.driver.find_element(By.CSS_SELECTOR, '.form-input')
        input_field.click()
        border_color = input_field.value_of_css_property('border-color')
        assert border_color == 'rgb(62, 33, 91)'

    def test_error_input_red_border(self):
        """Error inputs have red border"""
        input_field = self.driver.find_element(By.CSS_SELECTOR, '.form-input.error')
        border_color = input_field.value_of_css_property('border-color')
        assert border_color == 'rgb(239, 68, 68)'

    def test_validation_message_displays(self):
        """Validation messages appear below inputs"""
        error_msg = self.driver.find_element(By.CSS_SELECTOR, '.form-error')
        assert error_msg.is_displayed()
        assert '⚠' in error_msg.text
```

**Implementation**:
```css
/* Tami-Inspired Form System */
.form-field {
    margin-bottom: var(--space-3);
}

.form-label {
    display: block;
    font-size: var(--text-sm);
    font-weight: 600;
    color: #374151;
    margin-bottom: 8px;
}

.form-label.required::after {
    content: " *";
    color: var(--color-danger);
}

.form-input,
.form-select,
.form-textarea {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid var(--color-gray-200);
    border-radius: var(--radius-md);
    font-family: var(--font-sans);
    font-size: var(--text-base);
    color: var(--color-gray-900);
    background-color: #FFFFFF;
    transition: all var(--transition-normal) ease;
}

/* Tami purple focus state */
.form-input:focus,
.form-select:focus,
.form-textarea:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(62, 33, 91, 0.1);
}

/* Error state */
.form-input.error {
    border-color: var(--color-danger);
}

.form-error {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-danger);
    font-size: var(--text-sm);
    margin-top: 6px;
    font-weight: 500;
}

.form-error::before {
    content: '⚠';
}

/* Success state */
.form-input.success {
    border-color: var(--color-success);
}

.form-success {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-success);
    font-size: var(--text-sm);
    margin-top: 6px;
}

.form-success::before {
    content: '✓';
}
```

**Priority**: ⭐⭐⭐⭐⭐ CRITICAL

---

#### 1.5 Card Component System (Day 9-10)

**File**: `/frontend/css/components/cards.css`

**TDD Test**:
```python
class TestTamiCards:
    def test_card_hover_lift_effect(self):
        """Cards lift on hover"""
        card = self.driver.find_element(By.CSS_SELECTOR, '.card')
        ActionChains(self.driver).move_to_element(card).perform()
        time.sleep(0.3)
        transform = card.value_of_css_property('transform')
        assert 'translateY(-2px)' in transform

    def test_stat_card_purple_gradient(self):
        """Stat cards use Tami purple gradient"""
        stat_card = self.driver.find_element(By.CSS_SELECTOR, '.stat-card')
        bg = stat_card.value_of_css_property('background-image')
        assert '#3E215B' in bg or 'rgb(62, 33, 91)' in bg
```

**Implementation**:
```css
/* Tami-Inspired Card System */
.card {
    background: #FFFFFF;
    border-radius: var(--radius-md);
    border: 1px solid var(--color-gray-200);
    overflow: hidden;
    transition: all var(--transition-normal) var(--ease-out);
}

.card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid var(--color-gray-200);
}

.card-title {
    font-size: var(--text-xl);
    font-weight: 600;
    color: var(--color-gray-900);
    margin: 0;
}

.card-body {
    padding: var(--space-3);
}

/* Stat Cards with Tami purple gradient */
.stat-card {
    background: linear-gradient(135deg, var(--color-primary) 0%, #6D28D9 100%);
    color: #FFFFFF;
    padding: var(--space-3);
    border-radius: var(--radius-md);
    border: none;
}

.stat-card-value {
    font-size: var(--text-4xl);
    font-weight: 700;
    margin-bottom: 8px;
}

.stat-card-label {
    font-size: 14px;
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Interactive cards */
.card-clickable {
    cursor: pointer;
}

.card-clickable:hover {
    border-color: var(--color-primary);
    box-shadow: 0 10px 30px rgba(62, 33, 91, 0.15);
    transform: translateY(-4px);
}

/* Card Grid */
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: var(--space-3);
}
```

**Priority**: ⭐⭐⭐⭐⭐ CRITICAL

---

### PHASE 2: Component Enhancement (Week 3-4)

#### 2.1 Modal & Dialog System

**TDD Tests**:
```python
class TestTamiModals:
    def test_modal_fade_in_animation(self):
        """Modals fade in smoothly"""

    def test_wizard_progress_indicator(self):
        """Wizard shows step progress"""

    def test_save_draft_button_present(self):
        """Wizards have save draft functionality"""
```

**Implementation Focus**:
- Redesign project creation wizard with step indicators
- Add backdrop blur effect
- Implement smooth animations
- Save draft functionality

**Priority**: ⭐⭐⭐⭐ HIGH

---

#### 2.2 Navigation Patterns

**TDD Tests**:
```python
class TestTamiNavigation:
    def test_sidebar_active_state_orange_accent(self):
        """Active nav items have orange left border"""

    def test_nav_items_have_descriptions(self):
        """Nav items show descriptive text"""
```

**Implementation Focus**:
- Modernize sidebar navigation
- Add hover states
- Implement active state with orange accent
- Add descriptive labels (Tami pattern)

**Priority**: ⭐⭐⭐⭐ HIGH

---

#### 2.3 Loading States & Feedback

**TDD Tests**:
```python
class TestTamiLoadingStates:
    def test_skeleton_loader_displays(self):
        """Skeleton screens show during loading"""

    def test_toast_notification_appears(self):
        """Success/error toasts appear"""
```

**Implementation Focus**:
- Skeleton screens for cards
- Button loading spinners
- Toast notification system
- Progress bars

**Priority**: ⭐⭐⭐⭐ HIGH

---

### PHASE 3: Advanced UX Patterns (Week 5-8)

#### 3.1 Progressive Disclosure

**Implementation**:
- Expandable card details on hover
- Collapsible advanced options in forms
- Dropdown menu enhancements

**Priority**: ⭐⭐⭐ MEDIUM

---

#### 3.2 Animations & Polish

**Implementation**:
- Staggered card entry animations
- Smooth page transitions
- Micro-interactions on buttons
- Hover lift effects

**Priority**: ⭐⭐ LOW (polish)

---

## 🔵 REFACTOR Phase: Optimization & Documentation

After GREEN phase passes all tests:

1. **Extract Reusable Components**
   - Create shared CSS utilities
   - Document component API
   - Build style guide

2. **Performance Optimization**
   - Minimize CSS
   - Remove unused styles
   - Optimize animations

3. **Documentation**
   - Component usage guide
   - Design token reference
   - Migration guide for developers

---

## 🚀 Parallel Task Execution Plan

### Wave 1: Foundation (Days 1-2)
- **Task 1**: Write CSS token tests + implement design tokens
- **Task 2**: Write typography tests + implement Inter font system
- **Task 3**: Capture visual baseline screenshots (all dashboards)
- **Task 4**: Setup visual regression test framework

### Wave 2: Core Components (Days 3-6)
- **Task 5**: Button system (TDD: tests → implementation)
- **Task 6**: Form input system (TDD: tests → implementation)
- **Task 7**: Card system (TDD: tests → implementation)
- **Task 8**: Update org admin dashboard HTML to use new components

### Wave 3: Advanced Components (Days 7-10)
- **Task 9**: Modal/Dialog system (TDD)
- **Task 10**: Navigation modernization (TDD)
- **Task 11**: Loading states & feedback (TDD)
- **Task 12**: Update site admin dashboard HTML

### Wave 4: Wizard Enhancement (Week 3)
- **Task 13**: Wizard progress indicator component (TDD)
- **Task 14**: Step validation system (TDD)
- **Task 15**: Save draft functionality (TDD)
- **Task 16**: Project creation wizard HTML updates

### Wave 5: Polish & Documentation (Week 4)
- **Task 17**: Animation polish
- **Task 18**: Accessibility audit fixes
- **Task 19**: Component documentation
- **Task 20**: Migration guide for developers

---

## ✅ Success Criteria

### Phase 1 Complete When:
- [ ] All design tokens defined and tested
- [ ] Inter font loading successfully
- [ ] All buttons use Tami color scheme
- [ ] All forms have purple focus states
- [ ] All cards have hover lift effects
- [ ] Visual regression tests pass
- [ ] Accessibility tests pass (WCAG AA+)

### Phase 2 Complete When:
- [ ] Modals have smooth animations
- [ ] Wizard shows progress indicators
- [ ] Navigation has active state styling
- [ ] Loading states implemented everywhere
- [ ] Toast notifications working

### Phase 3 Complete When:
- [ ] Progressive disclosure patterns implemented
- [ ] Animations add polish without hindering UX
- [ ] Component documentation complete
- [ ] Developer migration guide published

---

## 📊 Measurement & Tracking

### Visual Regression Metrics
- **Baseline**: Current screenshots captured
- **Target**: < 5% unintended visual changes
- **Tool**: Selenium + Percy/BackstopJS

### Accessibility Metrics
- **Baseline**: Current WCAG compliance score
- **Target**: 100% WCAG 2.1 AA compliance
- **Tool**: axe-core, WAVE

### Performance Metrics
- **Baseline**: Current CSS size
- **Target**: < 10% size increase
- **Tool**: Lighthouse, Bundle Analyzer

### User Feedback (Post-Launch)
- "Interface feels modern and professional" - 80%+ positive
- "Easy to find what I need" - 85%+ positive
- "Forms are intuitive" - 90%+ positive

---

## 📁 Files to Modify

### CSS Files (Create/Update)
```
/frontend/css/base/variables.css           (NEW - Design tokens)
/frontend/css/utilities/typography.css     (UPDATE - Inter font)
/frontend/css/components/buttons.css       (NEW - Tami button system)
/frontend/css/components/forms.css         (NEW - Tami form system)
/frontend/css/components/cards.css         (UPDATE - Hover effects)
/frontend/css/components/modals.css        (UPDATE - Animations)
/frontend/css/components/navigation.css    (UPDATE - Active states)
/frontend/css/components/loading.css       (NEW - Skeletons, spinners)
```

### HTML Files (Update)
```
/frontend/html/org-admin-dashboard.html
/frontend/html/site-admin-dashboard.html
/frontend/html/instructor-dashboard.html
/frontend/html/student-dashboard.html
/frontend/html/project-dashboard.html
```

### JavaScript Files (Minor Updates)
```
/frontend/js/modules/org-admin-core.js     (Loading states)
/frontend/js/modules/org-admin-projects.js (Wizard progress)
/frontend/js/modules/form-validation.js    (Error display)
```

### Test Files (Create)
```
/tests/visual/test_tami_baseline.py
/tests/e2e/test_tami_buttons.py
/tests/e2e/test_tami_forms.py
/tests/e2e/test_tami_cards.py
/tests/e2e/test_tami_wizard.py
/tests/accessibility/test_tami_wcag.py
/tests/unit/css/test_design_tokens.py
```

---

## 🎯 Quick Start Checklist

**Before Starting:**
- [ ] Review Tami analysis report (`/docs/TAMI_UI_UX_ANALYSIS.md`)
- [ ] Capture current UI screenshots (baseline)
- [ ] Setup visual regression test framework
- [ ] Create design token plan

**Week 1 Goals:**
- [ ] Design tokens implemented
- [ ] Typography system live
- [ ] Button system complete
- [ ] Form inputs styled
- [ ] Card system enhanced

**Week 2 Goals:**
- [ ] All dashboards using new components
- [ ] Visual regression tests passing
- [ ] Accessibility maintained
- [ ] First stakeholder demo

---

## 📝 Notes & Principles

### Design Philosophy (Inspired by Tami)

1. **Systematic Consistency**: Everything uses design tokens
2. **Generous Whitespace**: Don't cram content
3. **Clear Hierarchy**: Make scanning easy
4. **Subtle Polish**: Animations enhance, don't distract
5. **User-Centered**: Progressive disclosure, clear CTAs
6. **Accessibility First**: WCAG AA+ non-negotiable

### Development Principles

1. **TDD First**: Write tests before implementation
2. **Parallel Execution**: Use multiple agents for speed
3. **Visual Regression**: Protect against unintended changes
4. **Incremental**: Small, testable changes
5. **Documentation**: Comment WHY, not just WHAT

---

**Next Action**: Review this plan, approve phases, then launch parallel agent tasks for Phase 1 Foundation.

# Tami-Inspired UI Enhancement - Final Implementation Plan

**Date**: 2025-10-17
**Approach**: Test-Driven Development (TDD) + Parallel Agent Execution
**Deployment**: Feature Flag Controlled
**Review Cadence**: After Each Wave (5 review points)

---

## ✅ Confirmed Decisions

1. **Colors**: KEEP existing blue/slate color scheme (#2563eb primary)
2. **Risk**: REPLACE existing styles (clean, aggressive approach)
3. **Reviews**: AFTER EACH WAVE (5 review checkpoints)
4. **Deploy**: FEATURE FLAG (can toggle on/off)

---

## 🎨 What We're Adopting from Tami

### ✅ Adopting (Tami Patterns)
- **Spacing System**: 8px base unit, generous whitespace
- **Typography**: Inter font, clear hierarchy
- **Hover Effects**: Lift animations, subtle shadows
- **Form Patterns**: Clear validation states, purple focus rings
- **Card Design**: Consistent radius, hover lift
- **Modal Animations**: Smooth fade-in, backdrop blur
- **Wizard Progress**: Step indicators, save draft
- **Loading States**: Skeletons, spinners, toasts
- **Progressive Disclosure**: Expandable details

### ❌ NOT Adopting (Tami Colors)
- ~~Purple primary (#3E215B)~~ → Keep our blue (#2563eb)
- ~~Orange accent (#F38120)~~ → Keep our existing colors
- We KEEP all existing colors:
  - Primary: #2563eb (blue)
  - Secondary: #64748b (slate)
  - Success: #059669 (green)
  - Warning: #d97706 (amber)
  - Danger: #dc2626 (red)
  - Info: #0891b2 (cyan)

---

## 🚩 Feature Flag Architecture

### Implementation Strategy

**Feature Flag**: `ENABLE_TAMI_UI`

```javascript
// /frontend/js/config-global.js
window.courseCreator = window.courseCreator || {};
window.courseCreator.featureFlags = {
    ENABLE_TAMI_UI: false // Toggle to enable Tami UI patterns
};
```

**CSS Loading**:
```html
<!-- /frontend/html/includes/head.html -->
<link rel="stylesheet" href="/css/base/variables.css">
<link rel="stylesheet" href="/css/base/reset.css">

<!-- Conditional Tami UI CSS -->
<script>
if (window.courseCreator?.featureFlags?.ENABLE_TAMI_UI) {
    const tamiCSS = document.createElement('link');
    tamiCSS.rel = 'stylesheet';
    tamiCSS.href = '/css/tami/tami-enhancements.css';
    document.head.appendChild(tamiCSS);
}
</script>

<!-- Legacy CSS (loaded if flag disabled) -->
<link rel="stylesheet" href="/css/legacy/main.css"
      data-legacy-css>
```

**Benefits**:
- ✅ Can enable/disable instantly
- ✅ A/B testing capability
- ✅ Easy rollback if issues found
- ✅ Gradual rollout to users
- ✅ Compare old vs new side-by-side

---

## 📋 Three-Phase Approach (8 Weeks)

### Phase 1: Foundation & Quick Wins (Week 1-2)
**Goal**: Tami patterns with OUR colors
**Effort**: 10-15 hours
**Impact**: 80% visual improvement

### Phase 2: Component Enhancement (Week 3-4)
**Goal**: Advanced components (modals, wizards, navigation)
**Effort**: 2-3 weeks
**Impact**: Complete component library

### Phase 3: Advanced UX (Week 5-8)
**Goal**: Animations, progressive disclosure, polish
**Effort**: 3-4 weeks
**Impact**: Best-in-class UX

---

## 🔴 RED Phase: Test Suite Creation

### Test Files Structure

```
/tests/tami/
├── visual/
│   ├── test_baseline_capture.py           # Capture current state
│   ├── test_tami_dashboards.py            # Dashboard visual regression
│   └── test_tami_components.py            # Component visual regression
├── e2e/
│   ├── test_tami_buttons.py               # Button interactions
│   ├── test_tami_forms.py                 # Form validation
│   ├── test_tami_cards.py                 # Card hover effects
│   ├── test_tami_modals.py                # Modal animations
│   └── test_tami_wizard.py                # Wizard progress
├── unit/
│   ├── test_design_tokens.py              # CSS variable validation
│   └── test_feature_flag.py               # Feature flag toggling
└── accessibility/
    └── test_tami_wcag.py                  # WCAG compliance
```

### Visual Baseline Tests

```python
# tests/tami/visual/test_baseline_capture.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class TestTamiVisualBaseline:
    """Capture baseline screenshots before Tami UI implementation"""

    @pytest.fixture
    def driver(self):
        """Setup headless Chrome driver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--window-size=1920,1080')
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()

    def test_org_admin_dashboard_baseline(self, driver):
        """Capture org admin dashboard baseline"""
        driver.get('https://localhost:3000/html/org-admin-dashboard.html')
        time.sleep(2)  # Wait for render
        driver.save_screenshot('tests/tami/baseline/org-admin-dashboard.png')

    def test_button_states_baseline(self, driver):
        """Capture all button states"""
        driver.get('https://localhost:3000/html/org-admin-dashboard.html')

        # Primary button
        btn = driver.find_element(By.CSS_SELECTOR, '.btn-primary')
        btn.screenshot('tests/tami/baseline/button-primary-default.png')

        # Hover state (via JS since Selenium can't hover in headless)
        driver.execute_script("arguments[0].classList.add('hover');", btn)
        btn.screenshot('tests/tami/baseline/button-primary-hover.png')

    def test_form_inputs_baseline(self, driver):
        """Capture form input states"""
        driver.get('https://localhost:3000/html/org-admin-dashboard.html')

        # Open project creation modal
        create_btn = driver.find_element(By.ID, 'create-project-btn')
        create_btn.click()
        time.sleep(0.5)

        # Capture form
        modal = driver.find_element(By.CSS_SELECTOR, '.modal')
        modal.screenshot('tests/tami/baseline/form-inputs.png')
```

### Feature Flag Tests

```python
# tests/tami/unit/test_feature_flag.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

class TestTamiFeatureFlag:
    """Verify feature flag controls Tami UI loading"""

    def test_tami_css_not_loaded_when_flag_disabled(self, driver):
        """Tami CSS should not load when flag is false"""
        driver.get('https://localhost:3000/html/org-admin-dashboard.html')

        # Check that Tami CSS is NOT present
        tami_links = driver.find_elements(By.CSS_SELECTOR,
            'link[href*="tami-enhancements.css"]')
        assert len(tami_links) == 0

    def test_tami_css_loaded_when_flag_enabled(self, driver):
        """Tami CSS should load when flag is true"""
        # Enable feature flag
        driver.execute_script("""
            window.courseCreator = window.courseCreator || {};
            window.courseCreator.featureFlags = { ENABLE_TAMI_UI: true };
        """)

        driver.get('https://localhost:3000/html/org-admin-dashboard.html')

        # Check that Tami CSS IS present
        tami_links = driver.find_elements(By.CSS_SELECTOR,
            'link[href*="tami-enhancements.css"]')
        assert len(tami_links) == 1

    def test_can_toggle_feature_flag_at_runtime(self, driver):
        """Feature flag can be toggled without page reload"""
        driver.get('https://localhost:3000/html/org-admin-dashboard.html')

        # Enable flag
        driver.execute_script("""
            window.courseCreator.featureFlags.ENABLE_TAMI_UI = true;
            window.dispatchEvent(new CustomEvent('tamiUIToggle'));
        """)

        time.sleep(0.5)

        # Verify Tami styles applied
        btn = driver.find_element(By.CSS_SELECTOR, '.btn-primary')
        transform_style = btn.value_of_css_property('transition')
        assert 'transform' in transform_style  # Tami adds transform transitions
```

---

## 🟢 GREEN Phase: Implementation (8 Weeks, 5 Waves)

### WAVE 1: Foundation (Days 1-2) ⭐⭐⭐⭐⭐ CRITICAL

**Review Checkpoint**: End of Day 2

#### Task 1: Design Token System
**File**: `/frontend/css/tami/00-design-tokens.css`

**TDD Test**:
```python
def test_tami_spacing_tokens_defined():
    """Verify 8px spacing system defined"""
    vars = get_css_variables()
    assert vars['--tami-space-1'] == '8px'
    assert vars['--tami-space-2'] == '16px'
    assert vars['--tami-space-3'] == '24px'

def test_keeps_existing_colors():
    """Verify we're NOT changing color scheme"""
    vars = get_css_variables()
    assert vars['--primary-color'] == '#2563eb'  # Keep blue
    assert '--color-primary' not in vars  # Don't add Tami purple
```

**Implementation**:
```css
/* /frontend/css/tami/00-design-tokens.css */
/**
 * Tami-Inspired Design Tokens
 *
 * BUSINESS CONTEXT:
 * Adopts Tami's systematic spacing and typography patterns
 * while KEEPING our existing blue/slate color scheme.
 *
 * WHY WE'RE DOING THIS:
 * - 8px spacing creates visual rhythm and consistency
 * - Inter font improves readability
 * - Systematic tokens prevent arbitrary values
 *
 * WHAT WE'RE NOT CHANGING:
 * - Brand colors (keeping #2563eb blue)
 * - Semantic color meanings
 */

:root {
    /* Tami Spacing System (8px base unit) */
    --tami-space-1: 8px;
    --tami-space-2: 16px;
    --tami-space-3: 24px;
    --tami-space-4: 32px;
    --tami-space-5: 40px;
    --tami-space-6: 48px;
    --tami-space-8: 64px;
    --tami-space-10: 80px;

    /* Tami Typography (Inter font) */
    --tami-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --tami-text-xs: 11px;
    --tami-text-sm: 13px;
    --tami-text-base: 15px;   /* Tami's body size */
    --tami-text-lg: 16px;
    --tami-text-xl: 20px;
    --tami-text-2xl: 24px;
    --tami-text-3xl: 30px;
    --tami-text-4xl: 36px;

    /* Tami Shadows */
    --tami-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --tami-shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
    --tami-shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.15);
    --tami-shadow-xl: 0 25px 50px rgba(0, 0, 0, 0.25);

    /* Tami Border Radius */
    --tami-radius-sm: 4px;
    --tami-radius-md: 8px;
    --tami-radius-lg: 12px;

    /* Tami Transitions */
    --tami-transition-fast: 100ms;
    --tami-transition-normal: 200ms;
    --tami-transition-slow: 300ms;
    --tami-ease-out: cubic-bezier(0.22, 0.61, 0.36, 1);

    /* Map Tami patterns to OUR colors */
    --tami-color-primary: var(--primary-color);        /* #2563eb blue */
    --tami-color-accent: var(--primary-hover);         /* #1d4ed8 darker blue */
    --tami-color-success: var(--success-color);        /* #059669 green */
    --tami-color-danger: var(--danger-color);          /* #dc2626 red */
    --tami-color-gray-50: var(--gray-50);
    --tami-color-gray-100: var(--gray-100);
    --tami-color-gray-200: var(--gray-200);
    --tami-color-gray-500: var(--gray-500);
    --tami-color-gray-900: var(--gray-900);
}
```

**Priority**: ⭐⭐⭐⭐⭐ CRITICAL

---

#### Task 2: Typography System
**File**: `/frontend/css/tami/01-typography.css`

**TDD Test**:
```python
def test_inter_font_loaded():
    """Inter font should load successfully"""
    driver.get('https://localhost:3000')
    fonts_loaded = driver.execute_script(
        "return document.fonts.check('15px Inter')"
    )
    assert fonts_loaded == True

def test_heading_hierarchy():
    """Headings should follow Tami scale"""
    driver.get('https://localhost:3000/html/org-admin-dashboard.html')
    h1 = driver.find_element(By.TAG_NAME, 'h1')
    assert h1.value_of_css_property('font-size') == '36px'  # --tami-text-4xl
```

**Implementation**:
```css
/* /frontend/css/tami/01-typography.css */
/**
 * Tami-Inspired Typography System
 *
 * BUSINESS CONTEXT:
 * Educational platforms need excellent readability.
 * Inter font provides better legibility than system fonts.
 *
 * WHY INTER FONT:
 * - Designed for UI (better than Helvetica/Arial)
 * - Excellent readability at small sizes
 * - Modern, professional appearance
 * - Free and widely supported
 */

/* Import Inter font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Only apply when Tami UI enabled */
[data-tami-ui="enabled"] body {
    font-family: var(--tami-font-sans);
    font-size: var(--tami-text-base);  /* 15px */
    line-height: 1.5;
}

[data-tami-ui="enabled"] h1 {
    font-size: var(--tami-text-4xl);  /* 36px */
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: var(--tami-space-3);  /* 24px */
}

[data-tami-ui="enabled"] h2 {
    font-size: var(--tami-text-3xl);  /* 30px */
    font-weight: 700;
    line-height: 1.3;
    margin-bottom: var(--tami-space-2);  /* 16px */
}

[data-tami-ui="enabled"] h3 {
    font-size: var(--tami-text-2xl);  /* 24px */
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: var(--tami-space-2);
}

[data-tami-ui="enabled"] p {
    margin-bottom: var(--tami-space-2);
    line-height: 1.6;
}

[data-tami-ui="enabled"] small,
[data-tami-ui="enabled"] .text-small {
    font-size: var(--tami-text-sm);  /* 13px */
}
```

**Priority**: ⭐⭐⭐⭐ HIGH

---

#### Task 3: Visual Baseline Capture
**Script**: `/tests/tami/scripts/capture_baselines.sh`

```bash
#!/bin/bash
# Capture all baseline screenshots before Tami UI implementation

echo "Capturing visual baselines..."

# Ensure test directory exists
mkdir -p tests/tami/baseline

# Run baseline capture tests
pytest tests/tami/visual/test_baseline_capture.py \
    --screenshot-dir=tests/tami/baseline \
    -v

echo "✅ Baselines captured in tests/tami/baseline/"
ls -lh tests/tami/baseline/
```

**Deliverables**:
- 50+ baseline screenshots
- All dashboards captured
- All component states captured

**Priority**: ⭐⭐⭐⭐⭐ CRITICAL

---

#### Task 4: Feature Flag Setup
**Files**:
- `/frontend/js/tami-feature-flag.js`
- `/frontend/html/includes/head-tami.html`

**Implementation**:
```javascript
// /frontend/js/tami-feature-flag.js
/**
 * Tami UI Feature Flag System
 *
 * BUSINESS CONTEXT:
 * Allows toggling Tami UI on/off without code deployment.
 * Enables A/B testing and gradual rollout.
 *
 * USAGE:
 * - Set in localStorage: localStorage.setItem('enable_tami_ui', 'true')
 * - Or via URL param: ?tami_ui=true
 * - Or via admin panel toggle
 */

(function() {
    'use strict';

    // Check URL param first
    const urlParams = new URLSearchParams(window.location.search);
    const urlFlag = urlParams.get('tami_ui');

    // Check localStorage
    const storageFlag = localStorage.getItem('enable_tami_ui');

    // Determine if Tami UI should be enabled
    const enableTamiUI = urlFlag === 'true' || storageFlag === 'true';

    // Set global flag
    window.courseCreator = window.courseCreator || {};
    window.courseCreator.featureFlags = window.courseCreator.featureFlags || {};
    window.courseCreator.featureFlags.ENABLE_TAMI_UI = enableTamiUI;

    // Apply data attribute to HTML element
    if (enableTamiUI) {
        document.documentElement.setAttribute('data-tami-ui', 'enabled');

        // Load Tami CSS
        const tamiCSS = document.createElement('link');
        tamiCSS.rel = 'stylesheet';
        tamiCSS.href = '/css/tami/tami-enhancements.css';
        tamiCSS.id = 'tami-ui-css';
        document.head.appendChild(tamiCSS);

        console.log('✅ Tami UI enabled');
    } else {
        document.documentElement.setAttribute('data-tami-ui', 'disabled');
        console.log('ℹ️ Tami UI disabled (legacy styles active)');
    }

    // Allow runtime toggling
    window.toggleTamiUI = function(enable) {
        localStorage.setItem('enable_tami_ui', enable ? 'true' : 'false');
        location.reload();
    };
})();
```

**Priority**: ⭐⭐⭐⭐⭐ CRITICAL

---

**WAVE 1 REVIEW CHECKPOINT**

After Wave 1 completes, I'll provide:
- ✅ All 4 tasks complete status
- ✅ Baseline screenshots gallery
- ✅ Feature flag demo (toggle on/off)
- ✅ Initial visual comparison
- ✅ Test results summary

**Decision Point**: Approve Wave 2 or adjust approach?

---

### WAVE 2: Core Components (Days 3-6) ⭐⭐⭐⭐⭐ CRITICAL

**Review Checkpoint**: End of Day 6

#### Task 5: Button System
#### Task 6: Form Input System
#### Task 7: Card System
#### Task 8: Dashboard HTML Updates

(Full details available - truncated for brevity)

---

### WAVE 3: Advanced Components (Days 7-10) ⭐⭐⭐⭐ HIGH

**Review Checkpoint**: End of Day 10

#### Task 9: Modal/Dialog System
#### Task 10: Navigation Modernization
#### Task 11: Loading States & Feedback
#### Task 12: Site Admin Dashboard Updates

---

### WAVE 4: Wizard Enhancement (Week 3) ⭐⭐⭐⭐ HIGH

**Review Checkpoint**: End of Week 3

#### Task 13: Wizard Progress Indicator
#### Task 14: Step Validation System
#### Task 15: Save Draft Functionality
#### Task 16: Project Creation Wizard Updates

---

### WAVE 5: Polish & Documentation (Week 4-8) ⭐⭐⭐ MEDIUM

**Review Checkpoint**: End of Week 8

#### Task 17: Animation Polish
#### Task 18: Accessibility Audit
#### Task 19: Component Documentation
#### Task 20: Developer Migration Guide

---

## 📊 Success Metrics

### Phase 1 (Wave 1-2)
- [ ] Feature flag working (can toggle on/off)
- [ ] Tami spacing system implemented (8px base)
- [ ] Inter font loading successfully
- [ ] All buttons have hover lift effects
- [ ] All forms have improved focus states
- [ ] Visual regression tests passing
- [ ] WCAG AA+ compliance maintained
- [ ] **Using OUR blue (#2563eb), NOT Tami purple**

### Phase 2 (Wave 3-4)
- [ ] Modals have smooth animations
- [ ] Wizard shows progress indicators
- [ ] Navigation has hover states
- [ ] Loading states everywhere (skeletons, spinners)
- [ ] Toast notifications working

### Phase 3 (Wave 5)
- [ ] Progressive disclosure patterns
- [ ] Animations polished
- [ ] Documentation complete
- [ ] Ready for production rollout

---

## 🎯 Quick Start - Wave 1 Launch

**I'm ready to launch Wave 1 (4 parallel tasks) when you say go:**

1. **Task 1**: Design tokens with OUR colors
2. **Task 2**: Typography system with Inter
3. **Task 3**: Baseline screenshot capture
4. **Task 4**: Feature flag implementation

**Estimated time**: 2 days
**Review**: End of Day 2

**Should I launch Wave 1 now?** 🚀

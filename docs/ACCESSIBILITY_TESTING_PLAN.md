# Accessibility Testing Plan - Phase 1 & Phase 2 Verification

**Date:** 2025-10-07
**Scope:** Verify Phase 1 (P0) and Phase 2 (P1) accessibility fixes
**Target:** WCAG 2.1 AA Compliance
**Estimated Time:** 6-8 hours

---

## Testing Objectives

1. **Verify Phase 1 + Phase 2 work together** - No conflicts between fixes
2. **Confirm WCAG compliance improvements** - From 45% → 90%
3. **Ensure no broken functionality** - Existing features still work
4. **Identify edge cases and bugs** - Early detection before Phase 3
5. **Get baseline metrics** - Establish current compliance level

---

## Test Environment Setup

### Prerequisites

```bash
# 1. Ensure platform is running
./scripts/app-control.sh status
# All 16 services should be healthy

# 2. Verify HTTPS is working
curl -k https://localhost:3000
# Should return 200 OK

# 3. Install testing tools (optional but recommended)
npm install -g @axe-core/cli
npm install -g pa11y
npm install -g lighthouse
```

### Browser Setup

- **Primary:** Chrome/Chromium (for DevTools and extensions)
- **Secondary:** Firefox (for cross-browser testing)
- **Optional:** Safari (macOS only)

### Browser Extensions to Install

1. **axe DevTools** - https://chrome.google.com/webstore/detail/axe-devtools
2. **WAVE** - https://chrome.google.com/webstore/detail/wave-evaluation-tool
3. **Lighthouse** - Built into Chrome DevTools

---

## Test Categories

### 1. Automated Testing (1-2 hours)

**Automated tests catch ~30-40% of accessibility issues**

#### 1.1 axe-core CLI Tests

Run on all key pages:

```bash
# Landing page
axe https://localhost:3000 --exit

# Public pages
axe https://localhost:3000/html/register.html --exit
axe https://localhost:3000/html/student-login.html --exit

# Dashboards
axe https://localhost:3000/html/org-admin-dashboard.html?org_id=1 --exit
axe https://localhost:3000/html/instructor-dashboard.html --exit
axe https://localhost:3000/html/student-dashboard.html --exit
axe https://localhost:3000/html/site-admin-dashboard.html --exit

# Forms
axe https://localhost:3000/html/password-change.html --exit
axe https://localhost:3000/html/organization-registration.html --exit

# Interactive pages
axe https://localhost:3000/html/quiz.html --exit
axe https://localhost:3000/html/lab.html --exit
```

**Expected Results:**
- 0 critical violations
- 0-5 serious violations
- <10 moderate violations
- Improved scores from pre-Phase 1 baseline

#### 1.2 pa11y Tests (Alternative)

```bash
# Run with WCAG2AA standard
pa11y --standard WCAG2AA --reporter json https://localhost:3000 > results.json
```

#### 1.3 Lighthouse Accessibility Audit

```bash
# Run Lighthouse (requires Chrome)
lighthouse https://localhost:3000 --only-categories=accessibility --output=html --output-path=lighthouse-report.html
```

**Expected Score:**
- Accessibility score: 90-95+
- Previous score (before fixes): ~70-75

---

### 2. Manual Keyboard Navigation Testing (2-3 hours)

**Manual testing catches ~60-70% of accessibility issues**

#### 2.1 Skip Link Testing

**Pages:** All 18 pages

**Test Steps:**
1. Load page in browser
2. Press `Tab` key ONCE
3. Verify skip link appears at top-left
4. Press `Enter` to activate
5. Verify focus jumps to main content

**Expected Results:**
- ✅ Skip link visible on first Tab press
- ✅ Has clear blue focus indicator
- ✅ Text reads "Skip to main content"
- ✅ Clicking jumps to #main-content
- ✅ Focus indicator visible on main content after jump

**Test Matrix:**

| Page | Skip Link Appears | Focus Visible | Works Correctly |
|------|-------------------|---------------|-----------------|
| index.html | ☐ | ☐ | ☐ |
| register.html | ☐ | ☐ | ☐ |
| student-login.html | ☐ | ☐ | ☐ |
| student-dashboard.html | ☐ | ☐ | ☐ |
| instructor-dashboard.html | ☐ | ☐ | ☐ |
| org-admin-dashboard.html | ☐ | ☐ | ☐ |
| site-admin-dashboard.html | ☐ | ☐ | ☐ |
| admin.html | ☐ | ☐ | ☐ |
| quiz.html | ☐ | ☐ | ☐ |
| lab.html | ☐ | ☐ | ☐ |
| lab-multi-ide.html | ☐ | ☐ | ☐ |
| password-change.html | ☐ | ☐ | ☐ |
| organization-registration.html | ☐ | ☐ | ☐ |
| project-dashboard.html | ☐ | ☐ | ☐ |

#### 2.2 Focus Indicator Testing

**Pages:** All 18 pages

**Test Steps:**
1. Load page
2. Press `Tab` repeatedly through all interactive elements
3. For each element, verify:
   - 3px blue outline visible
   - 2px offset from element
   - Outline clearly distinguishes focused element
   - No invisible focus states

**Elements to Test:**
- Links (navigation, content links)
- Buttons (primary, secondary, icon buttons)
- Form inputs (text, email, password, select, textarea)
- Custom controls (tabs, accordions, modals)
- Sidebar toggles
- Modal close buttons

**Expected Results:**
- ✅ All interactive elements have visible focus
- ✅ Focus order is logical (top to bottom, left to right)
- ✅ No focus traps (can Tab out of all elements)
- ✅ Modal focus is trapped within modal when open

**Test Matrix (sample key pages):**

| Page | All Links | All Buttons | All Inputs | Custom Controls |
|------|-----------|-------------|------------|-----------------|
| index.html | ☐ | ☐ | N/A | ☐ Slideshow |
| register.html | ☐ | ☐ | ☐ | N/A |
| org-admin-dashboard.html | ☐ | ☐ | ☐ | ☐ Tabs, Modals |
| instructor-dashboard.html | ☐ | ☐ | ☐ | ☐ Tabs, Modals |

#### 2.3 Keyboard Interaction Testing

**Test Sidebar Toggles:**

Pages: Dashboard pages (4 dashboards)

**Test Steps:**
1. Navigate to dashboard
2. Tab to sidebar toggle button
3. Press `Enter` key
4. Verify sidebar opens/closes
5. Press `Space` key
6. Verify sidebar opens/closes

**Expected Results:**
- ✅ Enter key toggles sidebar
- ✅ Space key toggles sidebar
- ✅ No JavaScript errors in console

**Test Modal Dialogs:**

Pages: Dashboard pages with modals

**Test Steps:**
1. Tab to button that opens modal
2. Press `Enter` to open modal
3. Verify focus moves to modal
4. Press `Tab` repeatedly - verify focus stays in modal
5. Press `Esc` key
6. Verify modal closes
7. Verify focus returns to trigger button

**Expected Results:**
- ✅ Focus moves to modal on open
- ✅ Focus trapped within modal (can't Tab out)
- ✅ Esc key closes modal
- ✅ Focus returns to trigger button

---

### 3. Form Validation Testing (1-2 hours)

**Pages:** 4 form pages

#### 3.1 Real-time Validation Testing

**Test register.html:**

**Test Steps:**
1. Load registration page
2. Click into "Email" field
3. Type invalid email: "test@"
4. Tab out of field (blur event)
5. Verify error message appears
6. Continue typing valid email: "test@example.com"
7. Verify error message clears in real-time

**Expected Results:**
- ✅ Error message appears on blur with invalid data
- ✅ Error message has red text with warning icon
- ✅ Input has red border
- ✅ `aria-invalid="true"` set on input
- ✅ Error message clears as user types valid data
- ✅ Input border changes to green when valid
- ✅ `aria-invalid="false"` set on input

**Test Matrix:**

| Field | Validation Triggers | Error Shows | Error Clears | ARIA Updated |
|-------|---------------------|-------------|--------------|--------------|
| Email | ☐ | ☐ | ☐ | ☐ |
| Password | ☐ | ☐ | ☐ | ☐ |
| Confirm Password | ☐ | ☐ | ☐ | ☐ |
| First Name | ☐ | ☐ | ☐ | ☐ |
| Last Name | ☐ | ☐ | ☐ | ☐ |

**Repeat for:**
- student-login.html
- password-change.html
- organization-registration.html

#### 3.2 Form Submission Prevention

**Test Steps:**
1. Load form page
2. Fill in some fields (leave required fields empty)
3. Click submit button
4. Verify form does NOT submit
5. Verify error messages appear for all invalid/empty fields
6. Fill in all fields correctly
7. Click submit
8. Verify form submits successfully

**Expected Results:**
- ✅ Form blocked from submission with errors
- ✅ All errors displayed simultaneously
- ✅ Focus moves to first error field
- ✅ Form submits when all fields valid

#### 3.3 Screen Reader Announcements

**Requires screen reader (NVDA, JAWS, or VoiceOver)**

**Test Steps:**
1. Enable screen reader
2. Load form page
3. Tab to field, enter invalid data, tab out
4. Listen for announcement

**Expected Results:**
- ✅ Error message announced immediately
- ✅ Announcement includes field name and error
- ✅ Example: "Email: Please enter a valid email address"

---

### 4. Slideshow Pause Control Testing (15 minutes)

**Page:** index.html

#### 4.1 Visual Testing

**Test Steps:**
1. Load homepage
2. Observe slideshow auto-advances every 5 seconds
3. Locate pause button (top-right of slideshow)
4. Click pause button
5. Verify slideshow stops
6. Verify button icon changes to "play"
7. Click play button
8. Verify slideshow resumes
9. Verify button icon changes to "pause"

**Expected Results:**
- ✅ Pause button visible
- ✅ Clicking pauses slideshow
- ✅ Icon changes pause ↔ play
- ✅ Clicking play resumes slideshow
- ✅ Button has focus indicator when tabbed to

#### 4.2 Keyboard Testing

**Test Steps:**
1. Load homepage
2. Tab to pause button
3. Verify focus indicator visible
4. Press `Enter` key
5. Verify slideshow pauses
6. Press `Enter` again
7. Verify slideshow resumes

**Expected Results:**
- ✅ Button keyboard accessible
- ✅ Enter key toggles pause/play

#### 4.3 ARIA Testing

**Test Steps:**
1. Inspect pause button with DevTools
2. Verify initial ARIA attributes:
   - `aria-label="Pause slideshow"`
   - `aria-pressed="false"`
3. Click button to pause
4. Verify ARIA updates:
   - `aria-label="Play slideshow"`
   - `aria-pressed="true"`

**Expected Results:**
- ✅ ARIA attributes present
- ✅ ARIA updates on state change

---

### 5. Semantic Landmark Testing (30 minutes)

**Tool:** Browser DevTools or WAVE extension

**Test Steps:**
1. Load page
2. Open DevTools → Accessibility panel (Chrome)
3. OR: Run WAVE extension
4. Verify landmarks present:
   - `<header role="banner">`
   - `<nav role="navigation">`
   - `<main role="main">`
   - `<footer role="contentinfo">` (if present)

**Expected Results for ALL 18 pages:**
- ✅ Header has `role="banner"`
- ✅ Nav has `role="navigation"` and `aria-label`
- ✅ Main content has `role="main"` and `id="main-content"`
- ✅ No duplicate landmarks

**Quick Check Script:**

```javascript
// Paste in browser console
const landmarks = {
  banner: document.querySelectorAll('header[role="banner"]'),
  navigation: document.querySelectorAll('nav[role="navigation"]'),
  main: document.querySelectorAll('main[role="main"]'),
  contentinfo: document.querySelectorAll('footer[role="contentinfo"]')
};

console.table({
  'Header (banner)': landmarks.banner.length,
  'Nav (navigation)': landmarks.navigation.length,
  'Main (main)': landmarks.main.length,
  'Footer (contentinfo)': landmarks.contentinfo.length
});
```

**Expected Output:**
```
Header (banner): 1
Nav (navigation): 1
Main (main): 1
Footer (contentinfo): 0-1
```

---

### 6. Modal ARIA Testing (1 hour)

**Pages:** Dashboard pages with modals

#### 6.1 Modal ARIA Attributes

**Test Steps:**
1. Open modal
2. Inspect modal with DevTools
3. Verify attributes:
   - `role="dialog"`
   - `aria-modal="true"`
   - `aria-labelledby="modalTitleId"`
4. Verify modal title has matching ID

**Expected Results:**
- ✅ All modals have `role="dialog"`
- ✅ All modals have `aria-modal="true"`
- ✅ All modals have `aria-labelledby`
- ✅ Modal title has ID referenced by `aria-labelledby`

**Test Matrix (sample):**

| Dashboard | Modal Name | role | aria-modal | aria-labelledby |
|-----------|-----------|------|------------|-----------------|
| Org Admin | Add Instructor | ☐ | ☐ | ☐ |
| Org Admin | Create Project | ☐ | ☐ | ☐ |
| Org Admin | Add Student | ☐ | ☐ | ☐ |
| Instructor | Create Course | ☐ | ☐ | ☐ |
| Instructor | Add Lab | ☐ | ☐ | ☐ |

#### 6.2 Modal Focus Management

**Test Steps:**
1. Tab to button that opens modal
2. Press Enter to open
3. Verify focus moves to modal
4. Press Tab repeatedly
5. Verify focus ONLY cycles within modal
6. Verify cannot Tab to elements behind modal
7. Press Esc
8. Verify modal closes AND focus returns to trigger button

**Expected Results:**
- ✅ Focus moves to modal on open
- ✅ Focus trapped in modal (Tab only cycles within)
- ✅ Esc closes modal
- ✅ Focus returns to trigger button

---

### 7. Color Contrast Testing (30 minutes)

**Tool:** WebAIM Contrast Checker or browser DevTools

#### 7.1 Text Color Contrast

**Test Steps:**
1. Load page
2. Inspect text elements with DevTools
3. Check contrast ratio in Accessibility panel
4. Verify meets 4.5:1 minimum (WCAG AA)

**Elements to Check:**
- Body text
- Headings (h1, h2, h3, etc.)
- Link text
- Button text
- Form labels
- Placeholder text
- Disabled text

**Quick Check URLs:**
- **WebAIM Contrast Checker:** https://webaim.org/resources/contrastchecker/
- **Chrome DevTools:** Inspect element → Styles → Contrast ratio

**Expected Results:**
- ✅ All text meets 4.5:1 minimum
- ✅ Large text (18pt+ or 14pt+ bold) meets 3:1 minimum
- ✅ No contrast failures in DevTools

#### 7.2 Color Variables Verification

**Test Steps:**
1. Open `/frontend/css/base/variables.css`
2. Verify color variables:

```css
:root {
    --text-primary: #212529;     /* Should be ~16:1 on white */
    --text-secondary: #495057;   /* Should be ~8:1 on white */
    --text-muted: #6c757d;       /* Should be ~5:1 on white */
}
```

3. Test each color with WebAIM Contrast Checker against white (#FFFFFF)

**Expected Results:**
- ✅ --text-primary: ≥12:1 ratio
- ✅ --text-secondary: ≥7:1 ratio
- ✅ --text-muted: ≥4.5:1 ratio

---

### 8. Screen Reader Testing (Optional - 1-2 hours)

**Requires:** NVDA (Windows), JAWS (Windows), or VoiceOver (macOS)

#### 8.1 Basic Navigation

**Test Steps (NVDA):**
1. Launch NVDA
2. Load homepage
3. Press `H` key - should navigate by headings
4. Press `D` key - should navigate by landmarks
5. Press `F` key - should navigate by form fields
6. Press `B` key - should navigate by buttons

**Expected Results:**
- ✅ Headings announced correctly
- ✅ Landmarks announced (banner, navigation, main)
- ✅ Form fields announced with labels
- ✅ Buttons announced with accessible names

#### 8.2 Form Field Announcements

**Test Steps:**
1. Navigate to form (register.html)
2. Tab through form fields
3. Listen for announcements

**Expected Announcements:**
- "Email address, required, edit"
- "Password, required, edit"
- etc.

**Expected Results:**
- ✅ Field name announced
- ✅ "Required" status announced
- ✅ Field type announced
- ✅ Error messages announced immediately when they appear

---

## Test Execution Order

**Recommended order for efficiency:**

1. **Start Platform** (5 minutes)
   ```bash
   ./scripts/app-control.sh start
   ./scripts/app-control.sh status
   ```

2. **Run Automated Tests** (30 minutes)
   ```bash
   # Run axe-core on all pages
   # Run Lighthouse audit
   ```

3. **Manual Keyboard Testing** (2 hours)
   - Skip links (all pages)
   - Focus indicators (all pages)
   - Keyboard interactions (dashboards)

4. **Form Validation Testing** (1 hour)
   - Real-time validation (4 forms)
   - Submission prevention
   - ARIA announcements

5. **Slideshow Pause Testing** (15 minutes)
   - Visual + keyboard + ARIA

6. **Landmark & Modal Testing** (1 hour)
   - Semantic landmarks (all pages)
   - Modal ARIA (dashboards)

7. **Color Contrast** (30 minutes)
   - Text colors
   - Variable verification

8. **Screen Reader (Optional)** (1-2 hours)
   - Navigation
   - Form announcements

---

## Test Result Documentation

### Template for Each Test

```markdown
## Test: [Test Name]
**Page:** [Page URL]
**Date:** [Date]
**Tester:** [Name]

### Test Steps
1. [Step 1]
2. [Step 2]
...

### Expected Results
- ✅ [Expected result 1]
- ✅ [Expected result 2]

### Actual Results
- [✅/❌] [Actual result 1]
- [✅/❌] [Actual result 2]

### Issues Found
| Issue ID | Severity | Description | Location |
|----------|----------|-------------|----------|
| ACC-001 | High | [Description] | [File:Line] |

### Screenshots
- [Attach screenshots if applicable]

### Notes
[Any additional observations]
```

---

## Success Criteria

**Phase 1 + Phase 2 testing is successful if:**

✅ **Automated Tests:**
- axe-core: 0 critical violations, <5 serious violations
- Lighthouse: 90+ accessibility score
- pa11y: <10 errors

✅ **Manual Tests:**
- Skip links work on 100% of pages
- Focus indicators visible on 100% of interactive elements
- Form validation works on 100% of forms
- Slideshow pause control works correctly
- All modals have proper ARIA
- All landmarks present on all pages
- All text meets 4.5:1 contrast

✅ **No Regressions:**
- All existing functionality still works
- No new bugs introduced
- No console errors related to accessibility JS

✅ **WCAG Compliance:**
- Estimated 90% WCAG 2.1 AA compliance
- All Level A criteria met
- Most Level AA criteria met

---

## Issue Tracking

### Issue Severity Levels

- **Critical:** Blocks users with disabilities completely
- **High:** Significantly impacts usability
- **Medium:** Minor usability impact
- **Low:** Cosmetic or nice-to-have

### Issue Template

```markdown
### Issue ACC-XXX: [Title]

**Severity:** [Critical/High/Medium/Low]
**WCAG Violation:** [Guideline number]
**Page:** [URL]
**Location:** [File:Line]

**Description:**
[Detailed description of the issue]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Impact:**
[How this affects users with disabilities]

**Recommended Fix:**
[Suggested solution]

**Priority:**
[ ] Fix before Phase 3
[ ] Fix during Phase 3
[ ] Defer to Phase 4
```

---

## Next Steps After Testing

1. **Document all results** in `/docs/ACCESSIBILITY_TEST_RESULTS.md`
2. **Create GitHub issues** for all bugs found
3. **Prioritize fixes** (critical → high → medium → low)
4. **Fix critical bugs immediately** (block Phase 3 until fixed)
5. **Proceed to Phase 3** (Tab ARIA patterns + final polish)

---

## Resources

### Tools
- **axe DevTools:** https://www.deque.com/axe/devtools/
- **WAVE:** https://wave.webaim.org/extension/
- **Lighthouse:** Built into Chrome DevTools
- **NVDA:** https://www.nvaccess.org/download/
- **WebAIM Contrast Checker:** https://webaim.org/resources/contrastchecker/

### Documentation
- **WCAG 2.1 Guidelines:** https://www.w3.org/WAI/WCAG21/quickref/
- **ARIA Authoring Practices:** https://www.w3.org/WAI/ARIA/apg/
- **MDN Accessibility:** https://developer.mozilla.org/en-US/docs/Web/Accessibility

### Internal Docs
- Phase 1 Report: `/docs/PHASE1_FIXES_COMPLETED.md`
- Phase 2 Report: `/docs/PHASE2_ACCESSIBILITY_FIXES_COMPLETED.md`
- UI/UX Audit: `/docs/UI_UX_AUDIT_REPORT.md`

---

**End of Testing Plan**

# E2E Test Coverage - Action Plan to 90%

**Goal:** Achieve 257+/285 tests passing (90%+ coverage)
**Current:** 97/285 tests passing (34%)
**Gap:** 160 tests need to pass
**Timeline:** 6-8 weeks

---

## Priority Task List

### 🔴 Critical Path (Must Do)

#### Week 1-2: Public Homepage Implementation
**Task:** Implement guest/anonymous user homepage
**Unlocks:** ~20 guest journey tests
**Components Needed:**
- [ ] Homepage header with navigation
- [ ] Public course catalog section
- [ ] Course search input (`#course-search`)
- [ ] Category filter dropdown
- [ ] Difficulty filter dropdown
- [ ] Course cards display
- [ ] "About" page link
- [ ] "Contact" page link
- [ ] "Privacy Policy" page link
- [ ] "Terms of Service" page link

**Files to Create/Modify:**
- `frontend/html/index.html` (enhance existing)
- `frontend/css/homepage.css` (new)
- `frontend/js/homepage.js` (new)

**Estimated Effort:** 3 days
**Expected Test Gains:** +15-20 tests passing

---

#### Week 2-4: Site Admin Dashboard
**Task:** Build complete site admin dashboard
**Unlocks:** ~40-50 site admin tests
**Components Needed:**
- [ ] Dashboard layout with tabs
- [ ] Platform health monitoring section
- [ ] Services status container (`#servicesStatusContainer`)
- [ ] Service status cards (`.service-status-card`)
- [ ] Docker health indicator (`#dockerHealthIndicator`)
- [ ] Resource usage chart (`#resourceUsageChart`)
- [ ] Organizations table and management
- [ ] Users table and management (platform-wide)
- [ ] Courses table and management (platform-wide)
- [ ] System configuration forms
- [ ] Analytics dashboards
- [ ] Audit log viewer
- [ ] Security alerts panel

**Files to Enhance:**
- `frontend/html/site-admin-dashboard.html` (exists, needs enhancement)
- `frontend/css/site-admin-dashboard.css` (new)
- `frontend/js/site-admin-dashboard.js` (new)

**Estimated Effort:** 7 days
**Expected Test Gains:** +40-45 tests passing

---

#### Week 4: Org Admin Completion
**Task:** Fix remaining org admin test failures
**Unlocks:** ~15 org admin tests
**Issues to Fix:**
- [ ] Fix `test_15_view_all_organization_projects` failure
- [ ] Complete remaining 16 untested workflows
- [ ] Add missing navigation elements
- [ ] Fix session persistence issues

**Files to Modify:**
- `frontend/html/organization-admin-dashboard.html`
- `frontend/js/organization-admin.js`

**Estimated Effort:** 2 days
**Expected Test Gains:** +15 tests passing

---

### 🟡 High Priority (Should Do)

#### Week 5: RAG AI Frontend Integration
**Task:** Complete AI assistant frontend
**Unlocks:** ~25-30 RAG AI tests
**Components Needed:**
- [ ] WebSocket connection to AI service
- [ ] Chat interface UI
- [ ] Learning path visualization
- [ ] Progressive hints display
- [ ] Context-aware responses UI
- [ ] Knowledge gap indicators

**Files to Create/Modify:**
- `frontend/html/ai-assistant.html` (new)
- `frontend/js/ai-assistant-websocket.js` (exists, enhance)
- `frontend/css/ai-assistant.css` (exists, enhance)

**Estimated Effort:** 3-4 days
**Expected Test Gains:** +25-28 tests passing

---

#### Week 5-6: Content Generation UI
**Task:** Complete content generation workflow UI
**Unlocks:** ~20-30 content generation tests
**Components Needed:**
- [ ] Course generation wizard
- [ ] Syllabus editor
- [ ] Slides generator UI
- [ ] Quiz builder interface
- [ ] Lab template selector
- [ ] Content preview panel

**Files to Modify:**
- `frontend/html/instructor-dashboard.html` (add generation tab)
- `frontend/js/content-generation.js` (new)

**Estimated Effort:** 3-4 days
**Expected Test Gains:** +25-30 tests passing

---

### 🟢 Medium Priority (Nice to Have)

#### Week 6: Platform Workflow Integration
**Task:** Cross-role integration testing
**Unlocks:** ~12-15 platform tests
**Components Needed:**
- [ ] Cross-service integration verification
- [ ] Multi-tenant isolation checks
- [ ] Service health monitoring

**Estimated Effort:** 2 days
**Expected Test Gains:** +12-14 tests passing

---

## Implementation Checklist

### Homepage (Week 1-2)
```html
<!-- Required Elements -->
<header class="homepage-header">
  <nav>
    <a href="/">Home</a>
    <a href="/about">About</a>
    <a href="/contact">Contact</a>
    <a href="/login">Login</a>
    <a href="/register">Register</a>
  </nav>
</header>

<section class="course-catalog">
  <input id="course-search" type="text" placeholder="Search courses...">
  <button aria-label="Search">Search</button>

  <div class="filters">
    <select name="category">Category</select>
    <select name="difficulty">Difficulty</select>
  </div>

  <div class="course-cards">
    <!-- Course cards -->
  </div>
</section>
```

### Site Admin Dashboard (Week 2-4)
```html
<!-- Required Elements -->
<div id="servicesStatusContainer">
  <div class="service-status-card" data-service="user-management">
    <span class="service-name">User Management</span>
    <span class="service-status">Healthy</span>
  </div>
  <!-- More service cards... -->
</div>

<div id="dockerHealthIndicator">
  <span class="total-containers">16</span>
  <span class="healthy-containers">16</span>
</div>

<div id="resourceUsageChart">
  <!-- CPU/Memory charts -->
</div>

<div id="organizationsContainer">
  <table class="organizations-table">
    <!-- Organizations list -->
  </table>
</div>
```

### RAG AI Assistant (Week 5)
```html
<!-- Required Elements -->
<div class="ai-chat-container">
  <div class="chat-messages" id="aiChatMessages">
    <!-- Messages -->
  </div>
  <input id="aiChatInput" placeholder="Ask a question...">
  <button id="aiSendButton">Send</button>
</div>

<div class="learning-path-display">
  <!-- Personalized path -->
</div>
```

---

## Testing Strategy

### After Each Implementation Sprint

1. **Run Affected Tests**
```bash
# After homepage implementation
HEADLESS=true TEST_BASE_URL=https://localhost:3000 pytest \
  tests/e2e/critical_user_journeys/test_guest_complete_journey.py -v

# After site admin implementation
HEADLESS=true TEST_BASE_URL=https://localhost:3000 pytest \
  tests/e2e/critical_user_journeys/test_site_admin_complete_journey.py -v
```

2. **Document Results**
   - Count passing vs failing
   - Identify new issues
   - Update coverage metrics

3. **Iterate**
   - Fix issues discovered
   - Re-run tests
   - Move to next sprint

---

## Success Milestones

### Milestone 1: Week 2
- ✅ Homepage complete
- ✅ ~115/285 tests passing (40%+)
- ✅ Guest journey validated

### Milestone 2: Week 4
- ✅ Site admin dashboard complete
- ✅ ~170/285 tests passing (60%+)
- ✅ All admin dashboards functional

### Milestone 3: Week 6
- ✅ RAG AI + Content Gen complete
- ✅ ~230/285 tests passing (80%+)
- ✅ All major workflows implemented

### Milestone 4: Week 8
- ✅ All features polished
- ✅ 257+/285 tests passing (90%+) 🎯
- ✅ Production-ready platform

---

## Risk Mitigation

### Risk 1: Implementation Takes Longer
**Mitigation:** Prioritize critical path items, defer nice-to-haves

### Risk 2: Tests Reveal New Issues
**Mitigation:** Fix iteratively, don't block on perfection

### Risk 3: Resource Constraints
**Mitigation:** Focus on high-value features first

---

## Daily Progress Tracking

### Template:
```markdown
## Day X - [Date]
**Sprint:** [Homepage/Site Admin/RAG AI/etc.]
**Tasks Completed:**
- [ ] Task 1
- [ ] Task 2

**Tests Passing:** X/285 (+Y from yesterday)
**Blockers:** None / [Description]
**Tomorrow:** [Next tasks]
```

---

## Quick Reference

### Current Status (2025-10-11)
```
Total Tests: 285
Passing: 97 (34%)
Need: 160 more passing tests
Timeline: 6-8 weeks
```

### Test Counts by Suite
```
✅ Student:     32/32  (100%)
✅ Instructor:  38/38  (100%)
⚠️  Org Admin:   25/41  (61%)
❌ Site Admin:   0/51  (0%)
❌ Guest:        2/36  (6%)
?  RAG AI:      ?/32  (?)
?  Content Gen: ?/39  (?)
?  Platform:    ?/16  (?)
```

---

## Contact & Resources

**Documentation:**
- `E2E_TEST_COVERAGE_REPORT.md` - Detailed analysis
- `E2E_TEST_COVERAGE_SUMMARY.md` - Executive summary
- `E2E_PHASE_2_STATUS.md` - Current status
- `E2E_ACTION_PLAN.md` - This document

**Test Files:**
- `tests/e2e/critical_user_journeys/` - All E2E test suites

**Implementation Files:**
- `frontend/html/` - HTML templates
- `frontend/css/` - Stylesheets
- `frontend/js/` - JavaScript functionality

---

**Last Updated:** 2025-10-11
**Status:** Ready for Implementation Sprint
**Next Action:** Start Homepage Implementation (Week 1)

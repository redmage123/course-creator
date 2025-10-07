# Agile Kanban Board: Guest Role & Demo Service Refactor

**Sprint Goal**: Implement guest role RBAC and refactor demo service to showcase all platform features

**Sprint Duration**: 2 weeks (10 business days)

**Methodology**: Test-Driven Development (TDD) - RED → GREEN → REFACTOR

---

## 📋 Product Backlog

### Epic 1: Guest Role RBAC System
**Business Value**: Allow anonymous users to explore platform without registration, reducing friction for potential customers

**User Stories**:
1. ✅ As an **anonymous user**, I want to **access a guest role automatically** so that **I can explore the platform without registration**
2. ✅ As a **guest user**, I want to **access the demo service** so that **I can see realistic platform features**
3. ✅ As a **guest user**, I want to **browse public course catalog** so that **I can see what courses are available**
4. ✅ As a **guest user**, I want to **use AI assistant with limits** so that **I can ask questions about the platform**
5. ✅ As a **guest user**, I want **clear prompts to register** so that **I understand how to get full access**

### Epic 2: Demo Service Enhancement
**Business Value**: Showcase ALL platform features (AI, RAG, content generation, labs) to increase conversion rates

**User Stories**:
1. ✅ As a **sales person**, I want to **demonstrate AI-powered content generation** so that **customers see the platform's intelligence**
2. ✅ As a **sales person**, I want to **show RAG-enhanced learning** so that **customers understand the knowledge graph value**
3. ✅ As a **sales person**, I want to **demonstrate Docker lab environments** so that **customers see hands-on learning capabilities**
4. ✅ As a **sales person**, I want to **showcase multi-role workflows** so that **customers see instructor, student, and admin experiences**
5. ✅ As a **sales person**, I want to **show analytics dashboards** so that **customers see data-driven insights**

### Epic 3: Guest-Demo Integration
**Business Value**: Seamless guest experience with demo service access and conversion tracking

**User Stories**:
1. ✅ As a **guest user**, I want **automatic demo session creation** so that **I can start exploring immediately**
2. ✅ As a **guest user**, I want **time-limited demo sessions** so that **I understand the trial nature**
3. ✅ As a **marketing team**, I want to **track which demo features drive registration** so that **we can optimize conversion**
4. ✅ As a **guest user**, I want **clear session expiration warnings** so that **I'm not surprised when my session ends**

---

## 🎯 Sprint Backlog (Current Sprint)

### Phase 1: TDD RED - Write Failing Tests (Days 1-2)

#### Task 1.1: Guest Role RBAC Tests ⏳ IN PROGRESS
- [ ] Test: Guest role exists in RoleType enum
- [ ] Test: Guest permissions defined (ACCESS_DEMO_SERVICE, VIEW_PUBLIC_COURSES, etc.)
- [ ] Test: Guest role cannot access protected resources
- [ ] Test: Guest role can access demo service endpoints
- [ ] Test: Guest sessions are time-limited (expire after 30 minutes)
- [ ] Test: Guest cannot modify any data (read-only)

**Acceptance Criteria**:
- All tests FAIL (RED phase)
- Tests cover all guest role permissions
- Tests validate guest limitations (time, read-only, rate-limiting)

#### Task 1.2: Demo Service Enhancement Tests ⏳ TODO
- [ ] Test: Demo service generates AI-powered course content
- [ ] Test: Demo service provides RAG knowledge graph interactions
- [ ] Test: Demo service simulates Docker lab environments
- [ ] Test: Demo service shows instructor workflow (create course → generate content)
- [ ] Test: Demo service shows student workflow (enroll → learn → quiz → lab)
- [ ] Test: Demo service shows analytics dashboards with realistic data
- [ ] Test: Demo service handles multi-role switching

**Acceptance Criteria**:
- All tests FAIL (RED phase)
- Tests cover all platform features (AI, RAG, labs, analytics)
- Tests validate realistic data generation

#### Task 1.3: Guest-Demo Integration Tests ⏳ TODO
- [ ] Test: Guest user automatically gets demo session on homepage visit
- [ ] Test: Guest can start instructor demo workflow
- [ ] Test: Guest can start student demo workflow
- [ ] Test: Guest session expires after 30 minutes inactivity
- [ ] Test: Guest gets prompted to register after demo
- [ ] Test: Guest conversion tracking records which features were used

**Acceptance Criteria**:
- All tests FAIL (RED phase)
- Tests cover automatic session creation, expiration, conversion

---

### Phase 2: TDD GREEN - Make Tests Pass (Days 3-6)

#### Task 2.1: Implement Guest Role RBAC ⏳ TODO
- [ ] Add GUEST to RoleType enum in `enhanced_role.py`
- [ ] Add guest permissions to Permission enum
- [ ] Implement guest permission checks in RBAC endpoints
- [ ] Add session expiration logic for guest users
- [ ] Implement read-only enforcement for guest role
- [ ] Add rate limiting for guest AI assistant access

**Acceptance Criteria**:
- All guest RBAC tests PASS (GREEN phase)
- Guest role integrated with existing RBAC system
- No regressions in other roles

#### Task 2.2: Enhance Demo Service Features ⏳ TODO
- [ ] Add AI content generation demo endpoint
- [ ] Add RAG knowledge graph demo endpoint
- [ ] Add Docker lab environment simulation
- [ ] Add instructor workflow demo (multi-step)
- [ ] Add student workflow demo (multi-step)
- [ ] Add analytics dashboard demo with realistic charts
- [ ] Add multi-role switching capability

**Acceptance Criteria**:
- All demo service tests PASS (GREEN phase)
- Demo showcases ALL platform features
- Realistic data generation for believable demos

#### Task 2.3: Integrate Guest with Demo Service ⏳ TODO
- [ ] Auto-create demo session on guest homepage visit
- [ ] Implement session expiration (30 min timeout)
- [ ] Add registration prompts after demo interactions
- [ ] Implement conversion tracking (which features viewed)
- [ ] Add session cleanup on expiration

**Acceptance Criteria**:
- All integration tests PASS (GREEN phase)
- Seamless guest → demo → registration flow
- Conversion tracking functional

---

### Phase 3: TDD REFACTOR - Clean Code (Days 7-8)

#### Task 3.1: Refactor Guest Role Implementation ⏳ TODO
- [ ] Extract guest session management into service class
- [ ] Consolidate permission checking logic
- [ ] Add comprehensive docstrings
- [ ] Remove code duplication
- [ ] Optimize database queries

**Acceptance Criteria**:
- All tests still PASS after refactoring
- Code follows CLAUDE.md standards (absolute imports, custom exceptions)
- Clean architecture maintained (domain/application/infrastructure)

#### Task 3.2: Refactor Demo Service ⏳ TODO
- [ ] Extract demo data generators into separate modules
- [ ] Create demo workflow orchestrator
- [ ] Add demo service configuration management
- [ ] Consolidate error handling
- [ ] Optimize demo data generation performance

**Acceptance Criteria**:
- All tests still PASS after refactoring
- Code is maintainable and extensible
- Performance targets met (demo responses < 2 seconds)

---

### Phase 4: E2E Testing & Documentation (Days 9-10)

#### Task 4.1: E2E Selenium Tests ⏳ TODO
- [ ] Update `test_guest_complete_journey.py` with demo service interactions
- [ ] Test: Guest lands on homepage → auto demo session created
- [ ] Test: Guest clicks "Try Demo" → demo service opens
- [ ] Test: Guest explores AI content generation demo
- [ ] Test: Guest explores student learning demo
- [ ] Test: Guest clicks "Register" → account creation
- [ ] Test: Session expires → guest gets warning and redirect

**Acceptance Criteria**:
- All E2E tests PASS
- Guest journey smooth and intuitive
- No broken workflows

#### Task 4.2: Documentation Updates ⏳ TODO
- [ ] Update CLAUDE.md with guest role information
- [ ] Update API documentation with guest endpoints
- [ ] Create demo service feature showcase documentation
- [ ] Add guest role to architecture diagrams
- [ ] Update version history (v3.3.0 - Guest Role & Demo Enhancement)

**Acceptance Criteria**:
- All documentation current and accurate
- Clear guidance for developers and users

#### Task 4.3: Docker Infrastructure Verification ⏳ TODO
- [ ] Run `./scripts/app-control.sh status` - all 16 services healthy
- [ ] Run guest role E2E tests in Docker environment
- [ ] Verify demo service accessible to guest users
- [ ] Test session expiration in Docker environment

**Acceptance Criteria**:
- All Docker containers healthy (16/16)
- All E2E tests pass in Docker environment
- Production-ready deployment

---

## 📊 Kanban Board Status

### 🔴 TO DO (Not Started)
- Write RED tests for demo service enhancement
- Write RED tests for guest-demo integration
- Implement demo service enhancements (GREEN)
- Implement guest-demo integration (GREEN)
- Refactor demo service
- Write E2E Selenium tests for guest
- Update documentation
- Verify Docker infrastructure

### 🟡 IN PROGRESS (Active Work)
- **Create Agile Kanban board** ← YOU ARE HERE
- Write RED tests for guest role RBAC (NEXT)

### 🟢 DONE (Completed)
- (None yet - starting sprint)

---

## 🎯 Definition of Done (DoD)

A task is considered DONE when:

1. ✅ **All unit tests PASS** (TDD GREEN phase complete)
2. ✅ **Code refactored** for maintainability (TDD REFACTOR phase complete)
3. ✅ **E2E tests PASS** (Selenium tests validate user journey)
4. ✅ **Docker infrastructure healthy** (all 16 services show ✅)
5. ✅ **Documentation updated** (CLAUDE.md, API docs, version history)
6. ✅ **Code follows CLAUDE.md standards** (absolute imports, custom exceptions, docstrings)
7. ✅ **No regressions** (existing tests still pass)
8. ✅ **Peer review approved** (if applicable)

---

## 📈 Sprint Metrics

**Velocity Target**: Complete all 12 tasks in 10 days

**Progress Tracking**:
- **Day 1-2**: RED phase (write failing tests) - 25% complete
- **Day 3-6**: GREEN phase (implement features) - 50% complete
- **Day 7-8**: REFACTOR phase (clean code) - 75% complete
- **Day 9-10**: E2E & Documentation - 100% complete

**Daily Standup Questions**:
1. What did I complete yesterday?
2. What am I working on today?
3. Are there any blockers?

---

## 🚀 Sprint Review & Retrospective

**Sprint Review** (End of Day 10):
- Demo guest role functionality to stakeholders
- Showcase enhanced demo service with all features
- Demonstrate guest → demo → registration conversion flow
- Review metrics: test coverage, performance, conversion tracking

**Sprint Retrospective**:
- What went well?
- What could be improved?
- Action items for next sprint

---

## 📝 Notes

**TDD Reminder**: Always follow RED → GREEN → REFACTOR cycle
1. **RED**: Write test that fails
2. **GREEN**: Write minimal code to make test pass
3. **REFACTOR**: Clean up code while keeping tests green

**Agile Reminder**:
- Deliver working software incrementally
- Welcome changing requirements
- Reflect and adjust regularly
- Prioritize working software over comprehensive documentation (but still document!)

**Memory System Reminder**:
- Search memory BEFORE starting each task
- Add discoveries to memory DURING work
- Update memory AFTER completing tasks

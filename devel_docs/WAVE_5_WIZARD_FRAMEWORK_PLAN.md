# Wave 5: Wizard Framework - TDD Plan

**Created**: 2025-10-17
**Status**: RED Phase (Planning)
**Methodology**: TDD (RED → GREEN → REFACTOR)

---

## Executive Summary

**Goal**: Extract wizard logic from Wave 4 implementation into a reusable, framework that can be applied to all multi-step wizards (Project Creation, Track Creation, Location Management, etc.).

**Business Value**:
- **Code Reusability**: 70% reduction in wizard code duplication
- **Consistent UX**: All wizards behave identically
- **Faster Development**: New wizards take hours instead of days
- **Easier Maintenance**: Fix bugs once, apply everywhere
- **Better Testing**: Framework tested once, reused everywhere

**Current State**: Wave 4 wizard enhancements embedded in Project Creation wizard
**Target State**: Reusable WizardFramework component used by all wizards

---

## Problem Statement

### Current Issues

1. **Code Duplication**: Each wizard (Project, Track, Location) implements its own navigation, validation, draft system
2. **Inconsistent UX**: Different wizards behave differently
3. **Hard to Maintain**: Bug fixes must be applied to each wizard separately
4. **Slow Development**: Creating new wizard requires reimplementing all logic
5. **Testing Burden**: Each wizard needs separate E2E tests

### Wave 4 Wizard Logic Currently Embedded

**In `org-admin-projects.js` (Project Creation Wizard)**:
- `initializeProjectWizard()` - Component initialization
- `showStep()` - Step visibility management
- `nextProjectStep()` - Forward navigation with validation
- `previousProjectStep()` - Backward navigation
- `resetProjectWizard()` - State cleanup
- Component instances: `wizardProgress`, `wizardValidator`, `wizardDraft`
- State tracking: `currentStepIndex`, `TOTAL_STEPS`

**This logic should be:**
- Extracted into `WizardFramework` class
- Reusable by any wizard
- Configurable via options
- Testable independently

---

## Wave 5 Objectives

### Primary Goals

1. **Create WizardFramework Component** (core framework)
2. **Refactor Project Wizard** (prove framework works)
3. **Apply to Track Wizard** (prove reusability)
4. **Apply to Location Wizard** (optional, time permitting)

### Success Criteria

- ✅ WizardFramework component passes all unit tests
- ✅ Project Wizard refactored to use framework (zero breaking changes)
- ✅ Track Wizard uses framework with <50 lines of custom code
- ✅ All Wave 4 E2E tests still pass
- ✅ Framework documentation complete
- ✅ Performance: No degradation vs Wave 4

---

## TDD Phases

### Phase 1: RED (Write Failing Tests)

**Duration**: 30-45 minutes

**Tasks**:
1. Create unit test file: `tests/unit/frontend/test_wizard_framework.test.js`
2. Write tests for WizardFramework class:
   - Constructor with options
   - `initialize()` method
   - `nextStep()` method with validation
   - `previousStep()` method
   - `goToStep(index)` method
   - `reset()` method
   - `getCurrentStep()` getter
   - `getTotalSteps()` getter
   - Event callbacks (`onStepChange`, `onComplete`, `onError`)
3. Run tests → All fail (framework doesn't exist yet)

**Acceptance Criteria**: 20+ unit tests written, all failing

---

### Phase 2: GREEN (Implementation)

**Duration**: 2-3 hours

#### Task 2.1: Create WizardFramework Component

**File**: `frontend/js/modules/wizard-framework.js`

**Class API**:
```javascript
class WizardFramework {
    constructor(options) {
        // Options: steps, containerId, progressComponent, validatorComponent, draftComponent
    }

    initialize() {
        // Initialize all components, show first step
    }

    async nextStep() {
        // Validate current step, save draft, advance
        // Returns: true if successful, false otherwise
    }

    previousStep() {
        // Navigate backward without validation
        // Returns: true if successful, false otherwise
    }

    goToStep(stepIndex) {
        // Navigate to specific step (if allowed)
        // Returns: true if successful, false otherwise
    }

    reset() {
        // Clear all state, go to step 0
    }

    getCurrentStep() {
        // Returns: current step index
    }

    getTotalSteps() {
        // Returns: total number of steps
    }

    destroy() {
        // Cleanup: stop timers, remove listeners
    }
}
```

**Acceptance Criteria**: All 20+ unit tests pass

#### Task 2.2: Refactor Project Wizard

**File**: `frontend/js/modules/org-admin-projects.js`

**Changes**:
- Replace embedded wizard logic with WizardFramework
- Remove: `showStep()`, local state tracking
- Replace: `nextProjectStep()` → calls `wizard.nextStep()`
- Replace: `previousProjectStep()` → calls `wizard.previousStep()`
- Replace: `resetProjectWizard()` → calls `wizard.reset()`
- Replace: `initializeProjectWizard()` → creates WizardFramework instance

**Acceptance Criteria**: All Wave 4 E2E tests pass (25 tests)

#### Task 2.3: Apply Framework to Track Wizard

**File**: `frontend/js/modules/org-admin-tracks.js` (or new file)

**Implementation**:
- Create Track Creation wizard HTML structure
- Initialize WizardFramework with track-specific config
- Custom logic: <50 lines

**Acceptance Criteria**: Track wizard functional, uses framework

---

### Phase 3: REFACTOR (Optimize & Polish)

**Duration**: 1-2 hours

**Tasks**:
1. **Performance Optimization**: Profile and optimize
2. **Error Handling**: Comprehensive error messages
3. **Documentation**: JSDoc comments, usage guide
4. **Code Quality**: Remove duplication, improve naming
5. **Framework Extensions**: Add hooks for custom behavior

**Acceptance Criteria**:
- Framework documented
- Performance: <10ms per navigation
- Zero breaking changes
- Usage guide created

---

## Technical Design

### WizardFramework Architecture

```
WizardFramework
├── Constructor (options)
├── Components
│   ├── WizardProgress (optional)
│   ├── WizardValidator (optional)
│   └── WizardDraft (optional)
├── State Management
│   ├── currentStepIndex
│   ├── totalSteps
│   ├── stepHistory[]
│   └── isDirty (has unsaved changes)
├── Navigation Methods
│   ├── nextStep()
│   ├── previousStep()
│   ├── goToStep(index)
│   └── canNavigateTo(index)
├── Lifecycle Methods
│   ├── initialize()
│   ├── reset()
│   └── destroy()
└── Event Callbacks
    ├── onStepChange(oldStep, newStep)
    ├── onValidationError(errors)
    ├── onDraftSaved(draft)
    └── onComplete(data)
```

### Configuration Schema

```javascript
const wizardConfig = {
    // Required
    wizardId: 'project-creation-wizard',
    steps: [
        {
            id: 'step-1',
            label: 'Project Details',
            panelSelector: '#projectStep1',
            required: true
        },
        // ... more steps
    ],

    // Optional Components
    progress: {
        enabled: true,
        containerSelector: '#wizard-progress',
        allowBackNavigation: true
    },

    validation: {
        enabled: true,
        formSelector: '#wizardForm',
        validateOnBlur: true,
        validateOnSubmit: true
    },

    draft: {
        enabled: true,
        autoSaveInterval: 30000,
        storage: 'localStorage'
    },

    // Callbacks
    onStepChange: (oldIndex, newIndex) => {},
    onValidationError: (errors) => {},
    onDraftSaved: (draft) => {},
    onComplete: (data) => {},
    onError: (error) => {}
};
```

### Usage Example

```javascript
// Initialize framework
const projectWizard = new WizardFramework({
    wizardId: 'project-creation-wizard',
    steps: [
        { id: 'basic-info', label: 'Project Details', panelSelector: '#projectStep1' },
        { id: 'sub-projects', label: 'Configure Locations', panelSelector: '#projectStep2' },
        { id: 'tracks', label: 'Training Tracks', panelSelector: '#projectStep3' },
        { id: 'members', label: 'Assign Members', panelSelector: '#projectStep4' },
        { id: 'review', label: 'Review & Create', panelSelector: '#projectStep5' }
    ],
    progress: { enabled: true, containerSelector: '#project-wizard-progress' },
    validation: { enabled: true, formSelector: '#createProjectForm' },
    draft: { enabled: true, autoSaveInterval: 30000 },
    onStepChange: (oldIdx, newIdx) => console.log(`Step ${oldIdx} → ${newIdx}`),
    onComplete: (data) => submitProjectForm(data)
});

// Initialize wizard
await projectWizard.initialize();

// Navigation (called from HTML buttons)
await projectWizard.nextStep();  // Forward
projectWizard.previousStep();     // Back
projectWizard.goToStep(2);        // Jump to step 3

// Cleanup
projectWizard.reset();
projectWizard.destroy();
```

---

## Test Strategy

### Unit Tests (20+ tests)

**File**: `tests/unit/frontend/test_wizard_framework.test.js`

**Test Categories**:
1. **Constructor & Initialization** (5 tests)
   - Valid options create instance
   - Invalid options throw errors
   - Optional components initialized when enabled
   - Callbacks registered correctly
   - First step shown after initialize()

2. **Navigation** (8 tests)
   - nextStep() advances to next step
   - nextStep() blocked by validation errors
   - previousStep() goes back
   - previousStep() blocked at step 0
   - goToStep() jumps to valid step
   - goToStep() blocked for invalid step
   - Step panels show/hide correctly
   - Progress indicator updates

3. **State Management** (4 tests)
   - getCurrentStep() returns correct index
   - getTotalSteps() returns step count
   - Step history tracked correctly
   - isDirty flag tracks unsaved changes

4. **Lifecycle** (3 tests)
   - reset() clears state and goes to step 0
   - destroy() stops timers and removes listeners
   - Re-initialize after destroy works

### Integration Tests (5+ tests)

**File**: `tests/integration/test_wizard_framework_integration.test.js`

**Test Categories**:
1. Framework + WizardProgress integration
2. Framework + WizardValidator integration
3. Framework + WizardDraft integration
4. Framework with all 3 components
5. Framework graceful degradation

### E2E Tests (Reuse Wave 4 tests)

**File**: `tests/e2e/test_project_wizard_integration.py`

**Status**: Should pass with zero changes (proves backward compatibility)

---

## File Structure

```
frontend/js/modules/
├── wizard-framework.js          # NEW - Core framework
├── wizard-progress.js           # Existing - Wave 4
├── wizard-validation.js         # Existing - Wave 4
├── wizard-draft.js              # Existing - Wave 4
├── org-admin-projects.js        # REFACTOR - Use framework
└── org-admin-tracks.js          # REFACTOR - Use framework

tests/unit/frontend/
├── test_wizard_framework.test.js        # NEW - Unit tests

tests/integration/
├── test_wizard_framework_integration.test.js  # NEW - Integration

tests/e2e/
├── test_project_wizard_integration.py   # Existing - Should still pass
└── test_track_wizard_integration.py     # NEW - Track wizard E2E
```

---

## Risk Analysis

### Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Breaking Changes** | Medium | High | Comprehensive E2E tests, backward compatibility tests |
| **Performance Degradation** | Low | Medium | Performance profiling, benchmarking |
| **Over-Engineering** | Medium | Low | Keep framework simple, add features incrementally |
| **Adoption Resistance** | Low | Low | Clear documentation, migration guide |
| **Bugs in Framework** | Medium | High | Extensive unit tests, integration tests |

---

## Success Metrics

### Quantitative Metrics

- **Code Reduction**: 70% less wizard code in project/track files
- **Test Coverage**: 90%+ coverage of WizardFramework
- **Performance**: <10ms per step navigation
- **Lines of Code**: Framework <500 lines
- **Reusability**: 3+ wizards using framework

### Qualitative Metrics

- **Developer Experience**: Faster wizard creation
- **User Experience**: Consistent behavior across wizards
- **Maintainability**: Single source of truth for wizard logic
- **Documentation Quality**: Complete usage guide, examples

---

## Timeline Estimate

| Phase | Duration | Tasks |
|-------|----------|-------|
| **RED (Tests)** | 30-45 min | Write 20+ failing unit tests |
| **GREEN (Implementation)** | 2-3 hours | Framework + Project refactor + Track wizard |
| **REFACTOR (Polish)** | 1-2 hours | Optimize, document, finalize |
| **Total** | 4-6 hours | Full Wave 5 completion |

---

## Dependencies

### Prerequisites

- ✅ Wave 4 complete (WizardProgress, WizardValidator, WizardDraft)
- ✅ Project wizard functional
- ✅ E2E tests passing

### Blocked By

- None (can start immediately)

### Blocks

- Future wizards (Location Management, Course Creation, etc.)

---

## Next Actions

### Immediate (RED Phase)

1. Create `tests/unit/frontend/test_wizard_framework.test.js`
2. Write 20+ unit tests for WizardFramework
3. Run tests → verify all fail
4. Document test expectations

### Next (GREEN Phase)

1. Create `frontend/js/modules/wizard-framework.js`
2. Implement WizardFramework class
3. Run unit tests → all pass
4. Refactor Project wizard
5. Run Wave 4 E2E tests → all pass
6. Apply to Track wizard

### Final (REFACTOR Phase)

1. Performance profiling
2. Error handling improvements
3. Documentation: JSDoc + usage guide
4. Code cleanup
5. Final testing

---

## Conclusion

Wave 5 will transform the wizard implementation from embedded, duplicated code to a clean, reusable framework. This sets the foundation for rapid wizard development across the platform.

**Expected Outcome**: Production-ready WizardFramework that powers all multi-step workflows in the Course Creator Platform.

---

**Status**: 🔴 RED Phase - Planning Complete
**Next Step**: Create unit tests for WizardFramework
**Estimated Completion**: 4-6 hours from start

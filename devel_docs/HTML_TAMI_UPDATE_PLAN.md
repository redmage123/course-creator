# Org Admin Dashboard - Tami Class Update Plan

**Date:** 2025-10-17
**Task:** Apply Tami button, form, and card classes to existing HTML

## Current Status Analysis

### Buttons (Already Complete ✅)
- **btn-primary**: ~29 instances found
- **btn-secondary**: ~10 instances found
- **btn-outline**: ~4 instances found
- All buttons already have proper Tami classes applied

### Forms (Needs Update ❌)
- **Total input fields**: 87
- **With form-input class**: 7 (8%)
- **Missing form-input class**: ~80 fields
- **Textarea fields**: Need form-input class
- **Select fields**: Need form-select class

### Cards (Mostly Complete ✅)
- **stat-card**: 5+ instances (complete)
- **action-card**: 4 instances (complete)
- **summary-card**: Present
- **card-hover-bg**: Present
- Cards appear to be properly structured

## Update Strategy

### Phase 1: Form Inputs (Text, Email, Tel, URL, Number, Date)
Add `class="form-input"` to:
1. Organization settings form (lines 1290-1430)
2. Add instructor modal (lines 1530-1540)
3. Project creation modal (lines 1716-1790)
4. Location forms (lines 1849-1871, 2160-2264)
5. Track search input (line 1244)
6. Other standalone inputs

### Phase 2: Textareas
Add `class="form-input"` to:
1. Organization description textarea (line 1301)
2. Any other textarea elements

### Phase 3: Select Dropdowns
Add `class="form-select"` to:
1. State/Province select (line 1315)
2. Country select (line 1367)
3. Track difficulty selects
4. Any other select elements

### Phase 4: Form Labels
Add `class="form-label"` to labels that don't have it:
1. Organization settings labels
2. Modal form labels
3. Other form labels

### Phase 5: Special Cases
- Checkboxes: Use existing classes (already styled)
- File inputs: Keep existing classes (file-input-hidden)
- Radio buttons: Use existing classes (project-type-radio)

## Specific Updates Required

### Organization Settings Section (Lines 1290-1450)
```html
<!-- BEFORE -->
<input type="text" id="orgNameSetting" name="name" required>

<!-- AFTER -->
<input type="text" id="orgNameSetting" name="name" class="form-input" required>
```

### Instructor Modal (Lines 1530-1540)
```html
<!-- BEFORE -->
<input type="email" id="instructorEmail" name="email" required>

<!-- AFTER -->
<input type="email" id="instructorEmail" name="email" class="form-input" required>
```

### Project Modal (Lines 1716-1790)
```html
<!-- BEFORE -->
<input type="text" id="projectName" name="name" required>

<!-- AFTER -->
<input type="text" id="projectName" name="name" class="form-input" required>
```

### Location Forms (Lines 1849-1871)
```html
<!-- BEFORE -->
<input type="text" id="locationName" class="form-input" placeholder="...">

<!-- AFTER (already has class) -->
<input type="text" id="locationName" class="form-input" placeholder="...">
```

### Select Dropdowns
```html
<!-- BEFORE -->
<select id="orgStateProvinceSetting" name="state_province">

<!-- AFTER -->
<select id="orgStateProvinceSetting" name="state_province" class="form-select">
```

### Textareas
```html
<!-- BEFORE -->
<textarea id="orgDescriptionSetting" name="description" rows="3"></textarea>

<!-- AFTER -->
<textarea id="orgDescriptionSetting" name="description" rows="3" class="form-input"></textarea>
```

## Testing Requirements

### Pre-Update Tests
1. ✅ Backup created: `org-admin-dashboard.html.backup`
2. ✅ Test suite created: `tests/tami/e2e/test_dashboard_updates.py`

### Post-Update Tests
1. All navigation tabs work
2. All buttons are clickable
3. All forms accept input
4. All modals open and close
5. Form validation still works
6. No JavaScript console errors
7. Visual appearance matches Tami design system

## Risk Mitigation

1. **Backup**: Original file backed up before changes
2. **Incremental**: Apply changes in small batches
3. **Testing**: Test each section after updates
4. **Rollback**: Can revert from backup if issues arise

## Success Criteria

- ✅ All text/email/tel/url/number/date inputs have `form-input` class
- ✅ All textareas have `form-input` class
- ✅ All select elements have `form-select` class
- ✅ All labels have `form-label` class (where appropriate)
- ✅ All buttons already have proper Tami classes (btn-primary, btn-secondary, btn-outline)
- ✅ All cards already have proper Tami classes (stat-card, action-card)
- ✅ No broken functionality
- ✅ No JavaScript console errors
- ✅ Visual consistency with Tami design system

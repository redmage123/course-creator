# Session Start Checklist

**Purpose:** Ensure Claude Code starts every session with proper context and methodology

**Frequency:** EVERY session start (mandatory)

---

## ✅ Session Initialization (30 seconds)

### 1. Memory Context Load
```bash
# Check user preferences (ALWAYS FIRST)
python3 .claude/query_memory.py search "Agile"
python3 .claude/query_memory.py search "TDD"
python3 .claude/query_memory.py search "TodoWrite"

# Check recent facts
python3 .claude/query_memory.py list 20
```

**Expected Results:**
- Found facts about Agile methodology
- Found facts about TDD approach
- Found facts about TodoWrite usage
- Reviewed last 20 facts for context

### 2. Methodology Reminder (Self-Check)
- [ ] User wants Agile with Kanban boards (automatic, not on request)
- [ ] User wants TDD (tests before code, always)
- [ ] User wants TodoWrite tracking (proactive, not reactive)
- [ ] User doesn't want to be reminded of these preferences

### 3. Session Type Identification

**Is this a NEW task?**
- [ ] Yes → Create TodoWrite Kanban board IMMEDIATELY
- [ ] No → Load existing TodoWrite board state

**Is this a CONTINUATION?**
- [ ] Yes → Review last session's memory updates
- [ ] No → Proceed with new task workflow

### 4. Domain-Specific Memory Check

**If working on API:**
```bash
python3 .claude/query_memory.py search "api-endpoints"
python3 .claude/query_memory.py search "authentication"
```

**If working on Frontend:**
```bash
python3 .claude/query_memory.py search "frontend"
python3 .claude/query_memory.py search "HTTPS"
```

**If fixing bugs:**
```bash
python3 .claude/query_memory.py search "bugfix"
python3 .claude/query_memory.py search "bug"
```

**If refactoring:**
```bash
python3 .claude/query_memory.py search "architecture"
python3 .claude/query_memory.py search "SOLID"
```

---

## 🎯 Session Goals Declaration

Before starting work, declare:

1. **Task Type:** <New feature | Bug fix | Refactoring | Testing | Documentation>
2. **Methodology:** Agile + Kanban + TDD
3. **Tools:** TodoWrite, Memory, TDD
4. **Success Criteria:** <What evidence will prove completion?>

---

## 🚨 Red Flags (Stop if Any Apply)

- [ ] No memory search performed yet → STOP, search first
- [ ] No TodoWrite board created for multi-step task → STOP, create board
- [ ] Starting to code without tests → STOP, write tests first
- [ ] About to claim success without evidence → STOP, gather evidence

---

## 📝 Session Start Template (Copy-Paste)

```markdown
## Session Start: <Date>

### Memory Context Loaded
- [x] User preferences checked (Agile/TDD/TodoWrite)
- [x] Recent facts reviewed (last 20)
- [x] Domain-specific facts loaded

### Methodology Confirmed
- [x] Agile with Kanban boards (automatic)
- [x] TDD (tests before code)
- [x] TodoWrite tracking (proactive)

### Task Identification
- **Task:** <task description>
- **Type:** <New feature | Bug fix | Refactoring | etc.>
- **Approach:** Memory → TodoWrite → TDD → Memory

### Ready to Start
✅ All context loaded, methodology internalized, proceeding with task
```

---

**Last Updated:** 2025-10-05
**Review Frequency:** Weekly
**Status:** Active Template

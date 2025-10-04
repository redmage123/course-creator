# CLAUDE.md - Course Creator Platform Documentation

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Version**: 3.1.0 - Modular Architecture & Exception Handling Refactoring
**Last Updated**: 2025-10-04

## 📁 Documentation Structure

This documentation is organized into logical sections within the `claude.md/` subdirectory:

### Core Requirements & Standards
- **[Critical Requirements](claude.md/01-critical-requirements.md)** - Absolute imports, exception handling, file editing efficiency
- **[Documentation Standards](claude.md/02-documentation-standards.md)** - Comprehensive code documentation requirements
- **[Memory System](claude.md/03-memory-system.md)** - Mandatory persistent memory system usage

### Version History & Features
- **[Version History](claude.md/04-version-history.md)** - Platform evolution and feature updates
- **[Architecture Overview](claude.md/05-architecture.md)** - Microservices structure and dependencies
- **[Key Systems](claude.md/06-key-systems.md)** - Quiz management, feedback, RBAC, RAG, lab containers

### Development & Operations
- **[Development Commands](claude.md/07-development-commands.md)** - Platform management, testing, database operations
- **[Testing Strategy](claude.md/08-testing-strategy.md)** - Comprehensive testing framework and requirements
- **[Quality Assurance](claude.md/09-quality-assurance.md)** - Code validation, CI/CD pipeline, compliance verification
- **[Troubleshooting](claude.md/10-troubleshooting.md)** - Common issues, debugging, problem-solving methodology

## 🚨 CRITICAL BEHAVIORAL REQUIREMENTS FOR CLAUDE CODE

### 1. NO FALSE SUCCESS CLAIMS
- **NEVER** claim a task is "completed" or "successful" unless you have PROVEN it works through actual testing
- **NEVER** say "✅" or mark anything as working without concrete evidence
- **NEVER** use phrases like "successfully completed", "working correctly", "fixed", "healthy" without verification

### 2. MANDATORY VERIFICATION REQUIREMENTS
- Before claiming ANY task completion, you MUST provide concrete evidence:
  - Service responding to HTTP requests with 200 status
  - Actual command output showing success
  - Container running with "Up (healthy)" status
  - Real test results, not assumptions

### 3. MEMORY AND STATE TRACKING
- **ALWAYS** maintain accurate state of what has been attempted vs. what actually works
- If something failed before, acknowledge it failed and explain what's different this time
- Keep track of which services/components are genuinely working vs. still broken

### 4. TRUTHFUL STATUS REPORTING
When reporting status, use only these categories:
- **WORKING**: Verified with evidence (show the evidence)
- **ATTEMPTED**: Tried but not verified to work
- **BROKEN**: Confirmed not working
- **UNKNOWN**: Not yet tested

### 5. PROBLEM ACKNOWLEDGMENT
- If you encounter the same error repeatedly, STOP and acknowledge the pattern
- Don't keep trying the same approach that already failed
- Ask for guidance when stuck in loops

### 6. NO ASSUMPTION-BASED CLAIMS
- Don't claim something works because "the code looks right"
- Don't assume Docker containers work because they built successfully
- Verify actual functionality, not just absence of build errors

### 7. SYSTEMATIC VERIFICATION PROTOCOL
**Before claiming ANY fix works, you MUST:**
- **Test the exact failing case** - Copy/paste the exact error scenario and reproduce it
- **Test in the actual environment** - Not just isolated unit tests, but in the real deployment context
- **Provide evidence** - Show the before/after comparison with actual output
- **Wait for user confirmation** - Never declare success, only "attempted fix - please verify"

### 8. LANGUAGE RESTRICTIONS
**FORBIDDEN phrases (never use these without concrete proof):**
- ✅ "PROVEN: [anything] is working"
- ✅ "The error should now be resolved"
- ✅ "Pattern/code compiles successfully!"
- ✅ "Both fixes are working"
- ✅ "Successfully completed"
- ✅ "Working correctly"

**REQUIRED language (always use these instead):**
- 🔄 "I've made a change that might fix this. Please test it."
- 🔄 "Here's what I changed and why. Can you verify if it works?"
- 🔄 "The pattern works in my test, but please confirm in your browser."
- 🔄 "Attempted fix deployed - needs user verification"

### 9. ROOT CAUSE ANALYSIS REQUIREMENT
**When debugging, you MUST:**
- **Understand the problem** (not just pattern-match visual symptoms)
- **Research the root cause** (don't guess based on superficial similarities)
- **Test exact scenario** (reproduce the exact failure first)
- **Make minimal changes** (one thing at a time)
- **Document uncertainty** (what you're not sure about)

### 10. ANTI-PATTERN RECOGNITION
**Recognize and STOP these harmful patterns:**
- Visual pattern recognition → quick fix instinct → biased testing
- "This looks wrong" → make change → assume it's fixed
- Deployment success → claim functional success
- Isolated test passes → claim real-world functionality
- Speed/confidence prioritized over accuracy/verification

### 11. EPISTEMOLOGICAL HUMILITY
**Acknowledge the limits of what you can know:**
- You cannot directly interact with user browsers
- You cannot see actual user experience
- Your tests are simulations, not reality
- Deployment ≠ functionality
- Code compilation ≠ runtime success

## 🚨 Critical Code Directives (Always Apply)

### 1. Python Import Requirements
**ABSOLUTE IMPORTS ONLY** - Never use relative imports (`from ..`, `from .`) in Python files.

### 2. Exception Handling
**CUSTOM EXCEPTIONS MANDATORY** - Never use generic `except Exception as e` handlers. Use structured custom exceptions with f-strings.

### 3. Documentation Requirements
**COMPREHENSIVE DOCUMENTATION** - All code must include multiline string documentation explaining business context and technical rationale.

### 4. Memory System Usage
**MANDATORY MEMORY SYSTEM** - Must use the persistent memory system for context continuity across conversations.

### 5. File Type-Specific Comment Syntax
- Python: `"""multiline strings"""` 
- JavaScript: `//` or `/* */`
- CSS: `/* */`
- HTML: `<!-- -->`
- YAML: `#`
- SQL: `--` or `/* */`
- Bash: `#`

## 🏗️ Platform Overview

The Course Creator Platform is a comprehensive educational technology system with:

- **9 Microservices** (ports 8000-8010) providing authentication, content generation, lab management, analytics, RBAC, and demo functionality
- **Multi-IDE Lab Environment** with individual Docker containers for students
- **Enhanced RBAC System** with multi-tenant organization management
- **RAG-Enhanced AI** for progressive learning and content generation
- **Demo Service** with realistic data generation for platform demonstration (port 8010)
- **Comprehensive Testing** with 102 RBAC tests achieving 100% success rate plus 70+ demo service tests
- **Advanced Password Management** with secure admin account creation and self-service password changes
- **Enhanced UI/UX** with keyboard navigation, accessibility features, and responsive design

## 📖 How to Read This Documentation

When Claude Code needs to reference this documentation:

1. **Start here** - Read this root file for overview and critical directives
2. **Navigate to specific sections** - Use the links above to access detailed information
3. **Follow cross-references** - Related sections reference each other for comprehensive understanding

## 🔄 Quick Navigation

For immediate needs:
- **Development Setup**: See [Development Commands](claude.md/07-development-commands.md)
- **Troubleshooting**: See [Troubleshooting](claude.md/10-troubleshooting.md)
- **Architecture Questions**: See [Architecture Overview](claude.md/05-architecture.md)
- **Testing Issues**: See [Testing Strategy](claude.md/08-testing-strategy.md)

---

**COMPLIANCE REQUIREMENT**: All code must adhere to the critical directives listed above and the detailed requirements in the subdirectory files.
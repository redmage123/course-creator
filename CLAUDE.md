# CLAUDE.md - Course Creator Platform Documentation

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Version**: 3.0.0 - Password Management & Enhanced UI Features  
**Last Updated**: 2025-08-11

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

## 🚨 Critical Directives (Always Apply)

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
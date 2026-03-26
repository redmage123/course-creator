# FNBC Complete Platform Walkthrough — First National Bank of Commerce

**Document Version:** 1.0
**Prepared By:** TechUni Course Creator Platform Team
**Date:** 2026-03-24
**Audience:** Platform Owner / Demo Reviewer

---

## Executive Summary

This document provides a complete, step-by-step walkthrough of the TechUni Course Creator Platform using First National Bank of Commerce (FNBC) as the demo client scenario. FNBC is launching an 8-week Graduate Developer Program for 2026, training two distinct cohorts simultaneously:

- **Track A — Software Developers:** 3 participants (Python, Java, SQL, DevOps, Agile, Code Quality, Capstone)
- **Track B — Business Analysts:** 2 participants (BA Fundamentals, Requirements Engineering, SQL for Analysts, Process Modeling, Data Analysis, Stakeholder Management, Agile for BAs, Capstone)

This walkthrough covers every major platform feature: organization registration, the project wizard, AI-assisted content creation via the chat interface, student enrollment and journey simulation, scheduling, and student metrics reporting. The scenario is designed to be realistic — scores vary, one student submits late in Week 4, and final capstone grades reflect genuine effort differentiation.

**Platform Access Points Referenced Throughout:**
- Main Platform: `https://app.techuni.ai` (or `http://localhost:3000` in self-hosted deployments)
- Admin Dashboard: `/admin.html`
- Instructor Dashboard: `/instructor-dashboard.html`
- Student Dashboard: `/student-dashboard.html`
- Interactive Labs: `/lab.html`
- AI Assistant (RAG): Port `8009` — accessible via the purple chat button (bottom-right corner)

---

## Part 1: Organization Setup — App Wizard

### Step 1.1 — Navigate to the Organization Registration Page

Open a browser and go to the platform home page. Click **"Register Your Organization"** or navigate directly to `/register-organization`. This launches the Organization Setup Wizard — a multi-step guided form.

> **Note on the Wizard Draft System:** The platform automatically saves wizard progress to browser `localStorage` every 30 seconds. If you close the browser mid-setup, reopening the wizard will prompt: *"Resume Draft? Last saved: X minutes ago."* Click **Resume Draft** to continue from where you left off. Drafts expire after 7 days.

---

### Step 1.2 — Wizard Step 1: Organization Details

Fill in the following fields:

| Field | Value |
|---|---|
| **Organization Name** | First National Bank of Commerce |
| **Slug / URL Handle** | `fnbc` (auto-generated, editable) |
| **Website** | `fnbc-training.com` |
| **Industry** | Financial Services |
| **Organization Size** | 1,000–5,000 employees |
| **Description** | FNBC's internal graduate development program for technical staff, delivering structured 8-week training tracks for Software Developers and Business Analysts. |
| **Country** | United States |
| **Timezone** | America/New_York (EST) |

Click **"Next: Admin Account"**.

---

### Step 1.3 — Wizard Step 2: Administrator Account

Create the primary organization administrator account:

| Field | Value |
|---|---|
| **Admin Full Name** | Sarah Thompson |
| **Admin Email** | sarah.training@fnbc.com |
| **Password** | `FNBC@Training2026` |
| **Confirm Password** | `FNBC@Training2026` |
| **Job Title** | Head of Graduate Development |
| **Phone** | +1 (212) 555-0147 |

The system enforces password complexity: minimum 8 characters, at least one uppercase, one number, one special character. `FNBC@Training2026` satisfies all requirements.

Click **"Next: Platform Configuration"**.

---

### Step 1.4 — Wizard Step 3: Platform Configuration

| Setting | Value |
|---|---|
| **Learning Format** | Instructor-Led with Self-Paced Content |
| **Session Type** | Hybrid (Live sessions + async lab work) |
| **Default Language** | English (US) |
| **Certificate Issuer Name** | First National Bank of Commerce — Graduate Development |
| **Completion Threshold** | 80% (students must achieve ≥80% average to pass) |
| **Allow Student Self-Enrollment** | No (Admin-controlled enrollment only) |
| **Two-Factor Authentication** | Optional (recommended for instructors) |

Click **"Next: Review & Launch"**.

---

### Step 1.5 — Wizard Step 4: Review and Confirm

The wizard displays a summary of all entered information. Verify:

- Organization: **First National Bank of Commerce**
- Admin: **sarah.training@fnbc.com**
- Website: **fnbc-training.com**
- Completion threshold: **80%**
- Student enrollment: **Admin-controlled**

Click **"Create Organization"**. The system provisions:

1. The FNBC organization record in the database
2. The org-admin account for `sarah.training@fnbc.com`
3. A default organization settings profile
4. Sends a verification email to `sarah.training@fnbc.com`

**Expected System Response:**

```
Organization "First National Bank of Commerce" created successfully.
Admin account activated for sarah.training@fnbc.com.
You are now being redirected to your Organization Dashboard.
```

Sarah is redirected to the **Org Admin Dashboard** at `/org-admin-dashboard.html`.

---

### Step 1.6 — First Login and Dashboard Tour

Sarah logs in with `sarah.training@fnbc.com` / `FNBC@Training2026`. The platform presents the **Org Admin Dashboard** with:

- **Overview Panel:** Zero projects, zero students, zero active sessions (fresh account)
- **Quick Actions:** Create Project, Invite Instructor, Bulk Enroll Students, View Analytics
- **Navigation Tabs:** Projects, Instructors, Students, Tracks, Analytics, Settings
- **AI Assistant:** Purple chat button visible in the bottom-right corner (powered by RAG service on port 8009)

The platform offers a **guided tour overlay** on first login. Sarah clicks **"Take the Tour"** to understand the dashboard layout before creating the program.

---

## Part 2: Content Creation — App Wizard (Software Developer Track)

### Step 2.1 — Create the Master Project

From the Org Admin Dashboard, Sarah clicks **"Create Project"**. This opens the **Project Creation Wizard**.

**Wizard Step 1 — Project Details:**

| Field | Value |
|---|---|
| **Project Name** | FNBC Graduate Developer Program 2026 |
| **Slug** | `fnbc-grad-dev-2026` |
| **Description** | Comprehensive 8-week graduate training program equipping new FNBC technical hires with foundational software development and business analysis skills. Two parallel tracks running April 7 – May 29, 2026. |
| **Target Audience** | Graduate-level new hires (0–2 years experience) |
| **Difficulty Level** | Beginner to Intermediate (progressive) |
| **Estimated Duration** | 8 weeks (40 hours total per track) |
| **Start Date** | 2026-04-07 |
| **End Date** | 2026-05-29 |

**Wizard Step 2 — Project Configuration:**

| Setting | Value |
|---|---|
| **Format** | Instructor-Led Cohort |
| **Assessment Model** | Weekly quizzes + hands-on labs + capstone project |
| **Passing Score** | 80% |
| **Certificate on Completion** | Yes |
| **Auto-balance students across instructors** | OFF (manual assignment) |

Click **"Next: Sub-Projects"**.

---

### Step 2.2 — Create Sub-Projects (Tracks)

**Wizard Step 3 — Sub-Projects:**

The wizard prompts: *"Does this project have multiple cohorts, departments, or tracks? Add sub-projects to organize them."*

Sarah clicks **"Add Sub-Project"** twice:

**Sub-Project 1:**

| Field | Value |
|---|---|
| **Name** | Software Development Track |
| **Slug** | `sw-dev-track` |
| **Description** | 8-week program covering Python, Java, SQL, Software Architecture, DevOps, Agile, Code Quality, and a capstone project. Designed for incoming software engineering graduates. |
| **Start Date** | 2026-04-07 |
| **End Date** | 2026-05-29 |
| **Target Roles** | Software Developer, Junior Engineer |

**Sub-Project 2:**

| Field | Value |
|---|---|
| **Name** | Business Analysis Track |
| **Slug** | `ba-track` |
| **Description** | 8-week program covering BA Fundamentals, Requirements Engineering, SQL for Analysts, Process Modeling, Data Analysis, Stakeholder Management, Agile for BAs, and a BA capstone project. |
| **Start Date** | 2026-04-07 |
| **End Date** | 2026-05-29 |
| **Target Roles** | Business Analyst, Junior BA |

Click **"Next: Review Tracks"**. The wizard auto-generates placeholder tracks for each sub-project. Sarah reviews and clicks **"Create Project"**.

**System confirmation:**

```
Project "FNBC Graduate Developer Program 2026" created.
  Sub-project: Software Development Track (sw-dev-track)
  Sub-project: Business Analysis Track (ba-track)
Redirecting to project management view...
```

---

### Step 2.3 — Assign Instructors

Before creating course content, Sarah creates instructor accounts. From the **Instructors** tab:

**Instructor 1 — Software Development Track:**

| Field | Value |
|---|---|
| **Name** | Dr. Michael Rivera |
| **Email** | m.rivera@fnbc-training.com |
| **Role** | Instructor |
| **Assigned Track** | Software Development Track |
| **Zoom Link** | https://zoom.us/j/fnbc-swdev |
| **Slack Channel** | #sw-dev-track-2026 |

**Instructor 2 — Business Analysis Track:**

| Field | Value |
|---|---|
| **Name** | Claire Okafor |
| **Email** | c.okafor@fnbc-training.com |
| **Role** | Instructor |
| **Assigned Track** | Business Analysis Track |
| **Zoom Link** | https://zoom.us/j/fnbc-ba |
| **Slack Channel** | #ba-track-2026 |

The platform enforces the rule: **at least one instructor must be assigned to each track** before any course is published or students are enrolled.

---

### Step 2.4 — Software Development Track: 8-Week Course Structure (App Wizard)

Dr. Rivera logs into the Instructor Dashboard (`m.rivera@fnbc-training.com`). He navigates to the **Software Development Track** and begins creating the 8-week curriculum using the **Course Creation Wizard**.

For each week, he clicks **"Create New Course"** → selects the Software Development Track → uses **"App Wizard"** path.

---

#### Week 1: Python Fundamentals

**Course Setup:**

| Field | Value |
|---|---|
| **Course Title** | Python Fundamentals |
| **Sequence Number** | 1 |
| **Week** | Week 1 (Apr 7–11, 2026) |
| **Difficulty** | Beginner |
| **Estimated Hours** | 5 hours |
| **Description** | Introduction to Python programming covering control flow, functions, object-oriented programming, and error handling. Students will write, test, and debug Python programs in the integrated lab environment. |

**Module 1.1: Python Syntax and Control Flow (90 min)**

*Lessons:*
- 1.1.1 — Python Setup and Environment (PyCharm, VS Code in Lab)
- 1.1.2 — Variables, Data Types, and Type Casting
- 1.1.3 — Conditional Statements: `if`, `elif`, `else`
- 1.1.4 — Loops: `for` and `while` with `range()`
- 1.1.5 — List Comprehensions

*Quiz — Module 1.1 Check:* 5 multiple-choice questions
- Q1: Which keyword is used to define a function in Python?
- Q2: What is the output of `print(type(3.14))`?
- Q3: Which loop is best suited for iterating over a list of unknown length?
- Q4: What does `break` do inside a loop?
- Q5: How do you write a comment in Python?

**Module 1.2: Functions and Scope (90 min)**

*Lessons:*
- 1.2.1 — Defining and Calling Functions
- 1.2.2 — Parameters, Arguments, and Return Values
- 1.2.3 — Default Parameters and `*args`, `**kwargs`
- 1.2.4 — Variable Scope: Local vs. Global
- 1.2.5 — Lambda Functions and `map()`/`filter()`

*Exercise:* Write a function `calculate_compound_interest(principal, rate, years)` that returns the final balance. Test with FNBC loan scenario values.

**Module 1.3: Object-Oriented Programming (90 min)**

*Lessons:*
- 1.3.1 — Classes and Objects: `__init__`, attributes
- 1.3.2 — Instance Methods and `self`
- 1.3.3 — Inheritance and Method Overriding
- 1.3.4 — Encapsulation and `__str__`
- 1.3.5 — Polymorphism in Practice

*Exercise:* Create a `BankAccount` class with `deposit()`, `withdraw()`, and `get_balance()` methods. Extend it with a `SavingsAccount` subclass that applies interest.

**Module 1.4: Error Handling (60 min)**

*Lessons:*
- 1.4.1 — Exception Types in Python
- 1.4.2 — `try`, `except`, `finally`
- 1.4.3 — Raising Custom Exceptions
- 1.4.4 — Logging Errors with `logging` module

*Lab — Week 1 Lab: Python Banking Calculator*

> **Lab Type:** Coding Exercise | **Duration:** 60 minutes | **IDE:** VS Code (recommended) or Python terminal
>
> **Instructions:** Build a command-line banking calculator that accepts user input for account operations (deposit, withdraw, check balance). Implement full error handling for invalid inputs, overdraft attempts, and divide-by-zero in interest calculations. Include at least 3 custom exception classes. The lab environment pre-loads Python 3.11 with `pytest`.
>
> **Acceptance Tests (auto-graded):**
> - `test_deposit_valid_amount` — passes
> - `test_withdraw_insufficient_funds_raises_exception` — passes
> - `test_custom_exception_hierarchy` — passes
> - `test_logging_on_error` — passes

**Week 1 Quiz (Graded — 10 questions, 20 minutes):**

| # | Question | Type |
|---|---|---|
| 1 | Write a list comprehension to square all even numbers from 1–20 | Code Completion |
| 2 | Explain the difference between `==` and `is` in Python | Short Answer |
| 3 | What is the output of `[x*2 for x in range(5)]`? | Multiple Choice |
| 4 | Which OOP principle does method overriding implement? | Multiple Choice |
| 5 | Write a function that catches `ValueError` and returns -1 | Code Completion |
| 6 | What does `__init__` do in a Python class? | Multiple Choice |
| 7 | True/False: Python uses static typing by default | True/False |
| 8 | What is `*args` used for? | Multiple Choice |
| 9 | Correct the syntax error: `def greet(name) print(name)` | Code Fix |
| 10 | Describe one advantage of OOP over procedural programming | Short Answer |

---

#### Week 2: Java Core Concepts

**Course Setup:**

| Field | Value |
|---|---|
| **Course Title** | Java Core Concepts |
| **Sequence Number** | 2 |
| **Week** | Week 2 (Apr 14–18, 2026) |
| **Difficulty** | Beginner–Intermediate |
| **Estimated Hours** | 5 hours |
| **Description** | Foundational Java programming: class design, interfaces, generics, the Collections Framework, and functional-style streams. Students transition from Python to a statically-typed, JVM-based language. |

**Module 2.1: Java Fundamentals and Class Design (90 min)**

*Lessons:*
- 2.1.1 — Java vs Python: Type System, Compilation, JVM
- 2.1.2 — Classes, Constructors, and Access Modifiers
- 2.1.3 — Static vs. Instance Members
- 2.1.4 — The `toString()`, `equals()`, and `hashCode()` Methods
- 2.1.5 — Packages and Import Statements

**Module 2.2: Interfaces and Abstract Classes (90 min)**

*Lessons:*
- 2.2.1 — Defining and Implementing Interfaces
- 2.2.2 — Abstract Classes: When to Use vs. Interfaces
- 2.2.3 — Default and Static Interface Methods (Java 8+)
- 2.2.4 — The `Comparable` and `Comparator` Interfaces
- 2.2.5 — Real-World Example: `Payable` Interface for FNBC Transactions

*Exercise:* Define a `Transaction` interface with `execute()` and `rollback()`. Implement `CreditTransaction` and `DebitTransaction` classes. Add a `FraudAlert` interface using `default` methods.

**Module 2.3: Collections Framework (90 min)**

*Lessons:*
- 2.3.1 — `List`, `Set`, `Map`, `Queue` Hierarchies
- 2.3.2 — `ArrayList` vs `LinkedList` Performance
- 2.3.3 — `HashMap` and `TreeMap`: Use Cases
- 2.3.4 — Iterators and Enhanced `for` Loop
- 2.3.5 — Generics: Type Safety in Collections

**Module 2.4: Streams and Functional Java (60 min)**

*Lessons:*
- 2.4.1 — Lambda Expressions and Functional Interfaces
- 2.4.2 — `Stream` API: `filter()`, `map()`, `collect()`
- 2.4.3 — `Optional` for Null Safety
- 2.4.4 — Method References

*Lab — Week 2 Lab: Java Transaction Processor*

> **Lab Type:** Project-Based | **Duration:** 90 minutes | **IDE:** VS Code with Java Extension Pack
>
> **Instructions:** Build a Java `TransactionProcessor` that reads a list of `Transaction` objects, filters by type (credit/debit), sorts by amount, and generates a summary report using the Streams API. The lab provides starter code and 6 JUnit test cases that must all pass before submission.

**Week 2 Quiz:** 10 questions (20 min) — Java syntax, OOP, generics, and one code-tracing question.

---

#### Week 3: SQL and Database Design

**Course Setup:**

| Field | Value |
|---|---|
| **Course Title** | SQL and Database Design |
| **Sequence Number** | 3 |
| **Week** | Week 3 (Apr 21–25, 2026) |
| **Difficulty** | Intermediate |
| **Estimated Hours** | 5 hours |
| **Description** | Relational database design and SQL proficiency: DDL, DML, complex joins, subqueries, indexing, and normalization up to 3NF. Lab uses a PostgreSQL instance seeded with an FNBC-themed banking schema. |

**Module 3.1: Relational Model and DDL (90 min)**

*Lessons:*
- 3.1.1 — Relational Model: Tables, Keys, Relationships
- 3.1.2 — `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`
- 3.1.3 — Data Types: `VARCHAR`, `INTEGER`, `DECIMAL`, `TIMESTAMP`, `UUID`
- 3.1.4 — Constraints: `NOT NULL`, `UNIQUE`, `CHECK`, `DEFAULT`
- 3.1.5 — Primary Keys, Foreign Keys, and Referential Integrity

**Module 3.2: DML — Querying and Manipulating Data (90 min)**

*Lessons:*
- 3.2.1 — `SELECT`, `WHERE`, `ORDER BY`, `LIMIT`
- 3.2.2 — `INSERT`, `UPDATE`, `DELETE`
- 3.2.3 — Aggregate Functions: `COUNT`, `SUM`, `AVG`, `MAX`, `MIN`
- 3.2.4 — `GROUP BY` and `HAVING`
- 3.2.5 — Subqueries and Correlated Subqueries

**Module 3.3: JOINs and Advanced Queries (90 min)**

*Lessons:*
- 3.3.1 — `INNER JOIN`, `LEFT JOIN`, `RIGHT JOIN`, `FULL OUTER JOIN`
- 3.3.2 — Self-Joins and Cross Joins
- 3.3.3 — `UNION` and `INTERSECT`
- 3.3.4 — Window Functions: `ROW_NUMBER()`, `RANK()`, `LAG()`
- 3.3.5 — Common Table Expressions (CTEs)

*Exercise:* Write a query using a CTE and window function to rank FNBC customers by total deposits per branch, then identify the top customer per branch.

**Module 3.4: Indexing and Normalization (60 min)**

*Lessons:*
- 3.4.1 — What Indexes Do and When to Use Them
- 3.4.2 — B-Tree vs. Hash vs. GIN Index Types (PostgreSQL)
- 3.4.3 — 1NF, 2NF, 3NF — Rules and Application
- 3.4.4 — Denormalization Trade-offs

*Lab — Week 3 Lab: FNBC Banking Database Queries*

> **Lab Type:** SQL Coding Exercise | **Duration:** 75 minutes | **IDE:** pgAdmin or psql in browser
>
> **Database Schema (pre-seeded):** `customers`, `accounts`, `transactions`, `branches`, `employees`
>
> **Tasks:**
> 1. Find all customers with account balances exceeding $50,000 — ordered by balance DESC
> 2. Join `transactions` with `accounts` and `customers` to show the full name, account number, and transaction amount for all credits in March 2026
> 3. Using a window function, assign a rank to each branch by total transaction volume
> 4. Normalize a denormalized `customer_accounts_flat` table to 3NF — write the DDL
> 5. Add a GIN index for full-text search on `customer.notes` and explain why GIN was chosen

**Week 3 Quiz:** 10 questions — ERD reading, JOIN output prediction, normalization identification.

---

#### Week 4: Software Architecture

**Course Setup:**

| Field | Value |
|---|---|
| **Course Title** | Software Architecture |
| **Sequence Number** | 4 |
| **Week** | Week 4 (Apr 28–May 2, 2026) |
| **Difficulty** | Intermediate |
| **Estimated Hours** | 5 hours |
| **Description** | Core software architecture patterns: REST API design, microservices decomposition, SOLID principles, and common design patterns (Factory, Observer, Strategy). |

**Module 4.1: REST API Design (90 min)**

*Lessons:*
- 4.1.1 — HTTP Methods: GET, POST, PUT, PATCH, DELETE
- 4.1.2 — Resource Naming Conventions
- 4.1.3 — Status Codes: 200, 201, 400, 401, 403, 404, 422, 500
- 4.1.4 — Request/Response Bodies: JSON Schema
- 4.1.5 — API Versioning Strategies

**Module 4.2: Microservices Architecture (90 min)**

*Lessons:*
- 4.2.1 — Monolith vs. Microservices Trade-offs
- 4.2.2 — Service Boundaries and Domain Decomposition
- 4.2.3 — Inter-Service Communication: REST vs. Message Queues
- 4.2.4 — API Gateways and Service Discovery
- 4.2.5 — Data Isolation: Each Service Owns Its Database

**Module 4.3: Design Patterns (90 min)**

*Lessons:*
- 4.3.1 — Factory Pattern: Object Creation Without Tight Coupling
- 4.3.2 — Observer Pattern: Event-Driven Notifications
- 4.3.3 — Strategy Pattern: Swappable Algorithm Families
- 4.3.4 — Repository Pattern: Data Access Abstraction
- 4.3.5 — FNBC Use Case: Payment Gateway Pattern

**Module 4.4: SOLID Principles (60 min)**

*Lessons:*
- 4.4.1 — Single Responsibility Principle
- 4.4.2 — Open/Closed Principle
- 4.4.3 — Liskov Substitution Principle
- 4.4.4 — Interface Segregation Principle
- 4.4.5 — Dependency Inversion Principle

*Lab — Week 4 Lab: Design a Mini Payment API*

> **Lab Type:** Project-Based | **Duration:** 90 minutes
>
> **Instructions:** Design and partially implement a RESTful payment processing API for FNBC. Requirements: define resource endpoints (accounts, payments, transfers), implement the Strategy pattern for payment method selection (ACH, wire, card), apply the Repository pattern for data access, and demonstrate at least 2 SOLID principles in the code structure. Provide an OpenAPI-style endpoint table.

**Week 4 Quiz:** 10 questions — REST semantics, design pattern identification, SOLID violations.

---

#### Week 5: DevOps Foundations

**Course Setup:**

| Field | Value |
|---|---|
| **Course Title** | DevOps Foundations |
| **Sequence Number** | 5 |
| **Week** | Week 5 (May 5–9, 2026) |
| **Difficulty** | Intermediate |
| **Estimated Hours** | 5 hours |
| **Description** | Core DevOps practices: Git version control workflows, CI/CD pipeline design, Docker containerization, and Jenkins automation. |

**Module 5.1: Git and Branching Strategies (90 min)**

*Lessons:*
- 5.1.1 — Git Fundamentals: `clone`, `add`, `commit`, `push`, `pull`
- 5.1.2 — Branching: `feature/`, `hotfix/`, `release/` conventions
- 5.1.3 — Merging vs. Rebasing
- 5.1.4 — Pull Requests and Code Review Workflows
- 5.1.5 — Git Flow vs. Trunk-Based Development

**Module 5.2: CI/CD Pipelines (90 min)**

*Lessons:*
- 5.2.1 — Continuous Integration: Build → Test → Lint
- 5.2.2 — Continuous Delivery vs. Continuous Deployment
- 5.2.3 — GitHub Actions: Workflow YAML Anatomy
- 5.2.4 — Pipeline Stages: Build, Unit Test, Integration Test, Deploy
- 5.2.5 — Secrets Management in Pipelines

**Module 5.3: Docker and Containerization (90 min)**

*Lessons:*
- 5.3.1 — Containers vs. VMs: Why Containers Win for CI/CD
- 5.3.2 — `Dockerfile`: `FROM`, `COPY`, `RUN`, `EXPOSE`, `CMD`
- 5.3.3 — Docker Build, Tag, and Push
- 5.3.4 — Multi-Stage Builds for Production Images
- 5.3.5 — `docker-compose` for Local Development

**Module 5.4: Jenkins Fundamentals (60 min)**

*Lessons:*
- 5.4.1 — Jenkins Architecture: Master, Agents, Jobs
- 5.4.2 — Declarative vs. Scripted Pipelines (`Jenkinsfile`)
- 5.4.3 — Parameterized Builds
- 5.4.4 — Blue Ocean UI Overview

*Lab — Week 5 Lab: Containerize the Banking Calculator*

> **Lab Type:** Project-Based | **Duration:** 75 minutes | **Tools:** Docker, Git (both available in lab environment)
>
> **Instructions:** Take the Python banking calculator from Week 1 and containerize it. Write a `Dockerfile` using a multi-stage build (deps → builder → runner). Create a `docker-compose.yml` that starts the app and a PostgreSQL database. Write a GitHub Actions workflow YAML (`.github/workflows/ci.yml`) that builds the image and runs pytest. The lab auto-validates the `Dockerfile` syntax and `docker-compose.yml` service definitions.

**Week 5 Quiz:** 10 questions — Git commands, Dockerfile instructions, CI/CD concepts.

---

#### Week 6: Agile and Scrum

**Course Setup:**

| Field | Value |
|---|---|
| **Course Title** | Agile and Scrum |
| **Sequence Number** | 6 |
| **Week** | Week 6 (May 12–16, 2026) |
| **Difficulty** | Beginner–Intermediate |
| **Estimated Hours** | 5 hours |
| **Description** | Agile manifesto, Scrum framework, sprint ceremonies, user story writing, backlog management, Jira workflows, and retrospective facilitation. |

**Module 6.1: Agile Principles and Manifesto (60 min)**

*Lessons:*
- 6.1.1 — 12 Agile Principles and the Manifesto Values
- 6.1.2 — Waterfall vs. Agile: When Each Applies
- 6.1.3 — Agile at Scale: SAFe, LeSS Overview
- 6.1.4 — Agile in Regulated Industries (Banking Context)

**Module 6.2: Scrum Framework (90 min)**

*Lessons:*
- 6.2.1 — Scrum Roles: Product Owner, Scrum Master, Dev Team
- 6.2.2 — Scrum Artifacts: Product Backlog, Sprint Backlog, Increment
- 6.2.3 — Sprint Ceremonies: Planning, Daily Standup, Review, Retrospective
- 6.2.4 — Definition of Done and Acceptance Criteria
- 6.2.5 — Velocity, Story Points, and Burndown Charts

**Module 6.3: User Stories and Backlog Management (90 min)**

*Lessons:*
- 6.3.1 — User Story Format: "As a [role], I want [goal], so that [benefit]"
- 6.3.2 — INVEST Criteria for Good User Stories
- 6.3.3 — Epics, Stories, and Tasks: Hierarchy
- 6.3.4 — Backlog Refinement (Grooming) Techniques
- 6.3.5 — MoSCoW Prioritization

*Exercise:* Write 5 user stories for an FNBC mobile banking feature (balance check, fund transfer, bill payment, transaction history, fraud alert). Apply INVEST criteria to each.

**Module 6.4: Jira and Retrospectives (60 min)**

*Lessons:*
- 6.4.1 — Jira Board Setup: Kanban vs. Scrum Board
- 6.4.2 — Creating Epics, Stories, Sub-tasks in Jira
- 6.4.3 — Sprint Reports and Velocity Charts in Jira
- 6.4.4 — Retrospective Formats: Start/Stop/Continue, 4Ls, Mad/Sad/Glad
- 6.4.5 — Action Items and Follow-Through

*Lab — Week 6 Lab: Sprint Planning Simulation*

> **Lab Type:** Tutorial | **Duration:** 60 minutes
>
> **Instructions:** Using a provided FNBC product backlog (15 user stories for a customer portal), conduct a sprint planning exercise. Select stories for a 2-week sprint given a team velocity of 20 points. Write acceptance criteria for 3 selected stories. Create a sprint burndown chart template. Submit a written sprint plan document (PDF or plain text).

**Week 6 Quiz:** 10 questions — Scrum ceremonies, backlog prioritization, user story quality.

---

#### Week 7: Code Quality

**Course Setup:**

| Field | Value |
|---|---|
| **Course Title** | Code Quality |
| **Sequence Number** | 7 |
| **Week** | Week 7 (May 19–23, 2026) |
| **Difficulty** | Intermediate |
| **Estimated Hours** | 5 hours |
| **Description** | Test-Driven Development (TDD), code review practices, refactoring techniques, SOLID principles applied in practice, and static analysis tools. |

**Module 7.1: Test-Driven Development (90 min)**

*Lessons:*
- 7.1.1 — TDD Cycle: RED → GREEN → REFACTOR
- 7.1.2 — Writing Failing Tests First
- 7.1.3 — Unit Tests with `pytest` (Python) and JUnit (Java)
- 7.1.4 — Mocking and Stubbing: `unittest.mock`, Mockito
- 7.1.5 — Test Coverage: What 80% Really Means

**Module 7.2: Code Review Best Practices (60 min)**

*Lessons:*
- 7.2.1 — What to Look For in a Code Review
- 7.2.2 — Giving and Receiving Constructive Feedback
- 7.2.3 — Automated vs. Human Review
- 7.2.4 — Pre-Commit Hooks and Linting (ESLint, pylint, checkstyle)

**Module 7.3: Refactoring Techniques (90 min)**

*Lessons:*
- 7.3.1 — Code Smells: Long Methods, God Classes, Magic Numbers
- 7.3.2 — Extract Method, Rename Variable, Introduce Parameter Object
- 7.3.3 — Replace Conditional with Polymorphism
- 7.3.4 — Using IDE Refactoring Tools
- 7.3.5 — Refactoring with Test Safety Nets

**Module 7.4: SOLID in Practice and Static Analysis (60 min)**

*Lessons:*
- 7.4.1 — Detecting SRP Violations in Real Code
- 7.4.2 — SonarQube: Code Quality Gates
- 7.4.3 — Cyclomatic Complexity Explained
- 7.4.4 — Security Scanning in CI (SAST basics)

*Lab — Week 7 Lab: TDD Kata — Loan Calculator*

> **Lab Type:** Assessment Lab | **Duration:** 90 minutes (timed)
>
> **Instructions:** Implement a loan amortization calculator for FNBC using strict TDD. You are provided with 10 failing test cases. You must make all tests pass without modifying the test file. The code must achieve ≥85% test coverage as reported by `pytest-cov`. The lab environment runs automated coverage checks on submission.
>
> **Acceptance Criteria:**
> - All 10 tests pass
> - Coverage ≥ 85%
> - No functions longer than 20 lines (pylint check)
> - No unused imports

**Week 7 Quiz:** 10 questions — TDD cycle, code smell identification, refactoring patterns.

---

#### Week 8: Capstone Project

**Course Setup:**

| Field | Value |
|---|---|
| **Course Title** | Capstone Project — End-to-End Banking Application |
| **Sequence Number** | 8 |
| **Week** | Week 8 (May 26–29, 2026) |
| **Difficulty** | Advanced |
| **Estimated Hours** | 10 hours (intensive) |
| **Description** | Students build, deploy, and present a complete end-to-end banking application integrating all concepts from Weeks 1–7. The project is evaluated on functionality, code quality, test coverage, and a live demonstration. |

**Module 8.1: Project Brief and Requirements (60 min)**

*Lessons:*
- 8.1.1 — Capstone Brief: FNBC Customer Portal MVP
- 8.1.2 — Technical Requirements: Python/Java backend, REST API, PostgreSQL, Docker
- 8.1.3 — Agile Kick-off: Sprint Board Setup in Jira
- 8.1.4 — Grading Rubric Walkthrough

**Module 8.2: Architecture Planning (60 min)**

*Lessons:*
- 8.2.1 — High-Level Architecture Design (draw diagram)
- 8.2.2 — Database Schema Design and ERD
- 8.2.3 — API Contract Definition (OpenAPI)
- 8.2.4 — Test Strategy: What will be unit tested vs. integration tested

**Module 8.3: Build Sprint (Independent Work — 6 hours)**

Students work independently in the lab environment. Instructor holds 30-minute check-in sessions on Day 2 and Day 3.

*Milestones:*
- M1: Database schema created and seeded (Day 1, EOD)
- M2: Core API endpoints functional and tested (Day 2, EOD)
- M3: Dockerized and running locally (Day 3, AM)
- M4: Submission and live demo prep (Day 4, AM)

**Module 8.4: Presentation and Review (90 min)**

*Format:*
- 10-minute live demo per student
- 5-minute Q&A from instructor and peers
- Code review feedback provided within 48 hours

*Lab — Week 8 Capstone Submission:*

> **Lab Type:** Project-Based (Multi-session) | **Duration:** Up to 8 hours across 4 days
>
> **Deliverables:**
> 1. Git repository link (or ZIP export from lab) containing full source code
> 2. `README.md` with setup instructions, architecture notes, and feature list
> 3. Test suite with ≥80% coverage report (`pytest-cov` HTML output)
> 4. `Dockerfile` and `docker-compose.yml`
> 5. 10-minute recorded or live demo

**Week 8 Capstone Rubric:**

| Dimension | Weight | Criteria |
|---|---|---|
| Functionality | 30% | All required features work end-to-end |
| Code Quality | 20% | Clean, readable, SOLID principles applied |
| Test Coverage | 20% | ≥80% unit test coverage |
| DevOps | 15% | Dockerfile and docker-compose work; CI YAML valid |
| Presentation | 15% | Clear explanation, handles Q&A confidently |

---

## Part 3: Content Creation — AI Chat Path (Business Analyst Track)

The Business Analyst Track is created by Instructor Claire Okafor using the **AI Chat Assistant** — the platform's alternative to the step-by-step wizard. Claire accesses the assistant via the **purple chat button** in the bottom-right corner of the Instructor Dashboard, which connects to the RAG service on port `8009`.

The AI Assistant pipeline processes queries through 5 phases: NLP preprocessing → parallel context retrieval (Knowledge Graph + RAG + Metadata) → ensemble model generation (Mistral + LLaMA concurrently) → frontier model consensus (Claude/GPT-4) → response. This typically resolves in under 2 seconds.

---

### Step 3.1 — Initiating the Chat Session

Claire opens the AI Assistant panel. The system greeting reads:

> *"Hi Claire! I'm your Course Creation Assistant. I can help you design courses, generate learning objectives, create quizzes and exercises, or structure a full curriculum. What would you like to build today?"*

---

### Step 3.2 — Week 1: Business Analysis Fundamentals

**Claire's Prompt:**
```
I need to create Week 1 of an 8-week Business Analysis training program for new graduate
hires at a bank. The first week should cover Business Analysis Fundamentals. Please create
a complete course structure including: course description, 4 modules with lesson titles,
one coding-free exercise per module, a lab description, and a 10-question quiz.
Target audience: graduates with no prior BA experience.
```

**Expected AI Response (condensed):**

> **Course: Business Analysis Fundamentals (Week 1)**
> *Description:* Introduction to the Business Analyst role, core competencies, the software development lifecycle from a BA perspective, and stakeholder identification techniques. No technical background required.
>
> **Module 1.1 — The BA Role and Competency Framework (90 min)**
> - Lesson 1: What Does a Business Analyst Actually Do?
> - Lesson 2: The BABOK Knowledge Areas Overview (IIBA Framework)
> - Lesson 3: Hard Skills vs. Soft Skills for BAs
> - Lesson 4: The BA in Agile vs. Waterfall Projects
> - Lesson 5: Career Pathways: Junior BA to Principal BA
>
> *Exercise:* Map five activities from a typical bank project to their BABOK knowledge area.
>
> **Module 1.2 — The Software Development Lifecycle (SDLC) for BAs (90 min)**
> - Lesson 1: SDLC Phases: Initiation, Analysis, Design, Build, Test, Deploy
> - Lesson 2: Where BA Work Fits in Each Phase
> - Lesson 3: BA Artifacts by Phase: BRD, FRS, Use Cases, Test Scenarios
> - Lesson 4: Agile SDLC: The BA as Product Owner Proxy
> - Lesson 5: The Cost of Late Requirements Changes (cone of uncertainty)
>
> *Exercise:* Given a scenario ("FNBC wants to add Apple Pay to mobile banking"), identify what BA artifacts would be produced at each SDLC phase.
>
> **Module 1.3 — Stakeholder Identification and Analysis (90 min)**
> - [5 lessons on stakeholder mapping, RACI matrix, influence/interest grid]
>
> *Exercise:* Create a stakeholder register and interest/influence matrix for a fictional FNBC loan origination project.
>
> **Module 1.4 — Elicitation Techniques Introduction (60 min)**
> - [4 lessons on interviews, workshops, surveys, observation]
>
> *Exercise:* Draft 10 open-ended interview questions for a stakeholder meeting about a new online account opening feature.
>
> **Lab — Week 1 BA Lab:** Stakeholder Analysis Workshop
> *Duration: 60 minutes | Format: Written submission (PDF or DOCX)*
> Analyze a provided FNBC project charter for a Digital Onboarding project. Identify all stakeholders, classify them by role, create an interest/influence grid, and recommend an engagement strategy for three key stakeholders.
>
> **Week 1 Quiz (10 questions):**
> 1. What does BABOK stand for and which organization publishes it?
> 2. In the interest/influence grid, how should you handle a high-influence/low-interest stakeholder?
> 3. Which SDLC phase produces a Business Requirements Document (BRD)?
> 4. True/False: In Agile, the BA typically writes detailed upfront functional specifications.
> 5. What is the "cone of uncertainty" in project management?
> 6. Match the artifact to the SDLC phase: [Use Cases / BRD / Test Plan / Architecture Doc]
> 7. Which elicitation technique is best for understanding current workflows without interrupting users?
> 8. What is a RACI matrix used for?
> 9. Name two key differences between a BA in a Waterfall project vs. an Agile project.
> 10. A stakeholder says "I just want what I want, not what I need." Which elicitation challenge does this illustrate?

Claire reviews the response and clicks **"Accept and Create Course"**. The platform creates the Week 1 course structure in the Business Analysis Track.

---

### Step 3.3 — Week 2: Requirements Engineering

**Claire's Prompt:**
```
Create Week 2 for the same BA track: Requirements Engineering. Cover functional vs.
non-functional requirements, use cases, user stories vs. use cases comparison,
requirements traceability matrices, and ambiguity resolution.
Same format: 4 modules, exercises, a lab, and 10-question quiz.
```

**Expected AI Response (summary):**

> **Course: Requirements Engineering (Week 2)**
>
> **Module 2.1 — Functional vs. Non-Functional Requirements**
> *5 lessons covering FR/NFR definitions, categories of NFRs (performance, security, usability), writing testable requirements, and the "SMART" requirements framework.*
>
> *Exercise:* Given 10 requirements from a mobile banking spec, classify each as functional or non-functional. Rewrite 3 ambiguous ones using SMART criteria.
>
> **Module 2.2 — Use Cases and Use Case Diagrams (UML)**
> *5 lessons: actors, use case relationships (include, extend), use case narrative format, level of detail, UML notation in Lucidchart/draw.io.*
>
> *Exercise:* Write a fully dressed use case for "Transfer Funds Between Accounts" including pre/post-conditions, main flow, and 2 alternative flows.
>
> **Module 2.3 — User Stories vs. Use Cases: When to Use Which**
> *4 lessons: comparative analysis, contexts favoring each, hybrid approaches, INVEST vs. use case quality checks.*
>
> *Exercise:* Convert a 3-page use case document into a set of user stories and acceptance criteria suitable for an Agile sprint backlog.
>
> **Module 2.4 — Requirements Traceability Matrix (RTM)**
> *4 lessons: RTM structure, forward/backward traceability, maintaining the RTM through change, tool support (Jira, Confluence, Excel).*
>
> *Lab — Week 2 BA Lab:* Build a Requirements Traceability Matrix (spreadsheet submission) tracing 15 functional requirements from the FNBC Digital Onboarding project through design decisions, test cases, and defects.
>
> **Week 2 Quiz:** 10 questions covering requirement quality, use case reading, RTM concepts, and an ambiguity-spotting exercise.

---

### Step 3.4 — Week 3: SQL for Analysts

**Claire's Prompt:**
```
Week 3 is SQL for Analysts — but this is for Business Analysts, not developers.
Focus on reading and writing SELECT queries, understanding data models from an
analyst perspective, working with Excel and SQL together, and creating data extracts
for reporting. No DDL or database design needed. 4 modules, same format.
```

**Expected AI Response (summary):**

> **Course: SQL for Analysts (Week 3)**
>
> **Module 3.1 — Reading a Data Model as a BA**
> *5 lessons: entity-relationship diagrams for non-developers, identifying relevant tables, understanding foreign keys conceptually, reading a data dictionary, and asking the right questions of database developers.*
>
> **Module 3.2 — Writing SELECT Queries for Data Extraction**
> *5 lessons: SELECT/FROM/WHERE, filtering with AND/OR/IN/BETWEEN, sorting with ORDER BY, limiting results with LIMIT/TOP, aliases for readable output.*
>
> *Exercise:* Write 5 SELECT queries against the FNBC banking schema to answer business questions (e.g., "Which customers haven't logged in for 90 days?" / "What is the average balance for savings accounts opened this year?").
>
> **Module 3.3 — Joins and Aggregates for Reporting**
> *4 lessons: INNER JOIN explained visually, GROUP BY for summaries, COUNT/SUM/AVG, exporting results to CSV for Excel analysis.*
>
> **Module 3.4 — Practical SQL for Analyst Workflows**
> *4 lessons: connecting SQL to Excel/Power BI, parameterized query templates, data quality checks with SQL, communicating findings from query results.*
>
> *Lab — Week 3 BA Lab:* SQL Data Extract for Executive Report
> Using the provided FNBC PostgreSQL sandbox, write 8 SQL queries to populate a quarterly performance report template (provided as an Excel stub). Export results and paste into the correct cells.
>
> **Week 3 Quiz:** 10 questions — reading query output, fixing broken SQL, matching query to business question.

---

### Step 3.5 — Week 4: Process Modeling (BPMN and UML)

**Claire's Prompt:**
```
Week 4: Process Modeling. Cover BPMN 2.0 notation for business process diagrams,
UML activity diagrams, swimlane diagrams for cross-functional processes,
and how to document AS-IS vs. TO-BE processes. Include a lab using a free
online tool like draw.io or Lucidchart. 4 modules, exercises, lab, 10-question quiz.
```

**Expected AI Response (summary):**

> **Course: Process Modeling — BPMN and UML (Week 4)**
>
> **Module 4.1 — BPMN 2.0 Fundamentals**
> *5 lessons: BPMN elements (events, activities, gateways, flows, pools, lanes), exclusive vs. parallel vs. inclusive gateways, notation rules and best practices.*
>
> **Module 4.2 — AS-IS vs. TO-BE Process Analysis**
> *4 lessons: documenting current-state processes, pain point identification, gap analysis, designing future-state processes with improvement rationale.*
>
> *Exercise:* The instructor provides an AS-IS narrative of FNBC's manual loan approval process (8 steps, 3 departments). Students draw the AS-IS BPMN diagram, identify 3 inefficiencies, and propose a TO-BE process.
>
> **Module 4.3 — UML Activity Diagrams and Swimlanes**
> *4 lessons: activity diagram notation, swimlanes for cross-functional flows, decision nodes, merge nodes, comparing BPMN vs. UML activity diagrams.*
>
> **Module 4.4 — Process Modeling in Practice**
> *4 lessons: tool walkthrough (draw.io), version control for diagrams, reviewing process models with stakeholders, common mistakes to avoid.*
>
> *Lab — Week 4 BA Lab:* BPMN Diagram for FNBC Trade Finance Approval
> Draw a complete BPMN 2.0 diagram for an FNBC trade finance letter of credit approval process. The process involves 4 departments (Client, Relationship Manager, Credit Risk, Operations). Must include: start/end events, 2 exclusive gateways, 1 parallel gateway, error boundary event, and at least 2 swimlanes. Submit as PNG export from draw.io.
>
> **Week 4 Quiz:** 10 questions — BPMN symbol identification, gateway logic, activity diagram reading, AS-IS/TO-BE concepts.

---

### Step 3.6 — Week 5: Data Analysis and Visualization

**Claire's Prompt:**
```
Week 5: Data Analysis and Visualization for BAs. Cover descriptive statistics
without needing advanced math, Excel pivot tables and charts, basic data storytelling,
and an intro to Power BI dashboards. Emphasize business context over technical depth.
4 modules, same format.
```

**Expected AI Response (summary):**

> **Course: Data Analysis and Visualization (Week 5)**
>
> Modules cover: descriptive statistics (mean/median/mode/std dev in plain English), Excel pivot tables and VLOOKUP for analysis, data visualization best practices (choosing the right chart type), and a Power BI walkthrough building a simple dashboard from an FNBC data extract.
>
> *Lab:* Build a Power BI dashboard with 4 visuals using an FNBC branch performance dataset. Include a slicer for date range filtering and a KPI card for total deposits.
>
> *Quiz:* 10 questions — chart type selection, pivot table mechanics, data quality issues, interpreting a sample bar chart.

---

### Step 3.7 — Week 6: Stakeholder Management

**Claire's Prompt:**
```
Week 6: Stakeholder Management for BAs — advanced techniques. Cover conflict
resolution in requirements workshops, managing scope creep, difficult stakeholders,
communication planning, and building a business case. 4 modules, same format.
```

**Expected AI Response (summary):**

> **Course: Stakeholder Management (Week 6)**
>
> Modules cover: stakeholder communication planning (who needs what, when, how), managing conflicting stakeholder priorities using facilitation techniques, scope creep identification and change control, building a simple business case with ROI/cost-benefit, and handling resistant or disengaged stakeholders.
>
> *Lab:* Role-play scenario — written submission. Students respond to a series of 5 stakeholder emails from a difficult FNBC project (one stakeholder constantly adds new requirements, one refuses to attend reviews, one overrides the agreed scope). Write professional responses managing each situation.
>
> *Quiz:* 10 questions — communication planning, change control, stakeholder engagement techniques.

---

### Step 3.8 — Week 7: Agile for Business Analysts

**Claire's Prompt:**
```
Week 7: Agile for BAs — specifically backlog grooming, writing acceptance criteria
using Gherkin/BDD format, the BA role in sprint ceremonies, and how to collaborate
with developers in an Agile team. 4 modules, exercises, lab, 10-question quiz.
```

**Expected AI Response (summary):**

> **Course: Agile for Business Analysts (Week 7)**
>
> **Module 7.1 — The BA in Agile: Evolving Role**
> *Covers: BA as Product Owner proxy, embedded BA vs. traditional BA, continuous discovery, just-enough documentation.*
>
> **Module 7.2 — Backlog Grooming and Story Refinement**
> *Covers: splitting epics into stories, story point estimation techniques, three-amigos sessions (BA + Dev + QA), definition of ready.*
>
> **Module 7.3 — Acceptance Criteria and BDD**
> *Covers: Given/When/Then format, Gherkin syntax, writing scenarios from user stories, connecting ACs to automated tests.*
>
> *Exercise:* Write 3 Gherkin scenarios for: (1) successful online transfer, (2) transfer exceeding daily limit, (3) transfer to a blocked account.
>
> **Module 7.4 — Collaboration with Developers and QA**
> *Covers: Definition of Done, demo prep, participation in retrospectives, handling "that's out of scope" disputes.*
>
> *Lab:* Backlog Grooming Exercise — given a 20-story product backlog for an FNBC self-service portal, groom the top 8 stories: add acceptance criteria (3 Gherkin scenarios each), apply INVEST, estimate story points, and produce a prioritized sprint-ready backlog document.
>
> *Quiz:* 10 questions — Gherkin syntax, BDD concepts, Agile BA role, backlog refinement.

---

### Step 3.9 — Week 8: BA Capstone Project

**Claire's Prompt:**
```
Week 8: BA Capstone Project. Students must produce a complete BA deliverable package
for a realistic FNBC project — end-to-end, from stakeholder analysis through
requirements documentation, process models, and presentation.
Create the project brief, grading rubric (5 dimensions), and submission checklist.
```

**Expected AI Response (summary):**

> **Course: BA Capstone — FNBC Digital Banking Modernization (Week 8)**
>
> **Project Brief:** Students act as the lead BA on FNBC's Digital Banking Modernization initiative — migrating 3 legacy services (loan applications, account opening, customer support) to a new digital-first platform.
>
> **Required Deliverables:**
> 1. Stakeholder Register and Interest/Influence Matrix (minimum 8 stakeholders)
> 2. As-Is Process Model (BPMN) for one legacy service of their choice
> 3. Business Requirements Document (BRD) — minimum 15 functional requirements, 5 non-functional
> 4. Requirements Traceability Matrix linking BRD requirements to test scenarios
> 5. Executive Summary presentation (5 slides)
>
> **Capstone Rubric:**
>
> | Dimension | Weight | Criteria |
> |---|---|---|
> | Stakeholder Analysis | 20% | Completeness, classification accuracy, engagement strategy |
> | Process Models | 20% | BPMN correctness, clarity, AS-IS detail |
> | Requirements Quality | 25% | SMART criteria, FR/NFR coverage, ambiguity-free |
> | Traceability | 20% | RTM completeness, correct linkages |
> | Presentation | 15% | Clarity, professional structure, Q&A handling |
>
> *Lab:* Multi-session project workspace. Students save work progressively; instructor holds 2 check-in sessions during the week.

Claire accepts the AI-generated structure for all 8 weeks. Each course is automatically created in the Business Analysis Track sub-project.

---

## Part 4: Student Journey — James Okonkwo (8-Week Simulation)

### Step 4.1 — Student Registration and Enrollment

**Day 1 — Monday, April 7, 2026**

Sarah (Org Admin) registers the five students via the **Bulk Enrollment** feature:

1. Navigate to the **Students** tab in the Org Admin Dashboard
2. Click **"Bulk Enroll via Spreadsheet"**
3. Upload the following CSV:

```csv
first_name,last_name,email,role,track
James,Okonkwo,james.okonkwo@fnbc.com,student,Software Development Track
Priya,Sharma,priya.sharma@fnbc.com,student,Software Development Track
Marcus,Chen,marcus.chen@fnbc.com,student,Business Analysis Track
Fatima,Al-Hassan,fatima.alhassan@fnbc.com,student,Business Analysis Track
David,Kowalski,david.kowalski@fnbc.com,student,Software Development Track
```

**System Response:**
```json
{
  "total_students": 5,
  "successful_enrollments": 5,
  "failed_enrollments": 0,
  "created_accounts": 5,
  "processing_time_ms": 1847
}
```

Each student receives a welcome email with their temporary password. The platform enforces a password change on first login.

---

### Step 4.2 — James's Day 1 Experience

**08:55 AM — Login:**

James navigates to the Student Dashboard URL included in his welcome email. He enters `james.okonkwo@fnbc.com` and his temporary password. The system prompts him to set a new password: he sets `JamesOK@2026!`.

**09:00 AM — Dashboard Tour:**

The platform launches an interactive guided tour (opt-in overlay):

1. **"Welcome to TechUni"** — Introduction overlay highlighting the main sections
2. **"My Courses"** — Tour points to his enrolled courses panel showing "Python Fundamentals (Week 1)" ready to start
3. **"Labs"** — Tour explains the integrated coding environment accessible via the "Launch Lab" button
4. **"Progress Tracker"** — Shows 0% completion, 8 weeks ahead
5. **"AI Assistant"** — Tour highlights the purple chat button and explains it can answer questions about course content
6. **"Quiz Section"** — Explains that quizzes unlock as he progresses through modules

James completes the 4-minute tour and clicks **"Start Learning"**.

**09:10 AM — Enrollment Confirmation:**

James sees his Dashboard:
- **Active Course:** Python Fundamentals — Week 1 (0% complete)
- **Track:** Software Development Track
- **Program:** FNBC Graduate Developer Program 2026
- **Progress:** Week 1 of 8
- **Next Deadline:** Week 1 Quiz — Friday April 11, 5:00 PM EST

**09:15 AM — First Lesson:**

James opens Module 1.1 "Python Syntax and Control Flow". He reads Lesson 1.1.1 on the Python environment and launches the **Lab Environment** to install nothing — it's pre-configured with Python 3.11 in VS Code. He runs `print("Hello, FNBC!")` in the terminal. It works. He's off.

---

### Step 4.3 — James's Week-by-Week Learning Log

#### Week 1 (Apr 7–11): Python Fundamentals

**Daily Activity:**

| Day | Activity | Time Spent |
|---|---|---|
| Mon Apr 7 | Modules 1.1 and 1.2 — lessons + Module 1.2 exercise (BankAccount class first attempt) | 2.5 hrs |
| Tue Apr 8 | Module 1.3 OOP — completed BankAccount/SavingsAccount exercise; first run fails (forgot `super().__init__()`) | 2 hrs |
| Wed Apr 9 | Module 1.4 Error Handling + started Week 1 Lab | 1.5 hrs |
| Thu Apr 10 | Completed Week 1 Lab — all 4 acceptance tests pass on third attempt (initial issue: `withdraw()` didn't raise exception, just returned -1) | 2 hrs |
| Fri Apr 11 | **Week 1 Quiz** — 10 questions, 20 minutes | 20 min |

**Lab Submission — Week 1:**
- Attempt 1: 2/4 tests pass (submit 8:30 AM Thu)
- Attempt 2: 3/4 tests pass (submit 2:15 PM Thu)
- Attempt 3: 4/4 tests pass (submit 4:45 PM Thu) — FINAL

**Week 1 Quiz Score: 78/100**
- Strong on OOP and functions; lost 12 points on a code-fix question (incorrect indentation in solution) and one short-answer on OOP advantages.
- Instructor note: "Good effort James — review the `try/except` placement in your quiz answers. Otherwise solid start!"

---

#### Week 2 (Apr 14–18): Java Core Concepts

| Day | Activity | Time Spent |
|---|---|---|
| Mon Apr 14 | Modules 2.1–2.2 — Java syntax initially confusing after Python; rewatched Lesson 2.1.1 comparing Java/Python type systems | 2.5 hrs |
| Tue Apr 15 | Module 2.3 Collections; completed Transaction interface exercise on first attempt | 2 hrs |
| Wed Apr 16 | Module 2.4 Streams; struggled with lambda syntax initially, used AI assistant to ask: *"Can you explain how Java lambda expressions compare to Python lambda functions with an example?"* | 2 hrs |
| Thu Apr 17 | Week 2 Lab — TransactionProcessor. 4/6 JUnit tests pass by end of day | 2 hrs |
| Fri Apr 18 | Fixed 2 remaining JUnit failures (null handling); submitted lab; sat Week 2 Quiz | 1.5 hrs |

**Week 2 Quiz Score: 82/100**
- Improved from Week 1. Strong on Collections; lost points on a generics bounded-type question and one stream output trace.

---

#### Week 3 (Apr 21–25): SQL and Database Design

| Day | Activity | Time Spent |
|---|---|---|
| Mon Apr 21 | Module 3.1 DDL — found this more intuitive than Java; completed first 2 lab tasks early | 2 hrs |
| Tue Apr 22 | Module 3.2 DML; started working through the FNBC banking database in the lab sandbox | 2.5 hrs |
| Wed Apr 23 | Module 3.3 JOINs and CTEs — asked AI assistant: *"Show me the difference between a CTE and a subquery with a banking example"* | 2 hrs |
| Thu Apr 24 | Completed all 5 lab tasks (CTE/window function query took 45 minutes to get right) | 2.5 hrs |
| Fri Apr 25 | Week 3 Quiz | 20 min |

**Week 3 Quiz Score: 88/100**
- Best score so far. SQL clicked well. Lost points on a normalization question (confused 2NF/3NF boundary).

---

#### Week 4 (Apr 28–May 2): Software Architecture

**Note:** James submitted his Week 4 Lab one day late (submitted Thursday May 7 instead of Thursday May 2 at 5 PM). He notified Dr. Rivera via Slack: *"Lab environment was down Tuesday evening and I lost 3 hours of work. Restarted and resubmitted Thursday."* Dr. Rivera confirmed the lab outage in logs and waived the late penalty.

| Day | Activity | Time Spent |
|---|---|---|
| Mon Apr 28 | Module 4.1 REST + Module 4.2 Microservices | 2.5 hrs |
| Tue Apr 29 | Modules 4.3–4.4 (Design Patterns + SOLID); Lab environment outage 6–9 PM | 1.5 hrs |
| Wed Apr 30 | Rebuilt lost work; got Strategy pattern working | 2 hrs |
| Thu May 1 | Completed payment API design; submitted lab (1 day late, waived) | 2 hrs |
| Fri May 2 | Week 4 Quiz | 20 min |

**Week 4 Quiz Score: 75/100**
- Impact of lab disruption visible. Lost points on design pattern identification and a REST semantics question about PATCH vs. PUT.

---

#### Week 5 (May 5–9): DevOps Foundations

| Day | Activity | Time Spent |
|---|---|---|
| Mon May 5 | Git module — very engaged, already used Git before | 1.5 hrs |
| Tue May 6 | CI/CD and Docker modules | 2.5 hrs |
| Wed May 7 | Week 5 Lab — Dockerfile and docker-compose (initial build failed: missing ENV variable) | 2 hrs |
| Thu May 8 | Fixed Docker build; wrote GitHub Actions YAML; all lab validations pass | 2 hrs |
| Fri May 9 | Week 5 Quiz | 20 min |

**Week 5 Quiz Score: 84/100**
- Strong on Git. Lost points on a Jenkins declarative pipeline question and one `docker-compose` networking concept.

---

#### Week 6 (May 12–16): Agile and Scrum

| Day | Activity | Time Spent |
|---|---|---|
| Mon May 12 | Agile manifesto + Scrum framework — found this directly applicable; took detailed notes | 2 hrs |
| Tue May 13 | User stories exercise; wrote all 5 FNBC mobile banking user stories; peer review with Priya | 2 hrs |
| Wed May 14 | Jira module; completed sprint planning simulation | 2 hrs |
| Thu May 15 | Lab — sprint planning exercise submitted | 1.5 hrs |
| Fri May 16 | Week 6 Quiz | 20 min |

**Week 6 Quiz Score: 90/100**
- Best quiz score to date. Lost 10 points on one retrospective formats question (confused Mad/Sad/Glad with Start/Stop/Continue).

---

#### Week 7 (May 19–23): Code Quality

| Day | Activity | Time Spent |
|---|---|---|
| Mon May 19 | TDD module — RED/GREEN/REFACTOR practice on Module 7.1 exercises | 2 hrs |
| Tue May 20 | Code review and refactoring modules | 2 hrs |
| Wed May 21 | Started Week 7 Lab (TDD kata — loan calculator); all 10 tests pass on first run through RED phase, 7/10 GREEN by EOD | 2.5 hrs |
| Thu May 22 | Fixed 3 failing tests; coverage report: 87% (above 85% threshold); submitted | 1.5 hrs |
| Fri May 23 | Week 7 Quiz | 20 min |

**Week 7 Quiz Score: 86/100**
- Strong TDD understanding. Lost points on cyclomatic complexity calculation and one refactoring pattern question.

---

#### Week 8 (May 26–29): Capstone Project

**The capstone was James's most intensive week. He committed 14 hours over 4 days.**

| Day | Activity |
|---|---|
| Tue May 26 | Attended project kick-off session; designed database schema (ERD); created Jira sprint board |
| Wed May 27 | Built core API (3 endpoints: accounts, transactions, transfers); wrote unit tests; 73% coverage |
| Thu May 28 | Dockerized app; fixed 2 integration issues; coverage to 83%; instructor check-in at 11 AM |
| Fri May 29 | Final polish; README written; submitted ZIP + Git link; **live demo at 2:00 PM EST** |

**Capstone Submission Contents:**
- Python/FastAPI backend with 3 REST endpoints
- PostgreSQL schema with 4 tables (customers, accounts, transactions, audit_log)
- pytest suite: 22 tests, 83% coverage
- `Dockerfile` (multi-stage) and `docker-compose.yml` with PostgreSQL service
- GitHub Actions CI YAML
- 10-minute live demo: walked through account creation → deposit → transfer → transaction history

**Capstone Scores:**

| Dimension | Score |
|---|---|
| Functionality (30%) | 27/30 — All features worked; minor: no pagination on transaction list |
| Code Quality (20%) | 17/20 — Clean structure; one God Class in transaction service flagged |
| Test Coverage (20%) | 17/20 — 83% coverage (threshold 80%), missing edge cases |
| DevOps (15%) | 14/15 — Docker and CI all work; minor: no health check endpoint |
| Presentation (15%) | 13/15 — Confident demo, handled Q&A well; could have explained architecture diagram more clearly |

**Capstone Total: 88/100**

---

### Step 4.4 — Day 56 Summary

**Saturday May 30, 2026 — James Okonkwo Program Completion**

James logs into the platform to find:

- **"Program Complete!"** banner on his dashboard
- Certificate: *"FNBC Graduate Developer Program 2026 — Software Development Track"*
- Final average score displayed (see metrics table in Part 6)
- Completion badge added to profile
- Message from Dr. Rivera: *"James — great work this cohort. Your Week 8 capstone showed real architectural thinking. The pagination issue and the transaction service God Class are exactly the kinds of things code review would catch in a team setting — you'll nail it next time. Welcome to the FNBC engineering family."*

---

## Part 5: 8-Week Training Schedule

The program runs Monday–Friday, April 7 – May 29, 2026. Live sessions are 2 hours each, 9:00–11:00 AM EST. Afternoons are reserved for lab work and self-paced content (12:00–5:00 PM EST).

| Week | Date | Day | Time (EST) | Course Subject | Instructor | Track |
|---|---|---|---|---|---|---|
| 1 | Apr 7 | Mon | 9:00–11:00 AM | Python Fundamentals — Syntax and Control Flow | Dr. Michael Rivera | SW Dev |
| 1 | Apr 7 | Mon | 9:00–11:00 AM | BA Fundamentals — The BA Role and BABOK | Claire Okafor | BA |
| 1 | Apr 8 | Tue | 9:00–11:00 AM | Python Fundamentals — Functions and Scope | Dr. Michael Rivera | SW Dev |
| 1 | Apr 8 | Tue | 9:00–11:00 AM | BA Fundamentals — SDLC for BAs | Claire Okafor | BA |
| 1 | Apr 9 | Wed | 9:00–11:00 AM | Python Fundamentals — OOP | Dr. Michael Rivera | SW Dev |
| 1 | Apr 9 | Wed | 9:00–11:00 AM | BA Fundamentals — Stakeholder Identification | Claire Okafor | BA |
| 1 | Apr 10 | Thu | 9:00–11:00 AM | Python Fundamentals — Error Handling + Lab Work | Dr. Michael Rivera | SW Dev |
| 1 | Apr 10 | Thu | 9:00–11:00 AM | BA Fundamentals — Elicitation Techniques + Lab | Claire Okafor | BA |
| 1 | Apr 11 | Fri | 9:00–10:00 AM | Python Fundamentals — Week 1 Quiz Review | Dr. Michael Rivera | SW Dev |
| 1 | Apr 11 | Fri | 9:00–10:00 AM | BA Fundamentals — Week 1 Quiz Review | Claire Okafor | BA |
| 2 | Apr 14 | Mon | 9:00–11:00 AM | Java Core Concepts — Classes and OOP | Dr. Michael Rivera | SW Dev |
| 2 | Apr 14 | Mon | 9:00–11:00 AM | Requirements Engineering — FR vs. NFR | Claire Okafor | BA |
| 2 | Apr 15 | Tue | 9:00–11:00 AM | Java Core Concepts — Interfaces | Dr. Michael Rivera | SW Dev |
| 2 | Apr 15 | Tue | 9:00–11:00 AM | Requirements Engineering — Use Cases | Claire Okafor | BA |
| 2 | Apr 16 | Wed | 9:00–11:00 AM | Java Core Concepts — Collections Framework | Dr. Michael Rivera | SW Dev |
| 2 | Apr 16 | Wed | 9:00–11:00 AM | Requirements Engineering — User Stories vs. Use Cases | Claire Okafor | BA |
| 2 | Apr 17 | Thu | 9:00–11:00 AM | Java Core Concepts — Streams + Lab | Dr. Michael Rivera | SW Dev |
| 2 | Apr 17 | Thu | 9:00–11:00 AM | Requirements Engineering — RTM + Lab | Claire Okafor | BA |
| 2 | Apr 18 | Fri | 9:00–10:00 AM | Java Core Concepts — Week 2 Quiz Review | Dr. Michael Rivera | SW Dev |
| 2 | Apr 18 | Fri | 9:00–10:00 AM | Requirements Engineering — Week 2 Quiz Review | Claire Okafor | BA |
| 3 | Apr 21 | Mon | 9:00–11:00 AM | SQL and Database Design — Relational Model + DDL | Dr. Michael Rivera | SW Dev |
| 3 | Apr 21 | Mon | 9:00–11:00 AM | SQL for Analysts — Reading Data Models | Claire Okafor | BA |
| 3 | Apr 22 | Tue | 9:00–11:00 AM | SQL — DML: SELECT, INSERT, UPDATE | Dr. Michael Rivera | SW Dev |
| 3 | Apr 22 | Tue | 9:00–11:00 AM | SQL for Analysts — SELECT Queries for Reporting | Claire Okafor | BA |
| 3 | Apr 23 | Wed | 9:00–11:00 AM | SQL — JOINs and CTEs | Dr. Michael Rivera | SW Dev |
| 3 | Apr 23 | Wed | 9:00–11:00 AM | SQL for Analysts — Joins and Aggregates | Claire Okafor | BA |
| 3 | Apr 24 | Thu | 9:00–11:00 AM | SQL — Indexing and Normalization + Lab | Dr. Michael Rivera | SW Dev |
| 3 | Apr 24 | Thu | 9:00–11:00 AM | SQL for Analysts — SQL for Analyst Workflows + Lab | Claire Okafor | BA |
| 3 | Apr 25 | Fri | 9:00–10:00 AM | SQL — Week 3 Quiz Review | Dr. Michael Rivera | SW Dev |
| 3 | Apr 25 | Fri | 9:00–10:00 AM | SQL for Analysts — Week 3 Quiz Review | Claire Okafor | BA |
| 4 | Apr 28 | Mon | 9:00–11:00 AM | Software Architecture — REST API Design | Dr. Michael Rivera | SW Dev |
| 4 | Apr 28 | Mon | 9:00–11:00 AM | Process Modeling — BPMN 2.0 Fundamentals | Claire Okafor | BA |
| 4 | Apr 29 | Tue | 9:00–11:00 AM | Software Architecture — Microservices | Dr. Michael Rivera | SW Dev |
| 4 | Apr 29 | Tue | 9:00–11:00 AM | Process Modeling — AS-IS vs. TO-BE Analysis | Claire Okafor | BA |
| 4 | Apr 30 | Wed | 9:00–11:00 AM | Software Architecture — Design Patterns | Dr. Michael Rivera | SW Dev |
| 4 | Apr 30 | Wed | 9:00–11:00 AM | Process Modeling — UML Activity Diagrams + Swimlanes | Claire Okafor | BA |
| 4 | May 1 | Thu | 9:00–11:00 AM | Software Architecture — SOLID + Lab | Dr. Michael Rivera | SW Dev |
| 4 | May 1 | Thu | 9:00–11:00 AM | Process Modeling — Modeling Tools + Lab | Claire Okafor | BA |
| 4 | May 2 | Fri | 9:00–10:00 AM | Software Architecture — Week 4 Quiz Review | Dr. Michael Rivera | SW Dev |
| 4 | May 2 | Fri | 9:00–10:00 AM | Process Modeling — Week 4 Quiz Review | Claire Okafor | BA |
| 5 | May 5 | Mon | 9:00–11:00 AM | DevOps Foundations — Git and Branching | Dr. Michael Rivera | SW Dev |
| 5 | May 5 | Mon | 9:00–11:00 AM | Data Analysis and Visualization — Descriptive Stats | Claire Okafor | BA |
| 5 | May 6 | Tue | 9:00–11:00 AM | DevOps Foundations — CI/CD Pipelines | Dr. Michael Rivera | SW Dev |
| 5 | May 6 | Tue | 9:00–11:00 AM | Data Analysis — Excel Pivot Tables + Charts | Claire Okafor | BA |
| 5 | May 7 | Wed | 9:00–11:00 AM | DevOps Foundations — Docker and Containerization | Dr. Michael Rivera | SW Dev |
| 5 | May 7 | Wed | 9:00–11:00 AM | Data Analysis — Data Visualization Best Practices | Claire Okafor | BA |
| 5 | May 8 | Thu | 9:00–11:00 AM | DevOps Foundations — Jenkins + Lab | Dr. Michael Rivera | SW Dev |
| 5 | May 8 | Thu | 9:00–11:00 AM | Data Analysis — Power BI Dashboard + Lab | Claire Okafor | BA |
| 5 | May 9 | Fri | 9:00–10:00 AM | DevOps Foundations — Week 5 Quiz Review | Dr. Michael Rivera | SW Dev |
| 5 | May 9 | Fri | 9:00–10:00 AM | Data Analysis — Week 5 Quiz Review | Claire Okafor | BA |
| 6 | May 12 | Mon | 9:00–11:00 AM | Agile and Scrum — Agile Principles + Scrum Framework | Dr. Michael Rivera | SW Dev |
| 6 | May 12 | Mon | 9:00–11:00 AM | Stakeholder Management — Communication Planning | Claire Okafor | BA |
| 6 | May 13 | Tue | 9:00–11:00 AM | Agile and Scrum — User Stories and Backlog | Dr. Michael Rivera | SW Dev |
| 6 | May 13 | Tue | 9:00–11:00 AM | Stakeholder Management — Conflict Resolution | Claire Okafor | BA |
| 6 | May 14 | Wed | 9:00–11:00 AM | Agile and Scrum — Scrum Ceremonies in Practice | Dr. Michael Rivera | SW Dev |
| 6 | May 14 | Wed | 9:00–11:00 AM | Stakeholder Management — Scope Creep + Change Control | Claire Okafor | BA |
| 6 | May 15 | Thu | 9:00–11:00 AM | Agile and Scrum — Jira + Retrospectives + Lab | Dr. Michael Rivera | SW Dev |
| 6 | May 15 | Thu | 9:00–11:00 AM | Stakeholder Management — Business Case + Lab | Claire Okafor | BA |
| 6 | May 16 | Fri | 9:00–10:00 AM | Agile and Scrum — Week 6 Quiz Review | Dr. Michael Rivera | SW Dev |
| 6 | May 16 | Fri | 9:00–10:00 AM | Stakeholder Management — Week 6 Quiz Review | Claire Okafor | BA |
| 7 | May 19 | Mon | 9:00–11:00 AM | Code Quality — TDD: RED → GREEN → REFACTOR | Dr. Michael Rivera | SW Dev |
| 7 | May 19 | Mon | 9:00–11:00 AM | Agile for BAs — The BA in Agile | Claire Okafor | BA |
| 7 | May 20 | Tue | 9:00–11:00 AM | Code Quality — Code Review Best Practices | Dr. Michael Rivera | SW Dev |
| 7 | May 20 | Tue | 9:00–11:00 AM | Agile for BAs — Backlog Grooming and Story Refinement | Claire Okafor | BA |
| 7 | May 21 | Wed | 9:00–11:00 AM | Code Quality — Refactoring Techniques | Dr. Michael Rivera | SW Dev |
| 7 | May 21 | Wed | 9:00–11:00 AM | Agile for BAs — Acceptance Criteria and BDD (Gherkin) | Claire Okafor | BA |
| 7 | May 22 | Thu | 9:00–11:00 AM | Code Quality — SOLID Applied + Static Analysis + Lab | Dr. Michael Rivera | SW Dev |
| 7 | May 22 | Thu | 9:00–11:00 AM | Agile for BAs — Collaboration with Devs + QA + Lab | Claire Okafor | BA |
| 7 | May 23 | Fri | 9:00–10:00 AM | Code Quality — Week 7 Quiz Review | Dr. Michael Rivera | SW Dev |
| 7 | May 23 | Fri | 9:00–10:00 AM | Agile for BAs — Week 7 Quiz Review | Claire Okafor | BA |
| 8 | May 26 | Tue | 9:00–11:00 AM | Capstone Kick-off + Architecture Planning | Dr. Michael Rivera | SW Dev |
| 8 | May 26 | Tue | 9:00–11:00 AM | BA Capstone Kick-off + Project Brief | Claire Okafor | BA |
| 8 | May 27 | Wed | 9:00–10:00 AM | Capstone Check-in #1 (Office Hours) | Dr. Michael Rivera | SW Dev |
| 8 | May 27 | Wed | 9:00–10:00 AM | BA Capstone Check-in #1 (Office Hours) | Claire Okafor | BA |
| 8 | May 28 | Thu | 9:00–10:00 AM | Capstone Check-in #2 (Office Hours) | Dr. Michael Rivera | SW Dev |
| 8 | May 28 | Thu | 9:00–10:00 AM | BA Capstone Check-in #2 (Office Hours) | Claire Okafor | BA |
| 8 | May 29 | Fri | 9:00–11:00 AM | Capstone Presentations and Program Closing | Dr. Michael Rivera | SW Dev |
| 8 | May 29 | Fri | 9:00–11:00 AM | BA Capstone Presentations and Program Closing | Claire Okafor | BA |

*Note: May 25 (Memorial Day, US public holiday) — no sessions. Program continues Tuesday May 26.*

---

## Part 6: Student Metrics Dashboard

### How to Access This Report in the Platform

Sarah (Org Admin) navigates to: **Org Admin Dashboard → Analytics → Program Reports → FNBC Graduate Developer Program 2026 → Student Metrics**.

She selects:
- **Report Type:** Cohort Performance Summary
- **Date Range:** April 7 – May 29, 2026
- **Tracks:** All Tracks
- **Export Format:** PDF or Excel

The report generates the following table. Scores are out of 100. Lab scores are pass/fail converted to percentage (full marks for pass, 70% for late-but-waived, 0% for fail/not-submitted).

---

### Full Student Metrics Table

| Metric | James Okonkwo | Priya Sharma | David Kowalski | Marcus Chen | Fatima Al-Hassan |
|---|---|---|---|---|---|
| **Track** | SW Dev | SW Dev | SW Dev | BA | BA |
| **Week 1 Quiz** | 78 | 92 | 71 | 85 | 88 |
| **Week 2 Quiz** | 82 | 95 | 68 | 89 | 91 |
| **Week 3 Quiz** | 88 | 90 | 74 | 82 | 87 |
| **Week 4 Quiz** | 75 | 88 | 70 | 79 | 84 |
| **Week 5 Quiz** | 84 | 94 | 65 | 91 | 90 |
| **Week 6 Quiz** | 90 | 91 | 78 | 88 | 86 |
| **Week 7 Quiz** | 86 | 96 | 72 | 85 | 89 |
| **Week 8 Capstone** | 88 | 95 | 76 | 84 | 91 |
| **Quiz Average** | 83.9 | 92.6 | 71.8 | 85.4 | 88.3 |
| **Exercises Completed** | 8/8 | 8/8 | 7/8 | 8/8 | 8/8 |
| **Labs Completed** | 8/8 | 8/8 | 6/8 | 8/8 | 7/8 |
| **Late Submissions** | 1 (W4 Lab, waived) | 0 | 2 (W3, W6 Labs) | 0 | 1 (W7 Lab, 5% deduction) |
| **Attendance %** | 96% | 100% | 88% | 98% | 100% |
| **AI Assistant Queries** | 12 | 5 | 8 | 19 | 15 |
| **Avg Quiz Attempts** | 1.2 | 1.0 | 1.8 | 1.1 | 1.0 |
| **Lab Pass Rate** | 100% | 100% | 75% | 100% | 88% |
| **Final Program Score** | 83.9 | 92.6 | 71.8 | 85.4 | 88.3 |
| **Passed (≥80%)** | YES | YES | NO | YES | YES |
| **Certificate Issued** | YES | YES | NO | YES | YES |
| **Status** | PASSED | PASSED | REMEDIATION | PASSED | PASSED |

---

### Individual Student Notes

**James Okonkwo (SW Dev — PASSED, 83.9%)**
Strong overall performance with a clear progression arc. Stumbled in Week 4 due to a verified lab environment outage. Java week (Week 2) showed a strong recovery after initial syntax confusion. Best week: Agile (90%). Highly engaged learner; asked good questions in Q&A.

**Priya Sharma (SW Dev — PASSED, 92.6%)**
Top performer in the cohort. Perfect attendance, zero late submissions, lowest average quiz attempt count (1.0 — always passed first time). Priya took the fewest AI assistant queries, suggesting high confidence and independent problem-solving. Capstone scored 95 — near-perfect.

**David Kowalski (SW Dev — REMEDIATION, 71.8%)**
David is a candidate for the remediation program. His scores consistently trended below the 80% threshold across all weeks, with particular struggles in DevOps (65%). He missed 2 full days of sessions (Week 3 Thursday, Week 5 Wednesday) without advance notice, leading to 2 late lab submissions that were not waived (no technical justification provided). His capstone (76%) was functional but lacked test coverage (62%, below 80% requirement). Recommended: re-sit Week 5 (DevOps) and Week 3 (SQL) modules before formal re-assessment.

**Marcus Chen (BA — PASSED, 85.4%)**
Solid BA track performance. Marcus showed genuine strength in requirements engineering (Week 2 quiz: 89%) and stakeholder management (Week 6: 88%). High AI assistant usage (19 queries) — most of which were substantive questions about Gherkin scenarios and BPMN notation, suggesting active engagement rather than answer-seeking. His BA capstone was strong on traceability but light on the business case section.

**Fatima Al-Hassan (BA — PASSED, 88.3%)**
Second-highest overall scorer. Perfect attendance, no quiz re-attempts. One late lab in Week 7 (BA Agile Lab submitted Saturday due to a personal commitment) with a 5% deduction applied (82 → 77.9 for that component). Despite this, her overall average remained well above threshold. SQL for Analysts was her relative weakness (Week 3: 87%) but she leveraged the AI assistant effectively to work through JOIN concepts independently.

---

### Cohort Summary Statistics

| Metric | SW Dev Track | BA Track | Overall |
|---|---|---|---|
| **Students** | 3 | 2 | 5 |
| **Pass Rate** | 66.7% (2/3) | 100% (2/2) | 80% (4/5) |
| **Average Score** | 82.8% | 86.9% | 84.4% |
| **Top Scorer** | Priya Sharma (92.6%) | Fatima Al-Hassan (88.3%) | Priya Sharma (92.6%) |
| **Perfect Attendance** | 1 (Priya) | 2 (Marcus, Fatima) | 3/5 |
| **Avg Lab Completion** | 91.7% | 93.8% | 92.5% |
| **Certificates Issued** | 2 | 2 | 4 |

---

## Appendix: Sample Exercise Content

### Appendix A — Sample Week 1 Exercise (SW Dev Track)

**Exercise: BankAccount Class — Python OOP**

```python
# starter.py — provided to students
class BankAccount:
    """
    TODO: Implement the BankAccount class.
    Requirements:
    - __init__(owner: str, balance: float = 0.0)
    - deposit(amount: float) -> float  (returns new balance)
    - withdraw(amount: float) -> float  (raises InsufficientFundsError if amount > balance)
    - get_balance() -> float
    - __str__() -> str  (e.g. "BankAccount(owner=James, balance=£500.00)")
    """
    pass


class SavingsAccount(BankAccount):
    """
    TODO: Extend BankAccount.
    - __init__(owner: str, balance: float = 0.0, interest_rate: float = 0.03)
    - apply_interest() -> float  (returns balance after applying annual interest)
    """
    pass


class InsufficientFundsError(Exception):
    """Raised when a withdrawal exceeds the current balance."""
    pass
```

```python
# test_bank_account.py — provided, students must not modify
import pytest
from starter import BankAccount, SavingsAccount, InsufficientFundsError

def test_deposit_increases_balance():
    acc = BankAccount("James", 100.0)
    assert acc.deposit(50.0) == 150.0

def test_withdraw_decreases_balance():
    acc = BankAccount("James", 200.0)
    assert acc.withdraw(75.0) == 125.0

def test_withdraw_raises_on_overdraft():
    acc = BankAccount("James", 50.0)
    with pytest.raises(InsufficientFundsError):
        acc.withdraw(100.0)

def test_savings_interest():
    sav = SavingsAccount("James", 1000.0, 0.05)
    assert sav.apply_interest() == 1050.0
```

---

### Appendix B — Sample BA Lab Brief (Week 2 — RTM)

**Requirements Traceability Matrix Exercise**

**Background:** You have been provided with 15 functional requirements from the FNBC Digital Onboarding BRD (Business Requirements Document), an excerpt of the system design document (3 pages), and a test scenario template.

**Your Task:** Build a Requirements Traceability Matrix (RTM) in Excel with the following columns:

| Req ID | Requirement Description | Source (BRD Section) | Design Reference | Test Scenario ID | Test Type | Status |
|---|---|---|---|---|---|---|
| FR-001 | The system shall allow a customer to open a personal checking account online | BRD §3.1 | DES-004 | TC-001, TC-002 | Functional | Covered |
| FR-002 | The system shall validate customer identity using government-issued ID | BRD §3.2 | DES-007 | TC-005 | Functional | Covered |
| ... | ... | ... | ... | ... | ... | ... |

**Deliverable:** Completed Excel RTM file showing all 15 requirements traced through design and test scenarios. At least 3 requirements should show "Not Covered" status to demonstrate RTM gap analysis.

---

### Appendix C — Sample Gherkin Scenarios (Week 7 BA Track)

**User Story:** As an FNBC customer, I want to transfer funds between my accounts so that I can manage my money flexibly.

```gherkin
Feature: Fund Transfer Between Accounts
  As an FNBC customer
  I want to transfer funds between my accounts
  So that I can manage my money flexibly

  Scenario: Successful transfer between own accounts
    Given I am logged in as customer "james.okonkwo@fnbc.com"
    And I have a checking account with balance £1,000.00
    And I have a savings account with balance £500.00
    When I transfer £200.00 from checking to savings
    Then my checking balance should be £800.00
    And my savings balance should be £700.00
    And I should see a confirmation message "Transfer successful"

  Scenario: Transfer exceeds daily limit
    Given I am logged in as customer "james.okonkwo@fnbc.com"
    And my daily transfer limit is £5,000.00
    And I have already transferred £4,800.00 today
    When I attempt to transfer £500.00
    Then the transfer should be rejected
    And I should see an error "Daily transfer limit exceeded. Remaining today: £200.00"
    And no funds should be debited

  Scenario: Transfer to a blocked account
    Given I am logged in as customer "james.okonkwo@fnbc.com"
    And destination account "ACC-99872" has status "blocked"
    When I attempt to transfer £100.00 to "ACC-99872"
    Then the transfer should be rejected
    And I should see an error "This account is not currently accepting transfers"
    And a fraud alert should be logged with reference number
```

---

### Appendix D — Platform Admin Quick Reference for FNBC Scenario

**Service Ports (self-hosted deployment):**

| Service | Port | Purpose |
|---|---|---|
| Frontend (Legacy) | 3000 | Main platform UI (HTTPS) |
| Frontend (React) | 5173 | Vite dev server |
| User Management API | 8000 | Auth, user accounts, RBAC |
| Course Management API | 8001 | Courses, tracks, projects, enrollment |
| Course Generator | 8004 | AI course content generation |
| Content Management | 8005 | Content upload, processing |
| AI Assistant (RAG) | 8009 | Purple chat button — knowledge retrieval |
| Knowledge Graph | 8012 | Course relationship graph |
| NLP Preprocessing | 8013 | Query intent classification |
| Metadata Service | 8014 | Fuzzy course/content search |
| Ollama (LLMs) | 8015 | Local Mistral + LLaMA models |

**Key Admin Actions for FNBC Onboarding:**

```bash
# Check all services are running
./app-control.sh docker-status

# Create org admin manually (if wizard fails)
python create-admin.py --email sarah.training@fnbc.com --org "First National Bank of Commerce"

# Bulk import students from CSV
curl -X POST https://localhost:8001/tracks/{track_id}/bulk-enroll \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -F "file=@fnbc_students.csv"

# Check health of AI assistant
curl http://localhost:8009/health

# View quiz analytics for a course instance
curl http://localhost:8001/course-instances/{instance_id}/quiz-publications \
     -H "Authorization: Bearer $TOKEN"
```

**Troubleshooting Common FNBC Demo Issues:**

| Issue | Likely Cause | Solution |
|---|---|---|
| Students can't see Week 1 quiz | Quiz not published for course instance | Instructor → Quiz Management → Publish All |
| Lab won't start | Docker resource limit | `docker-compose restart lab-containers` |
| AI assistant not responding | RAG service on 8009 down | `./app-control.sh docker-restart ai-assistant` |
| Bulk enrollment fails silently | Missing `last_name` column in CSV | Ensure CSV has: email, last_name, first_name (optional) |
| Org admin can't see student progress | Student enrolled at course level only, not track | Re-enroll via `POST /tracks/{track_id}/bulk-enroll` |

---

*Document End — FNBC Complete Platform Walkthrough v1.0*
*Prepared for: Braun Brelin, AI Elevate (Owner Review)*
*Classification: Internal Demo Reference*

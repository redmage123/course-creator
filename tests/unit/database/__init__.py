"""
Database transaction and ACID property tests

BUSINESS CONTEXT:
Ensures database transactions maintain ACID properties (Atomicity, Consistency,
Isolation, Durability) which are critical for data integrity in the course
creator platform. Transaction failures could result in:
- Partial course enrollments (student charged but not enrolled)
- Inconsistent analytics data
- Lost course progress
- Corrupted user data

TECHNICAL IMPLEMENTATION:
Tests cover all four ACID properties:
- Atomicity: All-or-nothing transaction commits/rollbacks
- Consistency: Constraint enforcement and referential integrity
- Isolation: Concurrent transaction behavior and lock handling
- Durability: Committed data persists across failures

WHY THIS APPROACH:
Real PostgreSQL testing validates actual database behavior including
locking, isolation levels, deadlock detection, and performance characteristics
that cannot be tested with mocks.
"""

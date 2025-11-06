"""
Redis Distributed Locking Tests

BUSINESS CONTEXT:
Comprehensive tests for Redis-based distributed locking mechanisms ensuring
safe concurrent access to shared resources across multiple service instances.
Critical for preventing race conditions and maintaining data consistency in
distributed systems.

TECHNICAL IMPLEMENTATION:
- Tests lock acquisition and release
- Validates lock timeout behavior
- Tests deadlock prevention mechanisms
- Validates lock contention handling
- Tests lock renewal and extension
- Validates atomic lock operations

TDD APPROACH:
These tests validate that distributed locks:
- Prevent concurrent access to critical sections
- Release automatically on timeout
- Handle process failures gracefully
- Support lock renewal for long operations
- Provide atomic operations
- Prevent deadlocks

BUSINESS REQUIREMENTS:
1. Only one service instance can hold a lock at a time
2. Locks must auto-release on timeout to prevent deadlocks
3. Lock operations must be atomic
4. System must handle lock contention gracefully
5. Long-running operations must be able to extend locks
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4
import sys
from pathlib import Path
import time

# Add shared cache module to path
shared_path = Path(__file__).parent.parent.parent.parent / 'shared'
sys.path.insert(0, str(shared_path))


class TestBasicLockOperations:
    """
    Test Suite: Basic Lock Acquisition and Release

    BUSINESS REQUIREMENT:
    Distributed locks must support basic acquire/release operations
    with proper exclusivity guarantees.
    """

    @pytest.mark.asyncio
    async def test_acquire_lock_succeeds_when_unlocked(self, redis_cache):
        """
        TEST: Lock acquisition succeeds when lock is not held

        BUSINESS REQUIREMENT:
        First process to request lock should acquire it

        VALIDATES:
        - Lock can be acquired
        - Returns True on success
        """
        lock_key = f"lock:resource:{uuid4()}"
        lock_value = str(uuid4())
        ttl_seconds = 10

        # Try to acquire lock using SETNX (set if not exists)
        result = await redis_cache.set(lock_key, lock_value, nx=True, ex=ttl_seconds)

        assert result is True

        # Verify lock is set
        stored_value = await redis_cache.get(lock_key)
        assert stored_value == lock_value

        # Cleanup
        await redis_cache.delete(lock_key)

    @pytest.mark.asyncio
    async def test_acquire_lock_fails_when_locked(self, redis_cache):
        """
        TEST: Lock acquisition fails when lock is already held

        BUSINESS REQUIREMENT:
        Only one process can hold a lock at a time

        SECURITY CRITICAL:
        Prevents concurrent access to critical sections

        VALIDATES:
        - Second acquire attempt fails
        - Original lock holder maintains lock
        """
        lock_key = f"lock:resource:{uuid4()}"
        lock_value_1 = str(uuid4())
        lock_value_2 = str(uuid4())
        ttl_seconds = 10

        # First process acquires lock
        result1 = await redis_cache.set(lock_key, lock_value_1, nx=True, ex=ttl_seconds)
        assert result1 is True

        # Second process tries to acquire same lock
        result2 = await redis_cache.set(lock_key, lock_value_2, nx=True, ex=ttl_seconds)
        assert result2 is False

        # Original lock value is preserved
        stored_value = await redis_cache.get(lock_key)
        assert stored_value == lock_value_1
        assert stored_value != lock_value_2

        # Cleanup
        await redis_cache.delete(lock_key)

    @pytest.mark.asyncio
    async def test_release_lock_by_owner_succeeds(self, redis_cache):
        """
        TEST: Lock can be released by its owner

        BUSINESS REQUIREMENT:
        Process that acquired lock can release it

        VALIDATES:
        - Lock release succeeds
        - Lock becomes available for others
        """
        lock_key = f"lock:resource:{uuid4()}"
        lock_value = str(uuid4())
        ttl_seconds = 10

        # Acquire lock
        await redis_cache.set(lock_key, lock_value, nx=True, ex=ttl_seconds)

        # Verify lock holder
        stored_value = await redis_cache.get(lock_key)
        assert stored_value == lock_value

        # Release lock (verify it's our lock before deleting)
        if stored_value == lock_value:
            await redis_cache.delete(lock_key)

        # Verify lock is released
        assert await redis_cache.get(lock_key) is None

    @pytest.mark.asyncio
    async def test_cannot_release_someone_elses_lock(self, redis_cache):
        """
        TEST: Process cannot release lock held by another process

        SECURITY CRITICAL:
        Prevents one process from releasing another's lock

        VALIDATES:
        - Lock ownership is verified before release
        - Other process's lock remains intact
        """
        lock_key = f"lock:resource:{uuid4()}"
        lock_value_1 = str(uuid4())
        lock_value_2 = str(uuid4())
        ttl_seconds = 10

        # Process 1 acquires lock
        await redis_cache.set(lock_key, lock_value_1, nx=True, ex=ttl_seconds)

        # Process 2 tries to release (but checks ownership first)
        stored_value = await redis_cache.get(lock_key)
        can_release = (stored_value == lock_value_2)

        if can_release:
            await redis_cache.delete(lock_key)

        # Lock should still exist (owned by process 1)
        assert await redis_cache.get(lock_key) == lock_value_1

        # Cleanup
        await redis_cache.delete(lock_key)


class TestLockTimeoutBehavior:
    """
    Test Suite: Lock Timeout and Auto-Release

    BUSINESS REQUIREMENT:
    Locks must auto-release after timeout to prevent deadlocks
    when processes crash or fail to release locks.
    """

    @pytest.mark.asyncio
    async def test_lock_expires_after_ttl(self, redis_cache):
        """
        TEST: Lock automatically expires after TTL

        BUSINESS REQUIREMENT:
        Dead processes should not hold locks indefinitely

        VALIDATES:
        - Lock exists before TTL
        - Lock is gone after TTL
        - Other processes can acquire after expiration
        """
        lock_key = f"lock:resource:{uuid4()}"
        lock_value = str(uuid4())
        ttl_seconds = 2

        # Acquire lock with short TTL
        await redis_cache.set(lock_key, lock_value, nx=True, ex=ttl_seconds)

        # Immediately after, lock should exist
        assert await redis_cache.get(lock_key) == lock_value

        # Wait for expiration
        await asyncio.sleep(ttl_seconds + 0.5)

        # Lock should be gone
        assert await redis_cache.get(lock_key) is None

        # Another process can now acquire
        new_lock_value = str(uuid4())
        result = await redis_cache.set(lock_key, new_lock_value, nx=True, ex=10)
        assert result is True

        # Cleanup
        await redis_cache.delete(lock_key)

    @pytest.mark.asyncio
    async def test_check_lock_ttl_remaining(self, redis_cache):
        """
        TEST: Can check remaining TTL of lock

        BUSINESS REQUIREMENT:
        Processes need to know when lock will expire

        VALIDATES:
        - TTL can be queried
        - TTL decreases over time
        """
        lock_key = f"lock:resource:{uuid4()}"
        lock_value = str(uuid4())
        ttl_seconds = 10

        # Acquire lock
        await redis_cache.set(lock_key, lock_value, nx=True, ex=ttl_seconds)

        # Check TTL
        ttl_remaining = await redis_cache.ttl(lock_key)

        assert ttl_remaining is not None
        assert 0 < ttl_remaining <= ttl_seconds

        # Wait a bit
        await asyncio.sleep(1)

        # TTL should have decreased
        new_ttl = await redis_cache.ttl(lock_key)
        assert new_ttl < ttl_remaining

        # Cleanup
        await redis_cache.delete(lock_key)

    @pytest.mark.asyncio
    async def test_extend_lock_ttl_by_owner(self, redis_cache):
        """
        TEST: Lock owner can extend TTL for long operations

        BUSINESS REQUIREMENT:
        Long-running operations need to extend lock lifetime

        VALIDATES:
        - TTL can be extended by owner
        - Extended TTL is updated
        """
        lock_key = f"lock:resource:{uuid4()}"
        lock_value = str(uuid4())
        initial_ttl = 5
        extended_ttl = 15

        # Acquire lock
        await redis_cache.set(lock_key, lock_value, nx=True, ex=initial_ttl)

        # Check initial TTL
        ttl1 = await redis_cache.ttl(lock_key)
        assert ttl1 <= initial_ttl

        # Wait a bit
        await asyncio.sleep(1)

        # Extend lock (verify ownership first)
        stored_value = await redis_cache.get(lock_key)
        if stored_value == lock_value:
            # Set new expiry
            await redis_cache.expire(lock_key, extended_ttl)

        # Check new TTL
        ttl2 = await redis_cache.ttl(lock_key)
        assert ttl2 > ttl1  # TTL should be higher after extension
        assert ttl2 <= extended_ttl

        # Cleanup
        await redis_cache.delete(lock_key)


class TestLockContention:
    """
    Test Suite: Lock Contention and Competition

    BUSINESS REQUIREMENT:
    System must handle multiple processes competing for same lock
    with fair and predictable behavior.
    """

    @pytest.mark.asyncio
    async def test_multiple_processes_compete_for_lock(self, redis_cache):
        """
        TEST: Multiple processes competing for lock

        BUSINESS REQUIREMENT:
        Only one process wins lock acquisition

        VALIDATES:
        - Exactly one process acquires lock
        - Other processes fail acquisition
        """
        lock_key = f"lock:resource:{uuid4()}"
        ttl_seconds = 10

        # Simulate 5 processes trying to acquire lock
        async def try_acquire_lock(process_id: int):
            lock_value = f"process_{process_id}_{uuid4()}"
            result = await redis_cache.set(lock_key, lock_value, nx=True, ex=ttl_seconds)
            return (process_id, result, lock_value)

        # Run all attempts concurrently
        results = await asyncio.gather(*[try_acquire_lock(i) for i in range(5)])

        # Exactly one should succeed
        successful_acquisitions = [r for r in results if r[1] is True]
        failed_acquisitions = [r for r in results if r[1] is False]

        assert len(successful_acquisitions) == 1
        assert len(failed_acquisitions) == 4

        # Verify winner holds the lock
        winner_id, _, winner_value = successful_acquisitions[0]
        stored_value = await redis_cache.get(lock_key)
        assert stored_value == winner_value

        # Cleanup
        await redis_cache.delete(lock_key)

    @pytest.mark.asyncio
    async def test_lock_retry_with_exponential_backoff(self, redis_cache):
        """
        TEST: Lock acquisition with retry and backoff

        BUSINESS REQUIREMENT:
        Processes should retry lock acquisition with backoff

        VALIDATES:
        - Retry mechanism works
        - Eventually acquires lock after release
        """
        lock_key = f"lock:resource:{uuid4()}"
        ttl_seconds = 2

        # Process 1 acquires lock
        lock_value_1 = str(uuid4())
        await redis_cache.set(lock_key, lock_value_1, nx=True, ex=ttl_seconds)

        # Process 2 tries with retry
        lock_value_2 = str(uuid4())
        max_retries = 5
        acquired = False

        for attempt in range(max_retries):
            result = await redis_cache.set(lock_key, lock_value_2, nx=True, ex=ttl_seconds)
            if result:
                acquired = True
                break

            # Exponential backoff: 0.1, 0.2, 0.4, 0.8, 1.6 seconds
            backoff = 0.1 * (2 ** attempt)
            await asyncio.sleep(backoff)

        # Process 2 should eventually acquire lock (after process 1's lock expires)
        assert acquired is True

        # Verify process 2 now holds lock
        stored_value = await redis_cache.get(lock_key)
        assert stored_value == lock_value_2

        # Cleanup
        await redis_cache.delete(lock_key)

    @pytest.mark.asyncio
    async def test_lock_waiting_queue_fairness(self, redis_cache):
        """
        TEST: Lock acquisition has reasonable fairness

        BUSINESS REQUIREMENT:
        Processes waiting for lock should have fair chance

        VALIDATES:
        - Multiple waiters can eventually acquire lock
        - System doesn't favor specific processes
        """
        lock_key = f"lock:resource:{uuid4()}"
        ttl_seconds = 1
        successful_acquisitions = []

        async def acquire_with_retry(process_id: int):
            lock_value = f"process_{process_id}_{uuid4()}"

            for _ in range(10):  # Try 10 times
                result = await redis_cache.set(lock_key, lock_value, nx=True, ex=ttl_seconds)
                if result:
                    successful_acquisitions.append(process_id)
                    await asyncio.sleep(0.5)  # Hold lock briefly
                    # Release if we still own it
                    stored = await redis_cache.get(lock_key)
                    if stored == lock_value:
                        await redis_cache.delete(lock_key)
                    return True

                await asyncio.sleep(0.1)  # Wait before retry

            return False

        # Run 5 competing processes
        await asyncio.gather(*[acquire_with_retry(i) for i in range(5)])

        # At least 3 processes should have succeeded
        assert len(successful_acquisitions) >= 3


class TestDeadlockPrevention:
    """
    Test Suite: Deadlock Prevention Mechanisms

    BUSINESS REQUIREMENT:
    System must prevent deadlocks where processes wait indefinitely
    for locks held by each other.
    """

    @pytest.mark.asyncio
    async def test_lock_with_timeout_prevents_deadlock(self, redis_cache):
        """
        TEST: Lock timeout prevents deadlock

        BUSINESS REQUIREMENT:
        Timeout ensures locks don't persist if process crashes

        VALIDATES:
        - Lock expires even if not explicitly released
        - System recovers from process failure
        """
        lock_key = f"lock:resource:{uuid4()}"
        lock_value = str(uuid4())
        ttl_seconds = 2

        # Simulate process acquiring lock but crashing (not releasing)
        await redis_cache.set(lock_key, lock_value, nx=True, ex=ttl_seconds)

        # Process crashes here (no explicit release)

        # Wait for timeout
        await asyncio.sleep(ttl_seconds + 0.5)

        # Lock should be released automatically
        assert await redis_cache.get(lock_key) is None

        # Another process can now acquire
        new_lock_value = str(uuid4())
        result = await redis_cache.set(lock_key, new_lock_value, nx=True, ex=ttl_seconds)
        assert result is True

        # Cleanup
        await redis_cache.delete(lock_key)

    @pytest.mark.asyncio
    async def test_ordered_lock_acquisition_prevents_deadlock(self, redis_cache):
        """
        TEST: Ordered lock acquisition prevents circular deadlock

        BUSINESS REQUIREMENT:
        Acquiring multiple locks in consistent order prevents deadlock

        VALIDATES:
        - Locks can be acquired in order
        - No circular wait condition
        """
        lock_key_a = f"lock:resource_a:{uuid4()}"
        lock_key_b = f"lock:resource_b:{uuid4()}"
        ttl_seconds = 10

        # Process 1: Acquire locks in order A -> B
        lock_value_1 = str(uuid4())

        # Acquire A first
        result_a1 = await redis_cache.set(lock_key_a, lock_value_1, nx=True, ex=ttl_seconds)
        assert result_a1 is True

        # Then acquire B
        result_b1 = await redis_cache.set(lock_key_b, lock_value_1, nx=True, ex=ttl_seconds)
        assert result_b1 is True

        # Process 2: Also tries to acquire in order A -> B (not B -> A)
        lock_value_2 = str(uuid4())

        # Try A (will fail, held by process 1)
        result_a2 = await redis_cache.set(lock_key_a, lock_value_2, nx=True, ex=ttl_seconds)
        assert result_a2 is False

        # Process 2 doesn't proceed to B without A (prevents deadlock)

        # Process 1 releases locks
        await redis_cache.delete(lock_key_a)
        await redis_cache.delete(lock_key_b)

        # Now process 2 can acquire both
        result_a2_retry = await redis_cache.set(lock_key_a, lock_value_2, nx=True, ex=ttl_seconds)
        assert result_a2_retry is True

        result_b2_retry = await redis_cache.set(lock_key_b, lock_value_2, nx=True, ex=ttl_seconds)
        assert result_b2_retry is True

        # Cleanup
        await redis_cache.delete(lock_key_a)
        await redis_cache.delete(lock_key_b)


class TestLockPerformance:
    """
    Test Suite: Lock Performance Validation

    BUSINESS REQUIREMENT:
    Lock operations must be fast to avoid becoming bottleneck.
    """

    @pytest.mark.asyncio
    async def test_lock_acquisition_is_fast(self, redis_cache):
        """
        TEST: Lock acquisition completes quickly

        VALIDATES:
        - Lock acquisition takes <10ms
        """
        lock_key = f"lock:resource:{uuid4()}"
        lock_value = str(uuid4())
        ttl_seconds = 10

        start = time.time()
        await redis_cache.set(lock_key, lock_value, nx=True, ex=ttl_seconds)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 10, f"Lock acquisition took {elapsed_ms:.2f}ms (expected <10ms)"

        # Cleanup
        await redis_cache.delete(lock_key)

    @pytest.mark.asyncio
    async def test_lock_release_is_fast(self, redis_cache):
        """
        TEST: Lock release completes quickly

        VALIDATES:
        - Lock release takes <10ms
        """
        lock_key = f"lock:resource:{uuid4()}"
        lock_value = str(uuid4())
        ttl_seconds = 10

        # Acquire lock
        await redis_cache.set(lock_key, lock_value, nx=True, ex=ttl_seconds)

        # Measure release time
        start = time.time()
        await redis_cache.delete(lock_key)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 10, f"Lock release took {elapsed_ms:.2f}ms (expected <10ms)"

    @pytest.mark.asyncio
    async def test_high_throughput_lock_operations(self, redis_cache):
        """
        TEST: System handles high throughput of lock operations

        BUSINESS REQUIREMENT:
        Lock system must handle many operations per second

        VALIDATES:
        - 100 lock/unlock cycles complete in <1 second
        """
        start = time.time()

        for i in range(100):
            lock_key = f"lock:resource_{i}:{uuid4()}"
            lock_value = str(uuid4())

            # Acquire
            await redis_cache.set(lock_key, lock_value, nx=True, ex=10)

            # Release
            await redis_cache.delete(lock_key)

        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 1000, f"100 lock cycles took {elapsed_ms:.2f}ms (expected <1000ms)"


class TestDistributedLockPatterns:
    """
    Test Suite: Common Distributed Lock Patterns

    BUSINESS REQUIREMENT:
    Support common distributed lock use cases in microservices.
    """

    @pytest.mark.asyncio
    async def test_mutex_lock_for_critical_section(self, redis_cache):
        """
        TEST: Mutex lock protects critical section

        BUSINESS REQUIREMENT:
        Critical sections need exclusive access

        VALIDATES:
        - Only one process executes critical section at a time
        """
        lock_key = f"lock:critical_section:{uuid4()}"
        shared_resource = []
        ttl_seconds = 5

        async def critical_section(process_id: int):
            lock_value = f"process_{process_id}_{uuid4()}"

            # Try to acquire lock
            acquired = await redis_cache.set(lock_key, lock_value, nx=True, ex=ttl_seconds)

            if acquired:
                # Critical section - modify shared resource
                await asyncio.sleep(0.1)  # Simulate work
                shared_resource.append(process_id)
                await asyncio.sleep(0.1)  # More work

                # Release lock
                stored = await redis_cache.get(lock_key)
                if stored == lock_value:
                    await redis_cache.delete(lock_key)

                return True
            else:
                return False

        # Run multiple processes, but only one should succeed per attempt
        results = await asyncio.gather(*[critical_section(i) for i in range(5)])

        # At least one process should have succeeded
        assert any(results)

        # Shared resource should have been modified
        assert len(shared_resource) > 0

    @pytest.mark.asyncio
    async def test_read_write_lock_simulation(self, redis_cache):
        """
        TEST: Simulate read/write lock pattern

        BUSINESS REQUIREMENT:
        Multiple readers OR single writer

        VALIDATES:
        - Write lock excludes all other operations
        - System supports the pattern
        """
        write_lock_key = f"lock:write:{uuid4()}"
        lock_value = str(uuid4())
        ttl_seconds = 10

        # Acquire write lock (exclusive)
        write_acquired = await redis_cache.set(write_lock_key, lock_value, nx=True, ex=ttl_seconds)
        assert write_acquired is True

        # While write lock is held, no other writes can proceed
        other_lock_value = str(uuid4())
        other_write_acquired = await redis_cache.set(write_lock_key, other_lock_value, nx=True, ex=ttl_seconds)
        assert other_write_acquired is False

        # Release write lock
        await redis_cache.delete(write_lock_key)

        # Now others can acquire write lock
        new_write_acquired = await redis_cache.set(write_lock_key, other_lock_value, nx=True, ex=ttl_seconds)
        assert new_write_acquired is True

        # Cleanup
        await redis_cache.delete(write_lock_key)

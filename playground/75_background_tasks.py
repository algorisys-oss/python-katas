"""
Kata 75 -- Background Tasks
Run: python playground/75_background_tasks.py

Build a background task system for Ignite: after-response tasks,
BackgroundTasks collector, in-memory task queue with workers, and
task retry logic -- all using asyncio.

Completes within 5 seconds.
"""

from __future__ import annotations

import asyncio
import time
import traceback
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine


# ===========================================================================
# SECTION 1: Background Tasks Collector
# ===========================================================================
# During request handling, you collect tasks that should run AFTER the
# response is sent. This keeps response times fast while doing work
# like sending emails or updating caches in the background.

class BackgroundTasks:
    """Collects tasks to run after the HTTP response is sent.

    Usage in a route handler:
        async def create_user(request):
            user = save_user(request.body)
            request.background.add_task(send_welcome_email, user.email)
            request.background.add_task(update_analytics, "user_created")
            return {"id": user.id}  # Response sent immediately
            # Tasks run after response is sent
    """

    def __init__(self):
        self._tasks: list[tuple[Callable, tuple, dict]] = []

    def add_task(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Add a task to run after the response is sent."""
        self._tasks.append((func, args, kwargs))

    async def run(self) -> list[dict[str, Any]]:
        """Run all collected tasks.

        Returns a list of results for each task.
        """
        results = []
        for func, args, kwargs in self._tasks:
            start = time.monotonic()
            try:
                result = func(*args, **kwargs)
                # If the function is a coroutine, await it
                if asyncio.iscoroutine(result):
                    result = await result
                elapsed = (time.monotonic() - start) * 1000
                results.append({
                    "task": func.__name__,
                    "status": "success",
                    "result": result,
                    "elapsed_ms": round(elapsed, 2),
                })
            except Exception as exc:
                elapsed = (time.monotonic() - start) * 1000
                results.append({
                    "task": func.__name__,
                    "status": "error",
                    "error": str(exc),
                    "elapsed_ms": round(elapsed, 2),
                })
        self._tasks.clear()
        return results

    def __len__(self) -> int:
        return len(self._tasks)


# ===========================================================================
# SECTION 2: Task Status and Task Item
# ===========================================================================

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class TaskItem:
    """A task in the queue with metadata."""
    id: str
    func: Callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    max_retries: int = 0
    retry_count: int = 0
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None


# ===========================================================================
# SECTION 3: In-Memory Task Queue
# ===========================================================================
# A simple task queue that accepts tasks and processes them with workers.
# This is a toy version of what Celery or RQ do with Redis.

class TaskQueue:
    """In-memory task queue with worker processing.

    Features:
    - Enqueue tasks with optional retry configuration
    - Worker coroutine that processes tasks from the queue
    - Task status tracking
    - Retry logic with configurable max retries
    """

    def __init__(self):
        self._queue: deque[TaskItem] = deque()
        self._tasks: dict[str, TaskItem] = {}
        self._task_counter = 0
        self._running = False

    def enqueue(
        self,
        func: Callable,
        *args: Any,
        max_retries: int = 0,
        **kwargs: Any,
    ) -> str:
        """Add a task to the queue.

        Returns the task ID for status tracking.
        """
        self._task_counter += 1
        task_id = f"task-{self._task_counter}"

        task = TaskItem(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            max_retries=max_retries,
        )
        self._queue.append(task)
        self._tasks[task_id] = task
        return task_id

    def get_task(self, task_id: str) -> TaskItem | None:
        """Get task status by ID."""
        return self._tasks.get(task_id)

    async def _process_task(self, task: TaskItem) -> None:
        """Process a single task with retry logic."""
        task.status = TaskStatus.RUNNING

        try:
            result = task.func(*task.args, **task.kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            task.result = result
            task.status = TaskStatus.SUCCESS
            task.completed_at = time.time()

        except Exception as exc:
            task.error = str(exc)

            if task.retry_count < task.max_retries:
                # Retry the task
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                self._queue.append(task)  # Re-enqueue
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = time.time()

    async def process_all(self) -> list[str]:
        """Process all tasks currently in the queue.

        Returns list of completed task IDs.
        """
        completed = []
        while self._queue:
            task = self._queue.popleft()
            await self._process_task(task)
            if task.status in (TaskStatus.SUCCESS, TaskStatus.FAILED):
                completed.append(task.id)
        return completed

    async def run_worker(self, max_iterations: int = 100) -> None:
        """Run a worker that processes tasks from the queue.

        Args:
            max_iterations: Safety limit to prevent infinite loops.
        """
        self._running = True
        iterations = 0
        while self._running and iterations < max_iterations:
            if self._queue:
                task = self._queue.popleft()
                await self._process_task(task)
            else:
                break  # No more tasks
            iterations += 1
        self._running = False

    def stop(self) -> None:
        """Signal the worker to stop."""
        self._running = False

    @property
    def pending_count(self) -> int:
        return len(self._queue)

    @property
    def stats(self) -> dict[str, int]:
        """Get task statistics."""
        counts = {"pending": 0, "running": 0, "success": 0, "failed": 0, "retrying": 0}
        for task in self._tasks.values():
            counts[task.status.value] = counts.get(task.status.value, 0) + 1
        return counts


# ===========================================================================
# SECTION 4: Simulated Request Pipeline
# ===========================================================================
# Shows how background tasks integrate with the request/response cycle.

@dataclass
class Request:
    method: str
    path: str
    background: BackgroundTasks = field(default_factory=BackgroundTasks)


@dataclass
class Response:
    body: dict[str, Any]
    status_code: int = 200


async def simulate_request_pipeline(
    handler: Callable[[Request], Response],
    request: Request,
) -> tuple[Response, list[dict[str, Any]]]:
    """Simulate Ignite's request pipeline with background tasks.

    1. Call the handler to get the response
    2. Send the response (simulated)
    3. Run background tasks
    4. Return both for testing
    """
    response = handler(request)
    # Response would be sent to client here...
    # Now run background tasks
    task_results = await request.background.run()
    return response, task_results


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_background_tasks():
    """Show BackgroundTasks collector."""
    print("--- Section 1: BackgroundTasks Collector ---")

    log = []

    def send_email(to: str, subject: str):
        log.append(f"Email sent to {to}: {subject}")
        return "sent"

    def update_analytics(event: str):
        log.append(f"Analytics: {event}")
        return "recorded"

    tasks = BackgroundTasks()
    tasks.add_task(send_email, "alice@example.com", "Welcome!")
    tasks.add_task(update_analytics, "user_signup")
    print(f"  Tasks queued: {len(tasks)}")
    assert len(tasks) == 2

    results = asyncio.run(tasks.run())
    print(f"  Results: {len(results)} tasks completed")
    for r in results:
        print(f"    {r['task']}: {r['status']} ({r['elapsed_ms']:.2f}ms)")
    assert all(r["status"] == "success" for r in results)
    assert len(log) == 2
    print(f"  Side effects: {log}")

    print("  [PASS] BackgroundTasks collector works")


def demo_async_background_tasks():
    """Show async background tasks."""
    print("\n--- Section 2: Async Background Tasks ---")

    log = []

    async def async_notify(channel: str, message: str):
        # Simulate async work
        await asyncio.sleep(0.01)
        log.append(f"{channel}: {message}")
        return "notified"

    tasks = BackgroundTasks()
    tasks.add_task(async_notify, "slack", "Deploy complete")
    tasks.add_task(async_notify, "webhook", "Build passed")

    results = asyncio.run(tasks.run())
    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)
    print(f"  Async tasks: {log}")

    print("  [PASS] Async background tasks work")


def demo_task_error_handling():
    """Show error handling in background tasks."""
    print("\n--- Section 3: Task Error Handling ---")

    def succeed():
        return "ok"

    def fail():
        raise ValueError("Something went wrong")

    tasks = BackgroundTasks()
    tasks.add_task(succeed)
    tasks.add_task(fail)
    tasks.add_task(succeed)

    results = asyncio.run(tasks.run())
    print(f"  Task 1: {results[0]['status']}")
    print(f"  Task 2: {results[1]['status']} - {results[1]['error']}")
    print(f"  Task 3: {results[2]['status']}")

    assert results[0]["status"] == "success"
    assert results[1]["status"] == "error"
    assert results[2]["status"] == "success"  # Continues after error

    print("  [PASS] Task error handling works")


def demo_request_pipeline():
    """Show background tasks in the request pipeline."""
    print("\n--- Section 4: Request Pipeline ---")

    side_effects = []

    def create_user_handler(request: Request) -> Response:
        # Main work: create user
        user_id = 42

        # Queue background work
        request.background.add_task(
            lambda: side_effects.append("welcome_email_sent")
        )
        request.background.add_task(
            lambda: side_effects.append("analytics_updated")
        )

        # Return response immediately
        return Response(body={"id": user_id, "name": "Alice"}, status_code=201)

    request = Request(method="POST", path="/users")
    response, task_results = asyncio.run(
        simulate_request_pipeline(create_user_handler, request)
    )

    print(f"  Response: {response.status_code} {response.body}")
    print(f"  Background tasks: {len(task_results)} completed")
    print(f"  Side effects: {side_effects}")

    assert response.status_code == 201
    assert len(side_effects) == 2
    assert "welcome_email_sent" in side_effects
    assert "analytics_updated" in side_effects

    print("  [PASS] Request pipeline with background tasks works")


def demo_task_queue():
    """Show the in-memory task queue."""
    print("\n--- Section 5: Task Queue ---")

    queue = TaskQueue()
    results = []

    def process_order(order_id: int):
        results.append(f"order-{order_id}-processed")
        return f"processed-{order_id}"

    # Enqueue tasks
    id1 = queue.enqueue(process_order, 101)
    id2 = queue.enqueue(process_order, 102)
    id3 = queue.enqueue(process_order, 103)
    print(f"  Enqueued: {id1}, {id2}, {id3}")
    print(f"  Pending: {queue.pending_count}")
    assert queue.pending_count == 3

    # Process all
    completed = asyncio.run(queue.process_all())
    print(f"  Completed: {completed}")
    assert len(completed) == 3

    # Check individual task status
    task1 = queue.get_task(id1)
    print(f"  Task {id1}: status={task1.status.value}, result={task1.result}")
    assert task1.status == TaskStatus.SUCCESS
    assert task1.result == "processed-101"

    print(f"  Stats: {queue.stats}")
    print("  [PASS] Task queue works")


def demo_task_retry():
    """Show task retry logic."""
    print("\n--- Section 6: Task Retry ---")

    attempt_count = 0

    def flaky_task():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError(f"Attempt {attempt_count} failed")
        return "success on attempt 3"

    queue = TaskQueue()
    task_id = queue.enqueue(flaky_task, max_retries=3)

    asyncio.run(queue.run_worker())

    task = queue.get_task(task_id)
    print(f"  Attempts: {attempt_count}")
    print(f"  Status: {task.status.value}")
    print(f"  Result: {task.result}")
    print(f"  Retries: {task.retry_count}")

    assert task.status == TaskStatus.SUCCESS
    assert attempt_count == 3
    assert task.retry_count == 2  # 2 retries + 1 initial = 3 attempts

    print("  [PASS] Task retry works")


def demo_task_retry_exhausted():
    """Show what happens when retries are exhausted."""
    print("\n--- Section 7: Retry Exhausted ---")

    def always_fails():
        raise RuntimeError("Permanent failure")

    queue = TaskQueue()
    task_id = queue.enqueue(always_fails, max_retries=2)

    asyncio.run(queue.run_worker())

    task = queue.get_task(task_id)
    print(f"  Status: {task.status.value}")
    print(f"  Retries: {task.retry_count}/{task.max_retries}")
    print(f"  Error: {task.error}")

    assert task.status == TaskStatus.FAILED
    assert task.retry_count == 2
    assert "Permanent failure" in task.error

    print("  [PASS] Retry exhaustion works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_background_tasks()
    demo_async_background_tasks()
    demo_task_error_handling()
    demo_request_pipeline()
    demo_task_queue()
    demo_task_retry()
    demo_task_retry_exhausted()

    print("\n--- Summary ---")
    print("Background tasks give our Ignite framework:")
    print("  - BackgroundTasks collector for after-response work")
    print("  - Support for both sync and async task functions")
    print("  - Error isolation (one failing task doesn't block others)")
    print("  - Request pipeline integration (tasks run after response)")
    print("  - In-memory task queue with worker processing")
    print("  - Task retry logic with configurable max retries")
    print("  - Task status tracking (pending, running, success, failed)")
    print("\nAll 7 sections passed. Background tasks mastered!")
    print("Next up: Kata 76 -- testing utilities!")


if __name__ == "__main__":
    main()

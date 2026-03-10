# Kata 75 -- Background Tasks

[prev: 74-rate-limiting](./74-rate-limiting.md) | [next: 76-testing-utilities](./76-testing-utilities.md)

---

## What We're Building

A **background task system** for our Ignite framework. When a user creates an account, you want to send a welcome email and update analytics -- but you don't want to block the HTTP response while doing it. We build:

1. **BackgroundTasks collector** -- queue tasks during request handling, run them after the response is sent
2. **Sync and async support** -- both regular functions and async coroutines
3. **In-memory task queue** -- enqueue tasks for worker processing
4. **Task retry logic** -- automatically retry failed tasks with configurable max retries
5. **Status tracking** -- monitor task progress (pending, running, success, failed)

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| After-response tasks | Run work after the HTTP response is sent | Email, analytics, cleanup |
| `BackgroundTasks` | Collects tasks during request handling | FastAPI/Starlette pattern |
| `asyncio.iscoroutine` | Check if a result needs awaiting | Supporting sync + async |
| Task queue | FIFO queue with worker processing | Decoupling work from requests |
| Retry logic | Re-enqueue failed tasks | Flaky external services |
| Task status tracking | Pending/running/success/failed | Monitoring and debugging |

## The Code

### 1. BackgroundTasks Collector

```python
class BackgroundTasks:
    def __init__(self):
        self._tasks = []  # [(func, args, kwargs), ...]

    def add_task(self, func, *args, **kwargs):
        self._tasks.append((func, args, kwargs))

    async def run(self):
        results = []
        for func, args, kwargs in self._tasks:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            results.append({"task": func.__name__, "status": "success"})
        return results
```

### 2. Request Pipeline Integration

```python
async def simulate_request_pipeline(handler, request):
    response = handler(request)      # 1. Get response
    # Response sent to client here   # 2. Send response
    task_results = await request.background.run()  # 3. Run tasks
    return response, task_results
```

### 3. Task Queue with Retry

```python
class TaskQueue:
    async def _process_task(self, task):
        try:
            result = task.func(*task.args)
            task.status = TaskStatus.SUCCESS
        except Exception:
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                self._queue.append(task)  # Re-enqueue
            else:
                task.status = TaskStatus.FAILED
```

## Playground

```python
python playground/75_background_tasks.py
```

Expected output:

```
--- Section 1: BackgroundTasks Collector ---
  Tasks queued: 2
  Results: 2 tasks completed
    send_email: success (0.01ms)
    update_analytics: success (0.00ms)
  [PASS] BackgroundTasks collector works

--- Section 2: Async Background Tasks ---
  Async tasks: ['slack: Deploy complete', 'webhook: Build passed']
  [PASS] Async background tasks work

--- Section 3: Task Error Handling ---
  Task 1: success
  Task 2: error - Something went wrong
  Task 3: success
  [PASS] Task error handling works

--- Section 4-7: Pipeline, Queue, Retry ---
  [PASS] All sections pass
```

## How It Works

### Background Task Lifecycle

```
Request arrives
     |
     v
Route handler runs
     |
     +-- request.background.add_task(send_email, ...)
     +-- request.background.add_task(update_analytics, ...)
     |
     v
Response sent to client  <-- Client doesn't wait for tasks
     |
     v
request.background.run()
     |
     +-- send_email(...)      -> success
     +-- update_analytics(...) -> success
```

### Task Queue with Retry

```
enqueue(flaky_task, max_retries=3)

Attempt 1: flaky_task() -> ConnectionError
  retry_count=1, status=RETRYING, re-enqueue

Attempt 2: flaky_task() -> ConnectionError
  retry_count=2, status=RETRYING, re-enqueue

Attempt 3: flaky_task() -> "success!"
  status=SUCCESS
```

## Exercises

1. **Add task priorities** -- support HIGH, NORMAL, LOW priorities. Workers should process high-priority tasks first.

2. **Add task timeout** -- if a task takes longer than N seconds, cancel it and mark it as failed with a timeout error.

3. **Add exponential backoff** -- instead of immediate retry, wait 1s, 2s, 4s between retries.

4. **Add task dependencies** -- task B depends on task A. B only runs after A succeeds. If A fails, B is skipped.

5. **Add task progress** -- for long-running tasks, allow reporting progress (e.g., "processing item 5 of 100").

## What's Next

With background tasks handling post-response work, in [Kata 76: Testing Utilities](./76-testing-utilities.md) we'll build testing tools for our Ignite framework -- a TestClient that sends simulated requests and dependency overrides for mocking.

---

[prev: 74-rate-limiting](./74-rate-limiting.md) | [next: 76-testing-utilities](./76-testing-utilities.md)

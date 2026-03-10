"""
Kata 24 -- Multiprocessing
Run: python playground/24_multiprocessing.py

True parallelism with multiprocessing: Pool for CPU-bound work, Queue and Pipe
for inter-process communication, Value+Lock for shared state.

IMPORTANT: All multiprocessing code must be inside `if __name__ == "__main__":`
to prevent recursive process spawning.
"""

from multiprocessing import Process, Pool, Queue, Pipe, Value, Lock, Manager


# ===========================================================================
# SECTION 1: CPU-BOUND PARALLEL COMPUTATION WITH POOL
# ===========================================================================

def square(n: int) -> int:
    """Compute n squared (simulates CPU-bound work)."""
    return n * n


def sum_range(args: tuple[int, int]) -> int:
    """Sum numbers in a range (for chunked parallel reduction)."""
    start, end = args
    return sum(i * i for i in range(start, end))


# ===========================================================================
# SECTION 2: INTER-PROCESS COMMUNICATION WITH QUEUE
# ===========================================================================

def queue_producer(q: Queue, items: list[str]) -> None:
    """Put items into queue, then send sentinel."""
    for item in items:
        q.put(item.upper())
    q.put(None)  # sentinel = "I'm done"


def queue_consumer(q: Queue, result_queue: Queue) -> None:
    """Read from queue until sentinel, collect results."""
    results = []
    while True:
        item = q.get()
        if item is None:
            break
        results.append(f"processed:{item}")
    result_queue.put(results)


# ===========================================================================
# SECTION 3: INTER-PROCESS COMMUNICATION WITH PIPE
# ===========================================================================

def pipe_sender(conn) -> None:
    """Send messages through a pipe connection."""
    conn.send({"type": "greeting", "msg": "hello from child"})
    conn.send({"type": "data", "values": [10, 20, 30]})
    conn.send({"type": "done"})
    conn.close()


def pipe_receiver(conn) -> list[dict]:
    """Receive messages from a pipe connection until 'done'."""
    messages = []
    while True:
        msg = conn.recv()
        messages.append(msg)
        if msg.get("type") == "done":
            break
    conn.close()
    return messages


# ===========================================================================
# SECTION 4: SHARED COUNTER WITH VALUE + LOCK
# ===========================================================================

def increment_counter(counter: Value, lock: Lock, n: int) -> None:
    """Increment shared counter n times with lock protection."""
    for _ in range(n):
        with lock:
            counter.value += 1


def increment_counter_unsafe(counter: Value, n: int) -> None:
    """Increment shared counter WITHOUT lock (demonstrates race condition)."""
    for _ in range(n):
        counter.value += 1


# ===========================================================================
# SECTION 5: MANAGER FOR COMPLEX SHARED STATE
# ===========================================================================

def manager_worker(shared_dict: dict, key: str, value: int) -> None:
    """Write a computed result into a shared Manager dict."""
    shared_dict[key] = value * value


# ===========================================================================
# MAIN -- run all demonstrations
# ===========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("KATA 24 -- MULTIPROCESSING")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Pool.map() -- parallel computation
    # ------------------------------------------------------------------
    print("\n--- 1. Pool.map() -- parallel squares ---")

    numbers = list(range(16))
    with Pool(processes=2) as pool:
        results = pool.map(square, numbers)

    print(f"Input:   {numbers}")
    print(f"Squares: {results}")
    assert results == [n * n for n in numbers], "Pool.map squares failed"
    print("PASS: Pool.map computed all squares correctly")

    # ------------------------------------------------------------------
    # 1b. Pool.starmap() -- multiple arguments
    # ------------------------------------------------------------------
    print("\n--- 1b. Pool -- chunked parallel sum of squares ---")

    # Split range(100) into 4 chunks for parallel reduction
    chunk_size = 25
    chunks = [(i, i + chunk_size) for i in range(0, 100, chunk_size)]
    with Pool(processes=2) as pool:
        partial_sums = pool.map(sum_range, chunks)

    total = sum(partial_sums)
    expected = sum(i * i for i in range(100))
    print(f"Chunks: {chunks}")
    print(f"Partial sums: {partial_sums}")
    print(f"Total sum of squares 0..99: {total}")
    assert total == expected, f"Expected {expected}, got {total}"
    print("PASS: Parallel reduction matches sequential result")

    # ------------------------------------------------------------------
    # 2. Queue -- producer-consumer
    # ------------------------------------------------------------------
    print("\n--- 2. Queue -- producer-consumer ---")

    work_queue: Queue = Queue()
    result_queue: Queue = Queue()
    items = ["alpha", "beta", "gamma", "delta"]

    producer = Process(target=queue_producer, args=(work_queue, items))
    consumer = Process(target=queue_consumer, args=(work_queue, result_queue))

    producer.start()
    consumer.start()
    producer.join()
    consumer.join()

    results = result_queue.get()
    print(f"Input:    {items}")
    print(f"Produced: {results}")
    assert results == ["processed:ALPHA", "processed:BETA", "processed:GAMMA", "processed:DELTA"]
    print("PASS: Queue producer-consumer pipeline works")

    # ------------------------------------------------------------------
    # 3. Pipe -- point-to-point communication
    # ------------------------------------------------------------------
    print("\n--- 3. Pipe -- point-to-point ---")

    parent_conn, child_conn = Pipe()

    sender_proc = Process(target=pipe_sender, args=(child_conn,))
    sender_proc.start()

    # Receive in main process
    messages = pipe_receiver(parent_conn)
    sender_proc.join()

    for msg in messages:
        print(f"  Received: {msg}")

    assert len(messages) == 3
    assert messages[0]["msg"] == "hello from child"
    assert messages[1]["values"] == [10, 20, 30]
    assert messages[2]["type"] == "done"
    print("PASS: Pipe communication works")

    # ------------------------------------------------------------------
    # 4. Value + Lock -- shared counter (safe)
    # ------------------------------------------------------------------
    print("\n--- 4. Value + Lock -- shared counter ---")

    counter = Value('i', 0)  # 'i' = signed int
    lock = Lock()
    increments_per_process = 1000
    num_processes = 4

    procs = [
        Process(target=increment_counter, args=(counter, lock, increments_per_process))
        for _ in range(num_processes)
    ]
    for p in procs:
        p.start()
    for p in procs:
        p.join()

    expected_count = increments_per_process * num_processes
    print(f"Expected: {expected_count}")
    print(f"Actual:   {counter.value}")
    assert counter.value == expected_count, f"Race condition! Got {counter.value}"
    print("PASS: Shared counter with Lock is correct")

    # ------------------------------------------------------------------
    # 5. Manager -- shared dict
    # ------------------------------------------------------------------
    print("\n--- 5. Manager -- shared dict ---")

    with Manager() as manager:
        shared_dict = manager.dict()

        procs = [
            Process(target=manager_worker, args=(shared_dict, f"item_{i}", i + 1))
            for i in range(4)
        ]
        for p in procs:
            p.start()
        for p in procs:
            p.join()

        result = dict(shared_dict)

    print(f"Shared dict: {result}")
    assert result == {"item_0": 1, "item_1": 4, "item_2": 9, "item_3": 16}
    print("PASS: Manager dict shared across processes")

    # ------------------------------------------------------------------
    # 6. Process basics -- spawn and join
    # ------------------------------------------------------------------
    print("\n--- 6. Process basics ---")

    result_q: Queue = Queue()

    def basic_worker(name: str, q: Queue):
        q.put(f"Hello from {name} (pid will differ from main)")

    p = Process(target=basic_worker, args=("worker-1", result_q))
    p.start()
    p.join()

    msg = result_q.get()
    print(f"  {msg}")
    assert "Hello from worker-1" in msg
    print("PASS: Basic Process spawn and join works")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("ALL MULTIPROCESSING TESTS PASSED")
    print("=" * 60)
    print("""
Key takeaways:
  - Pool.map()     → parallel map over data (best for CPU-bound batch work)
  - Queue          → process-safe FIFO (producer-consumer pattern)
  - Pipe           → fast two-process channel (point-to-point)
  - Value + Lock   → shared memory scalar (counters, flags)
  - Manager        → shared complex objects (dicts, lists) via proxy
  - Always guard multiprocessing code with: if __name__ == "__main__"
  - Use multiprocessing for CPU-bound, threading for I/O-bound
""")

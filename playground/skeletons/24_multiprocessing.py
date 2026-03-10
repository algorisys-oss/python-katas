"""
Kata 24 -- Multiprocessing
Run: python playground/skeletons/24_multiprocessing.py

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
    # TODO: return n squared
    pass


def sum_range(args: tuple[int, int]) -> int:
    """Sum of squares for numbers in range [start, end)."""
    start, end = args
    # TODO: return sum of i*i for i in range(start, end)
    pass


# ===========================================================================
# SECTION 2: INTER-PROCESS COMMUNICATION WITH QUEUE
# ===========================================================================

def queue_producer(q: Queue, items: list[str]) -> None:
    """Put items into queue (uppercased), then send None sentinel."""
    # TODO: iterate over items, put each item.upper() into queue
    # TODO: put None as sentinel to signal "done"
    # HINT: q.put(item.upper()) for each item, then q.put(None)
    pass


def queue_consumer(q: Queue, result_queue: Queue) -> None:
    """Read from queue until sentinel, prefix each with 'processed:', collect into result_queue."""
    # TODO: loop getting items from q until None
    # TODO: append f"processed:{item}" to a results list
    # TODO: put the results list into result_queue
    # HINT: while True: item = q.get(); if item is None: break
    pass


# ===========================================================================
# SECTION 3: INTER-PROCESS COMMUNICATION WITH PIPE
# ===========================================================================

def pipe_sender(conn) -> None:
    """Send three messages through a pipe: greeting, data, done."""
    # TODO: send {"type": "greeting", "msg": "hello from child"}
    # TODO: send {"type": "data", "values": [10, 20, 30]}
    # TODO: send {"type": "done"}
    # TODO: close the connection
    # HINT: conn.send(dict_msg) then conn.close()
    pass


def pipe_receiver(conn) -> list[dict]:
    """Receive messages from pipe until type=='done', return list of all messages."""
    # TODO: loop receiving messages with conn.recv()
    # TODO: append each to a list
    # TODO: break when msg["type"] == "done"
    # TODO: close conn and return the list
    # HINT: msg = conn.recv(); messages.append(msg); check msg.get("type")
    pass


# ===========================================================================
# SECTION 4: SHARED COUNTER WITH VALUE + LOCK
# ===========================================================================

def increment_counter(counter: Value, lock: Lock, n: int) -> None:
    """Increment shared counter n times with lock protection."""
    # TODO: loop n times, acquire lock, increment counter.value
    # HINT: use `with lock:` context manager, then counter.value += 1
    pass


# ===========================================================================
# SECTION 5: MANAGER FOR COMPLEX SHARED STATE
# ===========================================================================

def manager_worker(shared_dict: dict, key: str, value: int) -> None:
    """Write value*value into shared_dict[key]."""
    # TODO: set shared_dict[key] = value * value
    pass


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

    try:
        numbers = list(range(16))
        # TODO: create a Pool with 2 processes, use pool.map(square, numbers)
        # HINT: with Pool(processes=2) as pool: results = pool.map(square, numbers)
        results = []  # replace with Pool.map result

        print(f"Input:   {numbers}")
        print(f"Squares: {results}")
        assert results == [n * n for n in numbers], "Pool.map squares failed"
        print("PASS: Pool.map computed all squares correctly")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"❌ Not yet implemented: {e}")

    # ------------------------------------------------------------------
    # 1b. Pool -- chunked parallel sum of squares
    # ------------------------------------------------------------------
    print("\n--- 1b. Pool -- chunked parallel sum of squares ---")

    try:
        chunk_size = 25
        chunks = [(i, i + chunk_size) for i in range(0, 100, chunk_size)]
        # TODO: use Pool.map(sum_range, chunks) to compute partial sums
        # TODO: sum the partial_sums to get total
        partial_sums = []  # replace with Pool.map result
        total = 0  # replace with sum(partial_sums)

        expected = sum(i * i for i in range(100))
        print(f"Chunks: {chunks}")
        print(f"Partial sums: {partial_sums}")
        print(f"Total sum of squares 0..99: {total}")
        assert total == expected, f"Expected {expected}, got {total}"
        print("PASS: Parallel reduction matches sequential result")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"❌ Not yet implemented: {e}")

    # ------------------------------------------------------------------
    # 2. Queue -- producer-consumer
    # ------------------------------------------------------------------
    print("\n--- 2. Queue -- producer-consumer ---")

    try:
        work_queue: Queue = Queue()
        result_queue: Queue = Queue()
        items = ["alpha", "beta", "gamma", "delta"]

        # TODO: create Process for queue_producer and queue_consumer
        # TODO: start both, join both
        # TODO: get results from result_queue
        # HINT: Process(target=queue_producer, args=(work_queue, items))
        results = []  # replace with result_queue.get()

        print(f"Input:    {items}")
        print(f"Produced: {results}")
        assert results == ["processed:ALPHA", "processed:BETA", "processed:GAMMA", "processed:DELTA"]
        print("PASS: Queue producer-consumer pipeline works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"❌ Not yet implemented: {e}")

    # ------------------------------------------------------------------
    # 3. Pipe -- point-to-point communication
    # ------------------------------------------------------------------
    print("\n--- 3. Pipe -- point-to-point ---")

    try:
        # TODO: create a Pipe() -- returns (parent_conn, child_conn)
        # TODO: spawn a Process running pipe_sender with child_conn
        # TODO: call pipe_receiver(parent_conn) in main process
        # TODO: join the sender process
        # HINT: parent_conn, child_conn = Pipe()
        messages = []  # replace with pipe_receiver result

        for msg in messages:
            print(f"  Received: {msg}")

        assert len(messages) == 3
        assert messages[0]["msg"] == "hello from child"
        assert messages[1]["values"] == [10, 20, 30]
        assert messages[2]["type"] == "done"
        print("PASS: Pipe communication works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"❌ Not yet implemented: {e}")

    # ------------------------------------------------------------------
    # 4. Value + Lock -- shared counter (safe)
    # ------------------------------------------------------------------
    print("\n--- 4. Value + Lock -- shared counter ---")

    try:
        # TODO: create Value('i', 0) and Lock()
        # TODO: spawn 4 processes each calling increment_counter with 1000 increments
        # TODO: start all, join all
        # HINT: counter = Value('i', 0); lock = Lock()
        increments_per_process = 1000
        num_processes = 4
        counter_value = 0  # replace with counter.value after joining

        expected_count = increments_per_process * num_processes
        print(f"Expected: {expected_count}")
        print(f"Actual:   {counter_value}")
        assert counter_value == expected_count, f"Race condition! Got {counter_value}"
        print("PASS: Shared counter with Lock is correct")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"❌ Not yet implemented: {e}")

    # ------------------------------------------------------------------
    # 5. Manager -- shared dict
    # ------------------------------------------------------------------
    print("\n--- 5. Manager -- shared dict ---")

    try:
        # TODO: create a Manager context, get a manager.dict()
        # TODO: spawn 4 processes calling manager_worker with keys "item_0".."item_3" and values 1..4
        # TODO: start all, join all, convert to regular dict
        # HINT: with Manager() as manager: shared_dict = manager.dict()
        result = {}  # replace with dict(shared_dict)

        print(f"Shared dict: {result}")
        assert result == {"item_0": 1, "item_1": 4, "item_2": 9, "item_3": 16}
        print("PASS: Manager dict shared across processes")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"❌ Not yet implemented: {e}")

    # ------------------------------------------------------------------
    # 6. Process basics -- spawn and join
    # ------------------------------------------------------------------
    print("\n--- 6. Process basics ---")

    try:
        result_q: Queue = Queue()

        def basic_worker(name: str, q: Queue):
            q.put(f"Hello from {name} (pid will differ from main)")

        # TODO: create a Process targeting basic_worker, start it, join it
        # TODO: get the message from result_q
        # HINT: p = Process(target=basic_worker, args=("worker-1", result_q))
        msg = ""  # replace with result_q.get()

        print(f"  {msg}")
        assert "Hello from worker-1" in msg
        print("PASS: Basic Process spawn and join works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"❌ Not yet implemented: {e}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("SKELETON RUN COMPLETE")
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

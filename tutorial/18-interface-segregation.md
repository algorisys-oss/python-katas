# Kata 18 -- Interface Segregation Principle

[prev: 17-liskov-substitution](./17-liskov-substitution.md) | [next: 19-dependency-inversion](./19-dependency-inversion.md)

---

## What We're Building

The **Interface Segregation Principle** (ISP) is the fourth SOLID principle. It states: *no client should be forced to depend on methods it does not use*. In practice, this means preferring many small, focused interfaces over one large "fat" interface.

In this kata we'll start with a fat `Worker` interface that forces every worker to implement `work()`, `eat()`, and `sleep()` -- even when some workers don't need all three. We'll split it into narrow role-based protocols, then apply the same technique to a document printer example. Along the way, you'll see how Python's `Protocol` class makes ISP natural and elegant.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Interface Segregation Principle | Clients shouldn't depend on methods they don't use | Designing interfaces/protocols for collaborators |
| Fat interface | One interface with too many methods | Recognizing the anti-pattern to refactor |
| Role interface | Small, focused interface for one capability | Splitting fat interfaces into composable pieces |
| `typing.Protocol` | Structural subtyping (duck typing with type safety) | Defining narrow interfaces without inheritance |
| Composition over inheritance | Combine small protocols instead of inheriting a big one | Building flexible, testable designs |

## The Code

### Step 1: The fat interface -- everything in one place

Here's a `Worker` ABC that forces every implementation to provide three methods. This works fine for a human worker, but what about a robot?

```python
from abc import ABC, abstractmethod


class Worker(ABC):
    """Fat interface: every worker MUST work, eat, AND sleep."""

    @abstractmethod
    def work(self) -> str: ...

    @abstractmethod
    def eat(self) -> str: ...

    @abstractmethod
    def sleep(self) -> str: ...


class HumanWorker(Worker):
    def __init__(self, name: str):
        self.name = name

    def work(self) -> str:
        return f"{self.name} is writing code"

    def eat(self) -> str:
        return f"{self.name} is eating lunch"

    def sleep(self) -> str:
        return f"{self.name} is sleeping"


class RobotWorker(Worker):
    def __init__(self, model: str):
        self.model = model

    def work(self) -> str:
        return f"{self.model} is assembling parts"

    def eat(self) -> str:
        # Robots don't eat! But we're FORCED to implement this.
        raise NotImplementedError("Robots don't eat")

    def sleep(self) -> str:
        # Robots don't sleep! Another forced implementation.
        raise NotImplementedError("Robots don't sleep")
```

The `RobotWorker` is forced to implement `eat()` and `sleep()` even though they make no sense. This is the ISP violation: the client (robot) depends on methods it doesn't use.

### Step 2: Why this is a problem

The fat interface causes real issues:

1. **Liskov Substitution violation** -- any code that calls `worker.eat()` will crash on a `RobotWorker`
2. **Misleading API** -- the type system says robots can eat, but they can't
3. **Brittle code** -- adding a new method to `Worker` (e.g., `take_vacation()`) forces changes in *every* implementation
4. **Testing friction** -- test doubles must implement methods they'll never use

```python
# This function LOOKS safe because it accepts Worker...
def lunch_break(worker: Worker) -> str:
    return worker.eat()  # ...but CRASHES on RobotWorker!
```

### Step 3: Split into role-based protocols

Instead of one fat interface, define small protocols for each capability:

```python
from typing import Protocol


class Workable(Protocol):
    """Can perform work."""
    def work(self) -> str: ...


class Feedable(Protocol):
    """Needs to eat."""
    def eat(self) -> str: ...


class Sleepable(Protocol):
    """Needs to sleep."""
    def sleep(self) -> str: ...
```

Each protocol describes exactly one capability. No class is forced to implement methods it doesn't need.

### Step 4: Implement only what makes sense

Now each class implements only the protocols that apply:

```python
class Human:
    """Implements Workable, Feedable, and Sleepable -- all three make sense."""

    def __init__(self, name: str):
        self.name = name

    def work(self) -> str:
        return f"{self.name} is writing code"

    def eat(self) -> str:
        return f"{self.name} is eating lunch"

    def sleep(self) -> str:
        return f"{self.name} is sleeping"


class Robot:
    """Implements only Workable -- robots don't eat or sleep."""

    def __init__(self, model: str):
        self.model = model

    def work(self) -> str:
        return f"{self.model} is assembling parts"
```

Notice: `Robot` has no `eat()` or `sleep()` methods. It doesn't pretend to support them. The type system accurately reflects what each class can do.

### Step 5: Functions depend on narrow protocols

Each function declares exactly which capability it needs:

```python
def assign_task(worker: Workable) -> str:
    """Needs only the ability to work."""
    return worker.work()


def lunch_break(eater: Feedable) -> str:
    """Needs only the ability to eat."""
    return eater.eat()


def night_rest(sleeper: Sleepable) -> str:
    """Needs only the ability to sleep."""
    return sleeper.sleep()
```

Now the type signatures are honest:
- `assign_task()` accepts both `Human` and `Robot` (both are `Workable`)
- `lunch_break()` accepts only `Human` (only humans are `Feedable`)
- You can't accidentally pass a `Robot` to `lunch_break()` -- the type checker will catch it

### Step 6: The document printer example

Here's a more realistic example. An office has printers, scanners, fax machines, and staplers. A fat interface forces every device to support all operations:

```python
# BAD: Fat interface for office machines
class MultiFunctionDevice(ABC):
    @abstractmethod
    def print_doc(self, doc: str) -> str: ...

    @abstractmethod
    def scan(self, doc: str) -> str: ...

    @abstractmethod
    def fax(self, doc: str, number: str) -> str: ...

    @abstractmethod
    def staple(self, doc: str) -> str: ...
```

A simple printer can't fax or staple. A basic scanner can't print. ISP says: split it.

```python
class Printable(Protocol):
    def print_doc(self, doc: str) -> str: ...

class Scannable(Protocol):
    def scan(self, doc: str) -> str: ...

class Faxable(Protocol):
    def fax(self, doc: str, number: str) -> str: ...

class Stapleable(Protocol):
    def staple(self, doc: str) -> str: ...
```

Now devices implement only what they support:

```python
class SimplePrinter:
    """Only prints."""
    def print_doc(self, doc: str) -> str:
        return f"Printing: {doc}"


class AllInOnePrinter:
    """Prints, scans, faxes, and staples."""
    def print_doc(self, doc: str) -> str:
        return f"Printing: {doc}"

    def scan(self, doc: str) -> str:
        return f"Scanning: {doc}"

    def fax(self, doc: str, number: str) -> str:
        return f"Faxing '{doc}' to {number}"

    def staple(self, doc: str) -> str:
        return f"Stapling: {doc}"


class OldFaxMachine:
    """Only faxes."""
    def fax(self, doc: str, number: str) -> str:
        return f"Faxing '{doc}' to {number}"
```

Functions depend on exactly the protocol they need:

```python
def print_report(printer: Printable, report: str) -> str:
    return printer.print_doc(report)


def scan_document(scanner: Scannable, doc: str) -> str:
    return scanner.scan(doc)


def send_fax(faxer: Faxable, doc: str, number: str) -> str:
    return faxer.fax(doc, number)
```

`print_report()` works with both `SimplePrinter` and `AllInOnePrinter`. `send_fax()` works with both `AllInOnePrinter` and `OldFaxMachine`. Each function gets exactly the interface it needs -- no more, no less.

### Step 7: Protocols naturally support ISP in Python

Python's `Protocol` class is a perfect fit for ISP because of **structural subtyping** (duck typing with type safety):

1. **No inheritance required** -- classes don't need to explicitly inherit from Protocol
2. **Automatic conformance** -- if a class has the right methods, it satisfies the protocol
3. **Composable** -- functions can accept unions of protocols or create combined protocols
4. **Gradual typing** -- works with existing code that wasn't designed for protocols

```python
# Compose protocols for functions that need multiple capabilities
class WorkingEater(Workable, Feedable, Protocol):
    """Needs both work and eat -- only Human satisfies this."""
    ...


def full_workday(worker: WorkingEater) -> list[str]:
    """Needs someone who can both work AND eat."""
    return [worker.work(), worker.eat(), worker.work()]
```

Compare this with ABC inheritance:
- **ABC approach:** Classes must explicitly inherit -- coupling to the hierarchy
- **Protocol approach:** Classes just need the right methods -- structural compatibility

### Step 8: Detecting ISP violations

Signs that you're violating ISP:

1. **`NotImplementedError` / `pass` implementations** -- the class doesn't really support that operation
2. **"God interfaces"** with 10+ methods -- no single client uses all of them
3. **Conditional logic by type** -- `if isinstance(worker, Robot): skip_eating()` suggests the interface is too broad
4. **Every change to the interface ripples to many classes** -- tight coupling from a fat interface

The fix is always the same: **split the fat interface into focused protocols, one per capability**.

## Playground

Run the full before/after comparison with tests:

```bash
python playground/18_interface_segregation.py
```

```
--- Section 1: The Fat Interface Problem ---
  HumanWorker.work() = alice is writing code
  HumanWorker.eat() = alice is eating lunch
  HumanWorker.sleep() = alice is sleeping
  RobotWorker.work() = RX-78 is assembling parts
  RobotWorker.eat() raised NotImplementedError -- ISP violation!
  RobotWorker.sleep() raised NotImplementedError -- ISP violation!
  Fat interface forces robots to fake capabilities they don't have.

--- Section 2: Split Into Role Protocols ---
  Workable, Feedable, Sleepable protocols defined.
  Each protocol has exactly ONE method -- no forced dependencies.

--- Section 3: Segregated Implementations ---
  Human implements: work, eat, sleep
  Robot implements: work (only what it actually does)
  No NotImplementedError -- no lies in the API.

--- Section 4: Functions Depend on Narrow Protocols ---
  assign_task(human) = alice is writing code
  assign_task(robot) = RX-78 is assembling parts
  lunch_break(human) = alice is eating lunch
  night_rest(human) = alice is sleeping
  Robot correctly excluded from lunch_break and night_rest.

--- Section 5: Document Printer Example ---
  SimplePrinter.print_doc() = Printing: Q4 Report
  AllInOnePrinter.print_doc() = Printing: Q4 Report
  AllInOnePrinter.scan() = Scanning: Contract
  AllInOnePrinter.fax() = Faxing 'Invoice' to 555-0123
  AllInOnePrinter.staple() = Stapling: Packet
  OldFaxMachine.fax() = Faxing 'Invoice' to 555-0123
  print_report() works with both SimplePrinter and AllInOnePrinter.
  send_fax() works with both AllInOnePrinter and OldFaxMachine.
  Each function gets exactly the interface it needs.

--- Section 6: Protocol Composition ---
  full_workday(human) = ['alice is writing code', 'alice is eating lunch', 'alice is writing code']
  Composed WorkingEater protocol: only Human qualifies.
  Protocol composition lets you combine narrow interfaces on demand.

--- Section 7: Detecting ISP Violations ---
  Fat interface method count: 3 (too many for some clients)
  Segregated protocol method counts: Workable=1, Feedable=1, Sleepable=1
  Each client depends on exactly what it uses -- no more, no less.

--- Summary ---
Interface Segregation Principle:
  - No client should depend on methods it doesn't use
  - Split fat interfaces into focused role protocols
  - Python's Protocol enables structural subtyping (duck typing + types)
  - Classes implement only the protocols that make sense
  - Functions declare exactly which capability they need
  - Compose protocols when you need multiple capabilities

All 7 sections passed. You've mastered the Interface Segregation Principle!
```

## How It Works

```
BEFORE (Fat Interface):              AFTER (Segregated Protocols):

+------------------+                 +----------+  +----------+  +-----------+
|     Worker       |                 | Workable |  | Feedable |  | Sleepable |
|                  |                 | work()   |  | eat()    |  | sleep()   |
| work()           |                 +----+-----+  +----+-----+  +-----+-----+
| eat()            |                      |             |              |
| sleep()          |                +-----+------+ +----+-----+  +----+-----+
+--------+---------+                |            | |          |  |          |
         |                          |  +----+    | |  +----+  |  |  +----+  |
    +----+-----+                    |  |Human|---+-+  |Human|--+  |  |Human| |
    |          |                    |  +-----+   | |  +-----+  |  |  +-----+ |
+---+---+ +---+-------+            |             | |           |  |          |
| Human | | Robot     |            |  +-----+    | +----------+  +----------+
| work  | | work      |            |  |Robot|----+
| eat   | | eat  = N/A|            |  +-----+
| sleep | | sleep = N/A|           +-------------+
+-------+ +-----------+
                                   Robot only implements Workable.
Robot FORCED to implement           No forced, fake implementations.
eat() and sleep().
```

The key insight: **the fat interface treats all capabilities as a bundle**. If you need `work()`, you're forced to take `eat()` and `sleep()` too. Segregated protocols let each client pick exactly what it needs. Python's `Protocol` makes this zero-cost -- no inheritance required, just implement the methods.

## Exercises

### Exercise 1: Add a recharging protocol

Robots need to recharge but humans don't. Create a `Rechargeable` protocol and implement it only on `Robot`:

```python
class Rechargeable(Protocol):
    def recharge(self) -> str: ...

# Add recharge() to Robot
# Create a recharge_station() function that accepts Rechargeable
# Verify: Human can't be passed to recharge_station()
```

### Exercise 2: Build a document workflow

Create a `DocumentWorkflow` that chains operations from different protocols. Each step uses the narrowest possible protocol:

```python
def document_workflow(
    printer: Printable,
    scanner: Scannable,
    faxer: Faxable,
    doc: str,
    fax_number: str,
) -> list[str]:
    """
    1. Print the original
    2. Scan a copy
    3. Fax to the recipient
    Return a list of status messages.
    """
    ...

# Test with AllInOnePrinter for all three roles
# Test with separate SimplePrinter + Scanner + OldFaxMachine
```

### Exercise 3: Repository protocols

Apply ISP to a data repository. Instead of one fat `Repository` with `create`, `read`, `update`, `delete`, `search`, `count`, and `export` methods, split into focused protocols:

```python
class Readable(Protocol):
    def get(self, id: str) -> dict | None: ...

class Writable(Protocol):
    def save(self, id: str, data: dict) -> None: ...

class Searchable(Protocol):
    def find(self, query: str) -> list[dict]: ...

# Build a ReadOnlyCache that only implements Readable
# Build a FullRepository that implements all three
# Write functions that depend on the narrowest protocol possible
```

## What's Next

In [Kata 19 -- Dependency Inversion Principle](./19-dependency-inversion.md), we'll tackle the fifth and final SOLID principle: high-level modules should not depend on low-level modules -- both should depend on abstractions. You'll learn to invert dependencies using protocols and dependency injection, making your architecture flexible and testable from the ground up.

---

[prev: 17-liskov-substitution](./17-liskov-substitution.md) | [next: 19-dependency-inversion](./19-dependency-inversion.md)

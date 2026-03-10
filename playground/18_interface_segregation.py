"""
Kata 18 -- Interface Segregation Principle
Run: python playground/18_interface_segregation.py

Start with a fat Worker interface that forces every worker to implement work(),
eat(), and sleep() -- then split into narrow role-based protocols so each class
only implements what it actually supports.
"""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


# ===========================================================================
# BEFORE: FAT INTERFACE (violates ISP)
# ===========================================================================

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
        raise NotImplementedError("Robots don't eat")

    def sleep(self) -> str:
        raise NotImplementedError("Robots don't sleep")


# ===========================================================================
# AFTER: SEGREGATED PROTOCOLS (each protocol = one capability)
# ===========================================================================

@runtime_checkable
class Workable(Protocol):
    """Can perform work."""
    def work(self) -> str: ...


@runtime_checkable
class Feedable(Protocol):
    """Needs to eat."""
    def eat(self) -> str: ...


@runtime_checkable
class Sleepable(Protocol):
    """Needs to sleep."""
    def sleep(self) -> str: ...


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


# --- Functions that depend on narrow protocols ---

def assign_task(worker: Workable) -> str:
    """Needs only the ability to work."""
    return worker.work()


def lunch_break(eater: Feedable) -> str:
    """Needs only the ability to eat."""
    return eater.eat()


def night_rest(sleeper: Sleepable) -> str:
    """Needs only the ability to sleep."""
    return sleeper.sleep()


# --- Protocol composition ---

class WorkingEater(Workable, Feedable, Protocol):
    """Needs both work and eat -- only Human satisfies this."""
    ...


def full_workday(worker: WorkingEater) -> list[str]:
    """Needs someone who can both work AND eat."""
    return [worker.work(), worker.eat(), worker.work()]


# ===========================================================================
# DOCUMENT PRINTER EXAMPLE
# ===========================================================================

@runtime_checkable
class Printable(Protocol):
    def print_doc(self, doc: str) -> str: ...


@runtime_checkable
class Scannable(Protocol):
    def scan(self, doc: str) -> str: ...


@runtime_checkable
class Faxable(Protocol):
    def fax(self, doc: str, number: str) -> str: ...


@runtime_checkable
class Stapleable(Protocol):
    def staple(self, doc: str) -> str: ...


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


def print_report(printer: Printable, report: str) -> str:
    return printer.print_doc(report)


def scan_document(scanner: Scannable, doc: str) -> str:
    return scanner.scan(doc)


def send_fax(faxer: Faxable, doc: str, number: str) -> str:
    return faxer.fax(doc, number)


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: The Fat Interface Problem ---
    print("--- Section 1: The Fat Interface Problem ---")

    hw = HumanWorker("alice")
    rw = RobotWorker("RX-78")

    print(f"  HumanWorker.work() = {hw.work()}")
    print(f"  HumanWorker.eat() = {hw.eat()}")
    print(f"  HumanWorker.sleep() = {hw.sleep()}")
    print(f"  RobotWorker.work() = {rw.work()}")

    try:
        rw.eat()
    except NotImplementedError:
        print("  RobotWorker.eat() raised NotImplementedError -- ISP violation!")

    try:
        rw.sleep()
    except NotImplementedError:
        print("  RobotWorker.sleep() raised NotImplementedError -- ISP violation!")

    assert hw.work() == "alice is writing code"
    assert rw.work() == "RX-78 is assembling parts"
    print("  Fat interface forces robots to fake capabilities they don't have.")

    print()

    # --- Section 2: Split Into Role Protocols ---
    print("--- Section 2: Split Into Role Protocols ---")

    # Verify each protocol has exactly one method (excluding dunder methods)
    for proto_name, proto_cls in [("Workable", Workable), ("Feedable", Feedable), ("Sleepable", Sleepable)]:
        methods = [m for m in dir(proto_cls) if not m.startswith("_")]
        assert len(methods) == 1, f"{proto_name} should have 1 method, has {len(methods)}"

    print("  Workable, Feedable, Sleepable protocols defined.")
    print("  Each protocol has exactly ONE method -- no forced dependencies.")

    print()

    # --- Section 3: Segregated Implementations ---
    print("--- Section 3: Segregated Implementations ---")

    human = Human("alice")
    robot = Robot("RX-78")

    # Human satisfies all three protocols
    assert isinstance(human, Workable)
    assert isinstance(human, Feedable)
    assert isinstance(human, Sleepable)

    human_capabilities = []
    if isinstance(human, Workable):
        human_capabilities.append("work")
    if isinstance(human, Feedable):
        human_capabilities.append("eat")
    if isinstance(human, Sleepable):
        human_capabilities.append("sleep")
    print(f"  Human implements: {', '.join(human_capabilities)}")

    # Robot satisfies only Workable
    assert isinstance(robot, Workable)
    assert not isinstance(robot, Feedable)
    assert not isinstance(robot, Sleepable)

    robot_capabilities = []
    if isinstance(robot, Workable):
        robot_capabilities.append("work")
    print(f"  Robot implements: {', '.join(robot_capabilities)} (only what it actually does)")

    print("  No NotImplementedError -- no lies in the API.")

    print()

    # --- Section 4: Functions Depend on Narrow Protocols ---
    print("--- Section 4: Functions Depend on Narrow Protocols ---")

    # Both human and robot can work
    print(f"  assign_task(human) = {assign_task(human)}")
    print(f"  assign_task(robot) = {assign_task(robot)}")
    assert assign_task(human) == "alice is writing code"
    assert assign_task(robot) == "RX-78 is assembling parts"

    # Only human can eat and sleep
    print(f"  lunch_break(human) = {lunch_break(human)}")
    print(f"  night_rest(human) = {night_rest(human)}")
    assert lunch_break(human) == "alice is eating lunch"
    assert night_rest(human) == "alice is sleeping"

    # Robot correctly excluded -- isinstance check proves it
    assert not isinstance(robot, Feedable), "Robot should NOT be Feedable"
    assert not isinstance(robot, Sleepable), "Robot should NOT be Sleepable"
    print("  Robot correctly excluded from lunch_break and night_rest.")

    print()

    # --- Section 5: Document Printer Example ---
    print("--- Section 5: Document Printer Example ---")

    simple = SimplePrinter()
    allinone = AllInOnePrinter()
    fax_machine = OldFaxMachine()

    # SimplePrinter: only Printable
    print(f"  SimplePrinter.print_doc() = {simple.print_doc('Q4 Report')}")
    assert isinstance(simple, Printable)
    assert not isinstance(simple, Scannable)
    assert not isinstance(simple, Faxable)

    # AllInOnePrinter: all protocols
    print(f"  AllInOnePrinter.print_doc() = {allinone.print_doc('Q4 Report')}")
    print(f"  AllInOnePrinter.scan() = {allinone.scan('Contract')}")
    print(f"  AllInOnePrinter.fax() = {allinone.fax('Invoice', '555-0123')}")
    print(f"  AllInOnePrinter.staple() = {allinone.staple('Packet')}")
    assert isinstance(allinone, Printable)
    assert isinstance(allinone, Scannable)
    assert isinstance(allinone, Faxable)
    assert isinstance(allinone, Stapleable)

    # OldFaxMachine: only Faxable
    print(f"  OldFaxMachine.fax() = {fax_machine.fax('Invoice', '555-0123')}")
    assert isinstance(fax_machine, Faxable)
    assert not isinstance(fax_machine, Printable)

    # Functions work with any conforming object
    assert print_report(simple, "Q4 Report") == "Printing: Q4 Report"
    assert print_report(allinone, "Q4 Report") == "Printing: Q4 Report"
    print("  print_report() works with both SimplePrinter and AllInOnePrinter.")

    assert send_fax(allinone, "Invoice", "555-0123") == "Faxing 'Invoice' to 555-0123"
    assert send_fax(fax_machine, "Invoice", "555-0123") == "Faxing 'Invoice' to 555-0123"
    print("  send_fax() works with both AllInOnePrinter and OldFaxMachine.")

    print("  Each function gets exactly the interface it needs.")

    print()

    # --- Section 6: Protocol Composition ---
    print("--- Section 6: Protocol Composition ---")

    result = full_workday(human)
    print(f"  full_workday(human) = {result}")
    assert result == ["alice is writing code", "alice is eating lunch", "alice is writing code"]

    # Verify Human satisfies the composed protocol, Robot does not
    assert isinstance(human, Workable) and isinstance(human, Feedable)
    assert isinstance(robot, Workable) and not isinstance(robot, Feedable)
    print("  Composed WorkingEater protocol: only Human qualifies.")

    print("  Protocol composition lets you combine narrow interfaces on demand.")

    print()

    # --- Section 7: Detecting ISP Violations ---
    print("--- Section 7: Detecting ISP Violations ---")

    # Count methods on fat vs segregated interfaces
    fat_methods = [m for m in dir(Worker) if not m.startswith("_")]
    print(f"  Fat interface method count: {len(fat_methods)} (too many for some clients)")
    assert len(fat_methods) == 3

    workable_methods = [m for m in dir(Workable) if not m.startswith("_")]
    feedable_methods = [m for m in dir(Feedable) if not m.startswith("_")]
    sleepable_methods = [m for m in dir(Sleepable) if not m.startswith("_")]
    print(f"  Segregated protocol method counts: Workable={len(workable_methods)}, "
          f"Feedable={len(feedable_methods)}, Sleepable={len(sleepable_methods)}")
    assert len(workable_methods) == 1
    assert len(feedable_methods) == 1
    assert len(sleepable_methods) == 1

    print("  Each client depends on exactly what it uses -- no more, no less.")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Interface Segregation Principle:")
    print("  - No client should depend on methods it doesn't use")
    print("  - Split fat interfaces into focused role protocols")
    print("  - Python's Protocol enables structural subtyping (duck typing + types)")
    print("  - Classes implement only the protocols that make sense")
    print("  - Functions declare exactly which capability they need")
    print("  - Compose protocols when you need multiple capabilities")
    print()
    print("All 7 sections passed. You've mastered the Interface Segregation Principle!")

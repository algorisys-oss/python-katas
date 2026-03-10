"""
Kata 18 -- Interface Segregation Principle
Run: python playground/skeletons/18_interface_segregation.py

Start with a fat Worker interface that forces every worker to implement work(),
eat(), and sleep() -- then split into narrow role-based protocols so each class
only implements what it actually supports.
"""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


# ===========================================================================
# BEFORE: FAT INTERFACE (violates ISP) -- provided for reference
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
# AFTER: YOUR SEGREGATED PROTOCOLS (each protocol = one capability)
# ===========================================================================

@runtime_checkable
class Workable(Protocol):
    """Can perform work. Should have one method: work() -> str"""
    # TODO: define the work() method signature
    ...


@runtime_checkable
class Feedable(Protocol):
    """Needs to eat. Should have one method: eat() -> str"""
    # TODO: define the eat() method signature
    ...


@runtime_checkable
class Sleepable(Protocol):
    """Needs to sleep. Should have one method: sleep() -> str"""
    # TODO: define the sleep() method signature
    ...


class Human:
    """Implements Workable, Feedable, and Sleepable -- all three make sense.

    Should have:
    - __init__(self, name: str)
    - work() -> str: return f"{self.name} is writing code"
    - eat() -> str: return f"{self.name} is eating lunch"
    - sleep() -> str: return f"{self.name} is sleeping"
    """

    def __init__(self, name: str):
        self.name = name

    def work(self) -> str:
        # TODO: return f"{self.name} is writing code"
        pass

    def eat(self) -> str:
        # TODO: return f"{self.name} is eating lunch"
        pass

    def sleep(self) -> str:
        # TODO: return f"{self.name} is sleeping"
        pass


class Robot:
    """Implements only Workable -- robots don't eat or sleep.

    Should have:
    - __init__(self, model: str)
    - work() -> str: return f"{self.model} is assembling parts"
    - NO eat() or sleep() methods!
    """

    def __init__(self, model: str):
        self.model = model

    def work(self) -> str:
        # TODO: return f"{self.model} is assembling parts"
        pass


# --- Functions that depend on narrow protocols ---

def assign_task(worker: Workable) -> str:
    """Needs only the ability to work."""
    # TODO: call worker.work() and return the result
    pass


def lunch_break(eater: Feedable) -> str:
    """Needs only the ability to eat."""
    # TODO: call eater.eat() and return the result
    pass


def night_rest(sleeper: Sleepable) -> str:
    """Needs only the ability to sleep."""
    # TODO: call sleeper.sleep() and return the result
    pass


# --- Protocol composition ---

class WorkingEater(Workable, Feedable, Protocol):
    """Needs both work and eat -- only Human satisfies this."""
    ...


def full_workday(worker: WorkingEater) -> list[str]:
    """Needs someone who can both work AND eat.
    Should return [worker.work(), worker.eat(), worker.work()]
    """
    # TODO: return a list of work, eat, work
    # HINT: [worker.work(), worker.eat(), worker.work()]
    pass


# ===========================================================================
# DOCUMENT PRINTER EXAMPLE
# ===========================================================================

@runtime_checkable
class Printable(Protocol):
    """Should have: print_doc(self, doc: str) -> str"""
    # TODO: define the print_doc() method signature
    ...


@runtime_checkable
class Scannable(Protocol):
    """Should have: scan(self, doc: str) -> str"""
    # TODO: define the scan() method signature
    ...


@runtime_checkable
class Faxable(Protocol):
    """Should have: fax(self, doc: str, number: str) -> str"""
    # TODO: define the fax() method signature
    ...


@runtime_checkable
class Stapleable(Protocol):
    """Should have: staple(self, doc: str) -> str"""
    # TODO: define the staple() method signature
    ...


class SimplePrinter:
    """Only prints.

    Should have:
    - print_doc(doc) -> str: return f"Printing: {doc}"
    """

    def print_doc(self, doc: str) -> str:
        # TODO: return f"Printing: {doc}"
        pass


class AllInOnePrinter:
    """Prints, scans, faxes, and staples.

    Should have:
    - print_doc(doc) -> str: return f"Printing: {doc}"
    - scan(doc) -> str: return f"Scanning: {doc}"
    - fax(doc, number) -> str: return f"Faxing '{doc}' to {number}"
    - staple(doc) -> str: return f"Stapling: {doc}"
    """

    def print_doc(self, doc: str) -> str:
        # TODO: return f"Printing: {doc}"
        pass

    def scan(self, doc: str) -> str:
        # TODO: return f"Scanning: {doc}"
        pass

    def fax(self, doc: str, number: str) -> str:
        # TODO: return f"Faxing '{doc}' to {number}"
        pass

    def staple(self, doc: str) -> str:
        # TODO: return f"Stapling: {doc}"
        pass


class OldFaxMachine:
    """Only faxes.

    Should have:
    - fax(doc, number) -> str: return f"Faxing '{doc}' to {number}"
    """

    def fax(self, doc: str, number: str) -> str:
        # TODO: return f"Faxing '{doc}' to {number}"
        pass


def print_report(printer: Printable, report: str) -> str:
    """Print a report using any Printable device."""
    # TODO: call printer.print_doc(report) and return the result
    pass


def scan_document(scanner: Scannable, doc: str) -> str:
    """Scan a document using any Scannable device."""
    # TODO: call scanner.scan(doc) and return the result
    pass


def send_fax(faxer: Faxable, doc: str, number: str) -> str:
    """Send a fax using any Faxable device."""
    # TODO: call faxer.fax(doc, number) and return the result
    pass


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: The Fat Interface Problem ---
    print("--- Section 1: The Fat Interface Problem ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: Split Into Role Protocols ---
    print("--- Section 2: Split Into Role Protocols ---")

    try:
        for proto_name, proto_cls in [("Workable", Workable), ("Feedable", Feedable), ("Sleepable", Sleepable)]:
            methods = [m for m in dir(proto_cls) if not m.startswith("_")]
            assert len(methods) == 1, f"{proto_name} should have 1 method, has {len(methods)}"

        print("  Workable, Feedable, Sleepable protocols defined.")
        print("  Each protocol has exactly ONE method -- no forced dependencies.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: Segregated Implementations ---
    print("--- Section 3: Segregated Implementations ---")

    try:
        human = Human("alice")
        robot = Robot("RX-78")

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

        assert isinstance(robot, Workable)
        assert not isinstance(robot, Feedable)
        assert not isinstance(robot, Sleepable)

        robot_capabilities = []
        if isinstance(robot, Workable):
            robot_capabilities.append("work")
        print(f"  Robot implements: {', '.join(robot_capabilities)} (only what it actually does)")

        print("  No NotImplementedError -- no lies in the API.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: Functions Depend on Narrow Protocols ---
    print("--- Section 4: Functions Depend on Narrow Protocols ---")

    try:
        human = Human("alice")
        robot = Robot("RX-78")

        print(f"  assign_task(human) = {assign_task(human)}")
        print(f"  assign_task(robot) = {assign_task(robot)}")
        assert assign_task(human) == "alice is writing code"
        assert assign_task(robot) == "RX-78 is assembling parts"

        print(f"  lunch_break(human) = {lunch_break(human)}")
        print(f"  night_rest(human) = {night_rest(human)}")
        assert lunch_break(human) == "alice is eating lunch"
        assert night_rest(human) == "alice is sleeping"

        assert not isinstance(robot, Feedable), "Robot should NOT be Feedable"
        assert not isinstance(robot, Sleepable), "Robot should NOT be Sleepable"
        print("  Robot correctly excluded from lunch_break and night_rest.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: Document Printer Example ---
    print("--- Section 5: Document Printer Example ---")

    try:
        simple = SimplePrinter()
        allinone = AllInOnePrinter()
        fax_machine = OldFaxMachine()

        print(f"  SimplePrinter.print_doc() = {simple.print_doc('Q4 Report')}")
        assert isinstance(simple, Printable)
        assert not isinstance(simple, Scannable)
        assert not isinstance(simple, Faxable)

        print(f"  AllInOnePrinter.print_doc() = {allinone.print_doc('Q4 Report')}")
        print(f"  AllInOnePrinter.scan() = {allinone.scan('Contract')}")
        print(f"  AllInOnePrinter.fax() = {allinone.fax('Invoice', '555-0123')}")
        print(f"  AllInOnePrinter.staple() = {allinone.staple('Packet')}")
        assert isinstance(allinone, Printable)
        assert isinstance(allinone, Scannable)
        assert isinstance(allinone, Faxable)
        assert isinstance(allinone, Stapleable)

        print(f"  OldFaxMachine.fax() = {fax_machine.fax('Invoice', '555-0123')}")
        assert isinstance(fax_machine, Faxable)
        assert not isinstance(fax_machine, Printable)

        assert print_report(simple, "Q4 Report") == "Printing: Q4 Report"
        assert print_report(allinone, "Q4 Report") == "Printing: Q4 Report"
        print("  print_report() works with both SimplePrinter and AllInOnePrinter.")

        assert send_fax(allinone, "Invoice", "555-0123") == "Faxing 'Invoice' to 555-0123"
        assert send_fax(fax_machine, "Invoice", "555-0123") == "Faxing 'Invoice' to 555-0123"
        print("  send_fax() works with both AllInOnePrinter and OldFaxMachine.")

        print("  Each function gets exactly the interface it needs.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: Protocol Composition ---
    print("--- Section 6: Protocol Composition ---")

    try:
        human = Human("alice")
        robot = Robot("RX-78")

        result = full_workday(human)
        print(f"  full_workday(human) = {result}")
        assert result == ["alice is writing code", "alice is eating lunch", "alice is writing code"]

        assert isinstance(human, Workable) and isinstance(human, Feedable)
        assert isinstance(robot, Workable) and not isinstance(robot, Feedable)
        print("  Composed WorkingEater protocol: only Human qualifies.")

        print("  Protocol composition lets you combine narrow interfaces on demand.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7: Detecting ISP Violations ---
    print("--- Section 7: Detecting ISP Violations ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

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

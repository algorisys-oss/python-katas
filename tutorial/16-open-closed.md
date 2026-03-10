# Kata 16 -- Open/Closed Principle

[prev: 15-single-responsibility](./15-single-responsibility.md) | [next: 17-liskov-substitution](./17-liskov-substitution.md)

---

## What We're Building

The **Open/Closed Principle** (OCP) is the second SOLID principle. It states: *software entities should be open for extension but closed for modification*. In practice, this means you should be able to add new behavior to a system without changing existing, tested code.

In this kata we'll start with a payment processor that uses an `if/elif` chain to handle different payment methods -- the classic OCP violation. Every time you add a new payment method, you must modify the processor. We'll refactor it using the **strategy pattern** with Python's `Protocol` to create a system where adding a new payment method requires zero changes to existing code. Then we'll build a **plugin architecture** that discovers and registers payment methods automatically.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Open/Closed Principle | Extend behavior without modifying existing code | Always -- prevents regressions when adding features |
| Strategy pattern | Encapsulate interchangeable algorithms behind a common interface | When you have multiple variants of the same operation |
| `Protocol` (structural typing) | Define interfaces without inheritance | When you want duck typing with type-checker support |
| Plugin architecture | Discover and register extensions at runtime | When the set of strategies is not known at compile time |
| Registry pattern | Central lookup for named strategies | When strategies need to be selected dynamically |

## The Code

### Step 1: The `if/elif` chain -- the OCP violation

Here's a payment processor that handles credit cards, PayPal, and bank transfers. It works, but every new payment method requires modifying the `process` method:

```python
from dataclasses import dataclass


@dataclass
class PaymentResult:
    success: bool
    transaction_id: str
    message: str


class PaymentProcessor:
    """Processes payments -- but violates OCP with if/elif chain."""

    def process(self, method: str, amount: float, details: dict) -> PaymentResult:
        if method == "credit_card":
            card = details["card_number"]
            masked = f"****{card[-4:]}"
            # Simulate credit card processing
            if amount > 10000:
                return PaymentResult(False, "", f"Credit card limit exceeded: ${amount:.2f}")
            txn_id = f"CC-{id(details) % 100000:05d}"
            return PaymentResult(True, txn_id, f"Charged ${amount:.2f} to card {masked}")

        elif method == "paypal":
            email = details["email"]
            # Simulate PayPal processing
            txn_id = f"PP-{id(details) % 100000:05d}"
            return PaymentResult(True, txn_id, f"Charged ${amount:.2f} to PayPal {email}")

        elif method == "bank_transfer":
            account = details["account_number"]
            routing = details["routing_number"]
            masked_acct = f"****{account[-4:]}"
            # Simulate bank transfer
            if amount < 100:
                return PaymentResult(False, "", f"Bank transfer minimum is $100 (got ${amount:.2f})")
            txn_id = f"BT-{id(details) % 100000:05d}"
            return PaymentResult(True, txn_id, f"Transferred ${amount:.2f} from account {masked_acct}")

        else:
            return PaymentResult(False, "", f"Unknown payment method: {method}")
```

### Step 2: Why this violates OCP

Every time you add a new payment method (crypto, Apple Pay, gift cards), you must:

1. **Open** the `PaymentProcessor` class
2. **Add** another `elif` branch
3. **Modify** the existing method (risk breaking tested code)
4. **Re-test** the entire method, not just the new branch

The processor is **closed for extension** (can't add methods without modifying it) and **open for modification** (the `process` method keeps growing). OCP says it should be the opposite.

### Step 3: Define the extension point with Protocol

Python's `Protocol` (from `typing`) defines a structural interface -- any class with a matching `pay` method satisfies it, no inheritance required:

```python
from typing import Protocol


class PaymentMethod(Protocol):
    """Extension point: any class with a pay() method satisfies this."""

    @property
    def name(self) -> str:
        """Unique identifier for this payment method."""
        ...

    def pay(self, amount: float, details: dict) -> PaymentResult:
        """Process a payment and return the result."""
        ...
```

This is the contract. Any class that has a `name` property and a `pay` method with this signature is a valid `PaymentMethod` -- even without explicitly inheriting from it. That's structural (duck) typing with type safety.

### Step 4: Implement strategies for each payment method

Each payment method is now its own class with focused, testable logic:

```python
class CreditCardPayment:
    """Strategy: credit card processing."""

    @property
    def name(self) -> str:
        return "credit_card"

    def pay(self, amount: float, details: dict) -> PaymentResult:
        card = details["card_number"]
        masked = f"****{card[-4:]}"
        if amount > 10000:
            return PaymentResult(False, "", f"Credit card limit exceeded: ${amount:.2f}")
        txn_id = f"CC-{id(details) % 100000:05d}"
        return PaymentResult(True, txn_id, f"Charged ${amount:.2f} to card {masked}")


class PayPalPayment:
    """Strategy: PayPal processing."""

    @property
    def name(self) -> str:
        return "paypal"

    def pay(self, amount: float, details: dict) -> PaymentResult:
        email = details["email"]
        txn_id = f"PP-{id(details) % 100000:05d}"
        return PaymentResult(True, txn_id, f"Charged ${amount:.2f} to PayPal {email}")


class BankTransferPayment:
    """Strategy: bank transfer processing."""

    @property
    def name(self) -> str:
        return "bank_transfer"

    def pay(self, amount: float, details: dict) -> PaymentResult:
        account = details["account_number"]
        masked_acct = f"****{account[-4:]}"
        if amount < 100:
            return PaymentResult(False, "", f"Bank transfer minimum is $100 (got ${amount:.2f})")
        txn_id = f"BT-{id(details) % 100000:05d}"
        return PaymentResult(True, txn_id, f"Transferred ${amount:.2f} from account {masked_acct}")
```

Each strategy class:
- Owns exactly **one** payment method's logic
- Can be tested in **complete isolation**
- Can be added or removed **without touching other code**

### Step 5: The refactored processor (closed for modification)

Now the processor uses a **registry** of payment methods. Adding a new method means registering a new strategy -- the processor itself never changes:

```python
class OpenPaymentProcessor:
    """Processes payments -- open for extension, closed for modification.

    Register new payment methods without changing this class.
    """

    def __init__(self):
        self._methods: dict[str, PaymentMethod] = {}
        self._log: list[dict] = []

    def register(self, method: PaymentMethod):
        """Register a payment method. This is the extension point."""
        self._methods[method.name] = method

    def process(self, method_name: str, amount: float, details: dict) -> PaymentResult:
        """Process a payment using the registered method."""
        method = self._methods.get(method_name)
        if not method:
            available = ", ".join(sorted(self._methods.keys())) or "none"
            return PaymentResult(
                False, "", f"Unknown payment method: {method_name} (available: {available})"
            )

        result = method.pay(amount, details)
        self._log.append({
            "method": method_name,
            "amount": amount,
            "success": result.success,
            "transaction_id": result.transaction_id,
        })
        return result

    @property
    def supported_methods(self) -> list[str]:
        """List all registered payment methods."""
        return sorted(self._methods.keys())

    @property
    def transaction_log(self) -> list[dict]:
        """Read-only access to the transaction log."""
        return list(self._log)
```

Notice what changed:
- **No `if/elif` chain** -- method dispatch uses the registry
- **Adding a payment method** = create a new class + call `register()` -- zero modification to existing code
- **The processor is closed** -- its `process()` method never needs to change
- **The processor is open** -- `register()` accepts any object satisfying `PaymentMethod`

### Step 6: Extending without modification

Here's the proof that OCP works. Let's add cryptocurrency payments. We write one new class and register it -- nothing else changes:

```python
class CryptoPayment:
    """New payment method -- added WITHOUT modifying PaymentProcessor."""

    @property
    def name(self) -> str:
        return "crypto"

    def pay(self, amount: float, details: dict) -> PaymentResult:
        wallet = details["wallet_address"]
        short_wallet = f"{wallet[:6]}...{wallet[-4:]}"
        currency = details.get("currency", "BTC")
        txn_id = f"CRYPTO-{id(details) % 100000:05d}"
        return PaymentResult(
            True, txn_id, f"Sent ${amount:.2f} in {currency} to {short_wallet}"
        )
```

That's it. One new file (or class), one `register()` call. The processor, credit card, PayPal, and bank transfer code are completely untouched. No risk of regression.

### Step 7: Plugin architecture with auto-discovery

For truly extensible systems, you can auto-discover and register all payment methods. This is the plugin pattern:

```python
def create_processor_with_plugins(payment_classes: list[type]) -> OpenPaymentProcessor:
    """Plugin architecture: auto-discover and register payment methods."""
    processor = OpenPaymentProcessor()
    for cls in payment_classes:
        instance = cls()
        processor.register(instance)
        print(f"  [PLUGIN] Registered payment method: {instance.name}")
    return processor
```

In production, `payment_classes` could come from scanning a directory, reading a config file, or using entry points. The processor doesn't care where strategies come from -- it just calls `pay()` on whatever is registered.

### Step 8: OCP with ABC (alternative approach)

If you prefer explicit inheritance over structural typing, you can use `ABC` instead of `Protocol`:

```python
from abc import ABC, abstractmethod


class PaymentMethodABC(ABC):
    """Extension point using abstract base class (nominal typing)."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def pay(self, amount: float, details: dict) -> PaymentResult: ...
```

**Protocol vs ABC:**

| Aspect | Protocol | ABC |
|---|---|---|
| Typing style | Structural (duck typing) | Nominal (explicit inheritance) |
| Requires inheritance | No | Yes |
| Runtime checking | No (static only) | Yes (`isinstance` works) |
| Best for | Loose coupling, third-party code | Internal hierarchies, enforcement |

Both achieve OCP. Protocol is more Pythonic for extension points; ABC is better when you need runtime type checking.

## Playground

Run the full before/after comparison:

```bash
python playground/16_open_closed.py
```

```
--- Section 1: The if/elif Chain (Before OCP) ---
  Processing credit_card: Charged $99.99 to card ****5678
  Processing paypal: Charged $49.99 to PayPal alice@example.com
  Processing bank_transfer: Transferred $500.00 from account ****9012
  Processing unknown: Unknown payment method: unknown
  if/elif processor works -- but adding methods means modifying the class.

--- Section 2: Why This Violates OCP ---
  Problems with the if/elif approach:
    1. Adding a method requires modifying PaymentProcessor.process()
    2. Every modification risks breaking existing payment methods
    3. The process() method grows unboundedly
    4. Can't add methods from external code (closed for extension)

--- Section 3: Define the Protocol ---
  PaymentMethod protocol defines the extension point:
    - name property: identifies the payment method
    - pay() method: processes the payment
  Any class with these members satisfies the protocol -- no inheritance needed.

--- Section 4: Strategy Classes ---
  CreditCardPayment: credit_card
  PayPalPayment: paypal
  BankTransferPayment: bank_transfer
  Each strategy is self-contained and independently testable.

--- Section 5: Refactored Processor ---
  Registered: bank_transfer, credit_card, paypal
  Processing credit_card: Charged $99.99 to card ****5678
  Processing paypal: Charged $49.99 to PayPal alice@example.com
  Processing bank_transfer: Transferred $500.00 from account ****9012
  Processing unknown: Unknown payment method: unknown (available: bank_transfer, credit_card, paypal)
  Same behavior -- but now the processor never needs modification!

--- Section 6: Extending Without Modification ---
  Before: ['bank_transfer', 'credit_card', 'paypal']
  After:  ['bank_transfer', 'credit_card', 'crypto', 'paypal']
  Processing crypto: Sent $250.00 in BTC to 0x1a2b...9z0y
  Added crypto WITHOUT modifying the processor or any existing payment class!

--- Section 7: Plugin Architecture ---
  [PLUGIN] Registered payment method: credit_card
  [PLUGIN] Registered payment method: paypal
  [PLUGIN] Registered payment method: bank_transfer
  [PLUGIN] Registered payment method: crypto
  Plugin processor supports: ['bank_transfer', 'credit_card', 'crypto', 'paypal']
  Auto-discovered and registered 4 payment methods.

--- Section 8: Testing Strategies in Isolation ---
  Credit card success test passed!
  Credit card limit test passed!
  PayPal test passed!
  Bank transfer success test passed!
  Bank transfer minimum test passed!
  Crypto test passed!
  Processor unknown method test passed!
  Transaction log test passed!

--- Summary ---
Open/Closed Principle:
  - Open for extension: add new behavior via new classes
  - Closed for modification: existing code never changes
  - Strategy pattern: encapsulate variants behind a common interface
  - Protocol: structural typing for extension points (no inheritance required)
  - Registry pattern: central lookup for named strategies
  - Plugin architecture: auto-discover and register strategies
  - OCP eliminates the if/elif anti-pattern

All 8 sections passed. You've mastered the Open/Closed Principle!
```

## How It Works

```
BEFORE (if/elif chain):              AFTER (Strategy + Registry):

+----------------------+             +---------------------+
| PaymentProcessor     |             | OpenPaymentProcessor|
|                      |             |                     |
| process(method):     |             | register(method)    |
|   if credit_card:    |             | process(name):      |
|     ...              |             |   method = lookup   |
|   elif paypal:       |             |   method.pay(...)   |
|     ...              |             +----------+----------+
|   elif bank:         |                        |
|     ...              |               registered methods
|   elif NEW:          |             +----------+----------+
|     ... MODIFY!      |             |          |          |
+----------------------+          +--+---+  +---+--+  +---+---+
                                  |Credit|  |PayPal|  | Bank  |
Adding a method = modify          | Card |  |      |  |Xfer   |
existing code                     +------+  +------+  +-------+
                                       +------+
                                       |Crypto|  <-- NEW: just register!
                                       +------+
```

The key insight: **the `if/elif` chain couples the processor to every payment method**. Adding one method means modifying the processor (risk). With the strategy pattern, the processor only knows about the `PaymentMethod` protocol. New payment methods are **separate classes** that get **registered** -- the processor code is frozen.

## Exercises

### Exercise 1: Add a gift card payment method

Create a `GiftCardPayment` strategy that:
- Has `name = "gift_card"`
- Requires `card_code` and `balance` in details
- Fails if the amount exceeds the balance
- Returns the remaining balance in the success message

```python
class GiftCardPayment:
    @property
    def name(self) -> str:
        return "gift_card"

    def pay(self, amount: float, details: dict) -> PaymentResult:
        # Check balance, deduct amount, report remaining
        ...
```

### Exercise 2: Build a discount decorator

Create a wrapper that applies a discount before delegating to the real payment method. This combines OCP with the decorator pattern:

```python
class DiscountedPayment:
    """Wraps any PaymentMethod and applies a discount."""

    def __init__(self, wrapped: PaymentMethod, discount_pct: float):
        self._wrapped = wrapped
        self._discount = discount_pct

    @property
    def name(self) -> str:
        return self._wrapped.name

    def pay(self, amount: float, details: dict) -> PaymentResult:
        discounted = amount * (1 - self._discount / 100)
        # Delegate to wrapped method with discounted amount
        ...
```

## What's Next

In [Kata 17 -- Liskov Substitution Principle](./17-liskov-substitution.md), we'll tackle the third SOLID principle: subtypes must be substitutable for their base types without altering the correctness of the program. You'll learn to recognize subtle LSP violations -- like a `Square` that inherits from `Rectangle` -- and build type hierarchies that actually work.

---

[prev: 15-single-responsibility](./15-single-responsibility.md) | [next: 17-liskov-substitution](./17-liskov-substitution.md)

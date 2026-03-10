"""
Kata 16 -- Open/Closed Principle
Run: python playground/16_open_closed.py

Start with a payment processor using an if/elif chain -- then refactor to the
strategy pattern with a PaymentMethod protocol. Adding new payment methods
requires zero modification to existing code.
"""

from dataclasses import dataclass
from typing import Protocol


# ===========================================================================
# SHARED DATA CLASS
# ===========================================================================

@dataclass
class PaymentResult:
    success: bool
    transaction_id: str
    message: str


# ===========================================================================
# BEFORE: THE if/elif CHAIN (violates OCP)
# ===========================================================================

class PaymentProcessor:
    """Processes payments -- but violates OCP with if/elif chain."""

    def process(self, method: str, amount: float, details: dict) -> PaymentResult:
        if method == "credit_card":
            card = details["card_number"]
            masked = f"****{card[-4:]}"
            if amount > 10000:
                return PaymentResult(False, "", f"Credit card limit exceeded: ${amount:.2f}")
            txn_id = f"CC-{id(details) % 100000:05d}"
            return PaymentResult(True, txn_id, f"Charged ${amount:.2f} to card {masked}")

        elif method == "paypal":
            email = details["email"]
            txn_id = f"PP-{id(details) % 100000:05d}"
            return PaymentResult(True, txn_id, f"Charged ${amount:.2f} to PayPal {email}")

        elif method == "bank_transfer":
            account = details["account_number"]
            masked_acct = f"****{account[-4:]}"
            if amount < 100:
                return PaymentResult(False, "", f"Bank transfer minimum is $100 (got ${amount:.2f})")
            txn_id = f"BT-{id(details) % 100000:05d}"
            return PaymentResult(True, txn_id, f"Transferred ${amount:.2f} from account {masked_acct}")

        else:
            return PaymentResult(False, "", f"Unknown payment method: {method}")


# ===========================================================================
# AFTER: STRATEGY PATTERN (satisfies OCP)
# ===========================================================================

class PaymentMethod(Protocol):
    """Extension point: any class with name + pay() satisfies this."""

    @property
    def name(self) -> str:
        """Unique identifier for this payment method."""
        ...

    def pay(self, amount: float, details: dict) -> PaymentResult:
        """Process a payment and return the result."""
        ...


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


class CryptoPayment:
    """New payment method -- added WITHOUT modifying the processor."""

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


def create_processor_with_plugins(payment_classes: list[type]) -> OpenPaymentProcessor:
    """Plugin architecture: auto-discover and register payment methods."""
    processor = OpenPaymentProcessor()
    for cls in payment_classes:
        instance = cls()
        processor.register(instance)
        print(f"  [PLUGIN] Registered payment method: {instance.name}")
    return processor


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: The if/elif Chain (Before OCP) ---
    print("--- Section 1: The if/elif Chain (Before OCP) ---")

    old_processor = PaymentProcessor()

    cc_details = {"card_number": "4111111111115678"}
    pp_details = {"email": "alice@example.com"}
    bt_details = {"account_number": "12345679012", "routing_number": "021000021"}

    r1 = old_processor.process("credit_card", 99.99, cc_details)
    print(f"  Processing credit_card: {r1.message}")
    assert r1.success is True
    assert "5678" in r1.message

    r2 = old_processor.process("paypal", 49.99, pp_details)
    print(f"  Processing paypal: {r2.message}")
    assert r2.success is True
    assert "alice@example.com" in r2.message

    r3 = old_processor.process("bank_transfer", 500.00, bt_details)
    print(f"  Processing bank_transfer: {r3.message}")
    assert r3.success is True
    assert "9012" in r3.message

    r4 = old_processor.process("unknown", 100.00, {})
    print(f"  Processing unknown: {r4.message}")
    assert r4.success is False

    print("  if/elif processor works -- but adding methods means modifying the class.")

    print()

    # --- Section 2: Why This Violates OCP ---
    print("--- Section 2: Why This Violates OCP ---")

    problems = [
        "Adding a method requires modifying PaymentProcessor.process()",
        "Every modification risks breaking existing payment methods",
        "The process() method grows unboundedly",
        "Can't add methods from external code (closed for extension)",
    ]

    print("  Problems with the if/elif approach:")
    for i, problem in enumerate(problems, 1):
        print(f"    {i}. {problem}")

    # Verify the old processor has no extension mechanism
    assert not hasattr(old_processor, "register"), "Old processor shouldn't have register()"

    print()

    # --- Section 3: Define the Protocol ---
    print("--- Section 3: Define the Protocol ---")

    print("  PaymentMethod protocol defines the extension point:")
    print("    - name property: identifies the payment method")
    print("    - pay() method: processes the payment")
    print("  Any class with these members satisfies the protocol -- no inheritance needed.")

    # Verify Protocol has the expected members
    assert hasattr(PaymentMethod, "name")
    assert hasattr(PaymentMethod, "pay")

    print()

    # --- Section 4: Strategy Classes ---
    print("--- Section 4: Strategy Classes ---")

    strategies = [CreditCardPayment(), PayPalPayment(), BankTransferPayment()]
    for s in strategies:
        print(f"  {type(s).__name__}: {s.name}")
        assert hasattr(s, "name")
        assert hasattr(s, "pay")

    print("  Each strategy is self-contained and independently testable.")

    print()

    # --- Section 5: Refactored Processor ---
    print("--- Section 5: Refactored Processor ---")

    processor = OpenPaymentProcessor()
    for s in strategies:
        processor.register(s)

    print(f"  Registered: {', '.join(processor.supported_methods)}")

    r1 = processor.process("credit_card", 99.99, cc_details)
    print(f"  Processing credit_card: {r1.message}")
    assert r1.success is True

    r2 = processor.process("paypal", 49.99, pp_details)
    print(f"  Processing paypal: {r2.message}")
    assert r2.success is True

    r3 = processor.process("bank_transfer", 500.00, bt_details)
    print(f"  Processing bank_transfer: {r3.message}")
    assert r3.success is True

    r4 = processor.process("unknown", 100.00, {})
    print(f"  Processing unknown: {r4.message}")
    assert r4.success is False
    assert "available:" in r4.message

    print("  Same behavior -- but now the processor never needs modification!")

    print()

    # --- Section 6: Extending Without Modification ---
    print("--- Section 6: Extending Without Modification ---")

    before = processor.supported_methods.copy()
    print(f"  Before: {before}")

    crypto = CryptoPayment()
    processor.register(crypto)

    after = processor.supported_methods
    print(f"  After:  {after}")

    assert "crypto" in after
    assert "crypto" not in before
    assert len(after) == len(before) + 1

    crypto_details = {"wallet_address": "0x1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9z0y", "currency": "BTC"}
    r5 = processor.process("crypto", 250.00, crypto_details)
    print(f"  Processing crypto: {r5.message}")
    assert r5.success is True
    assert "BTC" in r5.message

    print("  Added crypto WITHOUT modifying the processor or any existing payment class!")

    print()

    # --- Section 7: Plugin Architecture ---
    print("--- Section 7: Plugin Architecture ---")

    all_payment_classes = [CreditCardPayment, PayPalPayment, BankTransferPayment, CryptoPayment]
    plugin_processor = create_processor_with_plugins(all_payment_classes)

    print(f"  Plugin processor supports: {plugin_processor.supported_methods}")
    assert len(plugin_processor.supported_methods) == 4
    assert "credit_card" in plugin_processor.supported_methods
    assert "crypto" in plugin_processor.supported_methods

    print(f"  Auto-discovered and registered {len(all_payment_classes)} payment methods.")

    print()

    # --- Section 8: Testing Strategies in Isolation ---
    print("--- Section 8: Testing Strategies in Isolation ---")

    # Test credit card success
    cc = CreditCardPayment()
    r = cc.pay(50.00, {"card_number": "4111111111111234"})
    assert r.success is True
    assert "1234" in r.message
    print("  Credit card success test passed!")

    # Test credit card limit
    r = cc.pay(15000.00, {"card_number": "4111111111111234"})
    assert r.success is False
    assert "limit exceeded" in r.message
    print("  Credit card limit test passed!")

    # Test PayPal
    pp = PayPalPayment()
    r = pp.pay(25.00, {"email": "test@test.com"})
    assert r.success is True
    assert "test@test.com" in r.message
    print("  PayPal test passed!")

    # Test bank transfer success
    bt = BankTransferPayment()
    r = bt.pay(200.00, {"account_number": "98765432100", "routing_number": "021000021"})
    assert r.success is True
    assert "2100" in r.message
    print("  Bank transfer success test passed!")

    # Test bank transfer minimum
    r = bt.pay(50.00, {"account_number": "98765432100", "routing_number": "021000021"})
    assert r.success is False
    assert "minimum" in r.message
    print("  Bank transfer minimum test passed!")

    # Test crypto
    cr = CryptoPayment()
    r = cr.pay(100.00, {"wallet_address": "0xabcdef1234567890abcdef1234567890", "currency": "ETH"})
    assert r.success is True
    assert "ETH" in r.message
    print("  Crypto test passed!")

    # Test processor with unknown method
    test_proc = OpenPaymentProcessor()
    r = test_proc.process("nonexistent", 100.00, {})
    assert r.success is False
    assert "Unknown" in r.message
    print("  Processor unknown method test passed!")

    # Test transaction log
    log_proc = OpenPaymentProcessor()
    log_proc.register(CreditCardPayment())
    log_proc.process("credit_card", 42.00, {"card_number": "4111111111119999"})
    log_proc.process("credit_card", 18.50, {"card_number": "4111111111119999"})
    assert len(log_proc.transaction_log) == 2
    assert log_proc.transaction_log[0]["amount"] == 42.00
    assert log_proc.transaction_log[1]["amount"] == 18.50
    assert log_proc.transaction_log[0]["success"] is True
    print("  Transaction log test passed!")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Open/Closed Principle:")
    print("  - Open for extension: add new behavior via new classes")
    print("  - Closed for modification: existing code never changes")
    print("  - Strategy pattern: encapsulate variants behind a common interface")
    print("  - Protocol: structural typing for extension points (no inheritance required)")
    print("  - Registry pattern: central lookup for named strategies")
    print("  - Plugin architecture: auto-discover and register strategies")
    print("  - OCP eliminates the if/elif anti-pattern")
    print()
    print("All 8 sections passed. You've mastered the Open/Closed Principle!")

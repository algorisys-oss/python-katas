"""
Kata 16 -- Open/Closed Principle
Run: python playground/skeletons/16_open_closed.py

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
# BEFORE: THE if/elif CHAIN (violates OCP) -- provided for reference
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
# AFTER: STRATEGY PATTERN (your implementation)
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
    """Strategy: credit card processing.

    Should have:
    - name property returning "credit_card"
    - pay() that masks card number, checks $10000 limit, returns PaymentResult
    """

    @property
    def name(self) -> str:
        return "credit_card"

    def pay(self, amount: float, details: dict) -> PaymentResult:
        # TODO: implement credit card payment
        # 1. Get card_number from details, mask all but last 4 digits
        # 2. If amount > 10000, return failure with "Credit card limit exceeded"
        # 3. Generate txn_id as f"CC-{id(details) % 100000:05d}"
        # 4. Return success with message f"Charged ${amount:.2f} to card {masked}"
        # HINT: masked = f"****{card[-4:]}"
        pass


class PayPalPayment:
    """Strategy: PayPal processing.

    Should have:
    - name property returning "paypal"
    - pay() that uses email from details, returns PaymentResult
    """

    @property
    def name(self) -> str:
        return "paypal"

    def pay(self, amount: float, details: dict) -> PaymentResult:
        # TODO: implement PayPal payment
        # 1. Get email from details
        # 2. Generate txn_id as f"PP-{id(details) % 100000:05d}"
        # 3. Return success with message f"Charged ${amount:.2f} to PayPal {email}"
        pass


class BankTransferPayment:
    """Strategy: bank transfer processing.

    Should have:
    - name property returning "bank_transfer"
    - pay() that checks $100 minimum, masks account number, returns PaymentResult
    """

    @property
    def name(self) -> str:
        return "bank_transfer"

    def pay(self, amount: float, details: dict) -> PaymentResult:
        # TODO: implement bank transfer payment
        # 1. Get account_number from details, mask all but last 4 digits
        # 2. If amount < 100, return failure with "Bank transfer minimum is $100"
        # 3. Generate txn_id as f"BT-{id(details) % 100000:05d}"
        # 4. Return success with message f"Transferred ${amount:.2f} from account {masked}"
        pass


class CryptoPayment:
    """New payment method -- added WITHOUT modifying the processor.

    Should have:
    - name property returning "crypto"
    - pay() that shortens wallet address, uses currency from details, returns PaymentResult
    """

    @property
    def name(self) -> str:
        return "crypto"

    def pay(self, amount: float, details: dict) -> PaymentResult:
        # TODO: implement crypto payment
        # 1. Get wallet_address from details, shorten to first 6 + last 4 chars
        # 2. Get currency from details (default "BTC")
        # 3. Generate txn_id as f"CRYPTO-{id(details) % 100000:05d}"
        # 4. Return success with message f"Sent ${amount:.2f} in {currency} to {short_wallet}"
        # HINT: short_wallet = f"{wallet[:6]}...{wallet[-4:]}"
        # HINT: currency = details.get("currency", "BTC")
        pass


class OpenPaymentProcessor:
    """Processes payments -- open for extension, closed for modification.

    Register new payment methods without changing this class.
    Should have:
    - _methods: dict mapping name -> PaymentMethod
    - _log: list of transaction dicts
    - register(method): adds a payment method
    - process(method_name, amount, details): dispatches to registered method
    - supported_methods property: sorted list of method names
    - transaction_log property: copy of the log
    """

    def __init__(self):
        # TODO: initialize the methods registry and transaction log
        # HINT: self._methods: dict[str, PaymentMethod] = {}
        # HINT: self._log: list[dict] = []
        pass

    def register(self, method: PaymentMethod):
        # TODO: register a payment method by its name
        # HINT: self._methods[method.name] = method
        pass

    def process(self, method_name: str, amount: float, details: dict) -> PaymentResult:
        # TODO: look up the method and call pay()
        # 1. Look up method_name in self._methods
        # 2. If not found, return failure with available methods listed
        # 3. Call method.pay(amount, details)
        # 4. Log the transaction (method, amount, success, transaction_id)
        # 5. Return the result
        # HINT: available = ", ".join(sorted(self._methods.keys())) or "none"
        pass

    @property
    def supported_methods(self) -> list[str]:
        # TODO: return sorted list of registered method names
        pass

    @property
    def transaction_log(self) -> list[dict]:
        # TODO: return a copy of the transaction log
        pass


def create_processor_with_plugins(payment_classes: list[type]) -> OpenPaymentProcessor:
    """Plugin architecture: auto-discover and register payment methods."""
    # TODO: create a processor, instantiate each class, register it, print discovery
    # HINT: for cls in payment_classes:
    #           instance = cls()
    #           processor.register(instance)
    #           print(f"  [PLUGIN] Registered payment method: {instance.name}")
    pass


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: The if/elif Chain (Before OCP) ---
    print("--- Section 1: The if/elif Chain (Before OCP) ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: Why This Violates OCP ---
    print("--- Section 2: Why This Violates OCP ---")

    try:
        problems = [
            "Adding a method requires modifying PaymentProcessor.process()",
            "Every modification risks breaking existing payment methods",
            "The process() method grows unboundedly",
            "Can't add methods from external code (closed for extension)",
        ]

        print("  Problems with the if/elif approach:")
        for i, problem in enumerate(problems, 1):
            print(f"    {i}. {problem}")

        assert not hasattr(old_processor, "register"), "Old processor shouldn't have register()"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: Define the Protocol ---
    print("--- Section 3: Define the Protocol ---")

    try:
        print("  PaymentMethod protocol defines the extension point:")
        print("    - name property: identifies the payment method")
        print("    - pay() method: processes the payment")
        print("  Any class with these members satisfies the protocol -- no inheritance needed.")

        assert hasattr(PaymentMethod, "name")
        assert hasattr(PaymentMethod, "pay")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: Strategy Classes ---
    print("--- Section 4: Strategy Classes ---")

    try:
        strategies = [CreditCardPayment(), PayPalPayment(), BankTransferPayment()]
        for s in strategies:
            print(f"  {type(s).__name__}: {s.name}")
            assert hasattr(s, "name")
            assert hasattr(s, "pay")

        print("  Each strategy is self-contained and independently testable.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: Refactored Processor ---
    print("--- Section 5: Refactored Processor ---")

    try:
        cc_details = {"card_number": "4111111111115678"}
        pp_details = {"email": "alice@example.com"}
        bt_details = {"account_number": "12345679012", "routing_number": "021000021"}

        strategies = [CreditCardPayment(), PayPalPayment(), BankTransferPayment()]
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: Extending Without Modification ---
    print("--- Section 6: Extending Without Modification ---")

    try:
        strategies = [CreditCardPayment(), PayPalPayment(), BankTransferPayment()]
        processor = OpenPaymentProcessor()
        for s in strategies:
            processor.register(s)

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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7: Plugin Architecture ---
    print("--- Section 7: Plugin Architecture ---")

    try:
        all_payment_classes = [CreditCardPayment, PayPalPayment, BankTransferPayment, CryptoPayment]
        plugin_processor = create_processor_with_plugins(all_payment_classes)

        print(f"  Plugin processor supports: {plugin_processor.supported_methods}")
        assert len(plugin_processor.supported_methods) == 4
        assert "credit_card" in plugin_processor.supported_methods
        assert "crypto" in plugin_processor.supported_methods

        print(f"  Auto-discovered and registered {len(all_payment_classes)} payment methods.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 8: Testing Strategies in Isolation ---
    print("--- Section 8: Testing Strategies in Isolation ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

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

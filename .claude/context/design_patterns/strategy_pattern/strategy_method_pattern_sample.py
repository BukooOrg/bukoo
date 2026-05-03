from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

# custom type
# Avoids importing real libraries. Used for illustration purposes.

type Date = str
# Replaces datetime.date — represents card expiry date (e.g., "2027-08-01").


# Data class — PaymentResult
# Standardised output produced by every concrete strategy.
# PaymentService and the route layer only ever see this object.
@dataclass
class PaymentResult:
    success: bool
    payment_method: str
    simulated_ref: str


# Abstract strategy — PaymentStrategy
# Defines the interface all concrete strategies must honour.
# PaymentService depends only on this abstraction — never on
# OnlineBankingPaymentStrategy or CardPaymentStrategy directly.
class PaymentStrategy(ABC):
    # Protected attribute: subclasses set this to identify their method name.
    _method_name: str = ""

    def get_method_name(self) -> str:
        return self._method_name

    @abstractmethod
    def processPayment(self, order_id: str, amount: float) -> PaymentResult:
        """
        Each concrete strategy implements its own payment algorithm here.
        Despite different internals, every implementation returns PaymentResult,
        so PaymentService never needs to know which strategy is active.
        """
        pass


# Concrete strategy 1: OnlineBankingPaymentStrategy
class OnlineBankingPaymentStrategy(PaymentStrategy):
    """
    Concrete strategy for online banking payments.
    Simulates a bank transfer using bank name and account number.
    """

    def __init__(self, bank_name: str, account_number: str) -> None:
        self._method_name = "online_banking"
        self._bank_name = bank_name
        self._account_number = account_number
        print(
            f"[OnlineBankingPaymentStrategy] Instantiated — bank: {bank_name}, account: {account_number}"
        )

    def processPayment(self, order_id: str, amount: float) -> PaymentResult:
        print("[OnlineBankingPaymentStrategy] Processing bank transfer...")
        print(f"[OnlineBankingPaymentStrategy] order_id={order_id}, amount={amount}")

        # stub: simulate bank transfer against banking network
        # response = banking_client.transfer(
        #     bank_name=self._bank_name,
        #     account_number=self._account_number,
        #     amount=amount,
        # )
        simulated_ref = f"BANK-TXN-{order_id[:8].upper()}"  # stub: mock transaction ID
        success = True  # stub: assume transfer success

        print(f"[OnlineBankingPaymentStrategy] Transfer complete. ref={simulated_ref}")
        return PaymentResult(
            success=success,
            payment_method=self._method_name,
            simulated_ref=simulated_ref,
        )


# Concrete strategy 2: CardPaymentStrategy
class CardPaymentStrategy(PaymentStrategy):
    """
    Concrete strategy for card payments.
    Simulates a card authorisation using card number, expiry date, and CVV.
    """

    def __init__(self, card_number: str, expiry_date: Date, cvv: int) -> None:
        self._method_name = "card"
        self._card_number = card_number
        self._expiry_date = expiry_date
        self._cvv = cvv
        print(
            f"[CardPaymentStrategy] Instantiated — card: ****{card_number[-4:]}, expiry: {expiry_date}"
        )

    def processPayment(self, order_id: str, amount: float) -> PaymentResult:
        print("[CardPaymentStrategy] Processing card authorisation...")
        print(f"[CardPaymentStrategy] order_id={order_id}, amount={amount}")

        # stub: simulate card authorisation against card network
        # response = card_client.authorise(
        #     card_number=self._card_number,
        #     expiry_date=self._expiry_date,
        #     cvv=self._cvv,
        #     amount=amount,
        # )
        simulated_ref = (
            f"CARD-AUTH-{order_id[:8].upper()}"  # stub: mock authorisation code
        )
        success = True  # stub: assume authorisation success

        print(f"[CardPaymentStrategy] Authorisation complete. ref={simulated_ref}")
        return PaymentResult(
            success=success,
            payment_method=self._method_name,
            simulated_ref=simulated_ref,
        )


# Context — PaymentService
# Holds a reference to the active PaymentStrategy.
# Delegates payment execution entirely to the strategy — it never
# contains any payment algorithm itself.
class PaymentService:
    """
    Context class in the Strategy Pattern.

    - Holds a reference to a PaymentStrategy (abstract type).
    - set_strategy() allows the active strategy to be swapped at runtime,
      triggered by the payment_method field in the incoming request payload.
    - execute_payment() delegates entirely to self._strategy.processPayment()
      without branching on payment type — the strategy handles all differences.
    """

    def __init__(self, strategy: PaymentStrategy) -> None:
        # PaymentService holds the abstract type — never a concrete strategy.
        self._strategy = strategy
        print(
            f"[PaymentService] Initialised with strategy: {strategy.get_method_name()}"
        )

    def set_strategy(self, strategy: PaymentStrategy) -> None:
        # Runtime swap: replaces the active strategy based on the incoming
        # payment_method field. No conditional logic needed here or in execute_payment().
        print(
            f"[PaymentService.set_strategy] Swapping strategy to: {strategy.get_method_name()}"
        )
        self._strategy = strategy

    def execute_payment(self, order_id: str, amount: float) -> PaymentResult:
        print(
            f"[PaymentService.execute_payment] Delegating to active strategy: {self._strategy.get_method_name()}"
        )
        # Delegation: PaymentService has no knowledge of how payment is processed.
        # The active strategy encapsulates the full algorithm.
        return self._strategy.processPayment(order_id, amount)


# route layer — Simulated checkout route handler
# Reads payment_method from payload, swaps strategy at runtime,
# then triggers payment execution via PaymentService.
def simulate_checkout(payload: dict[str, Any]) -> None:
    """
    Simulates POST /checkout.

    Route reads payment_method from payload → instantiates the correct
    concrete strategy → calls set_strategy() to swap it at runtime →
    calls execute_payment() to process the payment.
    """
    order_id = payload["order_id"]
    amount: float = payload["amount"]
    payment_method: str = payload["payment_method"]

    print(f"[CheckoutRoute] Received payment_method: '{payment_method}'")
    print(f"[CheckoutRoute] order_id={order_id}, amount={amount}")

    # Strategy selection: the only branching logic in the route.
    # Once set_strategy() is called, PaymentService is fully decoupled
    # from the concrete type — execute_payment() works identically for both.
    if payment_method == "online_banking":
        strategy: PaymentStrategy = OnlineBankingPaymentStrategy(
            bank_name=payload["bank_name"],
            account_number=payload["account_number"],
        )
    elif payment_method == "card":
        strategy: PaymentStrategy = CardPaymentStrategy(
            card_number=payload["card_number"],
            expiry_date=payload["expiry_date"],
            cvv=payload["cvv"],
        )
    else:
        print(f"[CheckoutRoute] Unsupported payment method: '{payment_method}'")
        return

    # Runtime strategy swap — PaymentService now holds the selected strategy.
    payment_service.set_strategy(strategy)

    # Execute payment — PaymentService delegates to the active strategy.
    result = payment_service.execute_payment(order_id, amount)

    # Dispatch response
    if result.success:
        print(f"[CheckoutRoute] 200 OK — Payment confirmed. ref={result.simulated_ref}")
    else:
        print("[CheckoutRoute] 402 Payment Required — Payment failed.")


# Entry point
# Simulates two checkout requests with different payment methods,
# demonstrating runtime strategy swapping on the same PaymentService instance.
if __name__ == "__main__":
    # PaymentService is initialised with a default no-op or initial strategy.
    # In production, this would be injected via FastAPI dependency injection.
    initial_strategy = OnlineBankingPaymentStrategy(bank_name="", account_number="")
    payment_service = PaymentService(strategy=initial_strategy)

    # Scenario 1: Online Banking
    print("\n" + "=" * 60)
    print("SCENARIO 1: POST /checkout  (Online Banking)")
    print("=" * 60)
    simulate_checkout(
        {
            "order_id": "order-uuid-001",
            "amount": 169.80,
            "payment_method": "online_banking",
            "bank_name": "Maybank",
            "account_number": "1234567890",
        }
    )

    # Scenario 2: Card Payment (strategy swapped at runtime)
    print("\n" + "=" * 60)
    print("SCENARIO 2: POST /checkout  (Card Payment — strategy swapped)")
    print("=" * 60)
    simulate_checkout(
        {
            "order_id": "order-uuid-002",
            "amount": 89.90,
            "payment_method": "card",
            "card_number": "4111111111111111",
            "expiry_date": "2027-08-01",
            "cvv": 123,
        }
    )

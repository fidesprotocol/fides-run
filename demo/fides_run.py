#!/usr/bin/env python3
"""
Fides Protocol - Reference Implementation Demo

Demonstrates the core principle: No record, no payment.

Expected output:
    [1] Creating Decision Record... OK
    [2] Attempting authorized payment... AUTHORIZED
    [3] Attempting payment exceeding limit... BLOCKED
    [4] Attempting payment after revocation... BLOCKED

    Fides: No record, no payment.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ledger import FidesLedger
from src.records import create_decision_record, create_revocation_record
from src.verify import Payment, is_payment_authorized


def main():
    # Create an in-memory ledger for the demo
    ledger = FidesLedger(":memory:")

    print()

    # =========================================================================
    # [1] Create a Decision Record
    # =========================================================================
    print("[1] Creating Decision Record... ", end="")

    dr = create_decision_record(
        ledger=ledger,
        authority_id="GOV-DEMO-001",
        deciders_id=["DECIDER-001", "DECIDER-002"],
        act_type="contract",
        currency="BRL",
        maximum_value="100000.00",
        beneficiary="SUPPLIER-ABC-123",
        legal_basis="Lei 14.133/2021 Art. 75",
        decision_date="2024-01-15T10:00:00Z",
        signatures=["SIG-001", "SIG-002"],
        record_timestamp="2024-01-15T10:30:00Z"
    )

    decision_id = dr['decision_id']
    print("OK")

    # =========================================================================
    # [2] Attempt an authorized payment (within limits)
    # =========================================================================
    print("[2] Attempting authorized payment... ", end="")

    payment1 = Payment(
        decision_id=decision_id,
        beneficiary="SUPPLIER-ABC-123",
        currency="BRL",
        value="50000.00",
        payment_date="2024-02-01T14:00:00Z"
    )

    # Execution layer: no authorization logic here, only verification
    if is_payment_authorized(ledger, payment1):
        print("AUTHORIZED")
        # Record the payment as executed
        ledger.record_payment(
            payment_id="PAY-001",
            decision_id=decision_id,
            beneficiary=payment1.beneficiary,
            currency=payment1.currency,
            value=payment1.value,
            payment_date=payment1.payment_date
        )
    else:
        print("BLOCKED")

    # =========================================================================
    # [3] Attempt payment exceeding the limit
    # =========================================================================
    print("[3] Attempting payment exceeding limit... ", end="")

    payment2 = Payment(
        decision_id=decision_id,
        beneficiary="SUPPLIER-ABC-123",
        currency="BRL",
        value="60000.00",  # Would exceed 100000 (50000 already paid)
        payment_date="2024-02-15T14:00:00Z"
    )

    if is_payment_authorized(ledger, payment2):
        print("AUTHORIZED")
    else:
        print("BLOCKED")

    # =========================================================================
    # [4] Revoke the decision and attempt another payment
    # =========================================================================

    # First, create the revocation record
    create_revocation_record(
        ledger=ledger,
        target_decision_id=decision_id,
        authority_id="GOV-DEMO-001",
        deciders_id=["DECIDER-001", "DECIDER-002"],
        revocation_reason="Contract cancelled by mutual agreement",
        signatures=["SIG-001", "SIG-002"],
        record_timestamp="2024-03-01T09:00:00Z"
    )

    print("[4] Attempting payment after revocation... ", end="")

    payment3 = Payment(
        decision_id=decision_id,
        beneficiary="SUPPLIER-ABC-123",
        currency="BRL",
        value="10000.00",  # Within limit, but decision is revoked
        payment_date="2024-03-05T14:00:00Z"
    )

    if is_payment_authorized(ledger, payment3):
        print("AUTHORIZED")
    else:
        print("BLOCKED")

    # =========================================================================
    # Footer
    # =========================================================================
    print()
    print("Fides: No record, no payment.")
    print()

    # Verify chain integrity
    valid, invalid_idx = ledger.verify_chain_integrity()
    if valid:
        print(f"Chain integrity: VALID ({len(ledger.get_all_records())} records)")
    else:
        print(f"Chain integrity: BROKEN at index {invalid_idx}")

    ledger.close()


if __name__ == "__main__":
    main()

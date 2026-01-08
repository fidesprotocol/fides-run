"""
Fides Protocol - Reference Implementation

A minimal implementation demonstrating the Fides Protocol.
No record, no payment.
"""

from .hash_chain import (
    canonical_json,
    genesis_hash,
    record_hash,
    compute_previous_hash,
    verify_chain_link,
    verify_genesis,
)
from .ledger import FidesLedger
from .records import (
    create_decision_record,
    create_revocation_record,
    validate_dr,
    validate_rr,
)
from .verify import (
    Payment,
    is_payment_authorized,
    is_payment_authorized_with_reason,
)

__version__ = "0.1.0"

__all__ = [
    # Hash chain
    "canonical_json",
    "genesis_hash",
    "record_hash",
    "compute_previous_hash",
    "verify_chain_link",
    "verify_genesis",
    # Ledger
    "FidesLedger",
    # Records
    "create_decision_record",
    "create_revocation_record",
    "validate_dr",
    "validate_rr",
    # Verify
    "Payment",
    "is_payment_authorized",
    "is_payment_authorized_with_reason",
]

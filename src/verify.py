"""
Fides Protocol - Verification Module

Core function: is_payment_authorized()

Binary. No exceptions. True or False.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from .ledger import FidesLedger
from .records import is_iso8601, parse_date, validate_dr


@dataclass
class Payment:
    """
    Represents a payment to be verified.

    Attributes:
        decision_id: The UUID of the authorizing decision
        beneficiary: Tax ID or entity identifier
        currency: ISO 4217 currency code
        value: Payment amount (decimal string)
        payment_date: Date of payment (ISO 8601)
    """
    decision_id: str
    beneficiary: str
    currency: str
    value: str
    payment_date: str


def is_payment_authorized(ledger: FidesLedger, payment: Payment) -> bool:
    """
    Verify if a payment is authorized.

    Returns True if payment is authorized, False otherwise.
    No exceptions. No partial results. Binary only.

    This is the core function of the Fides Protocol.

    Args:
        ledger: The FidesLedger containing records
        payment: The payment to verify

    Returns:
        True if authorized, False otherwise
    """
    # Step 1: Find the decision record
    dr = ledger.find_decision_record(payment.decision_id)

    if dr is None:
        return False  # No record found

    # Step 2: Check if revoked
    if ledger.is_revoked(payment.decision_id):
        return False  # Decision was revoked

    # Step 3: Validate record structure
    valid, _ = validate_dr(dr)
    if not valid:
        return False  # Record is invalid

    # Step 4: Check temporal order (payment must be after decision)
    if not is_iso8601(payment.payment_date):
        return False  # Invalid payment date

    if not is_iso8601(dr.get('decision_date', '')):
        return False  # Invalid decision date

    payment_dt = parse_date(payment.payment_date)
    decision_dt = parse_date(dr['decision_date'])

    if payment_dt < decision_dt:
        return False  # Payment before decision

    # Step 5: Check beneficiary match
    if payment.beneficiary != dr.get('beneficiary'):
        return False  # Wrong beneficiary

    # Step 6: Check currency match
    if payment.currency != dr.get('currency'):
        return False  # Wrong currency

    # Step 7: Check value limit
    try:
        payment_value = Decimal(payment.value)
        maximum_value = Decimal(str(dr.get('maximum_value', '0')))
    except (InvalidOperation, TypeError, ValueError):
        return False  # Invalid numeric values

    if payment_value <= 0:
        return False  # Invalid payment value

    total_paid = Decimal(ledger.sum_payments(payment.decision_id))

    if (total_paid + payment_value) > maximum_value:
        return False  # Would exceed limit

    # Step 8: Check expiration (for SDR only)
    if dr.get('record_type') == 'SDR':
        maximum_term = dr.get('maximum_term')
        if maximum_term and is_iso8601(maximum_term):
            if payment_dt > parse_date(maximum_term):
                return False  # Exception expired

    # All checks passed
    return True


def is_payment_authorized_with_reason(
    ledger: FidesLedger,
    payment: Payment
) -> tuple[bool, str]:
    """
    Same as is_payment_authorized but returns reason for rejection.

    FOR DEBUGGING/AUDIT ONLY. Production should use binary version.

    Security warning: Do not expose rejection reasons to payment operators
    or deciders in production, as this could enable adversarial probing.

    Args:
        ledger: The FidesLedger containing records
        payment: The payment to verify

    Returns:
        Tuple of (authorized, reason_code)
    """
    # Step 1: Find the decision record
    dr = ledger.find_decision_record(payment.decision_id)

    if dr is None:
        return (False, "RECORD_NOT_FOUND")

    # Step 2: Check if revoked
    if ledger.is_revoked(payment.decision_id):
        return (False, "DECISION_REVOKED")

    # Step 3: Validate record structure
    valid, errors = validate_dr(dr)
    if not valid:
        return (False, f"INVALID_RECORD: {errors}")

    # Step 4: Check temporal order
    if not is_iso8601(payment.payment_date):
        return (False, "INVALID_PAYMENT_DATE")

    if not is_iso8601(dr.get('decision_date', '')):
        return (False, "INVALID_DECISION_DATE")

    payment_dt = parse_date(payment.payment_date)
    decision_dt = parse_date(dr['decision_date'])

    if payment_dt < decision_dt:
        return (False, "PAYMENT_BEFORE_DECISION")

    # Step 5: Check beneficiary match
    if payment.beneficiary != dr.get('beneficiary'):
        return (False, "BENEFICIARY_MISMATCH")

    # Step 6: Check currency match
    if payment.currency != dr.get('currency'):
        return (False, "CURRENCY_MISMATCH")

    # Step 7: Check value limit
    try:
        payment_value = Decimal(payment.value)
        maximum_value = Decimal(str(dr.get('maximum_value', '0')))
    except (InvalidOperation, TypeError, ValueError):
        return (False, "INVALID_NUMERIC_VALUE")

    if payment_value <= 0:
        return (False, "INVALID_PAYMENT_VALUE")

    total_paid = Decimal(ledger.sum_payments(payment.decision_id))

    if (total_paid + payment_value) > maximum_value:
        return (False, "EXCEEDS_MAXIMUM_VALUE")

    # Step 8: Check expiration (for SDR only)
    if dr.get('record_type') == 'SDR':
        maximum_term = dr.get('maximum_term')
        if maximum_term and is_iso8601(maximum_term):
            if payment_dt > parse_date(maximum_term):
                return (False, "EXCEPTION_EXPIRED")

    return (True, "AUTHORIZED")

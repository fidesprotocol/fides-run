"""
Fides Protocol - Records Module

Functions to create Decision Records (DR) and Revocation Records (RR).
"""

import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from .hash_chain import compute_previous_hash
from .ledger import FidesLedger


def is_uuid_v4(value: str) -> bool:
    """Check if value is valid UUID v4."""
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    return bool(re.match(pattern, str(value).lower()))


def is_iso8601(value: str) -> bool:
    """Check if value is valid ISO 8601 datetime."""
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError):
        return False


def parse_date(value: str) -> datetime:
    """Parse ISO 8601 string to datetime."""
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def is_positive_decimal(value: Any) -> bool:
    """Check if value is a positive decimal."""
    try:
        d = Decimal(str(value))
        return d > 0
    except (InvalidOperation, TypeError, ValueError):
        return False


def generate_uuid() -> str:
    """Generate a new UUID v4."""
    return str(uuid.uuid4())


def current_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def validate_dr(dr: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate Decision Record structure and content.

    Args:
        dr: The Decision Record to validate

    Returns:
        Tuple of (valid, list of errors)
    """
    errors = []

    required = [
        'decision_id', 'authority_id', 'deciders_id', 'act_type',
        'currency', 'maximum_value', 'beneficiary', 'legal_basis',
        'decision_date', 'previous_record_hash', 'record_timestamp',
        'signatures'
    ]

    for field in required:
        if field not in dr or dr[field] is None:
            errors.append(f"MISSING_{field.upper()}")

    if errors:
        return (False, errors)

    if not is_uuid_v4(dr['decision_id']):
        errors.append("INVALID_DECISION_ID")

    if not isinstance(dr['deciders_id'], list) or len(dr['deciders_id']) == 0:
        errors.append("INVALID_DECIDERS_ID")

    if not isinstance(dr['act_type'], str) or len(dr['act_type']) == 0:
        errors.append("INVALID_ACT_TYPE")

    if not is_positive_decimal(dr['maximum_value']):
        errors.append("INVALID_MAXIMUM_VALUE")

    if not is_iso8601(dr['decision_date']):
        errors.append("INVALID_DECISION_DATE")

    if not is_iso8601(dr['record_timestamp']):
        errors.append("INVALID_RECORD_TIMESTAMP")

    # Temporal constraint: decision_date <= record_timestamp
    if is_iso8601(dr['decision_date']) and is_iso8601(dr['record_timestamp']):
        if parse_date(dr['decision_date']) > parse_date(dr['record_timestamp']):
            errors.append("DECISION_DATE_AFTER_RECORD_TIMESTAMP")

    if not isinstance(dr['signatures'], list) or len(dr['signatures']) == 0:
        errors.append("INVALID_SIGNATURES")

    # Binding rule: deciders_id count must match signatures count
    if (isinstance(dr.get('deciders_id'), list) and
        isinstance(dr.get('signatures'), list)):
        if len(dr['deciders_id']) != len(dr['signatures']):
            errors.append("DECIDERS_SIGNATURES_MISMATCH")

    return (len(errors) == 0, errors)


def validate_rr(rr: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate Revocation Record structure.

    Args:
        rr: The Revocation Record to validate

    Returns:
        Tuple of (valid, list of errors)
    """
    errors = []

    required = [
        'revocation_id', 'target_decision_id', 'authority_id',
        'deciders_id', 'revocation_reason', 'revocation_date',
        'previous_record_hash', 'record_timestamp', 'signatures'
    ]

    for field in required:
        if field not in rr or rr[field] is None:
            errors.append(f"MISSING_{field.upper()}")

    if errors:
        return (False, errors)

    if not is_uuid_v4(rr['revocation_id']):
        errors.append("INVALID_REVOCATION_ID")

    if not is_uuid_v4(rr['target_decision_id']):
        errors.append("INVALID_TARGET_DECISION_ID")

    if not isinstance(rr['deciders_id'], list) or len(rr['deciders_id']) == 0:
        errors.append("INVALID_DECIDERS_ID")

    if not is_iso8601(rr['revocation_date']):
        errors.append("INVALID_REVOCATION_DATE")

    if not is_iso8601(rr['record_timestamp']):
        errors.append("INVALID_RECORD_TIMESTAMP")

    if not isinstance(rr['signatures'], list) or len(rr['signatures']) == 0:
        errors.append("INVALID_SIGNATURES")

    return (len(errors) == 0, errors)


def create_decision_record(
    ledger: FidesLedger,
    authority_id: str,
    deciders_id: List[str],
    act_type: str,
    currency: str,
    maximum_value: str,
    beneficiary: str,
    legal_basis: str,
    decision_date: str,
    signatures: List[str],
    decision_id: Optional[str] = None,
    record_timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create and append a Decision Record to the ledger.

    Args:
        ledger: The FidesLedger instance
        authority_id: Unique identifier of the authority/agency
        deciders_id: List of decision maker IDs
        act_type: Type of administrative act
        currency: ISO 4217 currency code
        maximum_value: Maximum authorized value (decimal string)
        beneficiary: Tax ID or entity identifier
        legal_basis: Legal reference
        decision_date: Date of decision (ISO 8601)
        signatures: List of signature identifiers
        decision_id: Optional UUID, auto-generated if not provided
        record_timestamp: Optional timestamp, auto-generated if not provided

    Returns:
        The created Decision Record

    Raises:
        ValueError: If validation fails
    """
    if decision_id is None:
        decision_id = generate_uuid()

    if record_timestamp is None:
        record_timestamp = current_timestamp()

    # Get previous record for hash chaining
    records = ledger.get_all_records()
    previous_record = records[-1] if records else None

    previous_hash = compute_previous_hash(
        authority_id,
        record_timestamp,
        previous_record
    )

    dr = {
        'record_type': 'DR',
        'decision_id': decision_id,
        'authority_id': authority_id,
        'deciders_id': deciders_id,
        'act_type': act_type,
        'currency': currency,
        'maximum_value': maximum_value,
        'beneficiary': beneficiary,
        'legal_basis': legal_basis,
        'decision_date': decision_date,
        'previous_record_hash': previous_hash,
        'record_timestamp': record_timestamp,
        'signatures': signatures
    }

    # Validate
    valid, errors = validate_dr(dr)
    if not valid:
        raise ValueError(f"Invalid Decision Record: {errors}")

    # Append to ledger
    ledger.append_record(dr)

    return dr


def create_revocation_record(
    ledger: FidesLedger,
    target_decision_id: str,
    authority_id: str,
    deciders_id: List[str],
    revocation_reason: str,
    signatures: List[str],
    revocation_id: Optional[str] = None,
    revocation_date: Optional[str] = None,
    record_timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create and append a Revocation Record to the ledger.

    Args:
        ledger: The FidesLedger instance
        target_decision_id: The decision_id being revoked
        authority_id: Unique identifier of the authority/agency
        deciders_id: List of decision maker IDs
        revocation_reason: Reason for revocation
        signatures: List of signature identifiers
        revocation_id: Optional UUID, auto-generated if not provided
        revocation_date: Optional date, defaults to record_timestamp
        record_timestamp: Optional timestamp, auto-generated if not provided

    Returns:
        The created Revocation Record

    Raises:
        ValueError: If validation fails or target not found
    """
    # Check target exists
    target = ledger.find_decision_record(target_decision_id)
    if target is None:
        raise ValueError(f"Target decision not found: {target_decision_id}")

    # Check not already revoked
    if ledger.is_revoked(target_decision_id):
        raise ValueError(f"Decision already revoked: {target_decision_id}")

    if revocation_id is None:
        revocation_id = generate_uuid()

    if record_timestamp is None:
        record_timestamp = current_timestamp()

    if revocation_date is None:
        revocation_date = record_timestamp

    # Get previous record for hash chaining
    records = ledger.get_all_records()
    previous_record = records[-1] if records else None

    previous_hash = compute_previous_hash(
        authority_id,
        record_timestamp,
        previous_record
    )

    rr = {
        'record_type': 'RR',
        'revocation_id': revocation_id,
        'target_decision_id': target_decision_id,
        'authority_id': authority_id,
        'deciders_id': deciders_id,
        'revocation_reason': revocation_reason,
        'revocation_date': revocation_date,
        'previous_record_hash': previous_hash,
        'record_timestamp': record_timestamp,
        'signatures': signatures
    }

    # Validate
    valid, errors = validate_rr(rr)
    if not valid:
        raise ValueError(f"Invalid Revocation Record: {errors}")

    # Append to ledger
    ledger.append_record(rr)

    return rr

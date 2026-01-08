"""
Fides Protocol - Hash Chain Module

Implements genesis hash, record hash, and canonical JSON serialization.
"""

import hashlib
import json
from typing import Any, Dict, Optional


def canonical_json(record: Dict[str, Any]) -> str:
    """
    Convert record to canonical JSON form for hashing.

    Rules:
    - Sort keys alphabetically (recursive)
    - No whitespace
    - UTF-8 encoding
    """
    return json.dumps(
        record,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False
    )


def sha256_hash(data: bytes) -> str:
    """
    Compute SHA-256 hash and return as hex string.
    """
    return hashlib.sha256(data).hexdigest()


def genesis_hash(authority_id: str, genesis_timestamp: str) -> str:
    """
    Generate the hash for the first record in a chain.

    Args:
        authority_id: Unique identifier of the authority/agency
        genesis_timestamp: ISO 8601 timestamp of the first record

    Returns:
        SHA-256 hash as hex string
    """
    seed = f"FIDES-GENESIS-{authority_id}-{genesis_timestamp}"
    return sha256_hash(seed.encode('utf-8'))


def record_hash(record: Dict[str, Any]) -> str:
    """
    Compute the hash of a record.

    Args:
        record: The record dictionary

    Returns:
        SHA-256 hash as hex string
    """
    canonical = canonical_json(record)
    return sha256_hash(canonical.encode('utf-8'))


def compute_previous_hash(
    authority_id: str,
    record_timestamp: str,
    previous_record: Optional[Dict[str, Any]]
) -> str:
    """
    Compute the previous_record_hash field for a new record.

    Args:
        authority_id: Authority ID (used for genesis)
        record_timestamp: Timestamp of the new record (used for genesis)
        previous_record: The previous record, or None for genesis

    Returns:
        Hash to use as previous_record_hash
    """
    if previous_record is None:
        return genesis_hash(authority_id, record_timestamp)
    return record_hash(previous_record)


def verify_chain_link(current_record: Dict[str, Any], previous_record: Dict[str, Any]) -> bool:
    """
    Verify that current_record correctly chains from previous_record.

    Args:
        current_record: The record to verify
        previous_record: The expected previous record

    Returns:
        True if chain is valid, False otherwise
    """
    expected_hash = record_hash(previous_record)
    return current_record.get('previous_record_hash') == expected_hash


def verify_genesis(record: Dict[str, Any]) -> bool:
    """
    Verify that a record is a valid genesis record.

    Args:
        record: The genesis record to verify

    Returns:
        True if genesis hash is correct, False otherwise
    """
    expected = genesis_hash(
        record.get('authority_id', ''),
        record.get('record_timestamp', '')
    )
    return record.get('previous_record_hash') == expected

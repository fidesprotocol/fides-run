"""
Fides Protocol - Ledger Module

SQLite append-only ledger for storing records.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .hash_chain import record_hash, verify_genesis, verify_chain_link


class FidesLedger:
    """
    Append-only ledger backed by SQLite.

    Enforces:
    - No UPDATE
    - No DELETE
    - Hash chain integrity
    """

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize the ledger.

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Records table - stores all DR, SDR, RR
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_type TEXT NOT NULL,
                decision_id TEXT,
                revocation_id TEXT,
                target_decision_id TEXT,
                authority_id TEXT NOT NULL,
                previous_record_hash TEXT NOT NULL,
                record_timestamp TEXT NOT NULL,
                record_data TEXT NOT NULL,
                record_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Index for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_id ON records(decision_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_target_decision_id ON records(target_decision_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_record_type ON records(record_type)
        """)

        # Payments table - tracks executed payments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT UNIQUE NOT NULL,
                decision_id TEXT NOT NULL,
                beneficiary TEXT NOT NULL,
                currency TEXT NOT NULL,
                value TEXT NOT NULL,
                payment_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_payment_decision_id ON payments(decision_id)
        """)

        self.conn.commit()

    def _get_last_record(self) -> Optional[Dict[str, Any]]:
        """Get the most recent record from the ledger."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT record_data FROM records ORDER BY id DESC LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return json.loads(row['record_data'])
        return None

    def _get_record_count(self) -> int:
        """Get the total number of records."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM records")
        return cursor.fetchone()['cnt']

    def append_record(self, record: Dict[str, Any]) -> str:
        """
        Append a record to the ledger.

        Validates hash chain integrity before appending.

        Args:
            record: The record to append (DR, SDR, or RR)

        Returns:
            The hash of the appended record

        Raises:
            ValueError: If hash chain validation fails
        """
        last_record = self._get_last_record()
        record_count = self._get_record_count()

        # Validate hash chain
        if record_count == 0:
            # Genesis record
            if not verify_genesis(record):
                raise ValueError("Invalid genesis hash")
        else:
            # Chain link
            if not verify_chain_link(record, last_record):
                raise ValueError("Hash chain validation failed")

        # Determine record type and IDs
        record_type = record.get('record_type', 'DR')
        decision_id = record.get('decision_id')
        revocation_id = record.get('revocation_id')
        target_decision_id = record.get('target_decision_id')

        # Compute record hash
        rec_hash = record_hash(record)

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO records (
                record_type, decision_id, revocation_id, target_decision_id,
                authority_id, previous_record_hash, record_timestamp,
                record_data, record_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record_type,
            decision_id,
            revocation_id,
            target_decision_id,
            record.get('authority_id'),
            record.get('previous_record_hash'),
            record.get('record_timestamp'),
            json.dumps(record, sort_keys=True),
            rec_hash,
            datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        ))
        self.conn.commit()

        return rec_hash

    def find_decision_record(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a Decision Record by decision_id.

        Args:
            decision_id: The UUID of the decision

        Returns:
            The record dict or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT record_data FROM records
            WHERE decision_id = ? AND record_type IN ('DR', 'SDR')
            ORDER BY id ASC LIMIT 1
        """, (decision_id,))
        row = cursor.fetchone()
        if row:
            return json.loads(row['record_data'])
        return None

    def find_revocation_record(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a Revocation Record for a given decision.

        Args:
            decision_id: The UUID of the decision to check

        Returns:
            The revocation record or None if not revoked
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT record_data FROM records
            WHERE target_decision_id = ? AND record_type = 'RR'
            ORDER BY id ASC LIMIT 1
        """, (decision_id,))
        row = cursor.fetchone()
        if row:
            return json.loads(row['record_data'])
        return None

    def is_revoked(self, decision_id: str) -> bool:
        """
        Check if a decision has been revoked.

        Args:
            decision_id: The UUID of the decision

        Returns:
            True if revoked, False otherwise
        """
        return self.find_revocation_record(decision_id) is not None

    def get_all_records(self) -> List[Dict[str, Any]]:
        """
        Get all records in order.

        Returns:
            List of all records
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT record_data FROM records ORDER BY id ASC")
        return [json.loads(row['record_data']) for row in cursor.fetchall()]

    def record_payment(
        self,
        payment_id: str,
        decision_id: str,
        beneficiary: str,
        currency: str,
        value: str,
        payment_date: str
    ) -> None:
        """
        Record an executed payment.

        Args:
            payment_id: Unique payment identifier
            decision_id: The DR this payment is against
            beneficiary: Payment recipient
            currency: ISO 4217 currency code
            value: Payment amount as string (decimal)
            payment_date: ISO 8601 payment date
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO payments (
                payment_id, decision_id, beneficiary, currency, value,
                payment_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            payment_id,
            decision_id,
            beneficiary,
            currency,
            value,
            payment_date,
            datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        ))
        self.conn.commit()

    def sum_payments(self, decision_id: str) -> str:
        """
        Sum all payments made against a decision.

        Args:
            decision_id: The decision UUID

        Returns:
            Total as string (decimal)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT value FROM payments WHERE decision_id = ?
        """, (decision_id,))

        from decimal import Decimal
        total = Decimal('0')
        for row in cursor.fetchall():
            total += Decimal(row['value'])

        return str(total)

    def verify_chain_integrity(self) -> tuple[bool, Optional[int]]:
        """
        Verify the entire hash chain is intact.

        Returns:
            Tuple of (valid, first_invalid_index)
        """
        records = self.get_all_records()

        if len(records) == 0:
            return (True, None)

        # Verify genesis
        if not verify_genesis(records[0]):
            return (False, 0)

        # Verify chain
        for i in range(1, len(records)):
            if not verify_chain_link(records[i], records[i - 1]):
                return (False, i)

        return (True, None)

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()

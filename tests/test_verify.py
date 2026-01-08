"""
Fides Protocol - Unit Tests for Verification

Tests the core function: is_payment_authorized()
"""

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ledger import FidesLedger
from src.records import create_decision_record, create_revocation_record
from src.verify import Payment, is_payment_authorized, is_payment_authorized_with_reason
from src.hash_chain import genesis_hash, record_hash, canonical_json


class TestHashChain(unittest.TestCase):
    """Tests for hash chain functions."""

    def test_canonical_json_sorts_keys(self):
        """Canonical JSON should sort keys alphabetically."""
        record = {"z": 1, "a": 2, "m": 3}
        result = canonical_json(record)
        self.assertEqual(result, '{"a":2,"m":3,"z":1}')

    def test_canonical_json_no_whitespace(self):
        """Canonical JSON should have no whitespace."""
        record = {"key": "value", "nested": {"a": 1}}
        result = canonical_json(record)
        self.assertNotIn(" ", result)
        self.assertNotIn("\n", result)

    def test_genesis_hash_deterministic(self):
        """Genesis hash should be deterministic."""
        h1 = genesis_hash("AUTH-001", "2024-01-01T00:00:00Z")
        h2 = genesis_hash("AUTH-001", "2024-01-01T00:00:00Z")
        self.assertEqual(h1, h2)

    def test_genesis_hash_varies_with_input(self):
        """Genesis hash should vary with different inputs."""
        h1 = genesis_hash("AUTH-001", "2024-01-01T00:00:00Z")
        h2 = genesis_hash("AUTH-002", "2024-01-01T00:00:00Z")
        self.assertNotEqual(h1, h2)

    def test_record_hash_deterministic(self):
        """Record hash should be deterministic."""
        record = {"decision_id": "123", "authority_id": "AUTH"}
        h1 = record_hash(record)
        h2 = record_hash(record)
        self.assertEqual(h1, h2)


class TestPaymentAuthorization(unittest.TestCase):
    """Tests for is_payment_authorized()."""

    def setUp(self):
        """Create a fresh ledger and decision record for each test."""
        self.ledger = FidesLedger(":memory:")
        self.dr = create_decision_record(
            ledger=self.ledger,
            authority_id="GOV-TEST-001",
            deciders_id=["DECIDER-001"],
            act_type="contract",
            currency="BRL",
            maximum_value="10000.00",
            beneficiary="SUPPLIER-TEST",
            legal_basis="Test Law",
            decision_date="2024-01-01T10:00:00Z",
            signatures=["SIG-001"],
            record_timestamp="2024-01-01T10:30:00Z"
        )
        self.decision_id = self.dr['decision_id']

    def tearDown(self):
        """Close ledger after each test."""
        self.ledger.close()

    def test_authorized_payment(self):
        """Valid payment should be authorized."""
        payment = Payment(
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="5000.00",
            payment_date="2024-01-15T14:00:00Z"
        )
        self.assertTrue(is_payment_authorized(self.ledger, payment))

    def test_payment_no_record(self):
        """Payment without record should be blocked."""
        payment = Payment(
            decision_id="00000000-0000-4000-8000-000000000000",
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="5000.00",
            payment_date="2024-01-15T14:00:00Z"
        )
        self.assertFalse(is_payment_authorized(self.ledger, payment))

    def test_payment_wrong_beneficiary(self):
        """Payment to wrong beneficiary should be blocked."""
        payment = Payment(
            decision_id=self.decision_id,
            beneficiary="WRONG-BENEFICIARY",
            currency="BRL",
            value="5000.00",
            payment_date="2024-01-15T14:00:00Z"
        )
        self.assertFalse(is_payment_authorized(self.ledger, payment))

    def test_payment_wrong_currency(self):
        """Payment in wrong currency should be blocked."""
        payment = Payment(
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="USD",
            value="5000.00",
            payment_date="2024-01-15T14:00:00Z"
        )
        self.assertFalse(is_payment_authorized(self.ledger, payment))

    def test_payment_exceeds_limit(self):
        """Payment exceeding limit should be blocked."""
        payment = Payment(
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="15000.00",  # Exceeds 10000 limit
            payment_date="2024-01-15T14:00:00Z"
        )
        self.assertFalse(is_payment_authorized(self.ledger, payment))

    def test_payment_exceeds_cumulative_limit(self):
        """Cumulative payments exceeding limit should be blocked."""
        # First payment (authorized)
        payment1 = Payment(
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="6000.00",
            payment_date="2024-01-15T14:00:00Z"
        )
        self.assertTrue(is_payment_authorized(self.ledger, payment1))

        # Record the payment
        self.ledger.record_payment(
            payment_id="PAY-001",
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="6000.00",
            payment_date="2024-01-15T14:00:00Z"
        )

        # Second payment would exceed limit (6000 + 5000 > 10000)
        payment2 = Payment(
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="5000.00",
            payment_date="2024-01-20T14:00:00Z"
        )
        self.assertFalse(is_payment_authorized(self.ledger, payment2))

    def test_payment_before_decision(self):
        """Payment before decision date should be blocked."""
        payment = Payment(
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="5000.00",
            payment_date="2023-12-15T14:00:00Z"  # Before decision date
        )
        self.assertFalse(is_payment_authorized(self.ledger, payment))

    def test_payment_after_revocation(self):
        """Payment after revocation should be blocked."""
        # Create revocation
        create_revocation_record(
            ledger=self.ledger,
            target_decision_id=self.decision_id,
            authority_id="GOV-TEST-001",
            deciders_id=["DECIDER-001"],
            revocation_reason="Contract cancelled",
            signatures=["SIG-001"],
            record_timestamp="2024-02-01T09:00:00Z"
        )

        payment = Payment(
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="5000.00",
            payment_date="2024-02-15T14:00:00Z"
        )
        self.assertFalse(is_payment_authorized(self.ledger, payment))

    def test_payment_zero_value(self):
        """Payment with zero value should be blocked."""
        payment = Payment(
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="0.00",
            payment_date="2024-01-15T14:00:00Z"
        )
        self.assertFalse(is_payment_authorized(self.ledger, payment))

    def test_payment_negative_value(self):
        """Payment with negative value should be blocked."""
        payment = Payment(
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="-1000.00",
            payment_date="2024-01-15T14:00:00Z"
        )
        self.assertFalse(is_payment_authorized(self.ledger, payment))


class TestChainIntegrity(unittest.TestCase):
    """Tests for hash chain integrity."""

    def test_chain_integrity_valid(self):
        """Valid chain should pass integrity check."""
        ledger = FidesLedger(":memory:")

        create_decision_record(
            ledger=ledger,
            authority_id="GOV-TEST-001",
            deciders_id=["DECIDER-001"],
            act_type="contract",
            currency="BRL",
            maximum_value="10000.00",
            beneficiary="SUPPLIER-TEST",
            legal_basis="Test Law",
            decision_date="2024-01-01T10:00:00Z",
            signatures=["SIG-001"],
            record_timestamp="2024-01-01T10:30:00Z"
        )

        valid, invalid_idx = ledger.verify_chain_integrity()
        self.assertTrue(valid)
        self.assertIsNone(invalid_idx)

        ledger.close()

    def test_chain_with_multiple_records(self):
        """Chain with multiple records should be valid."""
        ledger = FidesLedger(":memory:")

        dr1 = create_decision_record(
            ledger=ledger,
            authority_id="GOV-TEST-001",
            deciders_id=["DECIDER-001"],
            act_type="contract",
            currency="BRL",
            maximum_value="10000.00",
            beneficiary="SUPPLIER-A",
            legal_basis="Test Law",
            decision_date="2024-01-01T10:00:00Z",
            signatures=["SIG-001"],
            record_timestamp="2024-01-01T10:30:00Z"
        )

        dr2 = create_decision_record(
            ledger=ledger,
            authority_id="GOV-TEST-001",
            deciders_id=["DECIDER-001"],
            act_type="contract",
            currency="BRL",
            maximum_value="20000.00",
            beneficiary="SUPPLIER-B",
            legal_basis="Test Law",
            decision_date="2024-01-02T10:00:00Z",
            signatures=["SIG-001"],
            record_timestamp="2024-01-02T10:30:00Z"
        )

        create_revocation_record(
            ledger=ledger,
            target_decision_id=dr1['decision_id'],
            authority_id="GOV-TEST-001",
            deciders_id=["DECIDER-001"],
            revocation_reason="Cancelled",
            signatures=["SIG-001"],
            record_timestamp="2024-01-03T10:00:00Z"
        )

        valid, invalid_idx = ledger.verify_chain_integrity()
        self.assertTrue(valid)
        self.assertEqual(len(ledger.get_all_records()), 3)

        ledger.close()


class TestWithReason(unittest.TestCase):
    """Tests for is_payment_authorized_with_reason()."""

    def setUp(self):
        """Create a fresh ledger and decision record for each test."""
        self.ledger = FidesLedger(":memory:")
        self.dr = create_decision_record(
            ledger=self.ledger,
            authority_id="GOV-TEST-001",
            deciders_id=["DECIDER-001"],
            act_type="contract",
            currency="BRL",
            maximum_value="10000.00",
            beneficiary="SUPPLIER-TEST",
            legal_basis="Test Law",
            decision_date="2024-01-01T10:00:00Z",
            signatures=["SIG-001"],
            record_timestamp="2024-01-01T10:30:00Z"
        )
        self.decision_id = self.dr['decision_id']

    def tearDown(self):
        self.ledger.close()

    def test_authorized_reason(self):
        """Authorized payment should return AUTHORIZED reason."""
        payment = Payment(
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="5000.00",
            payment_date="2024-01-15T14:00:00Z"
        )
        authorized, reason = is_payment_authorized_with_reason(self.ledger, payment)
        self.assertTrue(authorized)
        self.assertEqual(reason, "AUTHORIZED")

    def test_no_record_reason(self):
        """Missing record should return RECORD_NOT_FOUND."""
        payment = Payment(
            decision_id="00000000-0000-4000-8000-000000000000",
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="5000.00",
            payment_date="2024-01-15T14:00:00Z"
        )
        authorized, reason = is_payment_authorized_with_reason(self.ledger, payment)
        self.assertFalse(authorized)
        self.assertEqual(reason, "RECORD_NOT_FOUND")

    def test_revoked_reason(self):
        """Revoked decision should return DECISION_REVOKED."""
        create_revocation_record(
            ledger=self.ledger,
            target_decision_id=self.decision_id,
            authority_id="GOV-TEST-001",
            deciders_id=["DECIDER-001"],
            revocation_reason="Cancelled",
            signatures=["SIG-001"],
            record_timestamp="2024-02-01T09:00:00Z"
        )

        payment = Payment(
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="5000.00",
            payment_date="2024-02-15T14:00:00Z"
        )
        authorized, reason = is_payment_authorized_with_reason(self.ledger, payment)
        self.assertFalse(authorized)
        self.assertEqual(reason, "DECISION_REVOKED")

    def test_exceeds_limit_reason(self):
        """Exceeding limit should return EXCEEDS_MAXIMUM_VALUE."""
        payment = Payment(
            decision_id=self.decision_id,
            beneficiary="SUPPLIER-TEST",
            currency="BRL",
            value="15000.00",
            payment_date="2024-01-15T14:00:00Z"
        )
        authorized, reason = is_payment_authorized_with_reason(self.ledger, payment)
        self.assertFalse(authorized)
        self.assertEqual(reason, "EXCEEDS_MAXIMUM_VALUE")


if __name__ == "__main__":
    unittest.main()

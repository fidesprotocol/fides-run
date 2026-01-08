# fides-run

**Minimal executable proof of the Fides Protocol.**

This is not a product. It is executable proof that the protocol works.

---

## What This Is

A minimal Python implementation demonstrating the core Fides principle:

> **No record, no payment.**

This repository proves, through executable code, that the core invariants of the protocol are enforceable:

1. A payment can only proceed if a valid Decision Record exists
2. Payments exceeding the authorized limit are blocked
3. Payments after revocation are blocked
4. The hash chain detects any tampering

## What This Is NOT

- **Not production-ready** — No external anchor, no role separation, no API
- **Not a complete implementation** — SDR (exceptions) not demonstrated
- **Not a framework or library** — Copy and study, don't import
- **Not a product** — No roadmap, no features, no support
- **Not maintained as a service** — Stability comes from the protocol, not from this repository

## Scope

This implementation covers:

| Spec Section | Status |
|--------------|--------|
| Decision Record (DR) | Implemented |
| Revocation Record (RR) | Implemented |
| Hash Chain | Implemented |
| `is_payment_authorized()` | Implemented |
| Append-only ledger | Implemented |
| Chain integrity verification | Implemented |

This implementation does NOT cover:

| Spec Section | Reason |
|--------------|--------|
| Special Decision Record (SDR) | Out of demo scope |
| External Anchor | Requires external infrastructure |
| Role Separation | Governance, not code |
| API/Integration | This is proof, not product |

## Requirements

- Python 3.10+
- No external dependencies (stdlib only)

## Usage

```bash
python demo/fides_run.py
```

Expected output:

```
[1] Creating Decision Record... OK
[2] Attempting authorized payment... AUTHORIZED
[3] Attempting payment exceeding limit... BLOCKED
[4] Attempting payment after revocation... BLOCKED

Fides: No record, no payment.
```

## Running Tests

```bash
python -m unittest tests.test_verify -v
```

21 tests covering:
- Hash chain correctness
- Payment authorization logic
- Revocation enforcement
- Cumulative limit tracking

## Structure

```
fides-run/
├── src/
│   ├── __init__.py     # Package exports
│   ├── hash_chain.py   # Genesis hash, record hash, canonical JSON
│   ├── ledger.py       # SQLite append-only store
│   ├── records.py      # DR, RR creation and validation
│   └── verify.py       # is_payment_authorized()
├── demo/
│   └── fides_run.py    # Demo scenario
├── tests/
│   ├── __init__.py
│   └── test_verify.py  # Unit tests
├── LICENSE             # AGPLv3
└── README.md
```

## Core Function

The entire protocol reduces to one function:

```python
def is_payment_authorized(ledger, payment) -> bool:
    """
    Returns True if payment is authorized, False otherwise.
    No exceptions. No partial results. Binary only.
    """
```

This function checks:
1. Decision Record exists
2. Not revoked
3. Record is valid
4. Payment date >= decision date
5. Beneficiary matches
6. Currency matches
7. Cumulative value <= maximum_value

Any failure returns `False`. No exceptions. No override.

## Protocol Reference

This implementation follows:
- [Fides Protocol v0.1](https://github.com/fidesprotocol/fides/blob/main/spec/FIDES-v0.1.md)
- [Algorithms Reference](https://github.com/fidesprotocol/fides/blob/main/reference/algorithms.md)

---

## License

AGPLv3 — Same as the protocol.

Open source is not optional. It is a protocol requirement (Section 11.4).

---

*Proof, not product.*

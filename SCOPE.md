# fides-run — Scope Definition

## Purpose

**fides-run** exists for one reason: to prove that the Fides Protocol's core logic works.

It is executable evidence, not software infrastructure.

**Version:** This implementation follows Fides Protocol v0.1 (historical/frozen). The current protocol version is v0.3, which adds security hardening (cryptographic signatures, timestamp attestation, PKI requirements). This repository proves the *logic* — that blocking works — not the full security model.

---

## This Repository IS

1. **Executable proof** — Demonstrates that the protocol logic is implementable
2. **Reference code** — Shows one correct way to implement the spec
3. **Test harness** — Validates the core function behaves as specified
4. **Educational material** — ~500 lines anyone can read and understand

## This Repository IS NOT

1. **A product** — No roadmap, no releases, no support
2. **A library** — Do not `pip install`, do not import as dependency
3. **Production code** — Missing external anchor, role separation, hardening
4. **A framework** — No abstractions, no plugins, no extensibility
5. **Complete** — SDR, external anchor, API not implemented

---

## What We Prove

Running `python demo/fides_run.py` demonstrates:

| Scenario | Expected | Actual |
|----------|----------|--------|
| Payment with valid DR | AUTHORIZED | AUTHORIZED |
| Payment exceeding limit | BLOCKED | BLOCKED |
| Payment after revocation | BLOCKED | BLOCKED |

Running `python -m unittest tests.test_verify -v` proves:

- 21 test cases pass
- Hash chain is deterministic
- Validation is binary (True/False only)
- No edge case allows unauthorized payment

---

## What We Do NOT Prove

| Item | Why Not |
|------|---------|
| Scalability | Not relevant for proof |
| Performance | Not relevant for proof |
| Security hardening (v0.3) | Requires production context |
| Cryptographic signatures | v0.3 requirement, not in v0.1 |
| Timestamp attestation | v0.3 requirement, not in v0.1 |
| External anchor | Requires infrastructure |
| Multi-authority chains | Out of scope |
| Real-world integration | This is proof, not product |

---

## Boundaries

### Code Boundaries

- **Language:** Python 3.10+ only
- **Dependencies:** stdlib only (no pip packages)
- **Storage:** SQLite in-memory or file
- **Interface:** CLI demo only (no API, no GUI)

### Conceptual Boundaries

- **No interpretation:** Code does not evaluate merit or legality
- **No override:** No admin bypass, no emergency exception in code
- **No logging secrets:** Rejection reasons not exposed in production function

---

## When Is fides-run "Done"?

fides-run is done when:

1. The demo runs and produces expected output
2. All tests pass
3. Code matches spec exactly
4. README explains what it is and isn't

fides-run is NOT done when:

- Someone wants more features
- Someone wants production readiness
- Someone wants integrations

Those belong in different repositories.

---

## Maintenance Policy

- **Bug fixes:** Yes, if they break spec compliance
- **New features:** No
- **Refactoring:** No
- **Dependencies:** No (stdlib only, forever)
- **Python version:** Minimum version may advance only due to upstream EOL

---

## How to Use This Repository

### Correct Uses

- Read the code to understand the protocol
- Run the demo to see the protocol work
- Run tests to verify correctness
- Fork and modify for your own experiments
- Reference in discussions about feasibility

### Incorrect Uses

- Import as a library in production code
- Expect support or maintenance
- Request features
- Use as basis for production system without significant hardening

---

*This is proof. Proof doesn't need features. Proof needs to be correct.*

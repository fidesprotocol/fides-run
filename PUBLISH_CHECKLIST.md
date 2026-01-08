# fides-run — Publish Checklist

## Pre-Publish Verification

### Code Verification

- [x] `python demo/fides_run.py` produces expected output:
  ```
  [1] Creating Decision Record... OK
  [2] Attempting authorized payment... AUTHORIZED
  [3] Attempting payment exceeding limit... BLOCKED
  [4] Attempting payment after revocation... BLOCKED

  Fides: No record, no payment.
  ```

- [x] `python -m unittest tests.test_verify -v` — all 21 tests pass

- [x] No external dependencies (stdlib only)

- [x] No deprecation warnings

### Spec Compliance

- [x] `is_payment_authorized()` follows Appendix B pseudocode exactly
- [x] Decision Record has all required fields (Section 6.3)
- [x] Revocation Record has all required fields (Section 10)
- [x] Hash chain uses SHA-256
- [x] Canonical JSON: sorted keys, no whitespace, UTF-8
- [x] Genesis hash format: `FIDES-GENESIS-{authority}-{timestamp}`
- [x] Append-only: no UPDATE, no DELETE in ledger
- [x] Decimal for monetary values (not float)
- [x] Binding rule enforced: `len(deciders_id) == len(signatures)`

### Documentation

- [x] README.md explains what it is
- [x] README.md explains what it is NOT
- [x] SCOPE.md defines boundaries
- [x] LICENSE is AGPLv3
- [x] Links to protocol spec are correct

### Files Present

- [x] `src/__init__.py`
- [x] `src/hash_chain.py`
- [x] `src/ledger.py`
- [x] `src/records.py`
- [x] `src/verify.py`
- [x] `demo/fides_run.py`
- [x] `tests/__init__.py`
- [x] `tests/test_verify.py`
- [x] `LICENSE`
- [x] `README.md`
- [x] `SCOPE.md`

### What Should NOT Be Present

- [x] No `.env` files
- [x] No credentials
- [x] No `__pycache__` directories
- [x] No `.pyc` files
- [x] No IDE configuration files
- [x] No `node_modules` or `venv`

---

## Repository Settings (GitHub)

### Recommended Settings

- **Description:** "Minimal reference implementation of the Fides Protocol"
- **Website:** Link to main fides repo
- **Topics:** `fides`, `protocol`, `reference-implementation`, `python`
- **Visibility:** Public
- **License:** AGPL-3.0 (detected from LICENSE file)

### Branch Protection (optional for proof repo)

- Not required for a proof-of-concept
- If enabled: require PR reviews

### Issues/Discussions

- Issues: Enabled (for bug reports only)
- Discussions: Disabled (this is not a product)
- Wiki: Disabled

---

## Post-Publish Verification

After pushing to GitHub:

1. [ ] Clone fresh copy to new directory
2. [ ] Run `python demo/fides_run.py` — verify output
3. [ ] Run `python -m unittest tests.test_verify -v` — verify all pass
4. [ ] Verify LICENSE shows correctly on GitHub
5. [ ] Verify README renders correctly

---

## Ready to Publish

All items checked = ready to push.

```bash
git init
git add .
git commit -m "Initial commit: fides-run reference implementation"
git branch -M main
git remote add origin https://github.com/fidesprotocol/fides-run.git
git push -u origin main
```

---

*Checklist complete. Proof ready for publication.*

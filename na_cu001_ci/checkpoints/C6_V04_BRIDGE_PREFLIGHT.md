# Checkpoint C6 preflight: audited v0.4 bulk-to-surface bridge

**Status:** PASS, prospective preflight only  
**Recorded:** 2026-08-03 America/Chicago  
**Scientific bulk decision available at freeze time:** no  

## Frozen source

- verifier: `na_cu001_ci/bulk_v04_downstream_bridge_v1.py`
- verifier commit: `ec87cb85ab4ee2d312fb9aa7db9636678534bb2e`
- adversarial tests: `na_cu001_ci/test_bulk_v04_downstream_bridge_v1.py`
- test commit: `08838846dbc851a32195b10eefe87a286ce7d27d`
- isolated workflow: `.github/workflows/na-cu001-bulk-v04-bridge-tests.yml`
- workflow commit: `2551b5460902191835727d2a71c2a019737ec72e`

## Verification run

- GitHub Actions run: `30850160246`
- job: `bridge-contract`
- conclusion: success
- tests passed: 5/5
- artifact: `na-cu001-v04-bridge-test-record`
- artifact digest: `sha256:290e38f69dbc643938166f4410488326bd6a7982cde358a00cc1fb1b6c06b97b`
- temporary trigger PR: `#12`
- PR disposition: closed unmerged after successful verification

## Adversarial refusal tests

1. valid synthetic v0.4 PASS chain is accepted;
2. failed independent reference audit is rejected;
3. non-minimum-cost passing candidate is rejected;
4. corrupted EOS summary is rejected;
5. result-to-handoff hash disagreement is rejected.

## Real-data requirements

The verifier cannot open the surface route unless all of the following are true:

- the v0.4 result and handoff are PASS;
- the frozen protocol hash matches both;
- the 140 Ry/22-cubed reference independently passes against 150 Ry/24-cubed;
- the selected setting is the minimum frozen-cost eligible candidate satisfying both unchanged criteria;
- exactly 44 candidate rows plus one reference and one audit row exist;
- all 46 EOS summaries match their registered SHA-256 hashes;
- every summary contains six successful, converged SCF records with final energy and input/output hashes;
- the handoff settings reproduce the selected result values.

A successful preflight does not imply that the live bulk extension will PASS. It establishes only that the next bridge gate was frozen and independently tested before the result was known.

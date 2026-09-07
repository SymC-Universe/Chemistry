# Na/Cu(001) clean-slab protocol metadata erratum v0.1

**Recorded:** after C7 launch and before any clean-slab numerical result was inspected  
**Affected file:** `na_cu001_ci/slab_protocol_v0.3.json`  
**Affected field:** `bulk_input`  
**Classification:** documentation/provenance metadata mismatch only  

## Erratum

The frozen clean-slab protocol contains:

```json
"bulk_input": "na-cu001-bulk-to-slab-handoff-v0.3"
```

The executed C7 route does not consume a v0.3 handoff. The operational entrypoint `slab_runner_v3.py` requires all of the following before any slab SCF can run:

- result schema `na-cu001-bulk-selection-v0.4`;
- handoff schema `na-cu001-bulk-to-slab-handoff-v0.4`;
- bridge schema `na-cu001-audited-bulk-downstream-bridge-v0.1`;
- PASS reference audit;
- complete 46-EOS and 276-SCF inventory;
- agreement of the selected settings across the result, handoff, and bridge;
- matching result and handoff SHA-256 values.

The stale v0.3 string is not read by `slab_runner_v2.py`, `slab_runner_v3.py`, or the C7 workflow when constructing or analyzing a slab. The calculation therefore uses the audited v0.4 bulk setting despite the obsolete descriptive field.

## Non-effect on the frozen scientific method

This erratum does not alter:

- the selected 90/270 Ry cutoffs;
- the 14x14x14 bulk mesh;
- the fitted bulk lattice constant or energy;
- the 5/7/9/11-layer grid;
- the 12/16/20/24 A vacuum grid;
- the registered in-plane k-mesh rule;
- ESM `bc1` electrostatics;
- the 1.0 meV per-surface-atom criterion;
- the seven-layer downstream floor;
- any computed energy or selection result.

The frozen JSON is retained byte-for-byte as the historical preregistration record. This erratum and the v0.4 bridge hashes provide the corrected provenance interpretation. Future protocol versions must name `na-cu001-bulk-to-slab-handoff-v0.4` explicitly before launch.

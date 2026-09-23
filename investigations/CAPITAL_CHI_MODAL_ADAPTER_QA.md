# Capital-Chi modal adapter QA manifest

**Date:** 2026-09-22  
**Status:** additive reporting layer only; frozen ChemSA core not modified.

## Exact tested baseline

- ChemSA Release 38 ZIP SHA-256:
  `761b87010f22f5fc46810b36387ab7afcc95cb275f68c16f9379c60f7b217708`
- `chemsa_v3.py` SHA-256:
  `a5c51aa4df11b15cad170c6e4700a6560e53fcc5454e593a0597b21185b40710`
- `biorthogonal_response.py` SHA-256:
  `805fdc83f8b090b4d5c8354d1897856bac62654a28cbb106228c7ff16470f63f`

## Additive adapter

- `investigations/capital_chi_modal.py`
- tested local SHA-256:
  `a566b48151776783ac8f19f6d0ea816520eb16cbd56b49e40ca7f7636b15c201`

The adapter does not patch or import-modify the frozen core. It consumes:
- authoritative `BalancedSpectrum`;
- `SystemSummary` derived from that spectrum;
- `ModeGeometry` records derived from that same spectrum.

It emits modal/vector Capital Chi and preserves lowercase scalar chi separately.

## QA command

```bash
pytest -q   test_capital_chi_modal.py   test_biorthogonal.py   test_chi_rho_split.py   test_conditioning_gate.py   test_dho_roundtrip.py   test_two_mode_ep_corollary.py
```

Final targeted result after saddle/spectral-subspace extension:

```
115 passed
```

## Adversarial cases covered

1. two distinct licensed mechanical chi values assigned to their mass-normalized carrier vectors;
2. degenerate stiffness block correctly rotated to damping-resolved carriers;
3. non-proportional damping refuses mechanical chi while preserving spectral modal projection;
4. known cross-condition orthogonal mode rotation recovered by an explicitly declared correspondence metric;
5. cross-spectrum object drift refused by `spectrum_id`;
6. exact simultaneous mechanical degeneracy treated as a subspace rather than unique physical vectors;
7. individual correspondence inside such a degenerate subspace refused;
8. declared reaction coordinate retained as a spectral/subspace projection when mechanical chi is unavailable;
9. saddle reaction coordinate projects onto the unstable spectral carrier without inventing barrier chi;
10. A18 integration reproduces independently computed unstable-mode participation to <1e-10 across all seven frozen coupling orientations.

## Repository limitation

The public `SymC-Universe/Chemistry` landing repository does not currently contain the frozen Release 38 core files. The adapter and its tests are versioned here, and this manifest pins the exact tested Release 38 package by SHA-256.

The connected GitHub tool does not expose repository creation or visibility mutation, so a new private reproducibility repository cannot be created mechanically from this session.

Do not move manuscript source into this public repository.

# HCN-HNC first native molecular modal-Capital-Chi record

**Status:** P0-Q native modal-output record with validated reaction path.

## Provenance

All calculations use the same Rowan AIMNet2 level, `aimnet2_wb97md3`.

- HCN R0: `042c5369-54c1-4626-ba3d-8f3709e2e4de`
- HNC R0: `cf1a011d-e312-4950-8250-3df1b709febc`
- TS search R1: `c2653b1c-5fc8-49ca-8f24-9b465bdb01bf`
- TS frequency validation R2: `1d723abc-d91a-4a36-9be5-0fb93dabcf4e`
- IRC R3: `261b701c-f238-4d45-b39a-2f95b6e8f621`

R2 independently validates exactly one imaginary TS mode at -2006.267 cm^-1.
R3 returns optimized HCN and HNC endpoint frequency fingerprints matching the independently optimized R0 minima.

## Energetics at this computational level

- HCN: -93.493238 Ha
- HNC: -93.471647 Ha
- TS: -93.410584 Ha
- electronic barrier from HCN: 51.866 kcal/mol
- electronic barrier from HNC: 38.318 kcal/mol
- HNC-HCN electronic energy difference: 13.549 kcal/mol

These are method-level benchmark values, not experimental claims.

## Declared cross-configuration modal metric

Atom mapping is fixed H,C,N.

Each endpoint is:
1. mass-centred;
2. optimally rigidly aligned to the TS using a proper mass-weighted Kabsch rotation;
3. compared in the atomic-mass Cartesian metric.

The HCN/HNC linear bend pair is exactly degenerate and is therefore reported as a 2D subspace. Individual bend-vector identities are not promoted.

## Basis-invariant carrier -> TS-mode weights

| endpoint carrier | unstable TS | stable 2268 | stable 3420 |
|---|---:|---:|---:|
| HCN bend subspace | 0.09984 | 0.03908 | 0.74963 |
| HCN CN stretch | 0.13276 | 0.86109 | 0.00353 |
| HCN CH stretch | 0.71163 | 0.08760 | 0.05119 |
| HNC bend subspace | 0.12362 | 0.04726 | 0.66514 |
| HNC CN stretch | 0.14918 | 0.84395 | 0.00186 |
| HNC NH stretch | 0.68675 | 0.09365 | 0.05699 |

Thus the unstable reaction direction is dominated by the terminal X-H stretch carrier from either side, while a different stable TS mode is dominated by the CN stretch and another by the endpoint bend subspace.

This is a modal correspondence architecture. A list of scalar frequencies alone does not encode it.

## Lowercase chi

No mode-resolved damping matrix/lifetime is supplied by this gas-phase electronic-structure calculation.

Therefore mechanical lowercase chi_i is **unavailable** and is not invented.

The result demonstrates the intended separation:

- capital Chi: modal geometry/correspondence is available;
- lowercase chi: scalar damping coordinate is unavailable.

## Record completeness

Rowan exposes exact optimized structures, frequencies, reduced masses, force constants, and normal-mode displacement vectors, but not the raw Cartesian Hessian through the available connector interface.

Accordingly this is called a **native modal-output record**, not falsely labeled as a raw-Hessian record.

The returned full vibrational spectral decomposition is sufficient for the reported modal correspondence, while the generator/Hessian field remains explicitly unavailable.

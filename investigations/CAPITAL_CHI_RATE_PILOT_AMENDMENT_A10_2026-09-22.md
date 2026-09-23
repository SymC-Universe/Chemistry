# Capital-Chi rate pilot amendment A10: ttD related-solute replication

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE ttD CALCULATION

## Source

Same JACS 2024 source as A9: DOI 10.1021/jacs.4c09134.

## Replication target

Use trans,trans-diphenylbutadiene (ttD) as a distinct related solute measured in the same experimental platform.

Exact source tables:
- Table 4: ttD photoisomerization time tau_iso;
- Table 5: ttD rotational time tau_R.

Solvents: he, hp, oc, dc, hd, ch.
Temperatures: 293, 303, 313, 323 K.

## Frozen variables and models

Target:
[
y=-ln	au_{iso}.
]

Environment feature:
[
x=ln	au_R.
]

Temperature control:
[
z=1/T.
]

Use the identical models from A9A:
- T0 intercept only;
- T1 temperature only;
- X1 rotation only;
- TX temperature + rotation.

## Frozen validation

1. leave-one-condition-out;
2. leave-one-solvent-out;
3. within-solvent log-rate versus log-rotation trajectory diagnostics.

Primary replication statistic:
[
Delta MSE_{X|T}=MSE(T1)-MSE(TX)
]
under leave-one-solvent-out validation.

## Interpretation rules

- Positive Delta MSE under leave-one-solvent-out counts as related-solute internal replication of the A9 architecture effect.
- Null or negative Delta MSE is retained as replication failure.
- Results are not pooled with tS to improve significance.
- No solvent-specific corrections, nonlinear terms, or source-fit kinetic parameters are introduced.
- This remains P1/P1+ internal replication, not P2 cross-source validation.

# A18 result: reactive-normal-mode coupling redistribution

**Status:** controlled theoretical modal benchmark.

## Frozen scalar quantities

Every case has:
- bare barrier frequency omega_b = 1;
- bath frequency spectrum {0.5, 3.0};
- total scalar coupling norm S = sum(c_j^2 / omega_j^2) = 1.

The coupling vector is rotated through the two-dimensional bath-mode space while preserving S.

## Result

| phi | P_q in unstable mode | kappa_GH |
|---:|---:|---:|
| 0 | 0.6213 | 0.6248 |
| 15 | 0.6517 | 0.6441 |
| 30 | 0.7315 | 0.7002 |
| 45 | 0.8220 | 0.7829 |
| 60 | 0.8827 | 0.8685 |
| 75 | 0.9093 | 0.9307 |
| 90 | 0.9160 | 0.9531 |

The total scalar coupling strength is invariant, but redistributing that coupling between a slow and fast bath mode changes:
- the full Hessian eigenbasis;
- the composition of the unstable collective mode;
- reaction-coordinate participation P_q;
- the Grote-Hynes transmission factor.

The transmission factor changes by approximately 52.5% from phi=0 to phi=90 despite identical omega_b, bath spectrum, and scalar coupling norm.

## Interpretation

This is a direct controlled example of information loss under scalar compression.

The scalar quantity S says the two endpoints have identical total coupling strength.

Modal Capital Chi distinguishes them because the coupling vector and unstable-mode eigenvector differ.

The kinetic transmission follows the modal organization, not the scalar norm alone.

## Relation to scalar chi

No barrier-top mechanical chi is manufactured here. The Chemistry inheritance contract already forbids that shortcut.

This benchmark instead shows why a modal object remains meaningful at the saddle even when the stable-well scalar chi coordinate does not exist there.

## Promotion limit

Controlled mechanism only. Empirical chemical validation still required.

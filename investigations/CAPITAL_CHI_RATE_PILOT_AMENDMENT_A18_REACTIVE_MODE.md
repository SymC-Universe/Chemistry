# A18: Reactive-normal-mode coupling redistribution benchmark

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE CALCULATION

## Literature basis

Grote and Hynes (J. Chem. Phys. 1981, *Reactive modes in condensed phase reactions*) establish that, when reactive and nonreactive modes are coupled, the deviation of the rate from transition-state theory is governed by the effective reactive normal mode rather than by an uncoupled local coordinate alone.

This benchmark uses the standard bilinear harmonic-bath saddle Hamiltonian that yields the Grote-Hynes reactive root.

## Purpose

Test whether two systems with the same:
- local bare barrier curvature;
- bath-mode frequency spectrum;
- total scalar coupling strength;

but different **distribution/orientation of coupling across bath modes** have different reactive collective modes and different transmission factors.

## Frozen model

Dimensionless mass-weighted saddle potential:

[
U(q,x_1,x_2)
=
-\frac12\omega_b^2q^2
+
\sum_{j=1}^2
\frac12\omega_j^2
\left(x_j-\frac{c_j}{\omega_j^2}q\right)^2.
]

Fixed:
- omega_b = 1;
- bath frequencies omega_1 = 0.5, omega_2 = 3.0;
- scalar coupling norm
  [
  S=\sum_j c_j^2/\omega_j^2=1.
  ]

Redistribute the fixed coupling norm with angle phi:

[
g_1=\cos\phi,\qquad g_2=\sin\phi,
]

[
c_j=\omega_j g_j.
]

Thus (g_1^2+g_2^2=1) for every case.

Frozen phi values:
0, 15, 30, 45, 60, 75, 90 degrees.

## Modal Capital Chi

For each phi, record the full mass-weighted Hessian, its indexed eigenvalues/eigenvectors, and the normalized unstable-mode vector.

Capital Chi changes through:
- coupling-vector orientation;
- unstable-mode composition;
- stable-subspace composition.

The scalar coupling norm S does not change.

## Kinetic observable

Let the negative Hessian eigenvalue be (-\lambda_r^2). The harmonic Grote-Hynes transmission factor is

[
\kappa_{GH}=\lambda_r/\omega_b.
]

Compare kappa across phi.

Also record the reaction-coordinate participation

[
P_q=|v_{unstable,q}|^2.
]

## Falsification

If kappa is invariant under redistribution of the fixed coupling norm, then this benchmark provides no modal information beyond the scalar norm.

If kappa changes while S, omega_b, and the bath spectrum remain fixed, the benchmark shows that modal coupling organization carries rate information lost by the scalar coupling total.

## Promotion limit

Controlled theoretical modal benchmark only. No empirical rate-law claim.

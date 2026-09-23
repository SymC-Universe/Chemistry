# A18 modal-adapter integration check

**Status:** PASS

The additive Capital-Chi modal adapter was applied to the frozen A18 reactive-normal-mode benchmark without changing the A18 model.

For each coupling orientation:

- the declared physical reaction coordinate was q = (1,0,0);
- the adapter identified the positive real pole belonging to the unstable reaction subspace;
- the mass-metric spectral-subspace projection was compared with the independently computed Hessian unstable-eigenvector participation P_q;
- the adapter retained lowercase mechanical chi only on the two positive-stiffness stable carriers.

Across all seven frozen orientations, the adapter projection agrees with the direct P_q calculation to better than 1e-10.

This closes an implementation bridge that the scalar-only reporting path could not:

> capital Chi can represent and quantify reaction-subspace geometry at a saddle even though a stable-well mechanical chi is not defined for the unstable direction.

No barrier chi is introduced.

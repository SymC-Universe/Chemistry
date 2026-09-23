# Capital Chi as a rate-relevant architecture: pilot investigation

**Date:** 22 September 2026  
**Status:** P0-D / mathematical bridge established; heterogeneous empirical pilot supportive; direct trajectory validation blocked by raw-data access in the present runtime.

## 1. Question

The prior scalar question, whether local mechanical $\chi$ alone predicts chemical reaction rate, is closed negatively by the ChemSA scope proof and barrier counterexamples. The present investigation asks a different question:

> **Does the broader reconstructed stability architecture $\Chi$ contain a rate-relevant projection that adds kinetic information once the barrier/path physics is supplied independently?**

This is not a claim that $\Chi$ alone determines an absolute rate. The barrier, temperature, path geometry, and native kinetic theory remain independent inputs.

## 2. GOM firewall

Capital $\Chi$ is treated as a relationship among scalar/modal state, carrier structure, coupling, memory, environmental embedding, and whole-system organization. The target observed rate is forbidden from entering the construction of the predictor. Rate-derived barriers, target-rate-fitted friction, residual-selected features, and post-hoc redefinition of $\Chi$ are refused.

The investigation also refuses to rename ordinary tunneling or recrossing coefficients as $\Chi$. Those are native kinetic quantities. They are used only as a control showing that dynamical architecture beyond a classical barrier carries rate information.

## 3. Native-theory bridge

Netz (2026, Physical Review Research, DOI 10.1103/vrtr-9dby) derives, to first order in the cumulant construction and with the stated saddle-point conditions, an Arrhenius barrier-crossing form

$$
\tau_{\rm MFP} \simeq \tau_{\rm rel}\,\Phi[U]\,e^{\beta U_0},
$$

with the rate-relevant relaxation functional

$$
\boxed{\Pi_{\rm rate}[\Chi] \equiv \tau_{\rm rel}
=\frac{2}{C(0)^2}\int_0^\infty C(t)^2\,dt}.
$$

This is attractive for the present purpose because $C(t)$ can be determined from local/equilibrium relaxation trajectories rather than the global reaction waiting time. The barrier/path factor remains external.

## 4. Markovian scalar limit

For a harmonic Markovian well, Netz gives

$$
\tau_{\rm rel}=\frac{\gamma}{K}+\frac{m}{\gamma}.
$$

With

$$
\omega_0=\sqrt{K/m},\qquad \chi=\frac{\gamma}{2\sqrt{mK}},
$$

this becomes exactly

$$
\boxed{\omega_0\tau_{\rm rel}=2\chi+\frac{1}{2\chi}}.
$$

Consequences:

- $\chi$ alone does **not** determine a dimensional rate timescale; $\omega_0$ is also required.
- At fixed $\omega_0$ and fixed barrier/path factor, the relaxation-prefactor optimum is $\chi=1/2$, not the critical-damping boundary $\chi=1$.
- This is Kramers turnover physics, not an exceptional-point optimum.

## 5. Single-exponential-memory extension

For $\Gamma(t)=(\gamma/\tau)e^{-t/\tau}$, define the reference integrated-friction ratio and memory ratio

$$
\chi_{\rm ref}=\frac{\gamma}{2\sqrt{mK}},\qquad r=\tau\omega_0.
$$

For $r>0$, $\chi_{\rm ref}$ is **not** reported as a ChemSA mechanical damping ratio. It is a reference ratio inside the non-Markovian native model. The dimensionless pole equation is

$$
rz^3+z^2+(r+2\chi_{\rm ref})z+1=0.
$$

A state-space/Lyapunov evaluation of the squared-correlation integral reduces the published three-pole expression to

$$
\boxed{
\omega_0\tau_{\rm rel}
=2\chi_{\rm ref}+\frac{1+r^2}{2\chi_{\rm ref}}-r
}.
$$

This recasting was independently checked against the full rational transfer function at multiple $(\chi_{\rm ref},r)$ points with relative errors below numerical precision. It also reproduces both the published Markovian limit and the published zero-mass-after-regularization expression. The underlying physics is established non-Markovian rate theory; novelty of this compact dimensionless recasting is **not claimed**.

Useful consequences inside this declared model:

$$
\chi_{\rm ref}^*(r)=\frac12\sqrt{1+r^2},
$$

for the friction-ratio value minimizing $\tau_{\rm rel}$ at fixed $r$, and

$$
r^*(\chi_{\rm ref})=\chi_{\rm ref},
$$

for the memory ratio giving the strongest memory acceleration at fixed $\chi_{\rm ref}$. Relative to the Markovian case,

$$
\Delta(\omega_0\tau_{\rm rel})
=\frac{r(r-2\chi_{\rm ref})}{2\chi_{\rm ref}},
$$

so the model predicts a memory-accelerated region $0<r<2\chi_{\rm ref}$ and a memory-slowed region $r>2\chi_{\rm ref}$.

## 6. Existing-Atlas native-correction control

Nine coordinates across five reaction families in Barrier-Height/Rate Atlas v0.9 already contain a classical/no-tunneling baseline plus independently computed tunneling and, for the enzyme family, recrossing corrections. These rows were selected because the required components existed before this investigation, not because of their residuals.

This is a **control**, not a definition of $\Chi$. It asks whether architecture beyond the classical barrier matters at all before pursuing a new stability-architecture projection.

### Result

At row level, the mean absolute log error changes from 2.869023 to 0.454029, corresponding to geometric factors 17.620x and 1.575x.

After collapsing repeated temperatures/isotopologues to one median result per family, the mean absolute log error changes from 2.951757 to 0.607052, corresponding to geometric factors 19.140x and 1.835x. All 5/5 families improve.

The native log correction $\ln(\kappa_{\rm tun}\kappa_{\rm trans})$ correlates with the observed correction required relative to the classical baseline at $r=0.965$ across rows and $r=0.917$ after family collapse. These correlations are descriptive only because the sample is small, heterogeneous, and the correction factors are parts of established native rate theories.

## 7. Real-system collision

Independent literature supports the proposed direction without establishing the compact $\Chi$ projection:

- Roux (2022), DOI 10.1063/5.0084209: propagator eigenstructure, committor geometry, and reactive paths contain kinetic information beyond a simple local coordinate.
- Brünig, Netz & Kappler (2022), DOI 10.1103/physreve.106.044133: well/barrier memory architecture changes the rate-limiting regime; a local well damping descriptor is insufficient.
- Daldrop/Brünig/Netz pair-reaction work, DOI 10.1021/acs.jpcb.2c05923: memory, inertia and potential shape make opposing contributions to aqueous pair-reaction kinetics; the GLE parameters were obtained without target-rate fitting.
- Dalton, Kiefer & Netz (2024), DOI 10.1038/s41467-024-48016-7: memory kernels and free-energy profiles extracted independently from molecular trajectories explain large deviations from Markovian Kramers predictions in alkane isomerization. Raw butane/decane trajectories are deposited at DOI 10.5281/zenodo.10885500.
- Dalton et al. protein-folding work, DOI 10.1073/pnas.2220068120: including independently extracted memory-dependent friction improves folding-time prediction relative to a Markovian model.

## 8. Strongest claim licensed now

The current evidence licenses the following bounded statement:

> **Reaction rate is not determined by local scalar $\chi$. Under explicit native-model assumptions, however, the broader dynamical architecture admits a rate-relevant relaxation projection $\Pi_{\rm rate}[\Chi]=\tau_{\rm rel}$ that multiplies an independently specified barrier/path factor. In the single-exponential-memory GLE, this projection reduces to a compact function of an integrated-friction reference ratio and a memory ratio.**

This is a native-model result and verified algebraic recasting, not yet an empirical cross-chemistry rate law.

## 9. Direct empirical test still required

The strongest next test uses the deposited Dalton et al. trajectories without fitting transition times:

1. preregister basin boundaries and local-equilibrium segments without inspecting MFPT results;
2. compute $C(t)$ from local equilibrium fluctuations;
3. compute $\tau_{\rm rel}=2\int[C(t)/C(0)]^2dt$;
4. reconstruct $U(q)$ independently from the equilibrium coordinate distribution;
5. evaluate the full integral rate expression before using the saddle approximation;
6. compute MFPT from held-out transition trajectories;
7. compare Markovian versus $\Pi_{\rm rate}[\Chi]$ prediction across butane/decane and viscogenic conditions.

The raw Zenodo trajectory package could not be retrieved through the current runtime despite web and browser-automation attempts. **This is the present execution blocker.** Plot digitization is refused because the exact deposited data exist.

## 10. Bibliographic erratum discovered

Barrier Atlas v0.9 lists the Meisner-Kästner H2+OH source with DOI `10.1063/1.4952649`. The verified published DOI is `10.1063/1.4948319`. Frozen v0.9 is not edited in place; this should be carried as an additive bibliographic correction in the next release.

## 11. Decision state

- **$\Chi$ alone as an absolute rate predictor:** not supported / not the current hypothesis.
- **Barrier/path physics + rate-relevant $\Chi$ projection:** mathematically supported in a declared non-Markovian barrier-crossing model and consistent with independent kinetics literature.
- **Cross-chemistry empirical prediction:** PENDING direct trajectory-level validation and larger independent holdouts.
- **Scalar $\chi=1$ as rate optimum:** not supported; in the Markovian relaxation-prefactor limit the optimum is $\chi=1/2$.
- **Finite-memory reference ratio:** do not call $\chi_{\rm ref}$ a licensed mechanical $\chi$.

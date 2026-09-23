# Multi-memory architecture test

**Date:** 22 September 2026  
**Status:** constructive model result; literature-consistent; not a cross-chemistry rate law.

## Question

Does a total integrated-friction scalar determine the rate-relevant relaxation projection when the environment has memory?

## Native model

For a harmonic generalized Langevin coordinate with exponential memory components

$$
\Gamma(t)=\sum_i \frac{\gamma_i}{\tau_i}e^{-t/\tau_i},
$$

define

$$
\chi_i=\frac{\gamma_i}{2m\omega_0},
\qquad
r_i=\tau_i\omega_0.
$$

The total integrated-friction reference ratio is

$$
\chi_{\rm total}=\sum_i\chi_i.
$$

For a declared component set, the normalized position-correlation transfer function is evaluated and

$$
\Pi_{\rm rate}[\Chi]
=\tau_{\rm rel}
=2\int_0^\infty [C(t)/C(0)]^2dt
$$

is computed by a state-space Lyapunov/H2 calculation.

## Constructive counterexample at fixed scalar friction

Holding $\omega_0$, barrier/path factor, and $\chi_{\rm total}=1$ fixed:

| architecture | memory components $(\chi_i,r_i)$ | $\omega_0\tau_{\rm rel}$ | relative rate-prefactor $1/(\omega_0\tau_{\rm rel})$ |
|---|---|---:|---:|
| fast memory | $(1,0.1)$ | 2.4050 | 0.4158 |
| intermediate memory | $(1,1)$ | 2.0000 | 0.5000 |
| slow memory | $(1,10)$ | 42.5000 | 0.02353 |

The slow-memory and fast-memory systems have the same integrated friction and the same local harmonic scale but differ by a factor of **17.67** in the rate-relevant relaxation prefactor.

Therefore total integrated friction, and any scalar reference ratio formed from it, is insufficient to determine the relaxation-controlled prefactor.

## Stronger compression test

Even fixing both $\chi_{\rm total}=1$ and the friction-weighted mean memory ratio $\bar r=1$ does not fully determine the projection:

- single memory $(1,1)$: $\omega_0\tau_{\rm rel}=2.0000$;
- split memory $(0.5,0.1)+(0.5,1.9)$: $2.05435$;
- extreme split $(0.5,0.0001)+(0.5,1.9999)$: $2.09995$.

The distribution of memory times can therefore matter beyond total friction and the first memory moment.

## Independent literature collision

This behavior is consistent with established non-Markovian barrier-crossing work:

- Kappler, Hinrichsen & Netz (2019), DOI 10.1140/epje/i2019-11886-7: for two-time-scale memory, the faster memory component can dominate MFPT and total integrated friction alone is insufficient.
- Kappler et al. (2018), DOI 10.1063/1.4998239: at fixed integrated friction, changing the memory time generates memory-induced acceleration at intermediate memory and quadratic slow-down at long memory.
- Lavacchi, Kappler & Netz (2020), DOI 10.1209/0295-5075/131/40004: multi-exponential memory with unequal amplitudes and time scales requires retention of component structure.

## Licensed conclusion

> **Within memory-bearing GLE barrier-crossing models, rate-relevant relaxation is an architectural property of the memory spectrum, not a function of total integrated friction alone.**

This supports the capital-$\Chi$ framing because the relevant information is relational/multi-timescale. It does not establish that capital $\Chi$ by itself determines an absolute chemical reaction rate; the independently specified barrier/path factor remains required.

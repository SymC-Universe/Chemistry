# Approach-Region Dynamics and Rate Turnover in Thermally Activated Barrier Crossing

This repository supports the manuscript:

**Approach-Region Dynamics and Rate Turnover in Thermally Activated Barrier Crossing**  
Nate Christensen

The project develops a reaction-dynamical descriptor for thermally activated barrier crossing across electron transfer, proton-coupled electron transfer, and heterogeneous catalysis.

The central quantity is the dimensionless approach-region damping ratio

```math
\chi_0 = \frac{\Gamma_{\mathrm{eff}}}{2\Omega_0}
```

where \(\Gamma_{\mathrm{eff}}\) is the total projected dissipation rate and \(\Omega_0\) is the stable precursor-well approach frequency.

The framework distinguishes approach-region dynamics from saddle-point transition-state dynamics. The exceptional-point condition \(\chi_0 = 1\) belongs to the stable precursor-well generator, not to the inverted saddle itself.

---

## Core idea

Thermodynamic rate theory describes barriers, driving forces, and reaction energetics. This work adds a complementary dynamical coordinate describing whether a reactive trajectory commits productively, recrosses, or becomes overdamped and sluggish.

The three operational regimes are:

| \(\chi_0\) range | Regime | Dynamical behavior | Chemical consequence |
|---|---|---|---|
| \(\chi_0 < 0.8\) | Underdamped | Oscillatory approach, recrossing likely | Back-transfer, weak activation, poor commitment |
| \(0.8 \leq \chi_0 \leq 1.3\) | Near-critical | Fast monotonic commitment | Efficient ET, concerted PCET, high catalytic turnover |
| \(\chi_0 > 1.3\) | Overdamped | Monotonic but sluggish | Solvent-controlled ET, inhibited PCET, over-promoted or poisoned catalysis |

The window \(0.8 \leq \chi_0 \leq 1.3\) is treated as an operational near-critical band rather than an exact universal optimum.

---

## Scope

The framework applies to classical, thermally activated barrier crossing in systems where:

- a dominant reactive coordinate can be identified,
- the approach region is locally approximated by a stable damped generator,
- friction is near-Markovian or weakly non-Markovian,
- tunneling is not the dominant pathway,
- thermodynamic parameters are independently acceptable.

The framework is not intended to replace transition-state theory, Marcus theory, PCET theory, d-band theory, BEP scaling, adsorption-energy descriptors, or electronic-structure calculations. Instead, it provides a complementary reaction-dynamical coordinate for comparing commitment versus recrossing under otherwise comparable thermodynamic conditions.

---

## Estimator routes

The manuscript develops three calibrated routes from standard observables or computational quantities to \(\chi_0\).

### Route A: Spectroscopic linewidths

For operando IR or Raman measurements:

```math
\chi_{\mathrm{spec}} = \frac{\Delta\tilde{\nu}_L}{2\tilde{\nu}}
```

where \(\Delta\tilde{\nu}_L\) is the Lorentzian linewidth component and \(\tilde{\nu}\) is the vibrational frequency.

This route is valid only when homogeneous broadening dominates. Voigt or Fano fitting may be required.

---

### Route B: Solvent relaxation

For electron-transfer and PCET systems:

```math
\Gamma_{\mathrm{eff}} = \Omega_s^2 \tau_L
```

so that slower solvent relaxation generally increases \(\chi_0\). Relative comparisons are preferred:

```math
\frac{\chi_{\mathrm{ET}}^{(A)}}{\chi_{\mathrm{ET}}^{(B)}} \approx
\frac{\tau_L^{(A)}}{\tau_L^{(B)}}
```

with equality only when solvent bath frequencies are comparable.

Route B does not replace established solvent-dynamical descriptors such as longitudinal relaxation times or dielectric friction coefficients. It maps them onto a dimensionless coordinate by comparing solvent dissipation against intrinsic precursor-well stiffness.

---

### Route C: DFT electronic friction

For surface catalysis with electronic friction or Newns-Anderson hybridization data:

```math
\chi_{\mathrm{DFT}} =
\frac{\Gamma_{\mathrm{int}}+\Gamma_{\mathrm{cat}}}{2hc\tilde{\nu}}
```

Here \(\Gamma_{\mathrm{cat}}\) is an energy broadening in eV, not a time-domain friction coefficient. Ground-state Route C estimates are interpreted as lower-bound proxies when the reactive bond softens along the approach coordinate.

---

## Worked examples

The repository supports calculations and figures for:

### Electron transfer

A solvent-dependent ET example illustrating how longitudinal relaxation time and solvent bath frequency affect relative \(\chi_{\mathrm{ET}}\), with emphasis on the limits of cross-class solvent comparisons.

### Proton-coupled electron transfer

A PCET mechanism-selection example showing how isotope substitution can raise \(\chi_{\mathrm{eff}}\) in the proton-dominated limit:

```math
\chi_{\mathrm{eff}}^D \approx \sqrt{2}\,\chi_{\mathrm{eff}}^H
```

The predicted signature is a non-monotonic KIE feature as environmental friction moves the system across the near-critical window.

### Heterogeneous catalysis

A Route C analysis of N\(_2\) activation on Fe surfaces, including unpromoted Fe, Fe(110), and K-promoted Fe(111). The framework does not replace d-band theory, BEP scaling, or adsorption-energy descriptors. It provides a reaction-dynamical coordinate that may account for residual activity variation among systems with comparable thermodynamic descriptors.

---

## Repository contents

Typical contents include:

- main manuscript source files,
- supplementary derivations,
- reproducibility guide,
- Python scripts used to generate figures,
- figure source data,
- generated manuscript figures.

Key outputs include:

- dynamical efficiency schematic,
- Fe/BEP dynamical outlier figure,
- standard-state lattice \(\chi\)-map,
- estimator-route tables,
- falsification and robustness calculations.

---

## Reproducibility

The code in this repository is intended to reproduce the numerical values, tables, and figures reported in the manuscript and supplementary information.

Users should treat the repository code and deposited data files as the canonical computational source rather than copying code from PDF-rendered listings, which may introduce formatting artifacts.

---

## Data availability

Supporting data and code archived in this repository.

```

Repository:

```text
https://github.com/SymCUniverse/Chemistry
```

---

## Citation

If using this repository, please cite the associated manuscript:

Christensen, N.  
**Approach-Region Dynamics and Rate Turnover in Thermally Activated Barrier Crossing.**

A complete archival release, including manuscript, supplementary materials, data, and code, is available through Zenodo.

---

## License

Please see the repository license file for terms of use.

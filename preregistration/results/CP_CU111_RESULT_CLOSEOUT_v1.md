# Cp/Cu(111) preregistered perturbation-recovery result closeout v1

## Frozen-result disposition
- CP-PR-01 local recovery equivalence: **FAIL**
- CP-PR-02 embedding-dependent kinetics: **PASS**
- CP-PR-03 joint frozen claim: **FAIL**

No frozen threshold, model parameter, perturbation amplitude, endpoint, fitting interval, or expected direction was changed after production output was opened.

## CP-PR-01
- cross-embedding normalized recovery RMS: 0.0971801532
- bootstrap 95% interval: [0.0674107837, 0.1320336430]
- frozen equivalence margin: 0.05
- sign-symmetry RMS, 40 meV: 0.0289998339
- sign-symmetry RMS, 55 meV: 0.0498081269
- first zero crossing, 40 meV: 0.255 ps
- first zero crossing, 55 meV: 0.255 ps

The frozen equivalence rule is violated because the point estimate and bootstrap interval exceed 0.05. The identical zero-crossing time is preserved as an observed component result but cannot rescue CP-PR-01.

## CP-PR-02
- D_40 = 6.2614031759e-09 m^2 s^-1
- D_55 = 3.8065097025e-09 m^2 s^-1
- bootstrap 95% interval for log(D_55/D_40): [-0.5755382892, -0.4244586332]
- median FPT_40 = 2.2285 ps
- median FPT_55 = 3.5810 ps
- bootstrap 95% interval for log(FPT_55/FPT_40): [0.4241645059, 0.5237063113]
- censored fraction: 0 for both embeddings

Both frozen directional kinetic criteria pass.

## Promotion consequence
Under MFR-14, CP-PR-03 remains failed. The preregistered statement that matched local curvature and damping would yield equivalent early recovery across the two embeddings is not supported at the frozen perturbation and thermal conditions. No retuning or narrower post-result window is authorized under this freeze.

A possible post-result discovery is that the shared local mode fixes at least part of the early morphology (the zero crossing is identical), while the different embedding modifies the finite-amplitude thermal recovery trajectory before long-time transport. This is **not** promoted by this result record and would require a new frozen hypothesis and untouched decisive test if pursued.

## Production artifact hashes
- 40 meV NPZ: dc23b6ab3adb9aa3ade2d3c1a6c0cebb3544138a522dac10a7b38d1cd7997c3f
- 40 meV metadata: b093b5aa6379deae4f07543996687892451731155774a197fdd88eaa167e5961
- 55 meV NPZ: 746bccb282f5a26143e77bcc19407ce1942f79c39ddd63e61fd986aeb5ef187f
- 55 meV metadata: 42a1a0e66c15f39f212e6a4fbb0e1b88df985de94efbd7bcc3606745292d684b

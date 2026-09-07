# System 3 Parallel Selection Strategy v0.1

**Status:** prospective strategy only
**Computation:** not launched
**Purpose:** prepare a third system while System 2 begins, but make System 3 a deliberate contrast/limit test rather than a third attempt to collect a favorable result.

## 1. Scientific role

System 1, Na/Cu(001), is the development pilot.

System 2, provisionally CO/Cu(111), is the first external validation target for the layered chemistry pipeline.

System 3 should have a different purpose: test portability and expose limits. It should preferably differ from Systems 1 and 2 on at least two physically meaningful axes, for example:

- adsorbate class;
- substrate element;
- surface symmetry;
- classical versus nuclear-quantum diffusion;
- dominant dissipation channel;
- atomic versus molecular reaction coordinate.

Expected agreement with ChemSA is forbidden as a selection criterion.

## 2. Parallelism rule

The System 3 **source and selection audit may run while System 2 is being prepared or computed**.

The full System 3 production calculation should not begin until:

1. the generic layer contracts are frozen;
2. System 2's electronic-structure/method protocol is frozen for its own physics;
3. reusable Reaction-Path Engine code has been separated from Na/Cu-specific assumptions sufficiently to prevent copy-and-edit drift;
4. the System 3 protocol is frozen independently of its held-out kinetic outcomes.

This allows useful calendar-time overlap without debugging two new physical implementations simultaneously.

## 3. Eligibility rule

A System 3 candidate should satisfy:

1. a simple atomic, diatomic, or otherwise computationally tractable adsorbate/reaction coordinate;
2. a well-defined surface state and elementary diffusion/reaction path;
3. a published kinetic/diffusion data lineage that can be retained as a comparator;
4. published barrier/PES or first-principles literature sufficient to establish feasibility, without requiring that the published barrier be used to tune the new calculation;
5. at least one plausible well-mode/dissipation observable or a clearly informative failure of such a mapping;
6. open or otherwise verifiably accessible final published evidence sufficient for the audit;
7. no selection based on closeness to chi = 1, agreement with SymC, or prior residual size.

## 4. Initial metadata-level shortlist

### H/Pt(111) — leading contrast candidate, not selected

Why it is scientifically valuable:
- atomic adsorbate, but a different substrate from Cu;
- well-established nearest-neighbor surface diffusion literature;
- nuclear quantum effects and tunneling are known to matter, making it a stringent limit test for a classical/harmonic reaction-path treatment;
- published first-principles/force-field work and experimental surface-diffusion data exist.

Primary published evidence located in the exploratory audit includes a Physical Review Letters study of the quantum contribution to activated H/Pt(111) motion and a later open first-principles/active-learning dynamics study.

**Risk:** the nuclear-quantum problem may require path-integral or equivalent treatment before a classical TST comparison is scientifically adequate. This is a feature for limit mapping, but increases computation and method complexity.

### K/Cu(001) — engineering-easy but scientifically less independent

Why it is useful:
- analytical DFT PES and barrier geometry are already published;
- surface and alkali machinery is close to Na/Cu(001), so implementation would be comparatively cheap.

Why it is weaker as System 3:
- same Cu(001)/alkali family as the development pilot;
- the precise diffusion friction in the published HeSE analysis was fitted to the same dynamics, limiting independence;
- it tests reproducibility/portability more than breadth.

### CO/Pt(111) or another simple CO/metal surface — intermediate contrast

Why it is useful:
- retains the same molecular adsorbate as System 2 while changing the substrate;
- can isolate substrate dependence.

Why it is not currently preferred:
- CO adsorption on transition metals carries known electronic-structure site-preference challenges;
- a second CO system immediately after CO/Cu(111) may test method portability more than physical breadth.

## 5. Current recommendation

Do **not** select System 3 by judgment today.

Freeze a small eligible pool after a publication/source audit and use an objective prospective selection rule. Record:
- complete candidate list;
- inclusion/exclusion decisions before numerical outcome extraction where possible;
- selection seed or deterministic rule;
- hash of the canonical candidate list;
- exact selected target;
- all candidates rejected after selection and the pre-existing rule that forced rejection.

H/Pt(111) is presently the strongest **contrast hypothesis** to investigate, not the selected system.

## 6. Exposure warning

Exploratory literature review has already exposed some published H/Pt(111) and K/Cu(001) kinetic/barrier information. Therefore future System 3 claims should not use the word 'blind' unless a genuinely withheld dataset is defined and kept inaccessible during method construction.

The defensible protection is prospective method freezing and held-out comparison, not pretending published outcomes were unknown.

## 7. Decision point

Before launching a System 3 calculation, issue a `SYSTEM3_SELECTION_RECORD` containing the frozen eligibility rule, candidate pool, objective selection procedure, source identities, exposed-versus-held-out fields, and the intended scientific role (`contrast`, `limit`, or `portability`).
"""Additive modal-Capital-Chi reporting adapter for ChemSA Release 38.

This module DOES NOT modify ChemSA's frozen classification engine.  It assembles
already-authoritative spectral, mechanical-scalar, and response-geometry objects
into an explicit scalar-to-carrier modal record.

Capital Chi is represented as modal/vector information.  It is not scalarized.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import numpy as np
from scipy.linalg import eigh

from chemsa_v3 import (
    DEGENERATE_W2_RTOL,
    MODAL_OFFDIAG_RTOL,
    scalar_reduction_valid,
)


@dataclass(frozen=True)
class SpectralCarrierRecord:
    group_id: int
    eigenvalue: complex
    algebraic_mult: int
    geometric_mult: int
    structure: str
    pole_angle_rho: Optional[float]
    mechanical_chi: Optional[float]
    chi_applicable: bool
    right_basis: Optional[np.ndarray]
    left_basis: Optional[np.ndarray]
    overlap_matrix: Optional[np.ndarray]
    overlap_normalized: Optional[float]
    condition_number: Optional[float]
    resolved: bool
    refusal: Optional[str]


@dataclass(frozen=True)
class MechanicalCarrierRecord:
    modal_index: int
    omega0: float
    mechanical_chi: float
    poles: tuple[complex, ...]
    temporal: str
    vector: np.ndarray
    assignment_residual: float
    basis_unique: bool
    subspace_members: tuple[int, ...]


@dataclass(frozen=True)
class DeclaredProjectionRecord:
    name: str
    norm: float
    mechanical_amplitudes: np.ndarray
    mechanical_participation: np.ndarray
    subspace_participation: tuple[tuple[tuple[int, ...], float], ...] = field(default_factory=tuple)
    individual_basis_invariant: bool = True
    refused: bool = False
    reason: str = ""


@dataclass(frozen=True)
class CapitalChiModalRecord:
    spectrum_id: str
    n_coordinates: int
    mass_condition_number: float
    certified_conditioning: bool
    conditioning_reason: str
    spectral_carriers: tuple[SpectralCarrierRecord, ...]
    mechanical_carriers: tuple[MechanicalCarrierRecord, ...]
    declared_projections: tuple[DeclaredProjectionRecord, ...] = field(default_factory=tuple)
    refusal_state: tuple[str, ...] = field(default_factory=tuple)

    @property
    def scalarized(self) -> bool:
        """Always False by construction.  Capital Chi is a modal record."""
        return False


def _as_real_symmetric(A: Any, name: str) -> np.ndarray:
    A = np.asarray(A)
    if np.iscomplexobj(A):
        resid = np.max(np.abs(A.imag)) / max(np.max(np.abs(A)), 1e-300)
        if resid > 1e-12:
            raise ValueError(f"{name} has non-negligible imaginary content")
        A = A.real
    A = np.asarray(A, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError(f"{name} must be square")
    if not np.allclose(A, A.T, atol=1e-10 * max(np.linalg.norm(A, 2), 1.0), rtol=0):
        raise ValueError(f"{name} must be symmetric for mechanical modal assignment")
    return A


def _mechanical_modal_basis(M: Any, C: Any, K: Any):
    """Reconstruct the mass-normalized mechanical carrier basis additively.

    This mirrors Release 38's _modal_factors basis convention, including the
    rotation that diagonalizes C inside degenerate stiffness blocks.  It returns
    (w2, Xr, Cr).  No ChemSA core state is modified.
    """
    M = _as_real_symmetric(M, "M")
    C = _as_real_symmetric(C, "C")
    K = _as_real_symmetric(K, "K")
    ok, why = scalar_reduction_valid(M, C, K)
    if not ok:
        return None, None, None, why

    w2, X = eigh(K, M)  # X.T M X = I
    n = len(w2)
    scale = max(float(np.max(np.abs(w2))), 1.0) if n else 1.0
    blocks = []
    i = 0
    while i < n:
        j = i + 1
        while j < n and abs(w2[j] - w2[i]) <= DEGENERATE_W2_RTOL * scale:
            j += 1
        blocks.append(list(range(i, j)))
        i = j

    Cm = X.T @ C @ X
    Xr = X.copy()
    for block in blocks:
        if len(block) == 1:
            continue
        sub = Cm[np.ix_(block, block)]
        sub = 0.5 * (sub + sub.T)
        _, V = eigh(sub)
        Xr[:, block] = X[:, block] @ V

    Cr = Xr.T @ C @ Xr
    off = Cr - np.diag(np.diag(Cr))
    if np.linalg.norm(off, 2) > MODAL_OFFDIAG_RTOL * max(np.linalg.norm(Cr, 2), 1e-300):
        return None, None, None, "reconstructed mechanical basis does not diagonalize C"
    return w2, Xr, Cr, "proportional damping"


def _mode_map_by_group(summary) -> dict[int, Any]:
    out = {}
    for mode in summary.modes:
        gid = int(getattr(mode, "group_id", -1))
        if gid in out:
            raise ValueError(f"duplicate ModeRecord group_id {gid}")
        out[gid] = mode
    return out


def _geom_map_by_group(geometries) -> dict[int, Any]:
    out = {}
    for geom in geometries:
        gid = int(getattr(geom, "group_id", -1))
        if gid in out:
            raise ValueError(f"duplicate ModeGeometry group_id {gid}")
        out[gid] = geom
    return out


def _mechanical_degenerate_subspaces(w2: np.ndarray, Cr: np.ndarray):
    """Return simultaneous (K,C) degeneracy groups in the reconstructed basis.

    Inside such a group, individual vectors are not uniquely physical: only the
    span is invariant.  This is distinct from a stiffness degeneracy that C
    resolves into unique damping carriers.
    """
    n=len(w2)
    if n == 0:
        return {}
    wscale=max(float(np.max(np.abs(w2))),1.0)
    cdiag=np.diag(Cr)
    cscale=max(float(np.max(np.abs(cdiag))),1.0)
    groups={}
    seen=set()
    for i in range(n):
        if i in seen:
            continue
        members=[j for j in range(n)
                 if abs(w2[j]-w2[i]) <= DEGENERATE_W2_RTOL*wscale
                 and abs(cdiag[j]-cdiag[i]) <= MODAL_OFFDIAG_RTOL*cscale]
        members=tuple(sorted(members))
        for j in members:
            seen.add(j)
            groups[j]=members
    return groups


def build_capital_chi_modal_record(
    M: Any,
    C: Any,
    K: Any,
    *,
    spectrum,
    summary,
    geometries,
    declared_vectors: Optional[Mapping[str, Any]] = None,
    assignment_rtol: float = 1e-8,
) -> CapitalChiModalRecord:
    """Assemble an explicit modal-Capital-Chi record from Release 38 outputs.

    Preconditions:
    - spectrum is the authoritative BalancedSpectrum used by classification;
    - summary is derived from that same spectrum;
    - geometries are derived from that same spectrum without a second QEP solve.

    The function refuses cross-object drift through spectrum_id checks.
    """
    M = _as_real_symmetric(M, "M")
    C = _as_real_symmetric(C, "C")
    K = _as_real_symmetric(K, "K")
    n = M.shape[0]
    if C.shape != M.shape or K.shape != M.shape:
        raise ValueError("M, C, K shape mismatch")

    sid = str(getattr(spectrum, "spectrum_id", ""))
    if not sid:
        raise ValueError("spectrum_id is required")
    if str(getattr(summary, "spectrum_id", "")) != sid:
        raise ValueError("SystemSummary does not come from the supplied BalancedSpectrum")
    for g in geometries:
        if str(getattr(g, "spectrum_id", "")) != sid:
            raise ValueError("ModeGeometry does not come from the supplied BalancedSpectrum")

    mode_by_group = _mode_map_by_group(summary)
    geom_by_group = _geom_map_by_group(geometries)
    expected = {int(cl.group_id) for cl in spectrum.clusters}
    if set(geom_by_group) != expected:
        raise ValueError("ModeGeometry set does not exactly cover the authoritative clusters")

    spectral = []
    refusals = []
    for cl in spectrum.clusters:
        gid = int(cl.group_id)
        geom = geom_by_group[gid]
        mode = mode_by_group.get(gid)
        if mode is None:
            # Conjugate display compression can mean only one of a conjugate
            # cluster pair is represented in SystemSummary.  Keep the carrier
            # geometry and leave scalar spectral fields unset rather than guess.
            rho = None
            mchi = None
            chi_ok = False
            structure = geom.structure
            alg = geom.algebraic_mult
            geo = geom.geometric_mult
        else:
            rho = mode.pole_angle_rho
            mchi = mode.mechanical_chi
            chi_ok = bool(mode.chi_applicable)
            structure = mode.structure
            alg = mode.algebraic_mult
            geo = mode.geometric_mult
        spectral.append(SpectralCarrierRecord(
            group_id=gid,
            eigenvalue=complex(geom.eigenvalue),
            algebraic_mult=int(alg),
            geometric_mult=int(geo),
            structure=str(structure),
            pole_angle_rho=None if rho is None else float(rho),
            mechanical_chi=None if mchi is None else float(mchi),
            chi_applicable=chi_ok,
            right_basis=None if geom.right_basis is None else np.asarray(geom.right_basis).copy(),
            left_basis=None if geom.left_basis is None else np.asarray(geom.left_basis).copy(),
            overlap_matrix=None if geom.overlap_matrix is None else np.asarray(geom.overlap_matrix).copy(),
            overlap_normalized=None if geom.overlap_normalized is None else float(geom.overlap_normalized),
            condition_number=None if geom.condition_number is None else float(geom.condition_number),
            resolved=bool(geom.resolved),
            refusal=geom.refusal,
        ))
        if not geom.resolved:
            refusals.append(f"group {gid}: {geom.refusal or 'unresolved modal geometry'}")

    mechanical = []
    w2, Xr, Cr, basis_why = _mechanical_modal_basis(M, C, K)
    if summary.mechanical_modes:
        if Xr is None:
            raise ValueError(
                "SystemSummary contains mechanical modes but the additive adapter "
                f"cannot reconstruct their carrier basis: {basis_why}"
            )
        mm_by_idx = {int(mm.modal_index): mm for mm in summary.mechanical_modes}
        subspace_by_idx = _mechanical_degenerate_subspaces(w2, Cr)
        for idx, mm in sorted(mm_by_idx.items()):
            if idx < 0 or idx >= len(w2) or w2[idx] <= 0:
                raise ValueError(f"invalid mechanical modal_index {idx}")
            omega0 = float(np.sqrt(w2[idx]))
            chi = float(Cr[idx, idx] / (2.0 * omega0))
            # Scalar-to-carrier consistency is an adapter invariant.
            denom = max(abs(float(mm.mechanical_chi)), 1.0)
            residual = abs(chi - float(mm.mechanical_chi)) / denom
            if residual > assignment_rtol:
                raise ValueError(
                    f"mechanical chi/carrier mismatch at modal_index {idx}: "
                    f"summary={mm.mechanical_chi}, reconstructed={chi}"
                )
            mechanical.append(MechanicalCarrierRecord(
                modal_index=idx,
                omega0=float(mm.omega0),
                mechanical_chi=float(mm.mechanical_chi),
                poles=tuple(complex(x) for x in mm.poles),
                temporal=str(mm.temporal),
                vector=np.asarray(Xr[:, idx], dtype=float).copy(),
                assignment_residual=float(residual),
                basis_unique=(len(subspace_by_idx.get(idx, (idx,))) == 1),
                subspace_members=tuple(subspace_by_idx.get(idx, (idx,))),
            ))
    elif Xr is None:
        refusals.append("mechanical scalar-to-carrier assignment refused: " + basis_why)

    projections = []
    if declared_vectors:
        if not mechanical:
            for name in declared_vectors:
                projections.append(DeclaredProjectionRecord(
                    name=str(name), norm=float("nan"),
                    mechanical_amplitudes=np.array([], dtype=float),
                    mechanical_participation=np.array([], dtype=float),
                    refused=True,
                    reason="no licensed mechanical carrier basis is available",
                ))
        else:
            carrier_by_idx = {m.modal_index: m for m in mechanical}
            ordered_idx = sorted(carrier_by_idx)
            X = np.column_stack([carrier_by_idx[i].vector for i in ordered_idx])
            for name, vec in declared_vectors.items():
                d = np.asarray(vec)
                if np.iscomplexobj(d):
                    imag = np.max(np.abs(d.imag)) if d.size else 0.0
                    if imag > 1e-12 * max(np.max(np.abs(d)), 1.0):
                        projections.append(DeclaredProjectionRecord(
                            name=str(name), norm=float("nan"),
                            mechanical_amplitudes=np.array([], dtype=float),
                            mechanical_participation=np.array([], dtype=float),
                            refused=True, reason="declared vector is materially complex",
                        ))
                        continue
                    d = d.real
                d = np.asarray(d, dtype=float).ravel()
                if d.shape != (n,) or not np.all(np.isfinite(d)):
                    projections.append(DeclaredProjectionRecord(
                        name=str(name), norm=float("nan"),
                        mechanical_amplitudes=np.array([], dtype=float),
                        mechanical_participation=np.array([], dtype=float),
                        refused=True, reason=f"declared vector must be finite shape ({n},)",
                    ))
                    continue
                norm2 = float(d @ M @ d)
                if not np.isfinite(norm2) or norm2 <= 1e-300:
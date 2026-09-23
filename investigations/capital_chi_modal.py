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
    out = 
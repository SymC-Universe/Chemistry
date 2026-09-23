import numpy as np

from chemsa_v3 import build_balanced_spectrum, classify_modes
from biorthogonal_response import all_mode_geometries_from_spectrum
from capital_chi_modal import build_capital_chi_modal_record, modal_correspondence_matrix


def _record(M,C,K, declared=None):
    spec=build_balanced_spectrum(M,C,K)
    summary=classify_modes(M,C,K,provenance="full",_spectrum=spec)
    geoms=all_mode_geometries_from_spectrum(spec, perturbation_weights="relative")
    return build_capital_chi_modal_record(
        M,C,K,spectrum=spec,summary=summary,geometries=geoms,
        declared_vectors=declared,
    )


def test_two_distinct_mechanical_chi_are_assigned_to_carriers():
    M=np.eye(2)
    K=np.diag([4.0,9.0])
    C=np.diag([0.8,3.0])
    r=_record(M,C,K, {"q1":np.array([1.0,0.0])})
    assert r.scalarized is False
    assert len(r.mechanical_carriers)==2
    chis=[m.mechanical_chi for m in r.mechanical_carriers]
    assert np.allclose(chis,[0.2,0.5],atol=1e-12)
    assert np.allclose(np.abs(r.mechanical_carriers[0].vector),[1,0])
    assert np.allclose(np.abs(r.mechanical_carriers[1].vector),[0,1])
    p=r.declared_projections[0].mechanical_participation
    assert np.allclose(p,[1,0],atol=1e-12)


def test_degenerate_stiffness_block_rotates_to_damping_carriers():
    M=np.eye(2)
    K=np.eye(2)
    th=np.deg2rad(31)
    R=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])
    C=R @ np.diag([0.2,0.6]) @ R.T
    r=_record(M,C,K)
    chis=sorted(m.mechanical_chi for m in r.mechanical_carriers)
    assert np.allclose(chis,[0.1,0.3],atol=1e-12)
    X=np.column_stack([m.vector for m in r.mechanical_carriers])
    assert np.allclose(X.T@M@X,np.eye(2),atol=1e-12)
    assert np.allclose(X.T@C@X,np.diag([0.2,0.6]),atol=1e-12)


def test_nonproportional_system_refuses_mechanical_scalar_assignment():
    M=np.eye(2)
    K=np.diag([1.0,4.0])
    C=np.array([[0.4,0.2],[0.2,0.8]])
    r=_record(M,C,K, {"reaction":np.array([1.0,1.0])})
    assert len(r.mechanical_carriers)==0
    assert any("mechanical scalar-to-carrier assignment refused" in x for x in r.refusal_state)
    assert r.declared_projections[0].refused is False
    assert r.declared_projections[0].mechanical_participation.size == 0
    assert len(r.declared_projections[0].spectral_subspace_projection) > 0


def test_correspondence_requires_declared_metric_and_recovers_known_rotation():
    M=np.eye(2)
    K1=np.diag([1.0,4.0])
    C1=np.diag([0.2,0.8])
    a=_record(M,C1,K1)

    th=np.deg2rad(30)
    R=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])
    K2=R@K1@R.T
    C2=R@C1@R.T
    b=_record(M,C2,K2)
    O=modal_correspondence_matrix(a,b,metric=M)
    expected=np.abs(R)
    assert np.allclose(O,expected,atol=1e-12)


def test_spectrum_id_drift_is_refused():
    M=np.eye(1); C=np.array([[0.2]]); K=np.array([[1.0]])
    s1=build_balanced_spectrum(M,C,K)
    K2=np.array([[1.1]])
    s2=build_balanced_spectrum(M,C,K2)
    summary=classify_modes(M,C,K,provenance="full",_spectrum=s1)
    geoms=all_mode_geometries_from_spectrum(s2, perturbation_weights="relative")
    try:
        build_capital_chi_modal_record(M,C,K,spectrum=s1,summary=summary,geometries=geoms)
    except ValueError as e:
        assert "ModeGeometry does not come" in str(e)
    else:
        raise AssertionError("cross-spectrum geometry drift was not refused")

def test_exact_simultaneous_degeneracy_is_reported_as_subspace_not_unique_vectors():
    M=np.eye(2)
    K=np.eye(2)
    C=0.4*np.eye(2)
    r=_record(M,C,K, {"reaction":np.array([1.0,0.0])})
    assert len(r.mechanical_carriers)==2
    assert all(not m.basis_unique for m in r.mechanical_carriers)
    assert all(m.subspace_members == (0,1) for m in r.mechanical_carriers)
    p=r.declared_projections[0]
    assert p.individual_basis_invariant is False
    assert p.subspace_participation == (((0,1), 1.0),)

    try:
        modal_correspondence_matrix(r,r,metric=M)
    except ValueError as e:
        assert "basis-dependent" in str(e)
    else:
        raise AssertionError("ambiguous individual carrier correspondence was not refused")


def test_spectral_projection_survives_when_mechanical_chi_is_refused():
    M=np.eye(2)
    K=np.diag([1.0,4.0])
    C=np.array([[0.4,0.2],[0.2,0.8]])  # non-proportional: no mechanical chi basis
    r=_record(M,C,K, {"q1":np.array([1.0,0.0])})
    p=r.declared_projections[0]
    assert p.refused is False
    assert p.mechanical_participation.size == 0
    assert len(p.spectral_subspace_projection) > 0


def test_saddle_reaction_coordinate_projects_onto_unstable_spectral_mode():
    M=np.eye(2)
    C=np.zeros((2,2))
    K=np.diag([-1.0,4.0])
    r=_record(M,C,K, {"reaction":np.array([1.0,0.0])})
    p=r.declared_projections[0]
    # Find the positive real pole, whose right eigenvector is the unstable q coordinate.
    pos_groups=[sc.group_id for sc in r.spectral_carriers
                if abs(sc.eigenvalue.imag) < 1e-10 and sc.eigenvalue.real > 0]
    assert len(pos_groups)==1
    proj=dict(p.spectral_subspace_projection)
    assert np.isclose(proj[pos_groups[0]],1.0,atol=1e-10)

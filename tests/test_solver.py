import numpy as np
import pytest
from pydantic import ValidationError

from simjobs.solver import SimParams, run_simulation


def test_defaults_ignite_and_burn_out():
    p = SimParams()
    r = run_simulation(p)
    assert r.t_ignition_s is not None
    assert 0 < r.t_ignition_s < p.t_end_s
    assert r.T_max_K > SimParams().T0_K + 100
    assert r.conversion_A > 0.99


def test_mass_balance_and_monotonic_cA():
    p = SimParams()
    r = run_simulation(p)
    cA = np.array(r.series.cA_mol_m3)
    cB = np.array(r.series.cB_mol_m3)
    cC = p.cA0_mol_m3 - cA - cB  # C is not integrated, it follows from the balance
    assert np.allclose(cA + cB + cC, p.cA0_mol_m3)
    assert (cC >= -1e-6).all()
    assert (np.diff(cA) <= 1e-6).all()


def test_more_cooling_lowers_peak_temperature():
    peaks = [run_simulation(SimParams(UA_W_K=ua)).T_max_K for ua in (0.0, 1.0e4, 2.0e6)]
    assert peaks[0] > peaks[1] > peaks[2]
    assert peaks[2] < SimParams().T0_K + 10  # strong cooling quenches the runaway


def test_cpu_burn_repeats_the_same_integration():
    a = run_simulation(SimParams(cpu_burn=1))
    b = run_simulation(SimParams(cpu_burn=3))
    assert a.T_max_K == pytest.approx(b.T_max_K)
    assert b.wall_time_s > a.wall_time_s


def test_parameters_are_range_checked():
    with pytest.raises(ValidationError):
        SimParams(t_end_s=-1)
    with pytest.raises(ValidationError):
        SimParams(dH1_J_mol=1000)  # exothermic only
    with pytest.raises(ValidationError):
        SimParams(nonsense=1)

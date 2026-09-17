"""
Batch reactor solver: A -> B -> C, two exothermic first order reactions.

Pure functions only, no I/O. This code runs in CLI, API and worker.
"""

from __future__ import annotations

import time

import numpy as np
from pydantic import BaseModel, Field
from scipy.integrate import solve_ivp

R_GAS = 8.314  # J/(mol K)

# Heat capacity of the reaction mixture per unit volume.
# Fixed, not a parameter to keep the parameter set small.
RHO_CP_J_M3_K = 2.0e6  # J/(m3 K)


class SimParams(BaseModel):
    """
    Inputs of one simulation. Every field has a default, so later {} is a valid job.

    The cpu_burn parameter has no physical meaning, it will be used to repeat the integration
    to make an actual job last longer without changing the model.
    """

    model_config = {"extra": "forbid"}

    t_end_s: float = Field(default=600.0, gt=0, le=1.05e5)
    T0_K: float = Field(default=300.0, ge=200.0, le=1000.0)
    cA0_mol_m3: float = Field(default=2000.0, gt=0, le=1.0e5)
    k1_pre: float = Field(default=4.0e10, gt=0, le=1.0e20)
    Ea1_J_mol: float = Field(default=80_000.0, gt=0, le=5.0e5)
    k2_pre: float = Field(default=3.0e11, gt=0, le=1.0e20)
    Ea2_J_mol: float = Field(default=120_000.0, gt=0, le=5.0e5)
    dH1_J_mol: float = Field(default=-150_000.0, le=0, ge=-5.0e6)
    dH2_J_mol: float = Field(default=-100_000.0, le=0, ge=-5.0e6)
    UA_W_K: float = Field(default=500.0, ge=0, le=1.0e9)
    T_cool_K: float = Field(default=300.0, ge=200.0, le=1000.0)
    n_points: int = Field(default=200, ge=2, le=5000)
    cpu_burn: int = Field(default=1, ge=1, le=1000)


class TimeSeries(BaseModel):
    t_s: list[float]
    cA_mol_m3: list[float]
    cB_mol_m3: list[float]
    T_K: list[float]


class SimResult(BaseModel):
    conversion_A: float
    yield_B: float
    T_max_K: float
    t_ignition_s: float | None
    n_steps: int
    wall_time_s: float
    series: TimeSeries


def _rhs(t: float, y: np.ndarray, p: SimParams) -> list[float]:
    cA, cB, T = y
    k1 = p.k1_pre * np.exp(-p.Ea1_J_mol / (R_GAS * T))
    k2 = p.k2_pre * np.exp(-p.Ea2_J_mol / (R_GAS * T))
    r1 = k1 * cA
    r2 = k2 * cB
    q_react = (-p.dH1_J_mol) * r1 + (-p.dH2_J_mol) * r2
    q_cool = p.UA_W_K * (T - p.T_cool_K)
    return [-r1, r1 - r2, (q_react - q_cool) / RHO_CP_J_M3_K]


def run_simulation(params: SimParams) -> SimResult:
    start = time.perf_counter()
    y0 = [params.cA0_mol_m3, 0.0, params.T0_K]
    # Radau: the Arrhenius feedback makes the system stiff around the ignition point.
    for _ in range(params.cpu_burn):
        sol = solve_ivp(
            _rhs,
            (0.0, params.t_end_s),
            y0,
            method="Radau",
            args=(params,),
            dense_output=True,
            rtol=1e-8,
            atol=[1e-6, 1e-6, 1e-8],
        )
    if not sol.success:
        raise RuntimeError(f"integration failed: {sol.message}")

    # Scalars come from the integrator's own steps, so they do not depend on n_points.
    cA_f, cB_f, T_f = np.clip(sol.y[0], 0.0, None), np.clip(sol.y[1], 0.0, None), sol.y[2]
    # Ignition time = time of the steepest temperature rise, only if it is a real excursion.
    i_max = int(np.argmax(np.gradient(T_f, sol.t)))
    t_ign = float(sol.t[i_max]) if float(T_f.max() - params.T0_K) > 10.0 else None

    # The series is a plain downsample for plotting.
    t = np.linspace(0.0, params.t_end_s, params.n_points)
    cA, cB, T = sol.sol(t)

    return SimResult(
        conversion_A=float(1.0 - cA_f[-1] / params.cA0_mol_m3),
        yield_B=float(cB_f.max() / params.cA0_mol_m3),
        T_max_K=float(T_f.max()),
        t_ignition_s=t_ign,
        n_steps=int(sol.t.size),
        wall_time_s=time.perf_counter() - start,
        series=TimeSeries(
            t_s=t.tolist(),
            cA_mol_m3=np.clip(cA, 0.0, None).tolist(),
            cB_mol_m3=np.clip(cB, 0.0, None).tolist(),
            T_K=T.tolist(),
        ),
    )

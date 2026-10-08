"""Wealth projections: deterministic and Monte Carlo."""

from finengine.wealth.montecarlo import SimulationResult, simulate
from finengine.wealth.projection import PlanInputs, Projection, YearRow, project, to_real

__all__ = ["PlanInputs", "Projection", "SimulationResult", "YearRow", "project", "simulate", "to_real"]

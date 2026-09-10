"""CUMCM 2026 Problem A drying simulation package."""

from .config import ProjectPaths, SimulationConfig
from .integrator import SimulationResult
from .scenarios import run_question

__all__ = ["ProjectPaths", "SimulationConfig", "SimulationResult", "run_question"]


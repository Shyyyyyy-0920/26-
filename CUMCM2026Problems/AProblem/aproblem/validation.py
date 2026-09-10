#基础范围检查
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .integrator import SimulationResult
from .model import DryingModel
from .outputs import split_result


@dataclass(frozen=True)
class ValidationReport:
    all_finite: bool
    nonnegative_moisture: bool
    temperature_bounds_c: tuple[float, float]
    moisture_bounds: tuple[float, float]
    final_max_moisture: float


def validate_result(model: DryingModel, result: SimulationResult) -> ValidationReport:
    temperature, moisture = split_result(model, result)
    return ValidationReport(
        all_finite=bool(np.all(np.isfinite(result.state))),
        nonnegative_moisture=bool(np.all(moisture >= 0.0)),
        temperature_bounds_c=(float(np.min(temperature)), float(np.max(temperature))),
        moisture_bounds=(float(np.min(moisture)), float(np.max(moisture))),
        final_max_moisture=float(np.max(moisture[-1])),
    )


#附件读取、环境插值、半径 PCHIP
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator


@dataclass(frozen=True)
class EnvironmentBoundary:
    time_s: np.ndarray
    temperature_c: np.ndarray
    moisture: np.ndarray
    plateau_temperature_c: float
    plateau_moisture: float

    def __call__(self, time_s: float) -> tuple[float, float]:
        temperature = float(
            np.interp(
                time_s,
                self.time_s,
                self.temperature_c,
                left=self.temperature_c[0],
                right=self.plateau_temperature_c,
            )
        )
        moisture = float(
            np.interp(
                time_s,
                self.time_s,
                self.moisture,
                left=self.moisture[0],
                right=self.plateau_moisture,
            )
        )
        return temperature, moisture


@dataclass(frozen=True)
class RadiusBoundary:
    time_s: np.ndarray
    radius_m: np.ndarray
    _interpolator: PchipInterpolator

    @classmethod
    def from_arrays(cls, time_s: np.ndarray, radius_m: np.ndarray) -> "RadiusBoundary":
        interpolator = PchipInterpolator(time_s, radius_m, extrapolate=False)
        return cls(time_s=time_s, radius_m=radius_m, _interpolator=interpolator)

    def __call__(self, time_s: float) -> float:
        clipped_time = float(np.clip(time_s, self.time_s[0], self.time_s[-1]))
        return float(self._interpolator(clipped_time))


def _read_numeric_columns(path: Path, expected_columns: int) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"Input workbook not found: {path}")
    frame = pd.read_excel(path)
    if frame.shape[1] < expected_columns:
        raise ValueError(f"{path.name} requires at least {expected_columns} columns")
    values = frame.iloc[:, :expected_columns].apply(pd.to_numeric, errors="raise").to_numpy(float)
    if np.any(np.diff(values[:, 0]) <= 0):
        raise ValueError(f"Time column in {path.name} must be strictly increasing")
    return values


def load_environment(
    path: Path,
    plateau_temperature_c: float = 50.0,
    plateau_moisture: float = 0.05,
) -> EnvironmentBoundary:
    values = _read_numeric_columns(path, expected_columns=3)
    return EnvironmentBoundary(
        time_s=values[:, 0],
        temperature_c=values[:, 1],
        moisture=values[:, 2],
        plateau_temperature_c=plateau_temperature_c,
        plateau_moisture=plateau_moisture,
    )


def load_radius(path: Path) -> RadiusBoundary:
    values = _read_numeric_columns(path, expected_columns=2)
    radius_m = values[:, 1] * 0.01
    if np.any(np.diff(radius_m) > 1.0e-12):
        raise ValueError("Radius data must be non-increasing")
    return RadiusBoundary.from_arrays(values[:, 0], radius_m)


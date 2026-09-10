from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class MaterialProperties:
    density: np.ndarray
    heat_capacity: np.ndarray
    conductivity: np.ndarray
    diffusivity: np.ndarray


class PropertyModel(Protocol):
    def evaluate(self, temperature_c: np.ndarray, moisture: np.ndarray) -> MaterialProperties:
        ...


def _safe_moisture(moisture: np.ndarray) -> np.ndarray:
    return np.maximum(np.asarray(moisture, dtype=float), 1.0e-8)


@dataclass(frozen=True)
class Question1Properties:
    def evaluate(self, temperature_c: np.ndarray, moisture: np.ndarray) -> MaterialProperties:
        c = _safe_moisture(moisture)
        shape = np.asarray(temperature_c, dtype=float).shape
        return MaterialProperties(
            density=np.full(shape, 820.0),
            heat_capacity=np.full(shape, 2600.0),
            conductivity=np.full(shape, 0.36),
            diffusivity=7.0e-9 * np.exp(-0.89 / c),
        )


@dataclass(frozen=True)
class Question23Properties:
    def evaluate(self, temperature_c: np.ndarray, moisture: np.ndarray) -> MaterialProperties:
        c = _safe_moisture(moisture)
        temperature_k = np.asarray(temperature_c, dtype=float) + 273.15
        return MaterialProperties(
            density=650.0 + 128.0 * c,
            heat_capacity=1450.0 + 2736.0 * c / (c + 1.0),
            conductivity=0.21 + 0.38 * c / (c + 1.0),
            diffusivity=2.4e-3 * np.exp(-0.45 / c) * np.exp(-3850.0 / temperature_k),
        )


@dataclass(frozen=True)
class Question4Properties:
    def evaluate(self, temperature_c: np.ndarray, moisture: np.ndarray) -> MaterialProperties:
        c = _safe_moisture(moisture)
        temperature_k = np.asarray(temperature_c, dtype=float) + 273.15
        return MaterialProperties(
            density=760.0 + 90.0 * c,
            heat_capacity=1850.0 + 2150.0 * c / (c + 1.0),
            conductivity=0.12 + 0.20 * c / (c + 1.0),
            diffusivity=4.2e-4 * np.exp(-0.30 / c) * np.exp(-3850.0 / temperature_k),
        )


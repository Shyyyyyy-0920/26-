from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .grid import RadialGrid
from .physics import PropertyModel


EnvironmentFunction = Callable[[float], tuple[float, float]]
RadiusFunction = Callable[[float], float]


def harmonic_mean(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    denominator = left + right
    return np.divide(
        2.0 * left * right,
        denominator,
        out=np.zeros_like(denominator),
        where=denominator > 0,
    )


@dataclass(frozen=True)
class DryingModel:
    grid: RadialGrid
    properties: PropertyModel
    environment: EnvironmentFunction
    radius: RadiusFunction
    heat_transfer_coefficient: float
    mass_transfer_coefficient: float

    @property
    def node_count(self) -> int:
        return self.grid.intervals + 1

    def split_state(self, state: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if state.shape != (2 * self.node_count,):
            raise ValueError(f"Expected state shape {(2 * self.node_count,)}, got {state.shape}")
        return state[: self.node_count], state[self.node_count :]

    def rhs(self, time_s: float, state: np.ndarray) -> np.ndarray:
        temperature, moisture = self.split_state(np.asarray(state, dtype=float))
        geometry = self.grid.geometry(self.radius(time_s))
        material = self.properties.evaluate(temperature, moisture)
        environment_temperature, environment_moisture = self.environment(time_s)

        heat_rate = np.zeros(self.node_count)
        conductivity_faces = harmonic_mean(material.conductivity[:-1], material.conductivity[1:])
        heat_conductance = (
            conductivity_faces
            * geometry.interface_areas_per_length_m
            / geometry.spacing_m
        )
        delta_temperature = temperature[1:] - temperature[:-1]
        heat_rate[:-1] += heat_conductance * delta_temperature
        heat_rate[1:] -= heat_conductance * delta_temperature
        heat_rate[-1] += (
            self.heat_transfer_coefficient
            * geometry.surface_area_per_length_m
            * (environment_temperature - temperature[-1])
        )
        d_temperature = heat_rate / (
            material.density * material.heat_capacity * geometry.volumes_per_length_m2
        )

        moisture_rate = np.zeros(self.node_count)
        diffusivity_faces = harmonic_mean(material.diffusivity[:-1], material.diffusivity[1:])
        moisture_conductance = (
            diffusivity_faces
            * geometry.interface_areas_per_length_m
            / geometry.spacing_m
        )
        delta_moisture = moisture[1:] - moisture[:-1]
        moisture_rate[:-1] += moisture_conductance * delta_moisture
        moisture_rate[1:] -= moisture_conductance * delta_moisture
        moisture_rate[-1] += (
            self.mass_transfer_coefficient
            * geometry.surface_area_per_length_m
            * (environment_moisture - moisture[-1])
        )
        d_moisture = moisture_rate / geometry.volumes_per_length_m2

        return np.concatenate((d_temperature, d_moisture))


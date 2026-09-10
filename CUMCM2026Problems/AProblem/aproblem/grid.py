#圆柱节点型控制体几何
from __future__ import annotations
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RadialGeometry:
    radius_m: float
    nodes_m: np.ndarray
    inner_faces_m: np.ndarray
    outer_faces_m: np.ndarray
    volumes_per_length_m2: np.ndarray
    interface_areas_per_length_m: np.ndarray
    surface_area_per_length_m: float
    spacing_m: float


@dataclass(frozen=True)
class RadialGrid:
    intervals: int

    def geometry(self, radius_m: float) -> RadialGeometry:
        if radius_m <= 0:
            raise ValueError("radius_m must be positive")
        if self.intervals < 2:
            raise ValueError("intervals must be at least 2")

        nodes = np.linspace(0.0, radius_m, self.intervals + 1)
        spacing = radius_m / self.intervals

        inner_faces = np.empty_like(nodes)
        outer_faces = np.empty_like(nodes)
        inner_faces[0] = 0.0
        inner_faces[1:] = 0.5 * (nodes[:-1] + nodes[1:])
        outer_faces[:-1] = inner_faces[1:]
        outer_faces[-1] = radius_m

        volumes = np.pi * (outer_faces**2 - inner_faces**2)
        interface_radii = 0.5 * (nodes[:-1] + nodes[1:])
        interface_areas = 2.0 * np.pi * interface_radii
        surface_area = 2.0 * np.pi * radius_m

        return RadialGeometry(
            radius_m=radius_m,
            nodes_m=nodes,
            inner_faces_m=inner_faces,
            outer_faces_m=outer_faces,
            volumes_per_length_m2=volumes,
            interface_areas_per_length_m=interface_areas,
            surface_area_per_length_m=surface_area,
            spacing_m=spacing,
        )


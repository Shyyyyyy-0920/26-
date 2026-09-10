#路径、半径、步长和阈值配置
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    project_root: Path
    attachments: Path
    outputs: Path

    @classmethod
    def discover(
        cls,
        project_root: Path | None = None,
        attachments: Path | None = None,
    ) -> "ProjectPaths":
        root = (project_root or Path(__file__).resolve().parents[1]).resolve()
        default_attachments = root.parent / "CUMCM2026Problems" / "A题" / "附件"
        return cls(
            project_root=root,
            attachments=(attachments or default_attachments).resolve(),
            outputs=root / "outputs",
        )

    @property
    def environment_file(self) -> Path:
        return self.attachments / "附件1.xlsx"

    @property
    def radius_file(self) -> Path:
        return self.attachments / "附件2.xlsx"


@dataclass(frozen=True)
class SimulationConfig:
    radius_m: float = 0.02
    radial_intervals: int = 20
    dt_s: float = 0.5
    initial_temperature_c: float = 28.0
    initial_moisture: float = 2.55
    heat_transfer_coefficient: float = 25.0
    mass_transfer_coefficient: float = 8.0e-7
    moisture_threshold: float = 0.15
    plateau_temperature_c: float = 50.0
    plateau_moisture: float = 0.05

    def validate(self) -> None:
        if self.radius_m <= 0:
            raise ValueError("radius_m must be positive")
        if self.radial_intervals < 2:
            raise ValueError("radial_intervals must be at least 2")
        if self.dt_s <= 0:
            raise ValueError("dt_s must be positive")
        if self.initial_moisture <= 0:
            raise ValueError("initial_moisture must be positive")


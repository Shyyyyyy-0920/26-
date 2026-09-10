#路径、半径、步长和阈值配置
"""项目路径与仿真参数配置。

路径配置负责定位竞赛附件和输出目录；仿真配置集中保存四问共享的
几何、时间步、初值、边界换热/传质系数及终止阈值。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """项目中输入、输出目录的统一路径集合。"""

    project_root: Path
    attachments: Path
    outputs: Path

    @classmethod
    def discover(
        cls,
        project_root: Path | None = None,
        attachments: Path | None = None,
    ) -> "ProjectPaths":
        """根据项目根目录和可选附件目录生成绝对路径。"""

        root = (project_root or Path(__file__).resolve().parents[1]).resolve()
        default_attachments = root.parent / "CUMCM2026Problems" / "A题" / "附件"
        return cls(
            project_root=root,
            attachments=(attachments or default_attachments).resolve(),
            outputs=root / "outputs",
        )

    @property
    def environment_file(self) -> Path:
        """返回烘房温度和含水率附件的路径。"""

        return self.attachments / "附件1.xlsx"

    @property
    def radius_file(self) -> Path:
        """返回药材半径随时间变化附件的路径。"""

        return self.attachments / "附件2.xlsx"


@dataclass(frozen=True)
class SimulationConfig:
    """四问共享的数值模拟配置，内部单位统一采用 SI 制。"""

    radius_m: float = 0.02
    cylinder_length_m: float = 0.25
    radial_intervals: int = 20
    dt_s: float = 0.5
    initial_temperature_c: float = 28.0
    initial_moisture: float = 2.55
    heat_transfer_coefficient: float = 25.0
    mass_transfer_coefficient: float = 8.0e-7
    moisture_threshold: float = 0.15
    plateau_temperature_c: float = 50.0
    plateau_moisture: float = 0.05
    include_end_faces: bool = True

    def validate(self) -> None:
        """在运行前检查会导致求解失败的基础参数。"""

        if self.radius_m <= 0:
            raise ValueError("药材半径 radius_m 必须为正数")
        if self.cylinder_length_m <= 0:
            raise ValueError("药材长度 cylinder_length_m 必须为正数")
        if self.radial_intervals < 2:
            raise ValueError("径向区间数 radial_intervals 至少为 2")
        if self.dt_s <= 0:
            raise ValueError("内部时间步长 dt_s 必须为正数")
        if self.initial_moisture <= 0:
            raise ValueError("初始干基含水率 initial_moisture 必须为正数")

#基础范围检查
"""对仿真结果执行有限性、非负性和物理范围等基础检查。"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .integrator import SimulationResult
from .model import DryingModel
from .outputs import split_result


@dataclass(frozen=True)
class ValidationReport:
    """汇总一次仿真的基础数值与物理检查结果。"""

    all_finite: bool
    nonnegative_moisture: bool
    temperature_bounds_c: tuple[float, float]
    moisture_bounds: tuple[float, float]
    final_max_moisture: float

    def __str__(self) -> str:
        """以中文输出验证摘要，便于终端阅读和记录。"""

        finite_text = "是" if self.all_finite else "否"
        nonnegative_text = "是" if self.nonnegative_moisture else "否"
        return (
            f"数值全部有限：{finite_text}；含水率均非负：{nonnegative_text}；"
            f"温度范围：{self.temperature_bounds_c[0]:.4f}～"
            f"{self.temperature_bounds_c[1]:.4f} ℃；"
            f"含水率范围：{self.moisture_bounds[0]:.6f}～"
            f"{self.moisture_bounds[1]:.6f} kg/kg；"
            f"最终全场最大含水率：{self.final_max_moisture:.6f} kg/kg"
        )


def validate_result(model: DryingModel, result: SimulationResult) -> ValidationReport:
    """根据温度和含水率矩阵生成基础验证报告。"""

    temperature, moisture = split_result(model, result)
    return ValidationReport(
        all_finite=bool(np.all(np.isfinite(result.state))),
        nonnegative_moisture=bool(np.all(moisture >= 0.0)),
        temperature_bounds_c=(float(np.min(temperature)), float(np.max(temperature))),
        moisture_bounds=(float(np.min(moisture)), float(np.max(moisture))),
        final_max_moisture=float(np.max(moisture[-1])),
    )

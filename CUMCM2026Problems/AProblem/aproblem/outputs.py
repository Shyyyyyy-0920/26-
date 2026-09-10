#NPZ/CSV 预览输出
"""拆分仿真结果，并写出便于调试和复核的 NPZ/CSV 预览文件。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .integrator import SimulationResult
from .model import DryingModel


def split_result(model: DryingModel, result: SimulationResult) -> tuple[np.ndarray, np.ndarray]:
    """按模型节点数将状态矩阵拆分为温度矩阵和含水率矩阵。"""

    n = model.node_count
    return result.state[:, :n], result.state[:, n:]


def write_preview_files(
    output_dir: Path,
    question: int,
    model: DryingModel,
    result: SimulationResult,
) -> list[Path]:
    """保存全精度压缩结果和带中文表头的 CSV 预览文件。

    问题4的 CSV 使用归一化半径；正式 Excel 导出时还需映射到题目要求的
    固定物理距离。NPZ 保留英文键名，便于后续代码稳定读取。
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    temperature, moisture = split_result(model, result)
    initial_radius = model.radius(0.0)
    distance_cm = model.grid.geometry(initial_radius).nodes_m * 100.0
    radial_fraction = np.linspace(0.0, 1.0, model.node_count)
    radius_m = np.asarray([model.radius(time_s) for time_s in result.time_s])

    prefix = output_dir / f"question{question}"
    npz_path = prefix.with_suffix(".npz")
    np.savez_compressed(
        npz_path,
        time_s=result.time_s,
        temperature_c=temperature,
        moisture=moisture,
        initial_distance_cm=distance_cm,
        radial_fraction=radial_fraction,
        radius_m=radius_m,
        event_time_s=np.nan if result.event_time_s is None else result.event_time_s,
    )

    if question == 4:
        columns = [f"归一化半径 ξ={value:.4f}" for value in radial_fraction]
    else:
        columns = [f"距中心 {value:.4f} cm" for value in distance_cm]
    temperature_frame = pd.DataFrame(temperature, columns=columns)
    temperature_frame.insert(0, "时间（s）", result.time_s)
    moisture_frame = pd.DataFrame(moisture, columns=columns)
    moisture_frame.insert(0, "时间（s）", result.time_s)

    temperature_path = output_dir / f"question{question}_temperature_preview.csv"
    moisture_path = output_dir / f"question{question}_moisture_preview.csv"
    temperature_frame.to_csv(temperature_path, index=False, encoding="utf-8-sig")
    moisture_frame.to_csv(moisture_path, index=False, encoding="utf-8-sig")
    return [npz_path, temperature_path, moisture_path]

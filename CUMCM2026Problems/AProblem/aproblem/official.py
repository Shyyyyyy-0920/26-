"""按题目模板导出 result1~4.xlsx。

模板口径（直接读官方模板核对得到，不是猜的）：
  result1 / result2：工作表名 "温度"、"水分浓度"；时间列从 1 s 开始（不是 0），
                     到 1800 / 10800 s；表头 A1 = "时间\\到药材中心的距离"，
                     其余 21 列为 0.0, 0.1, …, 2.0 cm。
  result3          ：工作表名 "Sheet1"；时间从 60 s 开始，步长 60 s；列同上。
  result4          ：工作表名 "Sheet1"；时间同 result3；末列换成 "药材表面"，
                     即 0.0, 0.1, …, 1.9 cm 加"药材表面"，共 21 列。
                     收缩后落在药材之外的位置留空。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from openpyxl import Workbook

from .integrator import SimulationResult
from .model import DryingModel

HEADER = "时间\\到药材中心的距离"
REPORT_CM = np.round(np.arange(0.0, 2.01, 0.1), 4)          # 0.0 ~ 2.0 cm
REPORT_CM_Q4 = np.round(np.arange(0.0, 1.91, 0.1), 4)       # 0.0 ~ 1.9 cm + 药材表面


def _write(path: Path, sheets: dict[str, np.ndarray], times, columns, ndigits: int = 4) -> Path:
    """写出一个工作簿；None 表示该位置不存在（问题4 收缩到药材之外）。"""

    workbook = Workbook(write_only=True)
    for name, values in sheets.items():
        sheet = workbook.create_sheet(title=name)
        sheet.append([HEADER] + list(columns))
        for index, moment in enumerate(times):
            row: list[float | None] = [float(moment)]
            for value in values[index]:
                row.append(None if value is None or not np.isfinite(value)
                           else round(float(value), ndigits))
            sheet.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    return path


def _sample_fixed_radius(model: DryingModel, result: SimulationResult, times_s: np.ndarray):
    """固定半径问题：节点恰好落在上报位置上，按步长抽取，不插值。"""

    node_count = model.node_count
    stride = (node_count - 1) // 20
    if (node_count - 1) % 20:
        raise ValueError("径向区间数必须是 20 的倍数，上报位置才能落在节点上")
    picked = np.searchsorted(result.time_s, times_s)
    picked = np.clip(picked, 0, len(result.time_s) - 1)
    temperature = result.state[picked, :node_count][:, ::stride]
    moisture = result.state[picked, node_count:][:, ::stride]
    return temperature, moisture


def write_official_result(
    output_dir: Path,
    question: int,
    model: DryingModel,
    result: SimulationResult,
    radius_m: np.ndarray | None = None,
) -> Path:
    """生成题目要求格式的 result{question}.xlsx。"""

    path = Path(output_dir) / f"result{question}.xlsx"

    if question in (1, 2):
        end = 1800 if question == 1 else 10800
        times = np.arange(1, end + 1, 1.0)
        temperature, moisture = _sample_fixed_radius(model, result, times)
        return _write(path, {"温度": temperature, "水分浓度": moisture}, times, list(REPORT_CM))

    if question == 3:
        times = np.arange(60.0, result.time_s[-1] + 1e-9, 60.0)
        _, moisture = _sample_fixed_radius(model, result, times)
        return _write(path, {"Sheet1": moisture}, times, list(REPORT_CM))

    if question == 4:
        node_count = model.node_count
        times = np.arange(60.0, result.time_s[-1] + 1e-9, 60.0)
        picked = np.clip(np.searchsorted(result.time_s, times), 0, len(result.time_s) - 1)
        fraction = np.linspace(0.0, 1.0, node_count)
        rows = np.full((len(times), len(REPORT_CM_Q4) + 1), np.nan)
        for out_row, src_row in enumerate(picked):
            moisture = result.state[src_row, node_count:]
            current_radius = float(radius_m[src_row])
            inside = (REPORT_CM_Q4 / 100.0) <= current_radius + 1e-12
            rows[out_row, :len(REPORT_CM_Q4)][inside] = np.interp(
                (REPORT_CM_Q4[inside] / 100.0) / current_radius, fraction, moisture
            )
            rows[out_row, -1] = moisture[-1]          # 药材表面
        return _write(path, {"Sheet1": rows}, times, list(REPORT_CM_Q4) + ["药材表面"])

    raise ValueError(f"不支持的问题编号：{question}")

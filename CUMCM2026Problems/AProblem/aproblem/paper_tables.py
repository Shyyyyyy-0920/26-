"""按题目表1至表6的格式抽取论文展示数据。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .integrator import SimulationResult
from .model import DryingModel


@dataclass(frozen=True)
class PaperTable:
    """一张可直接用于论文排版的数据表。"""

    number: int
    quantity: str
    frame: pd.DataFrame

    @property
    def filename(self) -> str:
        """返回稳定、可识别的 CSV 文件名。"""

        return f"table{self.number}_{self.quantity}.csv"


def _states_at_times(result: SimulationResult, target_times_s: np.ndarray) -> np.ndarray:
    """对完整保存结果作线性时间插值，返回指定时刻的状态。"""

    times = np.asarray(result.time_s, dtype=float)
    targets = np.asarray(target_times_s, dtype=float)
    if times.ndim != 1 or result.state.shape[0] != len(times):
        raise ValueError("仿真时间与状态行数不一致")
    if np.any(np.diff(times) < 0):
        raise ValueError("仿真保存时刻必须单调不减")
    if np.any(targets < times[0] - 1.0e-9) or np.any(targets > times[-1] + 1.0e-9):
        raise ValueError("论文表格要求的时刻超出仿真结果范围")

    sampled = np.empty((len(targets), result.state.shape[1]), dtype=float)
    for row, target in enumerate(targets):
        right = int(np.searchsorted(times, target, side="right"))
        left = max(0, right - 1)
        if abs(times[left] - target) <= 1.0e-9 or right == len(times):
            sampled[row] = result.state[left]
            continue
        while right < len(times) and times[right] == times[left]:
            right += 1
        if right == len(times):
            sampled[row] = result.state[left]
            continue
        fraction = (target - times[left]) / (times[right] - times[left])
        sampled[row] = result.state[left] + fraction * (
            result.state[right] - result.state[left]
        )
    return sampled


def _sample_radial_field(
    model: DryingModel,
    times_s: np.ndarray,
    states: np.ndarray,
    positions_cm: np.ndarray,
    field: str,
    include_surface: bool = False,
) -> np.ndarray:
    """在固定物理距离处抽取温度或含水率，必要时追加实时表面值。"""

    node_count = model.node_count
    offset = 0 if field == "temperature" else node_count
    sampled = np.empty(
        (len(times_s), len(positions_cm) + int(include_surface)),
        dtype=float,
    )
    normalized_nodes = np.linspace(0.0, 1.0, node_count)
    for row, time_s in enumerate(times_s):
        radius_cm = model.radius(float(time_s)) * 100.0
        if np.any(positions_cm > radius_cm + 1.0e-10):
            raise ValueError(f"t={time_s:g} s 时论文取点超出药材实时半径")
        values = states[row, offset : offset + node_count]
        sampled[row, : len(positions_cm)] = np.interp(
            positions_cm / radius_cm,
            normalized_nodes,
            values,
        )
        if include_surface:
            sampled[row, -1] = values[-1]
    return sampled


def _position_label(position_cm: float) -> str:
    """按题目表头格式显示径向距离。"""

    return f"{position_cm:g}"


def _make_frame(
    time_header: str,
    time_labels: list[str],
    positions_cm: np.ndarray,
    values: np.ndarray,
    include_surface: bool = False,
) -> pd.DataFrame:
    """把抽取值组织为保留四位小数的论文表格。"""

    columns = [_position_label(value) for value in positions_cm]
    if include_surface:
        columns.append("药材表面")
    frame = pd.DataFrame(np.round(values, 4), columns=columns)
    frame.insert(0, time_header, time_labels)
    return frame


def _drying_report_times(result: SimulationResult) -> tuple[np.ndarray, list[str]]:
    """生成每6小时及连续烘干结束时刻的表格行。"""

    if result.event_time_s is None:
        raise ValueError("问题3/4未检测到烘干结束事件，无法生成论文表格")
    event_time_s = float(result.event_time_s)
    regular_times = np.arange(6.0 * 3600.0, event_time_s - 1.0e-9, 6.0 * 3600.0)
    report_times = np.concatenate((regular_times, np.array([event_time_s])))
    labels = [f"{time_s / 3600.0:g}" for time_s in regular_times]
    labels.append(f"烘干结束时间（{event_time_s / 3600.0:.4f} h）")
    return report_times, labels


def build_paper_tables(
    question: int,
    model: DryingModel,
    result: SimulationResult,
) -> list[PaperTable]:
    """依据 A 题原文生成当前问题对应的论文表格。"""

    fixed_positions_cm = np.arange(0.0, 2.0 + 0.25, 0.5)

    if question == 1:
        times_s = np.array([100, 300, 600, 900, 1200, 1500, 1800], dtype=float)
        labels = [f"{time_s:g}" for time_s in times_s]
        states = _states_at_times(result, times_s)
        temperature = _sample_radial_field(
            model, times_s, states, fixed_positions_cm, "temperature"
        )
        moisture = _sample_radial_field(
            model, times_s, states, fixed_positions_cm, "moisture"
        )
        return [
            PaperTable(
                1,
                "temperature",
                _make_frame("时间/s", labels, fixed_positions_cm, temperature),
            ),
            PaperTable(
                2,
                "moisture",
                _make_frame("时间/s", labels, fixed_positions_cm, moisture),
            ),
        ]

    if question == 2:
        hours = np.arange(0.5, 3.0 + 0.25, 0.5)
        times_s = hours * 3600.0
        labels = [f"{hour:.1f}" for hour in hours]
        states = _states_at_times(result, times_s)
        temperature = _sample_radial_field(
            model, times_s, states, fixed_positions_cm, "temperature"
        )
        moisture = _sample_radial_field(
            model, times_s, states, fixed_positions_cm, "moisture"
        )
        return [
            PaperTable(
                3,
                "temperature",
                _make_frame("时间/h", labels, fixed_positions_cm, temperature),
            ),
            PaperTable(
                4,
                "moisture",
                _make_frame("时间/h", labels, fixed_positions_cm, moisture),
            ),
        ]

    if question == 3:
        times_s, labels = _drying_report_times(result)
        states = _states_at_times(result, times_s)
        moisture = _sample_radial_field(
            model, times_s, states, fixed_positions_cm, "moisture"
        )
        return [
            PaperTable(
                5,
                "moisture",
                _make_frame("时间/h", labels, fixed_positions_cm, moisture),
            )
        ]

    if question == 4:
        times_s, labels = _drying_report_times(result)
        minimum_radius_cm = (
            min(model.radius(float(time_s)) for time_s in times_s) * 100.0
        )
        # 固定取点必须在所有报告时刻均位于材料内部；实时外边界单独作为“药材表面”。
        positions_cm = np.arange(0.0, minimum_radius_cm - 1.0e-10, 0.5)
        states = _states_at_times(result, times_s)
        moisture = _sample_radial_field(
            model,
            times_s,
            states,
            positions_cm,
            "moisture",
            include_surface=True,
        )
        return [
            PaperTable(
                6,
                "moisture",
                _make_frame(
                    "时间/h",
                    labels,
                    positions_cm,
                    moisture,
                    include_surface=True,
                ),
            )
        ]

    raise ValueError("问题编号 question 必须是 1、2、3、4 之一")


def write_paper_tables(
    output_dir: Path,
    question: int,
    model: DryingModel,
    result: SimulationResult,
) -> list[Path]:
    """将当前问题的论文展示表以 UTF-8 BOM CSV 写入结果目录。"""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for table in build_paper_tables(question, model, result):
        path = output_dir / table.filename
        table.frame.to_csv(
            path,
            index=False,
            encoding="utf-8-sig",
            float_format="%.4f",
        )
        paths.append(path)
    return paths

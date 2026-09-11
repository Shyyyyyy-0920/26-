"""论文表1至表6的数据抽取测试。"""

from dataclasses import dataclass

import numpy as np

from aproblem.integrator import SimulationResult
from aproblem.paper_tables import build_paper_tables


@dataclass(frozen=True)
class FakeModel:
    """仅提供论文表抽取所需接口的轻量模型。"""

    node_count: int
    radius_function: object

    def radius(self, time_s: float) -> float:
        return float(self.radius_function(time_s))


def _linear_state(times: np.ndarray, node_count: int) -> np.ndarray:
    """构造同时随时间和归一化半径线性变化的温湿状态。"""

    xi = np.linspace(0.0, 1.0, node_count)
    temperature = np.array([20.0 + time / 1000.0 + xi for time in times])
    moisture = np.array([2.5 - time / 100000.0 - xi for time in times])
    return np.hstack((temperature, moisture))


def test_question1_builds_tables_one_and_two() -> None:
    """问题1应生成7行、5个固定径向位置的温度表和含水率表。"""

    times = np.array([0.0, 1800.0])
    model = FakeModel(21, lambda _time: 0.02)
    result = SimulationResult(times, _linear_state(times, model.node_count))

    tables = build_paper_tables(1, model, result)

    assert [table.number for table in tables] == [1, 2]
    assert tables[0].frame.shape == (7, 6)
    assert list(tables[0].frame.columns) == ["时间/s", "0", "0.5", "1", "1.5", "2"]
    assert tables[0].frame.iloc[0, 0] == "100"
    assert np.isclose(tables[0].frame.iloc[-1, -1], 22.8)


def test_question2_builds_tables_three_and_four() -> None:
    """问题2应生成0.5至3.0小时的温度表和含水率表。"""

    times = np.array([0.0, 10800.0])
    model = FakeModel(41, lambda _time: 0.02)
    result = SimulationResult(times, _linear_state(times, model.node_count))

    tables = build_paper_tables(2, model, result)

    assert [table.number for table in tables] == [3, 4]
    assert tables[0].frame["时间/h"].tolist() == [
        "0.5",
        "1.0",
        "1.5",
        "2.0",
        "2.5",
        "3.0",
    ]
    assert tables[1].frame.shape == (6, 6)


def test_question3_appends_exact_event_row() -> None:
    """问题3应保留每6小时行，并追加带连续事件时刻的结束行。"""

    times = np.array([0.0, 21600.0, 43200.0, 50000.0])
    model = FakeModel(21, lambda _time: 0.02)
    state = _linear_state(times, model.node_count)
    result = SimulationResult(times, state, event_time_s=50000.0, event_state=state[-1])

    table = build_paper_tables(3, model, result)[0].frame

    assert table["时间/h"].tolist() == ["6", "12", "烘干结束时间（13.8889 h）"]
    assert table.shape == (3, 6)


def test_question4_uses_fixed_material_points_and_live_surface() -> None:
    """问题4只保留全过程都存在的0.5 cm取点，并单独输出实时表面。"""

    event_time = 50000.0
    times = np.array([0.0, 21600.0, 43200.0, event_time])
    model = FakeModel(21, lambda time: 0.02 - 0.008 * time / event_time)
    state = _linear_state(times, model.node_count)
    result = SimulationResult(
        times,
        state,
        event_time_s=event_time,
        event_state=state[-1],
    )

    table = build_paper_tables(4, model, result)[0].frame

    assert list(table.columns) == ["时间/h", "0", "0.5", "1", "药材表面"]
    assert table.iloc[-1, 0] == "烘干结束时间（13.8889 h）"
    assert np.isclose(table.iloc[-1, -1], state[-1, -1])

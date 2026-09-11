"""Heun 时间推进精度与事件定位功能的单元测试。"""

import numpy as np

from aproblem.integrator import integrate_heun


def test_heun_integrates_exponential_decay() -> None:
    """用已知指数衰减解析解检查 Heun 方法的二阶精度。"""

    result = integrate_heun(
        rhs=lambda _time, state: -state,
        initial_state=np.array([1.0]),
        end_time_s=1.0,
        dt_s=0.01,
        save_every_s=0.1,
    )
    assert np.isclose(result.state[-1, 0], np.exp(-1.0), rtol=1.0e-4)


def test_event_time_is_interpolated() -> None:
    """阈值落在两个离散时间步之间时，应插值得到连续事件时刻。"""

    result = integrate_heun(
        rhs=lambda _time, _state: np.array([-1.0]),
        initial_state=np.array([1.0]),
        end_time_s=2.0,
        dt_s=0.2,
        save_every_s=0.4,
        event=lambda _time, state: float(state[0] - 0.35),
    )
    assert result.event_time_s is not None
    assert np.isclose(result.event_time_s, 0.65)


def test_event_just_after_saved_time_keeps_the_event_state() -> None:
    """事件紧邻保存点时，最终记录仍必须是严格插值后的事件状态。"""

    threshold = 0.5999999
    result = integrate_heun(
        rhs=lambda _time, _state: np.array([-1.0]),
        initial_state=np.array([1.0]),
        end_time_s=1.0,
        dt_s=0.2,
        save_every_s=0.4,
        event=lambda _time, state: float(state[0] - threshold),
    )

    assert result.event_time_s is not None
    assert result.event_state is not None
    assert result.time_s[-1] == result.event_time_s
    assert np.array_equal(result.state[-1], result.event_state)
    assert np.isclose(result.time_s[-1], 0.4000001, rtol=0.0, atol=1.0e-12)
    assert np.isclose(result.state[-1, 0], threshold, rtol=0.0, atol=1.0e-12)

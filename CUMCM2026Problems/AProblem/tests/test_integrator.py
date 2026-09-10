import numpy as np

from aproblem.integrator import integrate_heun


def test_heun_integrates_exponential_decay() -> None:
    result = integrate_heun(
        rhs=lambda _time, state: -state,
        initial_state=np.array([1.0]),
        end_time_s=1.0,
        dt_s=0.01,
        save_every_s=0.1,
    )
    assert np.isclose(result.state[-1, 0], np.exp(-1.0), rtol=1.0e-4)


def test_event_time_is_interpolated() -> None:
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


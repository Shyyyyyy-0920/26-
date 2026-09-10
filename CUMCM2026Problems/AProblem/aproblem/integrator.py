from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


RightHandSide = Callable[[float, np.ndarray], np.ndarray]
EventFunction = Callable[[float, np.ndarray], float]


@dataclass(frozen=True)
class SimulationResult:
    time_s: np.ndarray
    state: np.ndarray
    event_time_s: float | None = None
    event_state: np.ndarray | None = None


def integrate_heun(
    rhs: RightHandSide,
    initial_state: np.ndarray,
    end_time_s: float,
    dt_s: float,
    save_every_s: float,
    event: EventFunction | None = None,
) -> SimulationResult:
    if end_time_s <= 0 or dt_s <= 0 or save_every_s <= 0:
        raise ValueError("end_time_s, dt_s and save_every_s must be positive")
    save_ratio = save_every_s / dt_s
    if not np.isclose(save_ratio, round(save_ratio), atol=1.0e-10):
        raise ValueError("save_every_s must be an integer multiple of dt_s")

    steps = int(np.ceil(end_time_s / dt_s))
    save_stride = int(round(save_ratio))
    state = np.asarray(initial_state, dtype=float).copy()
    saved_times = [0.0]
    saved_states = [state.copy()]

    previous_event_value = event(0.0, state) if event is not None else None
    event_time = None
    event_state = None

    for step in range(steps):
        time_s = step * dt_s
        actual_dt = min(dt_s, end_time_s - time_s)
        if actual_dt <= 0:
            break

        k1 = rhs(time_s, state)
        predictor = state + actual_dt * k1
        k2 = rhs(time_s + actual_dt, predictor)
        next_state = state + 0.5 * actual_dt * (k1 + k2)
        next_time = time_s + actual_dt

        if not np.all(np.isfinite(next_state)):
            raise FloatingPointError(f"Non-finite state at t={next_time:.6g} s")

        if event is not None:
            next_event_value = event(next_time, next_state)
            if previous_event_value is not None and previous_event_value > 0 >= next_event_value:
                fraction = previous_event_value / (previous_event_value - next_event_value)
                event_time = time_s + fraction * actual_dt
                event_state = state + fraction * (next_state - state)
                if not np.isclose(saved_times[-1], event_time):
                    saved_times.append(event_time)
                    saved_states.append(event_state.copy())
                break
            previous_event_value = next_event_value

        state = next_state
        if (step + 1) % save_stride == 0 or np.isclose(next_time, end_time_s):
            saved_times.append(next_time)
            saved_states.append(state.copy())

    return SimulationResult(
        time_s=np.asarray(saved_times),
        state=np.vstack(saved_states),
        event_time_s=event_time,
        event_state=event_state,
    )


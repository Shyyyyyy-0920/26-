#四问组装
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import ProjectPaths, SimulationConfig
from .data import load_environment, load_radius
from .grid import RadialGrid
from .integrator import SimulationResult, integrate_heun
from .model import DryingModel
from .physics import Question1Properties, Question23Properties, Question4Properties


@dataclass(frozen=True)
class QuestionSpec:
    end_time_s: float
    save_every_s: float
    shrinking: bool
    stop_at_threshold: bool


QUESTION_SPECS = {
    1: QuestionSpec(1800.0, 1.0, False, False),
    2: QuestionSpec(10800.0, 1.0, False, False),
    3: QuestionSpec(259200.0, 60.0, False, True),
    4: QuestionSpec(259200.0, 60.0, True, True),
}


def _property_model(question: int):
    if question == 1:
        return Question1Properties()
    if question in (2, 3):
        return Question23Properties()
    if question == 4:
        return Question4Properties()
    raise ValueError(f"Unsupported question: {question}")


def run_question(
    question: int,
    paths: ProjectPaths,
    config: SimulationConfig | None = None,
) -> tuple[DryingModel, SimulationResult]:
    if question not in QUESTION_SPECS:
        raise ValueError("question must be one of 1, 2, 3, 4")
    cfg = config or SimulationConfig()
    cfg.validate()
    spec = QUESTION_SPECS[question]

    environment = load_environment(
        paths.environment_file,
        plateau_temperature_c=cfg.plateau_temperature_c,
        plateau_moisture=cfg.plateau_moisture,
    )
    radius_data = load_radius(paths.radius_file) if spec.shrinking else None
    radius_function = radius_data if radius_data is not None else lambda _time: cfg.radius_m

    grid = RadialGrid(cfg.radial_intervals)
    model = DryingModel(
        grid=grid,
        properties=_property_model(question),
        environment=environment,
        radius=radius_function,
        heat_transfer_coefficient=cfg.heat_transfer_coefficient,
        mass_transfer_coefficient=cfg.mass_transfer_coefficient,
    )
    node_count = model.node_count
    initial_state = np.concatenate(
        (
            np.full(node_count, cfg.initial_temperature_c),
            np.full(node_count, cfg.initial_moisture),
        )
    )

    event = None
    if spec.stop_at_threshold:
        event = lambda _time, state: float(np.max(state[node_count:]) - cfg.moisture_threshold)

    result = integrate_heun(
        rhs=model.rhs,
        initial_state=initial_state,
        end_time_s=spec.end_time_s,
        dt_s=cfg.dt_s,
        save_every_s=spec.save_every_s,
        event=event,
    )
    return model, result


import numpy as np

from aproblem.grid import RadialGrid
from aproblem.model import DryingModel
from aproblem.physics import Question1Properties


def test_uniform_state_equal_to_environment_is_stationary() -> None:
    grid = RadialGrid(intervals=20)
    model = DryingModel(
        grid=grid,
        properties=Question1Properties(),
        environment=lambda _time: (28.0, 2.55),
        radius=lambda _time: 0.02,
        heat_transfer_coefficient=25.0,
        mass_transfer_coefficient=8.0e-7,
    )
    state = np.concatenate((np.full(21, 28.0), np.full(21, 2.55)))
    assert np.allclose(model.rhs(0.0, state), 0.0)


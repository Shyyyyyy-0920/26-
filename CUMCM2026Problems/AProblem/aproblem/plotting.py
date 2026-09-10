from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .integrator import SimulationResult
from .model import DryingModel
from .outputs import split_result


def plot_final_profiles(
    path: Path,
    model: DryingModel,
    result: SimulationResult,
) -> None:
    temperature, moisture = split_result(model, result)
    radius_cm = model.grid.geometry(model.radius(result.time_s[-1])).nodes_m * 100.0

    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(radius_cm, temperature[-1], marker="o")
    axes[0].set(xlabel="Distance from center (cm)", ylabel="Temperature (°C)")
    axes[0].grid(alpha=0.3)

    axes[1].plot(radius_cm, moisture[-1], marker="o", color="tab:blue")
    axes[1].set(xlabel="Distance from center (cm)", ylabel="Moisture (kg/kg)")
    axes[1].grid(alpha=0.3)

    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180)
    plt.close(figure)


from __future__ import annotations

import argparse
from pathlib import Path

from .config import ProjectPaths, SimulationConfig
from .outputs import write_preview_files
from .plotting import plot_final_profiles
from .scenarios import run_question
from .validation import validate_result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CUMCM 2026 A题药材烘干数值模拟")
    parser.add_argument("--question", type=int, choices=(1, 2, 3, 4), default=1)
    parser.add_argument("--attachments", type=Path, default=None)
    parser.add_argument("--dt", type=float, default=0.5, help="内部时间步长（秒）")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = ProjectPaths.discover(attachments=args.attachments)
    config = SimulationConfig(dt_s=args.dt)
    model, result = run_question(args.question, paths, config)
    files = write_preview_files(paths.outputs, args.question, model, result)
    figure_path = paths.outputs / f"question{args.question}_final_profiles.png"
    plot_final_profiles(figure_path, model, result)
    report = validate_result(model, result)

    print(f"Question {args.question} completed at t={result.time_s[-1]:.3f} s")
    if result.event_time_s is not None:
        print(f"Threshold event: {result.event_time_s:.3f} s ({result.event_time_s / 3600:.6f} h)")
    print(report)
    for path in [*files, figure_path]:
        print(path)


if __name__ == "__main__":
    main()


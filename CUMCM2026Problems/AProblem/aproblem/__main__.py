"""命令行入口：组装参数、运行指定问题并生成预览结果与图像。"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .config import ProjectPaths, SimulationConfig
from .official import write_official_result
from .outputs import write_preview_files
from .paper_tables import write_paper_tables
from .plotting import plot_final_profiles
from .scenarios import run_question
from .validation import validate_result


def parse_args() -> argparse.Namespace:
    """解析命令行参数，并限制题号只能为 1～4。"""

    parser = argparse.ArgumentParser(description="CUMCM 2026 A题药材烘干数值模拟")
    parser.add_argument(
        "--question",
        type=int,
        choices=(1, 2, 3, 4),
        default=1,
        help="要计算的问题编号，默认为问题1",
    )
    parser.add_argument(
        "--attachments",
        type=Path,
        default=None,
        help="附件目录；不填写时使用项目约定的默认目录",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="结果输出目录；不填写时使用项目内的 outputs 目录",
    )
    parser.add_argument("--dt", type=float, default=0.5, help="内部时间步长（秒）")
    parser.add_argument(
        "--intervals",
        type=int,
        default=0,
        help="径向区间数，必须是 20 的倍数；默认按题号取推荐值（问题1/2 为 160，问题3/4 为 80）",
    )
    parser.add_argument(
        "--end-faces",
        action="store_true",
        help="打开端面等效体积源项。默认关闭；该闭合已被二维轴对称计算证伪，仅供对照",
    )
    parser.add_argument(
        "--no-official",
        action="store_true",
        help="只生成预览文件，不导出题目格式的 result*.xlsx",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=0.5,
        help="N=20时的基线时间步长（秒）；各题网格加密后按平方律自动缩小",
    )
    end_face_group = parser.add_mutually_exclusive_group()
    end_face_group.add_argument(
        "--include-end-faces",
        action="store_true",
        help="仅用于敏感性分析：启用均匀端面等效源项（正式结果默认不启用）",
    )
    # 兼容旧命令；当前默认已是不考虑端面，因此该参数不再显示在帮助中。
    end_face_group.add_argument(
        "--ignore-end-faces",
        dest="include_end_faces",
        action="store_false",
        help=argparse.SUPPRESS,
    )
    parser.set_defaults(include_end_faces=False)
    return parser.parse_args()


def main() -> None:
    """执行一次完整仿真，并输出结果路径和基础物理检查报告。"""

    args = parse_args()
    paths = ProjectPaths.discover(attachments=args.attachments)
    output_dir = (args.output_dir or paths.outputs).resolve()
    config = SimulationConfig(
        dt_s=args.dt,
        radial_intervals=args.intervals if args.intervals else 20,
        include_end_faces=args.end_faces and not args.ignore_end_faces,
    )

    # 四个问题共用相同入口，只在场景组装阶段切换物性、时长和半径函数。
    model, result = run_question(args.question, paths, config)
    files = write_preview_files(output_dir, args.question, model, result)
    if not args.no_official:
        radius_m = np.array([model.radius(t) for t in result.time_s])
        files.append(
            write_official_result(output_dir, args.question, model, result, radius_m)
        )
    figure_path = output_dir / f"question{args.question}_final_profiles.png"
    plot_final_profiles(figure_path, model, result)
    report = validate_result(model, result)

    print(f"问题 {args.question} 计算完成，径向区间数 {model.node_count - 1}，"
          f"端面{'开启' if model.include_end_faces else '关闭'}，"
          f"最终时刻：{result.time_s[-1]:.3f} s")
    if result.event_time_s is not None:
        print(
            "达到含水率阈值的时刻："
            f"{result.event_time_s:.3f} s（{result.event_time_s / 3600:.6f} h）"
        )
    print(f"基础验证报告：{report}")
    print("已生成文件：")
    for path in [*files, figure_path]:
        print(f"- {path}")


if __name__ == "__main__":
    main()

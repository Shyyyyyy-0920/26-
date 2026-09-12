#路径、半径、步长和阈值配置
"""项目路径与仿真参数配置。

路径配置负责定位竞赛附件和输出目录；仿真配置集中保存四问共享的
几何、时间步、初值、边界换热/传质系数及终止阈值。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """项目中输入、输出目录的统一路径集合。"""

    project_root: Path
    attachments: Path
    outputs: Path

    @classmethod
    def discover(
        cls,
        project_root: Path | None = None,
        attachments: Path | None = None,
    ) -> "ProjectPaths":
        """根据项目根目录和可选附件目录生成绝对路径。"""

        root = (project_root or Path(__file__).resolve().parents[1]).resolve()
        default_attachments = root.parent / "CUMCM2026Problems" / "A题" / "附件"
        return cls(
            project_root=root,
            attachments=(attachments or default_attachments).resolve(),
            outputs=root / "outputs",
        )

    @property
    def environment_file(self) -> Path:
        """返回烘房温度和含水率附件的路径。"""

        return self.attachments / "附件1.xlsx"

    @property
    def radius_file(self) -> Path:
        """返回药材半径随时间变化附件的路径。"""

        return self.attachments / "附件2.xlsx"


@dataclass(frozen=True)
class SimulationConfig:
    """四问共享的数值模拟配置，内部单位统一采用 SI 制。"""

    radius_m: float = 0.02
    cylinder_length_m: float = 0.25
    # 问题3/4共用加密径向网格；问题1/2使用各自的网格收敛结果。
    radial_intervals: int = 40
    question1_radial_intervals: int = 160
    question2_radial_intervals: int = 40
    dt_s: float = 0.5
    # 各问推荐的径向区间数（不指定 radial_intervals 时按题号取用）。
    # 取值一律是 20 的倍数：R=2 cm、题目要求 0.0~2.0 cm 共 21 个上报位置，
    # 20 的倍数保证节点精确落在上报位置上，不需要插值。
    # 倍数由各问自己的网格收敛实验定：
    #   问题1  N=160  上报四位小数，p=2.11、GCI=0.024%、绝对不确定度 4e-5
    #   问题2  N=160  四个上报量 p≈2.0、GCI≤0.00065%、绝对 ≤6.5e-6
    #   问题3  N=80   达标时刻 p=1.91、GCI=0.0062%（13 秒）
    #   问题4  N=80   与问题3 同口径
    recommended_intervals: tuple[int, int, int, int] = (160, 160, 80, 80)
    initial_temperature_c: float = 28.0
    initial_moisture: float = 2.55
    heat_transfer_coefficient: float = 25.0
    mass_transfer_coefficient: float = 8.0e-7
    # 【已弃用】调和/算术凸组合的权重，现仅用于论文的界面取法稳健性对照。
    # 正式计算改用基尔霍夫通量势 D_face = ΔΦ/ΔC（见 model.kirchhoff_diffusivity_mean）。
    question23_diffusivity_arithmetic_weight: float = 0.7247
    # 【已弃用】同上，问题4 的对照权重。
    question4_diffusivity_arithmetic_weight: float = 0.8705
    moisture_threshold: float = 0.15
    plateau_temperature_c: float = 50.0
    plateau_moisture: float = 0.05
    # 端面默认关闭。把两端面的对流通量摊成体积源项，要求轴向分布接近平坦，
    # 而本题的轴向渗透深度远小于半长，该前提不成立：按源项估算，轴心因端面产生的
    # 失水时间常数约 44 h，与整个干燥过程同量级，等于给轴心开了一条绕过内部扩散的
    # 通道。二维轴对称计算已验证 t=1800 s 时端面影响的轴向范围仅 1.62 cm，
    # 中截面的径向分布与一维解一致到 1e-7 ℃。正式结果一律取"不含端面"。
    include_end_faces: bool = False

    def validate(self) -> None:
        """在运行前检查会导致求解失败的基础参数。"""

        if self.radius_m <= 0:
            raise ValueError("药材半径 radius_m 必须为正数")
        if self.cylinder_length_m <= 0:
            raise ValueError("药材长度 cylinder_length_m 必须为正数")
        interval_settings = {
            "问题3/4": self.radial_intervals,
            "问题1": self.question1_radial_intervals,
            "问题2": self.question2_radial_intervals,
        }
        for label, intervals in interval_settings.items():
            if intervals < 2:
                raise ValueError(f"{label}径向区间数至少为 2")
        if self.dt_s <= 0:
            raise ValueError("内部时间步长 dt_s 必须为正数")
        if self.initial_moisture <= 0:
            raise ValueError("初始干基含水率 initial_moisture 必须为正数")
        if len(self.recommended_intervals) != 4:
            raise ValueError("recommended_intervals 必须给出四个问题的网格数")
        if any(n % 20 for n in self.recommended_intervals):
            raise ValueError("径向区间数必须是 20 的倍数，否则上报位置需要插值")
        if not 0.0 <= self.question23_diffusivity_arithmetic_weight <= 1.0:
            raise ValueError("问题2/3扩散系数算术平均权重必须位于 0～1")
        if not 0.0 <= self.question4_diffusivity_arithmetic_weight <= 1.0:
            raise ValueError("问题4扩散系数算术平均权重必须位于 0～1")

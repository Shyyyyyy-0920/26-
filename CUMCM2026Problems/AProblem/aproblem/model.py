#热湿有限体积 RHS
"""建立温度—含水率耦合的一维圆柱有限体积半离散模型。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .grid import RadialGrid
from .physics import PropertyModel


EnvironmentFunction = Callable[[float], tuple[float, float]]
RadiusFunction = Callable[[float], float]


def harmonic_mean(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """计算相邻节点物性的调和平均，作为当前界面系数基线。"""

    denominator = left + right
    return np.divide(
        2.0 * left * right,
        denominator,
        out=np.zeros_like(denominator),
        where=denominator > 0,
    )


def calibrated_diffusivity_mean(
    left: np.ndarray,
    right: np.ndarray,
    arithmetic_weight: float,
) -> np.ndarray:
    """【已弃用，仅供对照】调和平均与算术平均的凸组合。

    该取法当初是为了绕开纯调和平均在低含水率外层造成的数值瓶颈——那个判断是对的，
    调和平均在 t=30 h 的 L∞ 误差比正确取法大约 2200 倍。但凸组合的权重需要按参考
    答案反标，且每个问题要重标一次（问题2/3 为 0.7247、问题4 为 0.8705）；更根本的是，
    反解出的"所需权重"随含水率从 4.0 变到 0.61 并跨越 1，任何固定的 w∈[0,1] 都不可能
    等价于由守恒律导出的界面值。

    现已改用 kirchhoff_diffusivity_mean。本函数保留，仅用于论文的稳健性对照表。
    """

    if not 0.0 <= arithmetic_weight <= 1.0:
        raise ValueError("扩散系数算术平均权重必须位于 0～1")
    harmonic = harmonic_mean(left, right)
    arithmetic = 0.5 * (left + right)
    return (1.0 - arithmetic_weight) * harmonic + arithmetic_weight * arithmetic


def kirchhoff_diffusivity_mean(
    potential_left: np.ndarray,
    potential_right: np.ndarray,
    moisture_left: np.ndarray,
    moisture_right: np.ndarray,
    diffusivity_midpoint: np.ndarray,
) -> np.ndarray:
    """由通量守恒唯一确定的界面扩散系数 D_face = ΔΦ/ΔC。

    界面上没有物质累积，通量处处相等，对 J = -D(C)·∂C/∂r 沿区间积分立即给出
        J·Δr = -∫ D dc  ⟹  D_face = (1/ΔC)·∫ D dc = ΔΦ/ΔC,
    其中 Φ 是基尔霍夫通量势。这是一个恒等式，不是"平均方式的选择"。

    ΔΦ 是两个相近大数之差，ΔC 越小抵消越厉害（实测 ΔC~1e-9 时相对误差已达 1e-6，
    1e-12 时达 6e-4）。而 |ΔC| 很小时 ΔΦ/ΔC 与中点值本来就只差 O(ΔC²)，
    因此在 |ΔC| < 1e-6·C 时直接退回中点值，既避开抵消又不损失精度。
    """

    delta_c = moisture_right - moisture_left
    mean_c = 0.5 * (moisture_left + moisture_right)
    tiny = np.abs(delta_c) < 1.0e-6 * np.maximum(np.abs(mean_c), 1.0e-12)
    safe_delta = np.where(tiny, 1.0, delta_c)
    return np.where(tiny, diffusivity_midpoint, (potential_right - potential_left) / safe_delta)


@dataclass(frozen=True)
class DryingModel:
    """封装网格、物性、侧面边界、端面等效源项和热湿有限体积右端项。

    状态向量前半段为温度，后半段为干基含水率。问题4通过固定节点编号
    配合随时间变化的物理半径实现材料坐标网格，不额外添加收缩拖曳项。
    """

    grid: RadialGrid
    properties: PropertyModel
    environment: EnvironmentFunction
    radius: RadiusFunction
    heat_transfer_coefficient: float
    mass_transfer_coefficient: float
    cylinder_length_m: float = 0.25
    include_end_faces: bool = True
    # 保留字段仅为兼容旧脚本；正式计算不再使用（界面取法已改为基尔霍夫通量势）。
    diffusivity_arithmetic_weight: float = 0.0

    def __post_init__(self) -> None:
        """检查端面等效源项所需的圆柱长度。"""

        if self.cylinder_length_m <= 0:
            raise ValueError("药材长度 cylinder_length_m 必须为正数")
        if not 0.0 <= self.diffusivity_arithmetic_weight <= 1.0:
            raise ValueError("扩散系数算术平均权重必须位于 0～1")

    @property
    def node_count(self) -> int:
        """返回包含圆心和表面的径向节点总数。"""

        return self.grid.intervals + 1

    def split_state(self, state: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """将一维状态向量拆分为温度场和含水率场。"""

        if state.shape != (2 * self.node_count,):
            raise ValueError(
                f"状态向量形状应为 {(2 * self.node_count,)}，实际为 {state.shape}"
            )
        return state[: self.node_count], state[self.node_count :]

    def rhs(self, time_s: float, state: np.ndarray) -> np.ndarray:
        """计算当前时刻温度和含水率在所有节点上的变化率。"""

        temperature, moisture = self.split_state(np.asarray(state, dtype=float))
        geometry = self.grid.geometry(self.radius(time_s))
        material = self.properties.evaluate(temperature, moisture)
        environment_temperature, environment_moisture = self.environment(time_s)

        # 先计算全部内部界面热通量，再以相反符号计入相邻控制体，保证守恒。
        heat_rate = np.zeros(self.node_count)
        # 导热系数在本题只随含水率变 2.3 倍，且连续无间断，调和平均的"串联分层"
        # 前提不成立；此处取算术平均（各取法在该跨度内相差不到 1%）。
        conductivity_faces = 0.5 * (material.conductivity[:-1] + material.conductivity[1:])
        heat_conductance = (
            conductivity_faces
            * geometry.interface_areas_per_length_m
            / geometry.spacing_m
        )
        delta_temperature = temperature[1:] - temperature[:-1]
        heat_rate[:-1] += heat_conductance * delta_temperature
        heat_rate[1:] -= heat_conductance * delta_temperature
        # 表面采用第三类边界条件：烘房温度高于表面时，热量流入药材。
        heat_rate[-1] += (
            self.heat_transfer_coefficient
            * geometry.surface_area_per_length_m
            * (environment_temperature - temperature[-1])
        )

        if self.include_end_faces:
            # 将两个端面的轴向对流通量除以长度，折算为一维径向方程中的体积热源。
            # 该闭合近似假设端面状态可由同一半径处的轴向平均状态表示。
            end_heat_source = (
                2.0
                * self.heat_transfer_coefficient
                / self.cylinder_length_m
                * (environment_temperature - temperature)
            )
            heat_rate += end_heat_source * geometry.volumes_per_length_m2

        d_temperature = heat_rate / (
            material.density * material.heat_capacity * geometry.volumes_per_length_m2
        )

        # 水分通量与热通量使用同一套控制体几何和符号约定。
        moisture_rate = np.zeros(self.node_count)
        # Φ 两端都在同一个界面温度上取值：D 同时依赖 C 和 T，而通量势只对 C 定义，
        # 故沿界面取 T_f = (T_i + T_{i+1})/2。本题 Le≈34，一格内温差极小，该近似可忽略。
        face_temperature = 0.5 * (temperature[:-1] + temperature[1:])
        potential_left = self.properties.flux_potential(face_temperature, moisture[:-1])
        potential_right = self.properties.flux_potential(face_temperature, moisture[1:])
        midpoint_diffusivity = self.properties.evaluate(
            face_temperature, 0.5 * (moisture[:-1] + moisture[1:])
        ).diffusivity
        diffusivity_faces = kirchhoff_diffusivity_mean(
            potential_left,
            potential_right,
            moisture[:-1],
            moisture[1:],
            midpoint_diffusivity,
        )
        moisture_conductance = (
            diffusivity_faces
            * geometry.interface_areas_per_length_m
            / geometry.spacing_m
        )
        delta_moisture = moisture[1:] - moisture[:-1]
        moisture_rate[:-1] += moisture_conductance * delta_moisture
        moisture_rate[1:] -= moisture_conductance * delta_moisture
        # 烘房含水率更低时，该项为负，表示药材从表面失水。
        moisture_rate[-1] += (
            self.mass_transfer_coefficient
            * geometry.surface_area_per_length_m
            * (environment_moisture - moisture[-1])
        )

        if self.include_end_faces:
            # 两个端面的失水通量等效为体积水分汇；环境更干时该项为负。
            end_moisture_source = (
                2.0
                * self.mass_transfer_coefficient
                / self.cylinder_length_m
                * (environment_moisture - moisture)
            )
            moisture_rate += end_moisture_source * geometry.volumes_per_length_m2

        d_moisture = moisture_rate / geometry.volumes_per_length_m2

        return np.concatenate((d_temperature, d_moisture))

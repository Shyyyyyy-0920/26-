# CUMCM 2026 A题：药材烘干数值模型

本项目采用一维圆柱径向有限体积法，将温度场和干基含水率场统一离散，并使用固定步长 Heun（显式二阶 Runge-Kutta）方法推进。

## 目录

```text
AProblem/
├── aproblem/
│   ├── __main__.py       # 命令行入口
│   ├── config.py         # 路径和仿真配置
│   ├── data.py           # 附件读取与边界插值
│   ├── grid.py           # 圆柱径向控制体几何
│   ├── physics.py        # 三组物性公式
│   ├── model.py          # 热湿有限体积半离散方程
│   ├── integrator.py     # Heun推进与终止事件
│   ├── scenarios.py      # 问题1-4的组装逻辑
│   ├── outputs.py        # NPZ/CSV预览输出
│   ├── plotting.py       # 剖面图与热力图
│   └── validation.py     # 数值和物理检查
├── tests/                # 不依赖竞赛附件的单元测试
└── outputs/              # 本地运行输出，不覆盖官方模板
```

## 快速开始

在本目录执行：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
python -m aproblem --question 1
```

默认附件目录为：

```text
../CUMCM2026Problems/A题/附件
```

也可以显式指定：

```powershell
python -m aproblem --question 1 --attachments "完整的附件目录"
```

## 当前约定

- 所有内部计算使用 SI 单位：m、s、K/Celsius 差值、kg/kg。
- 固定半径问题使用 20 个径向区间，即 21 个节点，恰好对应 0.0-2.0 cm、间隔 0.1 cm。
- 默认内部步长 0.5 s。问题1、2分别每1 s保存，问题3、4每60 s保存。
- 问题3、4在附件1结束后将烘房条件保持为 50°C 和 0.05 kg/kg。
- `outputs` 目前输出便于检查的 NPZ 和 CSV；官方 result*.xlsx 的模板填充单独实现，避免早期调试覆盖模板。
- 问题4的预览 CSV 使用归一化半径 `xi=r/R(t)` 作为列；NPZ 同时保存每个输出时刻的实际半径，正式导出时再插值到题目要求的物理距离。

## 建议开发顺序

1. 完成并核验问题1。
2. 在同一固定半径内核上切换问题2/3物性。
3. 加入问题3的含水率阈值事件。
4. 使用归一化径向坐标处理问题4的收缩半径。
5. 最后接入官方 Excel 模板和论文图表。

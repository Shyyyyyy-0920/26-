# CUMCM 2026 A题：药材烘干数值模型

本项目采用一维圆柱径向有限体积法，将温度场和干基含水率场统一离散，并使用固定步长 Heun（显式二阶 Runge-Kutta）方法推进。代码中的模块说明、关键类、函数和主要算法步骤均使用中文注释，便于队员阅读、复核和论文推导。

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

请先在终端进入 `AProblem` 目录，再依次执行下面的 PowerShell 命令。每行命令后的 `#` 内容是用途说明，可以连同命令一起复制到 PowerShell：

```powershell
python -m venv .venv                    # 在当前项目中创建名为 .venv 的独立 Python 虚拟环境
.venv\Scripts\Activate.ps1             # 激活虚拟环境，后续安装和运行都使用该环境中的 Python
python -m pip install -e ".[dev]"       # 以可编辑模式安装项目、数值计算依赖和 pytest 测试工具
pytest                                  # 运行 tests/ 中的全部单元测试，先确认基础算法没有被改坏
python -m aproblem --question 1         # 计算问题1，并在 outputs/ 中生成 NPZ、中文表头 CSV 和中文剖面图
```

如果 PowerShell 因执行策略阻止激活脚本，可以先在当前终端临时执行 `Set-ExecutionPolicy -Scope Process Bypass`，关闭该终端后设置会自动失效。

默认附件目录为：

```text
../CUMCM2026Problems/A题/附件
```

也可以显式指定：

```powershell
python -m aproblem --question 1 --attachments "完整的附件目录"  # 不使用默认路径，改为从指定目录读取附件1.xlsx和附件2.xlsx
```

其余问题只需修改题号：

```powershell
python -m aproblem --question 2         # 计算问题2：变物性、固定半径、计算3小时
python -m aproblem --question 3         # 计算问题3：变物性、达到全场含水率阈值时停止
python -m aproblem --question 4         # 计算问题4：变物性、半径随附件2收缩、达到阈值时停止
```

需要试验其他内部时间步时可增加 `--dt`，例如：

```powershell
python -m aproblem --question 1 --dt 0.25  # 用0.25秒内部步长重算问题1，可用于时间步收敛对照
```

## 当前约定

- 所有内部计算使用 SI 单位：m、s、K/Celsius 差值、kg/kg。
- 固定半径问题使用 20 个径向区间，即 21 个节点，恰好对应 0.0-2.0 cm、间隔 0.1 cm。
- 默认内部步长 0.5 s。问题1、2分别每1 s保存，问题3、4每60 s保存。
- 问题3、4在附件1结束后将烘房条件保持为 50°C 和 0.05 kg/kg。
- `outputs` 目前输出便于检查的 NPZ 和 CSV；官方 result*.xlsx 的模板填充单独实现，避免早期调试覆盖模板。
- 问题4的预览 CSV 使用归一化半径 `xi=r/R(t)` 作为列；NPZ 同时保存每个输出时刻的实际半径，正式导出时再插值到题目要求的物理距离。

## 图表约定

- 所有图题、坐标轴和图例均使用中文。
- 温度曲线使用橙红色圆点线，干基含水率曲线使用蓝色方点线，避免黑白之外难以区分。
- 横坐标统一为“距药材中心的距离（cm）”；纵坐标分别为“温度（℃）”和“干基含水率（kg/kg）”。
- 绘图模块会依次尝试微软雅黑、黑体、思源黑体等中文字体；若本机仍出现方框，请安装其中任意一种字体后重新运行。

## 建议开发顺序

1. 完成并核验问题1。
2. 在同一固定半径内核上切换问题2/3物性。
3. 加入问题3的含水率阈值事件。
4. 使用归一化径向坐标处理问题4的收缩半径。
5. 最后接入官方 Excel 模板和论文图表。

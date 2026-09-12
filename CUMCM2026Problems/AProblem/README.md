# CUMCM 2026 A题：药材烘干数值模型

本项目采用无端面的一维圆柱径向有限体积法，将温度场和干基含水率场统一离散，并使用固定步长 Heun（显式二阶 Runge-Kutta）方法推进。四问正式结果均解释为远离端面的圆柱中截面径向分布；均匀端面体积源不进入正式计算，仅保留为显式启用的启发式敏感性试算。代码中的模块说明、关键类、函数和主要算法步骤均使用中文注释，便于队员阅读、复核和论文推导。

完整建模、算法选择和验收流程见：[工作流详解_审核完善版.md](../工作流详解_审核完善版.md)。

## 目录

```text
AProblem/
├── aproblem/
│   ├── __main__.py       # 命令行入口
│   ├── config.py         # 路径、圆柱尺寸、端面开关和仿真配置
│   ├── data.py           # 附件读取与边界插值
│   ├── grid.py           # 圆柱径向控制体几何
│   ├── physics.py        # 三组物性公式
│   ├── model.py          # 热湿有限体积半离散方程与端面等效源项
│   ├── integrator.py     # Heun推进与终止事件
│   ├── scenarios.py      # 问题1-4的组装逻辑
│   ├── outputs.py        # NPZ/CSV预览输出
│   ├── paper_tables.py   # 按题目表1至表6抽取论文展示数据
│   ├── plotting.py       # 剖面图与热力图
│   └── validation.py     # 数值和物理检查
├── tests/                # 不依赖竞赛附件的单元测试
└── outputs/              # 本地运行输出，不覆盖官方模板
```

## 环境要求与依赖安装

建议使用 **Python 3.11 或更高版本**，不要直接使用系统全局环境。项目所需包已经写在 `pyproject.toml` 中：

| 环境包 | 最低版本 | 用途 |
|---|---:|---|
| `numpy` | 1.26 | 数组运算、有限体积状态和结果保存 |
| `pandas` | 2.1 | 读取附件 Excel、生成 CSV 预览 |
| `scipy` | 1.11 | PCHIP 半径插值及后续 BDF 对照 |
| `matplotlib` | 3.8 | 生成中文温度与含水率图像 |
| `openpyxl` | 3.1 | 供 pandas 读取 `.xlsx`，并用于正式 Excel 导出 |
| `pytest` | 8.0 | 运行项目测试，属于开发依赖 |

### 方案一：使用 Conda 环境

队员已经有 Anaconda/Miniconda 时，推荐为比赛单独创建环境：

```powershell
conda create -n cumcm-a python=3.11 -y  # 创建名为 cumcm-a 的独立 Python 3.11 环境
conda activate cumcm-a                  # 激活该环境，后续命令都在该环境中执行
cd "E:\数学建模\CUMCM2026Problems\AProblem"  # 进入项目根目录，路径不同的队员应替换成自己的路径
python -m pip install --upgrade pip setuptools  # 更新安装工具，减少可编辑安装失败的概率
python -m pip install -e ".[dev]"       # 安装项目及 numpy、pandas、scipy、matplotlib、openpyxl、pytest
python -m pytest                        # 使用当前环境的 Python 运行全部测试
```

如果想继续使用已有环境，例如 `si100`，无需重新创建：

```powershell
conda activate si100                    # 激活已有的 si100 环境
cd "E:\数学建模\CUMCM2026Problems\AProblem"  # 进入项目根目录
python -m pip install -e ".[dev]"       # 补齐该环境缺失的全部项目依赖，包括 openpyxl
python -m pytest                        # 确认安装后的环境能够通过测试
```

### 方案二：使用 Python 自带虚拟环境

没有 Conda、但已安装 Python 3.11 以上版本时使用：

```powershell
cd "E:\数学建模\CUMCM2026Problems\AProblem"  # 进入项目根目录
python -m venv .venv                    # 在项目内创建名为 .venv 的独立虚拟环境
.\.venv\Scripts\Activate.ps1           # 激活虚拟环境
python -m pip install --upgrade pip setuptools  # 更新 pip 和项目安装工具
python -m pip install -e ".[dev]"       # 一次安装程序运行和测试所需的全部环境包
python -m pytest                        # 运行 tests/ 中的全部测试
```

安装完成后可以一次检查所有关键包：

```powershell
python -c "import numpy, pandas, scipy, matplotlib, openpyxl, pytest; print('全部依赖安装成功')"  # 任一包缺失时会直接显示包名
```

## 快速开始：自己跑出前三问的正式答案

<<<<<<< HEAD
完成上面的任意一种环境安装方案后，在 `AProblem` 目录执行。四问正式结果默认均不考虑端面；以下以问题1为例：

```powershell
python -m pytest  # 再次确认当前代码和环境通过全部单元测试
python -m aproblem --question 1 --output-dir "outputs\问题1\正式结果"  # 默认无端面的一维径向结果
python -m aproblem --question 1 --include-end-faces --output-dir "outputs\敏感性分析\问题1\均匀端面源"  # 可选启发式敏感性试算
```

其中，不添加端面参数时程序默认**不考虑端面**。只有显式添加 `--include-end-faces` 才启用旧的均匀端面体积源近似；该结果不得作为表1至表6的正式结果。旧参数 `--ignore-end-faces` 仍兼容，但因与新默认行为相同而无需再写。
=======
完成环境安装后，在 `AProblem` 目录依次执行这四条命令。**默认配置就是论文用的配置**
（端面关闭、基尔霍夫界面、按题号取推荐网格），不需要额外加参数。

```powershell
python -m pytest                                              # 先确认环境和代码通过全部单元测试

python -m aproblem --question 1 --dt 0.02 --output-dir "outputs\问题1"   # 约 1 分钟
python -m aproblem --question 2 --dt 0.02 --output-dir "outputs\问题2"   # 约 8 分钟
python -m aproblem --question 3 --dt 0.05 --output-dir "outputs\问题3"   # 约 40 分钟
```

每条命令都会在对应目录下生成 **`result1.xlsx` / `result2.xlsx` / `result3.xlsx`**，
就是直接交上去的那个格式（工作表名、起始时刻、21 列表头都已按官方模板核对）。
同时还会生成 `question*.npz`（全精度原始数据）、两个预览 CSV 和一张剖面图。

跑完之后可以这样自查：

| 问题 | 终端会打印 | 应该看到 |
|---|---|---|
| 1 | 温度范围 | `28.0000～36.7856 ℃` |
| 2 | 含水率范围 | 下限 `1.008118` |
| 3 | 达到含水率阈值的时刻 | `≈ 206910 s（57.475 h）` |

**为什么 `--dt` 要这么给。** 程序用的是固定步长的显式格式，稳定步长随网格加密按
\(1/N^2\) 收紧：问题1 的推荐网格 \(N=160\) 对应稳定上限约 0.023 s，问题3 的
\(N=80\) 对应约 0.086 s。另外 `--dt` 必须能整除保存间隔（问题1、2 是 1 s，问题3 是 60 s），
所以取 0.02 和 0.05。步长给大了程序会发散并报错，不会静默给出错误答案。

### 想改配置时的开关

```powershell
python -m aproblem --question 3 --intervals 40 --dt 0.1 --output-dir "outputs\粗网格对照"  # 换网格，必须是 20 的倍数
python -m aproblem --question 1 --dt 0.02 --end-faces --output-dir "outputs\端面对照"       # 打开端面源项（仅供对照，见下文）
python -m aproblem --question 1 --dt 0.02 --no-official --output-dir "outputs\只要预览"     # 不导出 result*.xlsx
```

`--intervals` 不给时按题号取推荐值：问题1、2 为 160，问题3、4 为 80。
这些值由各问自己的网格收敛实验定出，理由写在 `config.py` 的注释里。

**端面默认是关闭的。** 早期版本默认打开，那是不对的——把两端面的对流通量摊成体积源项
要求轴向分布接近平坦，而本题的轴向渗透深度远小于半长，该前提不成立。
`--end-faces` 只保留作对照，正式结果一律不含端面。
>>>>>>> 方法层面定案：基尔霍夫界面取法、端面默认关闭、分问网格、导出题目格式结果

如果 PowerShell 因执行策略阻止激活脚本，可以先在当前终端临时执行 `Set-ExecutionPolicy -Scope Process Bypass`，关闭该终端后设置会自动失效。

### 常见环境报错

如果出现 `No module named 'openpyxl'`，说明当前正在运行程序的 Python 环境缺少 Excel 引擎。在项目目录执行：

```powershell
python -m pip install -e ".[dev]"       # 推荐：按项目配置补齐所有依赖，而不只安装单个缺失包
python -c "import openpyxl; print(openpyxl.__version__)"  # 验证 openpyxl 已安装到当前环境
```

如果旧版本项目安装时出现 `Multiple top-level packages discovered`，说明 `setuptools` 把 `outputs/` 误判成了 Python 包。当前 `pyproject.toml` 已明确只打包 `aproblem`；拉取或复制最新文件后重新执行：

```powershell
python -m pip install -e ".[dev]"       # 使用修正后的打包配置安装项目和全部依赖
```

比赛现场如果只需要立刻补装 Excel 读取包，也可以先绕过项目安装：

```powershell
python -m pip install "openpyxl>=3.1"   # 仅安装缺失的 openpyxl；版本表达式要放在引号内
```

如果安装后仍提示缺包，通常是 `pip` 和 `python` 指向了不同环境。使用下面命令检查：

```powershell
where.exe python                        # 查看终端实际找到的所有 python.exe 路径
python -c "import sys; print(sys.executable)"  # 显示当前运行程序使用的 Python 路径
python -m pip --version                 # 显示 pip 所属的 Python 环境，路径应与上一行一致
```

始终使用 `python -m pip ...` 和 `python -m pytest`，可以最大限度避免 Conda、系统 Python 和用户目录中的包互相混用。

默认附件目录为：

```text
../CUMCM2026Problems/A题/附件
```

也可以显式指定：

```powershell
python -m aproblem --question 1 --attachments "完整的附件目录" --output-dir "outputs\问题1\正式结果"
python -m aproblem --question 1 --attachments "完整的附件目录" --include-end-faces --output-dir "outputs\敏感性分析\问题1\均匀端面源"
```

### 四个问题的正式运行

四问各运行一次无端面正式模型：

```powershell
# 问题1：常物性、固定半径、计算30分钟
python -m aproblem --question 1 --output-dir "outputs\问题1\正式结果"

# 问题2：变物性、固定半径、计算3小时
python -m aproblem --question 2 --output-dir "outputs\问题2\正式结果"

# 问题3：变物性、达到全场含水率阈值时停止
python -m aproblem --question 3 --output-dir "outputs\问题3\正式结果"

# 问题4：变物性、半径随附件2收缩、达到阈值时停止
python -m aproblem --question 4 --output-dir "outputs\问题4\正式结果"
```

运行完成后的目录结构如下：

```text
outputs/
├── 问题1/
│   └── 正式结果/
├── 问题2/
│   └── 正式结果/
├── 问题3/
│   └── 正式结果/
└── 问题4/
    └── 正式结果/
```

每次运行还会在同一结果目录自动生成论文表格 CSV：问题1生成表1、表2，
问题2生成表3、表4，问题3生成表5，问题4生成表6。表中只保留题目指定时刻和
径向位置，数值统一保留四位小数；问题3、4会追加包含连续事件时刻的“烘干结束时间”行。

需要试验其他内部时间步时，可用 `--dt` 设置N=20基线步长。例如：

```powershell
python -m aproblem --question 1 --dt 0.25 --output-dir "outputs\问题1\时间步敏感性\基线0.25秒"
```

## 端面因素的处理

正式模型采用长圆柱中截面近似，不引入任何端面源项。有限端面可能使实际干燥略快，但题目没有要求轴向位置，也没有提供足以可靠闭合二维端面效应的信息，因此将其列为模型局限性。

代码仍保留以下旧的均匀体积源近似，仅供添加 `--include-end-faces` 后进行敏感性试算：

```text
温度体积源：S_T = (2 h_T / L) · (T_air - T)
水分体积汇：S_C = (2 h_m / L) · (C_air - C)
```

该近似会跳过真实的轴向扩散过程，可能明显放大端面影响，不得进入表1至表6，也不得称为严格的端面效应上界。若需正式研究端面，应建立含径向和轴向坐标的二维轴对称模型。

## 当前约定

- 所有内部计算使用 SI 单位：m、s、K/Celsius 差值、kg/kg。
<<<<<<< HEAD
- 圆柱长度默认为0.25 m；四问正式计算默认关闭端面源项，只考虑侧表面换热和传质。
- 问题1使用160个径向区间，问题2、3、4使用40个；论文取点通过空间插值得到。
- 默认 N=20 基线内部步长为0.5 s；四问均按网格间距平方自动缩小，问题3、4每60 s保存。
- 问题2/3的界面扩散算术平均权重为0.7247；问题4使用单独校准权重0.8705。
=======
- 圆柱长度默认为 0.25 m；**四问默认不计端面**，只保留侧面的对流换热与传质。
- 径向区间数必须是 20 的倍数：`R=2` cm、题目要求 0.0~2.0 cm 共 21 个上报位置，
  取 20 的倍数才能让节点精确落在上报位置上，不引入插值误差。倍数由各问自己的网格
  收敛实验定：问题1、2 为 160（上报四位小数，GCI ≤ 0.024%），问题3、4 为 80
  （达标时刻 GCI = 0.0062%，约 13 秒）。
- 默认内部步长 0.5 s，实际运行需按网格调小（见「快速开始」）。问题1、2 每 1 s 保存，问题3、4 每 60 s 保存。
- **界面扩散系数取基尔霍夫通量势的差商** \(D_\text{face}=\Delta\Phi/\Delta C\)，其中
  \(\Phi(C)=\int_0^C D\,\mathrm dc\)。三套附录的 \(D\) 都是 \(A(T)\mathrm e^{-b/C}\) 形式，
  \(\Phi\) 有初等解析原函数 \(\Phi=A(T)[C\mathrm e^{-b/C}-b E_1(b/C)]\)，不需要数值求积。
  该取法由通量守恒唯一确定，不含自由参数。早先的「调和/算术校准混合」已弃用，
  仅保留在 `model.calibrated_diffusivity_mean` 中供稳健性对照。
- 界面导热系数取算术平均（\(k\) 在本题只变 2.3 倍且连续，各取法相差不到 1%）。
>>>>>>> 方法层面定案：基尔霍夫界面取法、端面默认关闭、分问网格、导出题目格式结果
- 问题3、4在附件1结束后将烘房条件保持为 50°C 和 0.05 kg/kg。
- `outputs` 输出完整 NPZ、调试 CSV、论文表1至表6 CSV；官方 result*.xlsx 模板填充仍单独实现。
- 问题4完整预览使用归一化半径 `xi=r/R(t)`，论文表6则自动换算到固定物理距离并单列实时药材表面。

## 图表约定

- 所有图题、坐标轴和图例均使用中文。
- 温度曲线使用橙红色圆点线，干基含水率曲线使用蓝色方点线，避免黑白之外难以区分。
- 横坐标统一为“距药材中心的距离（cm）”；纵坐标分别为“温度（℃）”和“干基含水率（kg/kg）”。
- 绘图模块会依次尝试微软雅黑、黑体、思源黑体等中文字体；若本机仍出现方框，请安装其中任意一种字体后重新运行。

## 建议开发顺序

1. 完成并核验问题1。
2. 将有限端面写入模型局限性；如需敏感性分析，再显式启用旧均匀源试算。
3. 在同一固定半径内核上切换问题2/3物性。
4. 加入问题3的含水率阈值事件。
5. 使用归一化径向坐标处理问题4的收缩半径。
6. 最后接入官方 Excel 模板和论文图表。

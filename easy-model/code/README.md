# 2025A 烟幕干扰弹投放策略 —— 求解代码

## 依赖

```bash
python3 -m ensurepip --user
python3 -m pip install --user numpy scipy openpyxl matplotlib
```

（Python ≥ 3.9，需 `numpy`、`scipy`、`openpyxl`、`matplotlib`。）

## 运行

```bash
python3 run_all.py           # 求解 Q1~Q5，默认随机种子 42
python3 run_all.py 7         # 换随机种子（可多试几个取最好）
python3 multi_seed.py        # 多种子稳健性评估
python3 visualize.py         # 生成图表（几何图/时间线/结果/代码结构）
```

`run_all.py` 求解 Q1~Q5，并在 **easy-model 根目录**生成：
- `result1_out.xlsx`（Q3，FY1 三弹）
- `result2_out.xlsx`（Q4，三机各一弹）
- `result3_out.xlsx`（Q5，5 机 15 弹）

`visualize.py` 在 `../figures/` 生成 6 张 PNG 图表（见下）。

## 文件结构

| 文件 | 作用 |
|---|---|
| `core.py` | 常量、运动学（导弹/无人机/炸弹/云团）、遮蔽判定、遮蔽时长求值（引擎） |
| `solver.py` | 全局优化求解器（差分进化 + 视线锚定参数化 + 罚函数） |
| `q1.py` | Q1 确定性计算（锚点 ≈ 1.435 s） |
| `q2.py` | Q2 单弹优化 |
| `q3.py` | Q3 FY1 三弹优化 |
| `q4.py` | Q4 三机各一弹优化 |
| `q5.py` | Q5 多机多弹多导弹（分配 + 逐弹优化 + 目标(a)合并） |
| `write_xlsx.py` | 结果写回官方 xlsx 模板（模板从 `../strict-model/` 读取） |
| `run_all.py` | 一键运行入口 |
| `multi_seed.py` | 多种子稳健性评估 |
| `visualize.py` | 生成图表 |

## 图表（`../figures/`）

| 图 | 内容 |
|---|---|
| `fig1_几何三维图.png` | 场景三维图（导弹轨迹/无人机/真目标圆柱/假目标 + Q4 最优云团） |
| `fig2_Q1_Q4遮蔽时间线.png` | Q1~Q4 各弹云团存活窗口与有效遮蔽区间 |
| `fig3_Q5遮蔽时间线.png` | Q5 逐导弹遮蔽区间 + 同时遮蔽 |
| `fig4_结果汇总.png` | 各问求解结果柱状图 |
| `fig5_代码结构.png` | 代码模块依赖图 |

> 几何三维图的 **MATLAB 版**在 `../matlab/plot_geometry_3d.m`（含 Q4 最优云团参数，可直接运行出图）。

## 核心模型（详见 ../model-design.md）

- 遮蔽判定：云团球（半径 10 m）与"导弹→真目标中心 `(0,200,5)`"视线**线段相交**（最短距离 ≤10 m）。
- 有效遮蔽时长：导弹命中假目标（约 60~67 s）前，视线被至少一枚活云团遮挡的时间并集长度。
- Q5 目标 (a)：真目标同时被所有仍在飞行的导弹视线遮挡的总时长。

## 已知限制 / 调参建议

1. **优化质量**：Q2~Q5 用差分进化（`solver.py` 里 `popsize`/`maxiter`）求解，属启发式，结果随随机种子波动。可多试几个 seed、增大 `maxiter`，或改用更细 `dt`。
2. **Q5 的分配是启发式**（按 y 坐标就近分配无人机给导弹），未做弹-导弹的最优组合分配；`q5.py` 里 `ASSIGN` 可改。
3. **性能**：`dt=1e-4` 每次评估约 0.3 s，多弹维度高时较慢；粗搜索用 `dt=0.02`。
4. **近似**：真目标近似为几何中心点 `C=(0,200,5)`；未建模风、无人机碰撞、导弹变轨。

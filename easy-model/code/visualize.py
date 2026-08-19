# -*- coding: utf-8 -*-
"""
visualize.py —— 模型/数据/代码可视化

生成 PNG 图到 ../figures/：
  fig1_几何三维图.png     场景三维图(导弹轨迹/无人机/目标/假目标 + Q4 最优云团)
  fig2_Q1_Q4遮蔽时间线.png  Q1~Q4 各弹云团存活窗口与有效遮蔽区间
  fig3_Q5遮蔽时间线.png     Q5 逐导弹遮蔽区间 + 同时遮蔽
  fig4_结果汇总.png         各问求解结果柱状图
  fig5_代码结构.png         代码模块依赖图

用法：python3 visualize.py   （会重跑 Q1~Q5 求解，约 6~8 分钟）
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrow

import core
import q1, q2, q3, q4, q5

# ---------------------------------------------------------------- 样式
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['axes.edgecolor'] = '#52514e'
plt.rcParams['axes.labelcolor'] = '#0b0b0b'
plt.rcParams['xtick.color'] = '#52514e'
plt.rcParams['ytick.color'] = '#52514e'
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.color'] = '#e3e2de'
plt.rcParams['grid.linewidth'] = 0.6

# 分类色（固定顺序）：导弹 M1/M2/M3
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
RED = '#e34948'
INK, INK2 = '#0b0b0b', '#52514e'
MISSILE_COLOR = {'M1': BLUE, 'M2': ORANGE, 'M3': AQUA}

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGDIR = os.path.join(BASE, 'figures')


def _save(fig, name):
    os.makedirs(FIGDIR, exist_ok=True)
    path = os.path.join(FIGDIR, name)
    fig.savefig(path, dpi=160, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('  生成', path)


# ---------------------------------------------------------------- 几何图
def _cylinder_3d(ax, cx, cy, z0, r, h, color, alpha=0.55):
    """竖直圆柱（底面圆心 (cx,cy,z0)，半径 r，高 h）。"""
    th = np.linspace(0, 2 * np.pi, 48)
    z = np.linspace(z0, z0 + h, 6)
    th, z = np.meshgrid(th, z)
    x = cx + r * np.cos(th)
    y = cy + r * np.sin(th)
    ax.plot_surface(x, y, z, color=color, alpha=alpha, linewidth=0)


def _sphere_3d(ax, cx, cy, cz, r, color, alpha=0.28):
    """球（心 (cx,cy,cz)，半径 r）。"""
    u, v = np.mgrid[0:2 * np.pi:24j, 0:np.pi:14j]
    x = cx + r * np.cos(u) * np.sin(v)
    y = cy + r * np.sin(u) * np.sin(v)
    z = cz + r * np.cos(v)
    ax.plot_surface(x, y, z, color=color, alpha=alpha, linewidth=0)


def fig_geometry(r4):
    fig = plt.figure(figsize=(11, 7.5))
    ax = fig.add_subplot(111, projection='3d')

    # 导弹轨迹（起点 -> 假目标原点）
    for m in ['M1', 'M2', 'M3']:
        p0 = core.MISSILES[m]
        ax.plot([p0[0], 0], [p0[1], 0], [p0[2], 0],
                color=MISSILE_COLOR[m], lw=1.6)
        ax.text(p0[0], p0[1], p0[2] + 150, ' ' + m, color=MISSILE_COLOR[m],
                fontsize=9, fontweight='bold')

    # 无人机初始位置
    for u, p in core.UAVS.items():
        ax.scatter(p[0], p[1], p[2], marker='s', s=28, c='white',
                   edgecolors=INK2, linewidths=1.1)
        ax.text(p[0], p[1], p[2] + 140, u, color=INK2, fontsize=8)

    # 真目标（圆柱 r=7,h=10）与假目标（原点）
    _cylinder_3d(ax, 0, 200, 0, 7, 10, RED, alpha=0.6)
    ax.text(0, 200, 70, '真目标', color=RED, fontsize=9, fontweight='bold')
    ax.scatter([0], [0], [0], marker='x', s=40, color=INK)
    ax.text(0, -350, 100, '假目标(原点)', color=INK, fontsize=9)

    # Q4 最优云团（3 架无人机各 1 弹）+ 投放轨迹
    if r4 is not None:
        for b in r4['bombs']:
            D = core.bomb_pos(b['uav'], b['theta'], b['v'], b['t_drop'], b['delta'])
            _sphere_3d(ax, D[0], D[1], D[2], 10, BLUE, alpha=0.28)
            drop = core.uav_pos(b['uav'], b['theta'], b['v'], b['t_drop'])
            ax.plot([drop[0], D[0]], [drop[1], D[1]], [drop[2], D[2]],
                    ls='--', lw=0.9, color=BLUE, alpha=0.6)

    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.set_zlabel('z (m)')
    ax.set_xlim(-500, 20500)
    ax.set_ylim(-3300, 2300)
    ax.set_zlim(0, 2400)
    ax.set_box_aspect((1.4, 0.6, 0.7))
    ax.set_title('烟幕干扰弹投放场景三维图（蓝球为 Q4 最优云团，虚线为投放轨迹）', fontsize=12)
    _save(fig, 'fig1_几何三维图.png')


# ---------------------------------------------------------------- 遮蔽时间线
def _timeline(ax, bombs, missiles_of_bomb, title, t_end, ylabels):
    """画 Gantt 时间线：浅色=云团存活窗口，深色=有效遮蔽区间。"""
    for i, b in enumerate(bombs):
        m = missiles_of_bomb[i]
        t_det = b['t_drop'] + b['delta']
        alive_end = min(t_det + core.CLOUD_LIFE, t_end)
        if alive_end > t_det:
            ax.barh(i, alive_end - t_det, left=t_det, height=0.34,
                    color=MISSILE_COLOR[m], alpha=0.25)
        iv, _ = core.shielding_intervals([b], m, dt=1e-3)
        for a, bb in iv:
            ax.barh(i, min(bb, t_end) - a, left=a, height=0.34,
                    color=MISSILE_COLOR[m], alpha=1.0)
    ax.set_yticks(range(len(bombs)))
    ax.set_yticklabels(ylabels, fontsize=8)
    ax.set_xlim(0, t_end)
    ax.set_xlabel('时间 t (s)')
    ax.set_title(title, fontsize=11)
    ax.invert_yaxis()


def fig_timelines(r2, r3, r4, r5):
    # Q1
    bombs1, iv1, _ = q1.solve()
    fig, axes = plt.subplots(2, 2, figsize=(13, 7))
    _timeline(axes[0, 0], bombs1, ['M1'], 'Q1：FY1 单弹（给定）',
              core.missile_impact_time('M1'), ['弹1'])
    _timeline(axes[0, 1], [{'uav': 'FY1', 'theta': r2['theta'], 'v': r2['v'],
                            't_drop': r2['t_drop'], 'delta': r2['delta']}], ['M1'],
              'Q2：FY1 单弹（最优）', core.missile_impact_time('M1'), ['弹1'])
    _timeline(axes[1, 0], r3['bombs'], ['M1'] * 3, 'Q3：FY1 三弹',
              core.missile_impact_time('M1'), ['弹1', '弹2', '弹3'])
    _timeline(axes[1, 1], r4['bombs'], ['M1'] * 3, 'Q4：三机各一弹',
              core.missile_impact_time('M1'), ['FY1', 'FY2', 'FY3'])
    fig.suptitle('各问遮蔽时间线（深色=有效遮蔽区间，浅色=云团存活窗口）', fontsize=12)
    _save(fig, 'fig2_Q1_Q4遮蔽时间线.png')


def fig_q5_timeline(r5):
    bombs = []
    missiles = []
    ylabels = []
    for m in ['M1', 'M2', 'M3']:
        for b in r5['bombs_by_missile'][m]:
            bombs.append(b)
            missiles.append(m)
            ylabels.append(f"{b['uav']}→{m}")
    fig, ax = plt.subplots(figsize=(10, 6))
    _timeline(ax, bombs, missiles, 'Q5：5 机 15 弹逐导弹遮蔽时间线',
              core.missile_impact_time('M1'), ylabels)
    # 标题标注同时遮蔽时长
    sim_total = r5['sim_total']
    ax.text(0.5, 1.02, f'同时遮蔽时长(a) = {sim_total:.2f} s',
            transform=ax.transAxes, ha='center', color=RED, fontsize=11)
    fig.tight_layout()
    _save(fig, 'fig3_Q5遮蔽时间线.png')


# ---------------------------------------------------------------- 结果汇总
def fig_results():
    labels = ['Q1\n给定', 'Q2\n单弹\n最优', 'Q3\n三弹', 'Q4\n三机', 'Q5(b)\n逐导弹\n求和', 'Q5(a)\n同时\n遮蔽']
    vals = [1.4350, 4.8314, 6.4655, 16.5156, 23.63, 1.0335]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    bars = ax.bar(range(len(vals)), vals, color=[BLUE, BLUE, BLUE, BLUE, AQUA, ORANGE],
                  width=0.62, zorder=3)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.5, f'{v:.2f}s', ha='center', color=INK, fontsize=10, fontweight='bold')
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel('有效遮蔽时长 (s)')
    ax.set_title('各问求解结果（Q1~Q4 为对 M1；Q5 分 (b) 求和 与 (a) 同时遮蔽）', fontsize=11)
    ax.set_ylim(0, 26)
    ax.grid(axis='y')
    _save(fig, 'fig4_结果汇总.png')


# ---------------------------------------------------------------- 代码结构
def fig_code_structure():
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axis('off')
    ax.set_xlim(0, 10); ax.set_ylim(0, 8)
    nodes = {
        'core.py': (1.0, 1.0), 'solver.py': (1.0, 3.2),
        'q1.py': (3.4, 5.6), 'q2.py': (4.8, 5.6), 'q3.py': (6.2, 5.6),
        'q4.py': (3.4, 4.2), 'q5.py': (4.8, 4.2),
        'write_xlsx.py': (6.2, 3.0), 'run_all.py': (4.0, 1.6), 'multi_seed.py': (6.6, 1.6),
    }
    edges = [('solver.py', 'core.py'), ('q1.py', 'core.py'), ('q2.py', 'core.py'),
             ('q3.py', 'core.py'), ('q4.py', 'core.py'), ('q5.py', 'core.py'),
             ('q2.py', 'solver.py'), ('q3.py', 'solver.py'), ('q4.py', 'solver.py'),
             ('q5.py', 'solver.py'), ('write_xlsx.py', 'core.py'),
             ('run_all.py', 'q1.py'), ('run_all.py', 'q2.py'), ('run_all.py', 'q3.py'),
             ('run_all.py', 'q4.py'), ('run_all.py', 'q5.py'), ('run_all.py', 'write_xlsx.py'),
             ('multi_seed.py', 'q1.py'), ('multi_seed.py', 'q2.py'), ('multi_seed.py', 'q3.py'),
             ('multi_seed.py', 'q4.py'), ('multi_seed.py', 'q5.py'), ('multi_seed.py', 'write_xlsx.py')]
    for a, b in edges:
        (xa, ya), (xb, yb) = nodes[a], nodes[b]
        ax.plot([xa, xb], [ya, yb], color='#c9c7c2', lw=1.0, zorder=1)
    for name, (x, y) in nodes.items():
        ax.add_patch(plt.Rectangle((x - 0.75, y - 0.4), 1.5, 0.8, fc='#eef3fb',
                                   ec=BLUE, lw=1.2, zorder=3))
        ax.text(x, y, name, ha='center', va='center', fontsize=9, color=INK)
    ax.set_title('代码模块依赖结构（箭头指向被依赖模块）', fontsize=12)
    _save(fig, 'fig5_代码结构.png')


if __name__ == '__main__':
    print('开始求解（Q1~Q5）并生成图表...')
    r2 = q2.solve()
    r3 = q3.solve()
    r4 = q4.solve()
    r5 = q5.solve()
    fig_geometry(r4)
    fig_timelines(r2, r3, r4, r5)
    fig_q5_timeline(r5)
    fig_results()
    fig_code_structure()
    print(f'\n完成，图表在 {FIGDIR}/')

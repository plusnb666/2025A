# -*- coding: utf-8 -*-
"""
q1.py —— 问题 1（确定性计算）

FY1 以 120 m/s 朝向假目标方向飞行，受领任务 1.5 s 后投放 1 枚烟幕干扰弹，
间隔 3.6 s 后起爆。求该弹对 M1 的有效遮蔽时长。

给定参数：航向 theta=180°（朝原点，速度向量 (-120,0,0)），v=120 m/s，
          t_drop=1.5 s，delta=3.6 s。
"""
import core


def solve(dt=1e-4):
    bombs = [{
        'uav': 'FY1',
        'theta': 180.0,
        'v': 120.0,
        't_drop': 1.5,
        'delta': 3.6,
    }]
    intervals, total = core.shielding_intervals(bombs, 'M1', dt=dt)
    return bombs, intervals, total


if __name__ == '__main__':
    bombs, intervals, total = solve()
    drop = core.uav_pos('FY1', 180.0, 120.0, 1.5)
    det = core.bomb_pos('FY1', 180.0, 120.0, 1.5, 3.6)
    print(f"投放点  : ({drop[0]:.2f}, {drop[1]:.2f}, {drop[2]:.2f})")
    print(f"起爆点  : ({det[0]:.2f}, {det[1]:.2f}, {det[2]:.2f})")
    print(f"遮蔽区间: {[(round(a,4), round(b,4)) for a,b in intervals]}")
    print(f"有效遮蔽时长 = {total:.4f} s")

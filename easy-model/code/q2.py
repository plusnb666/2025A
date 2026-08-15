# -*- coding: utf-8 -*-
"""
q2.py —— 问题 2（单弹优化）

利用 FY1 投放 1 枚烟幕干扰弹干扰 M1，确定航向、速度、投放点、起爆点，
使遮蔽时间尽可能长。调用 solver.optimize_single（平滑代理引导 + 全局优化）。
"""
import solver


def solve(seed=42, verbose=False):
    return solver.optimize_single('FY1', 'M1', seed=seed, verbose=verbose)


if __name__ == '__main__':
    r = solve(verbose=True)
    print(f"航向 theta = {r['theta']:.2f}°")
    print(f"速度 v     = {r['v']:.2f} m/s")
    print(f"投放时刻   = {r['t_drop']:.3f} s")
    print(f"引信延迟   = {r['delta']:.3f} s")
    print(f"起爆点 D   = ({r['D'][0]:.1f}, {r['D'][1]:.1f}, {r['D'][2]:.1f})")
    print(f"遮蔽区间   = {[(round(a,3), round(b,3)) for a,b in r['intervals']]}")
    print(f"有效遮蔽时长 = {r['total']:.4f} s")

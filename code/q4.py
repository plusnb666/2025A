# -*- coding: utf-8 -*-
"""
q4.py —— 问题 4（FY1/FY2/FY3 各投 1 弹干扰 M1）

三架无人机各投 1 枚烟幕干扰弹，共同干扰 M1。输出到 result2.xlsx。
"""
import solver


def solve(seed=42, verbose=False):
    return solver.optimize_multi(['FY1', 'FY2', 'FY3'], 'M1', seed=seed, verbose=verbose)


if __name__ == '__main__':
    r = solve(verbose=True)
    print(f"总有效遮蔽时长 = {r['total']:.4f} s")
    print(f"遮蔽区间 = {[(round(a,3), round(b,3)) for a,b in r['intervals']]}")
    for i, b in enumerate(r['bombs'], 1):
        print(f"  弹{i}({b['uav']}): theta={b['theta']:.2f}° v={b['v']:.2f} "
              f"t_drop={b['t_drop']:.3f} delta={b['delta']:.3f}")

# -*- coding: utf-8 -*-
"""
q3.py —— 问题 3（FY1 投 3 弹干扰 M1）

利用 FY1 投放 3 枚烟幕干扰弹干扰 M1，使遮蔽时间尽可能长。输出到 result1.xlsx。
"""
import solver


def solve(seed=42, verbose=False):
    return solver.optimize_multi(['FY1', 'FY1', 'FY1'], 'M1', seed=seed, verbose=verbose)


if __name__ == '__main__':
    r = solve(verbose=True)
    print(f"总有效遮蔽时长 = {r['total']:.4f} s")
    print(f"遮蔽区间 = {[(round(a,3), round(b,3)) for a,b in r['intervals']]}")
    for i, b in enumerate(r['bombs'], 1):
        print(f"  弹{i}: theta={b['theta']:.2f}° v={b['v']:.2f} "
              f"t_drop={b['t_drop']:.3f} delta={b['delta']:.3f}")

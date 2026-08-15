# -*- coding: utf-8 -*-
"""
run_all.py —— 依次求解 Q1~Q5 并写回 result1/2/3.xlsx。

用法：python3 run_all.py [seed]
可选参数 seed 为随机种子（默认 42）。想得到更优结果可多试几个种子取最好。
"""
import sys
import time

import q1, q2, q3, q4, q5
import write_xlsx

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 42


def main():
    print("=" * 60)
    print(f"2025A 烟幕干扰弹投放策略  求解 (seed={SEED})")
    print("=" * 60)

    # Q1
    t0 = time.time()
    _, intervals1, total1 = q1.solve()
    print(f"\n[Q1] 有效遮蔽时长 = {total1:.4f} s  区间={[(round(a,3),round(b,3)) for a,b in intervals1]}")
    print(f"     用时 {time.time()-t0:.1f}s")

    # Q2
    t0 = time.time()
    r2 = q2.solve(seed=SEED)
    print(f"\n[Q2] 有效遮蔽时长 = {r2['total']:.4f} s")
    print(f"     theta={r2['theta']:.2f}° v={r2['v']:.2f} t_drop={r2['t_drop']:.3f} delta={r2['delta']:.3f}")
    print(f"     用时 {time.time()-t0:.1f}s")

    # Q3
    t0 = time.time()
    r3 = q3.solve(seed=SEED)
    r3['bombs'].sort(key=lambda b: b['t_drop'])
    out3 = write_xlsx.write_result1(r3['bombs'])
    print(f"\n[Q3] 有效遮蔽时长 = {r3['total']:.4f} s  区间={[(round(a,3),round(b,3)) for a,b in r3['intervals']]}")
    print(f"     写入 {out3}   用时 {time.time()-t0:.1f}s")

    # Q4
    t0 = time.time()
    r4 = q4.solve(seed=SEED)
    out4 = write_xlsx.write_result2(r4['bombs'])
    print(f"\n[Q4] 有效遮蔽时长 = {r4['total']:.4f} s  区间={[(round(a,3),round(b,3)) for a,b in r4['intervals']]}")
    print(f"     写入 {out4}   用时 {time.time()-t0:.1f}s")

    # Q5
    t0 = time.time()
    r5 = q5.solve(seed=SEED)
    out5 = write_xlsx.write_result3(r5['bombs'])
    sum_b = sum(r5['per_missile'].values())
    print(f"\n[Q5] 各导弹遮蔽: " + ", ".join(f"{m}={r5['per_missile'][m]:.2f}s" for m in r5['per_missile']))
    print(f"     逐导弹总和(b) = {sum_b:.2f} s")
    print(f"     同时遮蔽时长(a) = {r5['sim_total']:.4f} s")
    print(f"     写入 {out5}   用时 {time.time()-t0:.1f}s")

    print("\n完成。")


if __name__ == '__main__':
    main()

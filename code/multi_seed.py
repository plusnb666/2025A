# -*- coding: utf-8 -*-
"""
multi_seed.py —— 多种子稳健求解

对 Q2~Q5 各跑多个随机种子，报告每个 seed 的结果与统计量，并把最优结果写回
result1/2/3_out.xlsx。用法：python3 multi_seed.py
"""
import sys
import time
import json

import q1, q2, q3, q4, q5
import write_xlsx

SEEDS_Q2 = [42, 7, 123, 2024, 999, 3]
SEEDS_Q3 = [42, 7, 123, 2024]
SEEDS_Q4 = [42, 7, 123, 2024]
SEEDS_Q5 = [42, 7, 123]


def log(*a):
    print(*a, flush=True)


def run_multi(name, fn, seeds, metric):
    log(f"\n===== {name} =====")
    best = None
    best_val = -1e9
    vals = []
    for s in seeds:
        t0 = time.time()
        try:
            r = fn(seed=s)
            v = metric(r)
            vals.append(v)
            log(f"  seed={s:5d}  {name}_value={v:.4f}  用时{time.time()-t0:.0f}s")
            if v > best_val:
                best_val = v
                best = r
        except Exception as e:
            log(f"  seed={s:5d}  FAILED: {e}")
    if vals:
        import statistics
        log(f"  -> 最优 {best_val:.4f} | 均值 {statistics.mean(vals):.4f} | 最小 {min(vals):.4f}")
    return best, best_val, vals


def main():
    out = {}

    # Q1（确定性，只跑一次）
    _, _, total1 = q1.solve()
    log(f"[Q1] 有效遮蔽时长 = {total1:.4f} s（确定性）")
    out['Q1'] = total1

    # Q2
    best, val, vals = run_multi('Q2', q2.solve, SEEDS_Q2, lambda r: r['total'])
    out['Q2'] = {'best': val, 'vals': vals, 'best_theta': best['theta'],
                 'best_v': best['v'], 'best_t_drop': best['t_drop'], 'best_delta': best['delta']}

    # Q3
    best, val, vals = run_multi('Q3', q3.solve, SEEDS_Q3, lambda r: r['total'])
    if best:
        best['bombs'].sort(key=lambda b: b['t_drop'])
        write_xlsx.write_result1(best['bombs'])
    out['Q3'] = {'best': val, 'vals': vals}

    # Q4
    best, val, vals = run_multi('Q4', q4.solve, SEEDS_Q4, lambda r: r['total'])
    if best:
        write_xlsx.write_result2(best['bombs'])
    out['Q4'] = {'best': val, 'vals': vals}

    # Q5（b 与 a 分别追踪）
    log(f"\n===== Q5 =====")
    best_b = None; best_b_val = -1e9
    best_a = None; best_a_val = -1e9
    vals_b, vals_a = [], []
    for s in SEEDS_Q5:
        t0 = time.time()
        r = q5.solve(seed=s)
        vb = sum(r['per_missile'].values())
        va = r['sim_total']
        vals_b.append(vb); vals_a.append(va)
        log(f"  seed={s:5d}  (b)={vb:.2f}s  (a)={va:.4f}s  用时{time.time()-t0:.0f}s")
        if vb > best_b_val:
            best_b_val = vb; best_b = r
        if va > best_a_val:
            best_a_val = va; best_a = r
    if best_b:
        write_xlsx.write_result3(best_b['bombs'])
    out['Q5_b'] = {'best': best_b_val, 'vals': vals_b}
    out['Q5_a'] = {'best': best_a_val, 'vals': vals_a}

    log("\n========== 汇总 ==========")
    log(f"Q1 = {out['Q1']:.4f} s")
    log(f"Q2 = {out['Q2']['best']:.4f} s (seeds={out['Q2']['vals']})")
    log(f"Q3 = {out['Q3']['best']:.4f} s (seeds={out['Q3']['vals']})")
    log(f"Q4 = {out['Q4']['best']:.4f} s (seeds={out['Q4']['vals']})")
    log(f"Q5(b) = {out['Q5_b']['best']:.2f} s (seeds={out['Q5_b']['vals']})")
    log(f"Q5(a) = {out['Q5_a']['best']:.4f} s (seeds={out['Q5_a']['vals']})")

    with open('multi_seed_summary.json', 'w') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    log("\n已写 best 结果到 result1/2/3_out.xlsx，摘要到 multi_seed_summary.json")


if __name__ == '__main__':
    main()

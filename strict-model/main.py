"""CUMCM 2025A 主运行脚本 —— 求解问题3/4/5 并填表 result1/2/3.xlsx。"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import time
from problems import solve_q3, solve_q4, solve_q5
from fill_result import fill_result1, fill_result2, fill_result3


def q3_infos(x):
    theta, v, t_r1, dt1, g2, dt2, g3, dt3 = x
    return [(1, theta, v, t_r1, dt1),
            (1, theta, v, t_r1 + g2, dt2),
            (1, theta, v, t_r1 + g2 + g3, dt3)]


def q4_infos(x):
    out = []
    for i in range(3):
        theta, v, t_r, dt_ = x[4 * i:4 * i + 4]
        out.append((i + 1, theta, v, t_r, dt_))
    return out


def q5_entries(results):
    entries = []
    for k in (1, 2, 3):
        x = results[k]['x']; spec = results[k]['spec']
        idx = 0
        for drone_id, nb in spec:
            theta, v = x[idx], x[idx + 1]; idx += 2
            t_r = x[idx]; dt0 = x[idx + 1]; idx += 2
            t_rs, dts = [t_r], [dt0]
            for _ in range(1, nb):
                g = x[idx]; dtj = x[idx + 1]; idx += 2
                t_rs.append(t_rs[-1] + g); dts.append(dtj)
            for j, (tr, dtj) in enumerate(zip(t_rs, dts), start=1):
                entries.append((drone_id, j, (drone_id, theta, v, tr, dtj), k))
    return entries


if __name__ == '__main__':
    t_all = time.time()

    t0 = time.time()
    r3 = solve_q3()
    fill_result1(q3_infos(r3['x']))
    print('Q3: T=%.3f  (%.0fs)' % (r3['T'], time.time() - t0), flush=True)

    t0 = time.time()
    r4 = solve_q4()
    fill_result2(q4_infos(r4['x']))
    print('Q4: T=%.3f  (%.0fs)' % (r4['T'], time.time() - t0), flush=True)

    t0 = time.time()
    r5 = solve_q5()
    fill_result3(q5_entries(r5['results']))
    print('Q5: sum=%.3f  min=%.3f  sim=%.3f  (%.0fs)'
          % (r5['T_sum'], r5['T_min'], r5['T_sim'], time.time() - t0), flush=True)
    for k in (1, 2, 3):
        print('  M%d: T=%.3f' % (k, r5['results'][k]['T']), flush=True)

    print('总计 %.0fs' % (time.time() - t_all), flush=True)

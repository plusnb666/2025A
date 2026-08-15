# -*- coding: utf-8 -*-
"""
q5.py —— 问题 5（5 机、每机≤3 弹，干扰 M1/M2/M3）

两种目标都给出：
  (b) 逐导弹遮蔽时长：按 y 坐标就近分配无人机（FY1→M1；FY2/FY4→M2；FY3/FY5→M3），
      每机为分配导弹投 ≤3 弹、独立优化，逐导弹取并集时长，再求和。
  (a) 同时遮蔽时长：每枚导弹取一架最适无人机投 1 弹，联合调度时序，
      使三枚导弹视线同时被挡的时间尽量长（平滑代理引导 + 差分进化）。

输出到 result3.xlsx（用 (b) 的逐弹分配结果填表）。
"""
import numpy as np
from scipy.optimize import differential_evolution
import core
import solver

# 分配：导弹 -> 负责干扰它的无人机列表（每机至多投 3 弹）
ASSIGN = {
    'M1': ['FY1'],
    'M2': ['FY2', 'FY4'],
    'M3': ['FY3', 'FY5'],
}

# 目标 (a) 联合调度：每枚导弹取一架最适无人机投 1 弹
SIM_ASSIGN = [('M1', 'FY1'), ('M2', 'FY2'), ('M3', 'FY5')]


# ---------------------------------------------------------------- (b) 逐导弹
def solve_b(seed=42, verbose=False):
    bombs_by_missile = {m: [] for m in ASSIGN}
    for missile, uavs in ASSIGN.items():
        for uav in uavs:
            r = solver.optimize_multi([uav] * 3, missile, seed=seed, verbose=verbose)
            for b in r['bombs']:
                b['missile'] = missile
                bombs_by_missile[missile].append(b)
    per_missile = {m: core.shielding_time(bombs_by_missile[m], m, dt=1e-4)
                   for m in ASSIGN}
    rows = [b for m in ASSIGN for b in bombs_by_missile[m]]
    return {'bombs': rows, 'bombs_by_missile': bombs_by_missile, 'per_missile': per_missile}


# ---------------------------------------------------------------- (a) 联合调度
def _decode_simultaneous(x):
    """x: [T_ref, s1,off1, s2,off2, s3,off3]（共享参考时刻 T_ref）。

    令云团在 T_ref 时刻精确落在各自导弹视线的 3D 点上（dist=0），
    保证三枚导弹在 T_ref 附近同时被遮蔽。offset 为起爆提前量（=T_ref−t_det）。
    """
    T_ref = float(x[0])
    bbm = {m: [] for m, _ in SIM_ASSIGN}
    pen = 0.0
    for i, (m, uav) in enumerate(SIM_ASSIGN):
        s = float(x[1 + 2 * i])
        offset = float(x[2 + 2 * i])
        P = core.missile_pos(m, T_ref)
        D_xy = (1.0 - s) * P[:2] + s * core.CENTER[:2]
        LOS_z = (1.0 - s) * P[2] + s * core.CENTER[2]
        D_z = LOS_z + core.SINK_SPEED * offset      # 云团沉 offset 秒后正好到视线高度
        t_det = T_ref - offset
        if t_det <= 0.0:
            return None, 1e6 - t_det * 100.0
        U0 = core.UAVS[uav]
        z0 = U0[2]
        r = np.hypot(D_xy[0] - U0[0], D_xy[1] - U0[1])
        v = r / t_det
        delta2 = (z0 - D_z) / (0.5 * core.G)
        if delta2 < 0.0:
            return None, 1e6 + (D_z - z0) * 100.0
        delta = float(np.sqrt(delta2))
        t_drop = t_det - delta
        if t_drop < 0.0:
            pen += (0.0 - t_drop) * 20.0
        if v < core.V_MIN:
            pen += (core.V_MIN - v) * 5.0
        elif v > core.V_MAX:
            pen += (v - core.V_MAX) * 5.0
        theta = float(np.degrees(np.arctan2(D_xy[1] - U0[1], D_xy[0] - U0[0])) % 360.0)
        D = np.array([D_xy[0], D_xy[1], D_z])
        bbm[m].append({'uav': uav, 'theta': theta, 'v': float(v),
                       't_drop': t_drop, 'delta': delta, 'missile': m})
    return bbm, pen


def _joint_surrogate(x, radius, dt):
    bbm, pen = _decode_simultaneous(x)
    if bbm is None:
        return pen
    T_end = max(core.missile_impact_time(m) for m in bbm)
    t = np.arange(0.0, T_end + dt, dt)
    Cs = [core.closeness_array(bbm[m], m, radius, t) for m in bbm]
    joint = np.minimum.reduce(Cs)
    return -float(joint.sum()) * dt + pen


def solve_a(seed=42, verbose=False):
    Tmax = core.missile_impact_time('M1')
    bounds = [(0.0, Tmax)]
    for _ in SIM_ASSIGN:
        bounds += [(0.0, 1.0), (1.0, core.CLOUD_LIFE)]   # offset>=1s 强制云团上方起爆下沉

    # 阶段 1：宽半径代理引导
    res = differential_evolution(lambda x: _joint_surrogate(x, 40.0, 0.02), bounds,
                                 seed=seed, popsize=20, maxiter=400, tol=1e-4,
                                 polish=False, init='latinhypercube', disp=False, workers=1)
    x = res.x
    # 阶段 2：收紧半径
    res = differential_evolution(lambda x: _joint_surrogate(x, 12.0, 0.01), bounds,
                                 seed=seed, popsize=15, maxiter=300, tol=1e-4,
                                 polish=False, init='latinhypercube', disp=False, workers=1)
    x = res.x

    bbm, _ = _decode_simultaneous(x)
    total = core.simultaneous_shielding_time(bbm, dt=1e-4)
    return {'bombs_by_missile': bbm, 'total': total}


def solve(seed=42, verbose=False):
    rb = solve_b(seed=seed, verbose=verbose)
    ra = solve_a(seed=seed)
    return {'bombs': rb['bombs'], 'bombs_by_missile': rb['bombs_by_missile'],
            'per_missile': rb['per_missile'],
            'sim_total': ra['total'], 'sim_bombs': ra['bombs_by_missile'],
            'total': ra['total']}


if __name__ == '__main__':
    r = solve(verbose=True)
    print("各导弹遮蔽时长: " + ", ".join(f"{m}={r['per_missile'][m]:.2f}s" for m in r['per_missile']))
    print(f"逐导弹总和(b) = {sum(r['per_missile'].values()):.2f} s")
    print(f"同时遮蔽时长(a) = {r['sim_total']:.4f} s")
    for m in r['sim_bombs']:
        for b in r['sim_bombs'][m]:
            D = core.bomb_pos(b['uav'], b['theta'], b['v'], b['t_drop'], b['delta'])
            print(f"  [{m}] {b['uav']}: theta={b['theta']:.1f} v={b['v']:.1f} "
                  f"D=({D[0]:.0f},{D[1]:.0f},{D[2]:.0f}) t_det={b['t_drop']+b['delta']:.1f}")


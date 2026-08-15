"""CUMCM 2025A 求解模块 —— 问题 2~5 优化。

代理目标（破解 0 平台）：
    fit = T - lam*min_dist_sum + mu*F + nu*M   （最大化，DE 取负）
- T     遮蔽总时长（多弹并集）
- min_dist_sum  各烟幕球到"导弹→目标视线"的最小距离之和（引导爬向可行流形）
- F     遮挡率积分（破平局）
- M     深度裕量积分（把解推向"遮得最深"的中心）

目标函数均为模块级函数 + 全局 _CFG，供 multiprocessing(fork) 并行。
"""
import multiprocessing as _mp
try:
    _mp.set_start_method('fork', force=True)   # scipy1.18/Py3.12 默认 forkserver 无法反序列化 __main__ 函数
except RuntimeError:
    pass
import numpy as np
from scipy.optimize import differential_evolution
from model import *


# ======================================================================
# 遮蔽指标
# ======================================================================

def shield_all(k, bombs, sample_pts, dt, t_end=None):
    """返回 (T, F, M, min_dist_sum)。"""
    if t_end is None:
        t_end = hit_time(k)
    tds = [td for _, td in bombs]
    lo = max(0.0, min(tds))
    hi = min(t_end, max(td + DURATION for td in tds))
    if hi <= lo:
        return 0.0, 0.0, 0.0, 0.0
    t = np.arange(lo, hi + dt, dt)
    Mpos = missile_pos(k, t)
    n_p, n_t = len(sample_pts), len(t)
    union = np.full((n_p, n_t), -np.inf)
    min_dist_sum = 0.0
    for det, td in bombs:
        active = (t >= td - 1e-9) & (t <= td + DURATION + 1e-9)
        C = smoke_centers(det, td, t)
        bm = np.full((n_p, n_t), -np.inf)
        for qi, Q in enumerate(sample_pts):
            d = seg_dist(C, Mpos, Q)
            bm[qi] = np.where(active, R_SMOKE - d, -np.inf)
        min_dist_sum += float(R_SMOKE - bm.max())   # 该球到视线的最小距离
        union = np.maximum(union, bm)
    occ = union.min(axis=0) >= 0.0
    f = (union >= 0.0).mean(axis=0)
    mw = union.min(axis=0)
    return (dt * occ.sum(), dt * f.sum(),
            dt * np.maximum(mw, 0.0).sum(), min_dist_sum)


# ======================================================================
# 全局配置（DE 并行子进程经 fork 继承）
# ======================================================================

_CFG = dict(k=1, sample=None, dt=0.02, t_end=None,
            lam=1.0, mu=0.01, nu=0.001)

# DE 导航阶段的粗采样与粗 dt（最终核验用精细采样 + 细 dt，见 solve 内的 fine 重估）
_SAMPLE_DE = cylinder_surface(12, 2)   # 侧壁 3 层×12 + 上下圆盘 ≈ 50 点
_DT_DE = 0.1


def _fit(bombs):
    T, F, M, md = shield_all(_CFG['k'], bombs, _CFG['sample'], _CFG['dt'], _CFG['t_end'])
    return -(T - _CFG['lam'] * md + _CFG['mu'] * F + _CFG['nu'] * M)


def _report(bombs, dt_fine=0.001):
    """精报：细 dt 下的 (T, F, M)。"""
    return shield_all(_CFG['k'], bombs, _CFG['sample'], dt_fine, _CFG['t_end'])


# ======================================================================
# 解码 + 目标函数（模块级，可 pickle）
# ======================================================================

def _q2_bombs(x):
    theta, v, t_r, dt_ = x
    det, td = detonation(1, theta, v, t_r, dt_)
    return [(det, td)]


def _q2_obj(x):
    return _fit(_q2_bombs(x))


def _q3_bombs(x):
    theta, v, t_r1, dt1, g2, dt2, g3, dt3 = x
    out = []
    for t_r, dt_ in ((t_r1, dt1), (t_r1 + g2, dt2), (t_r1 + g2 + g3, dt3)):
        det, td = detonation(1, theta, v, t_r, dt_)
        out.append((det, td))
    return out


def _q3_obj(x):
    return _fit(_q3_bombs(x))


def _q4_bombs(x):
    out = []
    for i in range(3):
        theta, v, t_r, dt_ = x[4 * i:4 * i + 4]
        det, td = detonation(i + 1, theta, v, t_r, dt_)
        out.append((det, td))
    return out


def _q4_obj(x):
    return _fit(_q4_bombs(x))


# ======================================================================
# 求解入口
# ======================================================================

def _dt_max(i):
    return np.sqrt(2.0 * DRONES[i][2] / G)


def _run_de(obj, bounds, popsize, maxiter, workers, seed):
    return differential_evolution(obj, bounds, workers=workers, seed=seed,
                                  popsize=popsize, maxiter=maxiter,
                                  tol=1e-4, polish=False, disp=False)


def solve_q2(dt=0.02, workers=-1, seed=0, maxiter=400, popsize=15):
    _CFG.update(k=1, sample=cylinder_circles(48), dt=dt, t_end=hit_time(1),
                lam=1.0, mu=0.01, nu=0.001)
    bounds = [(0.0, 360.0), (70.0, 140.0), (0.0, 30.0), (0.0, _dt_max(1))]
    res = _run_de(_q2_obj, bounds, popsize, maxiter, workers, seed)
    bombs = _q2_bombs(res.x)
    Tf, _, _, _ = shield_all(1, bombs, _CFG['sample'], 0.001, hit_time(1))
    theta, v, t_r, dt_ = res.x
    det, td = detonation(1, theta, v, t_r, dt_)
    return dict(theta=theta, v=v, t_r=t_r, dt=dt_, det=det, t_d=td,
                T=Tf, nfev=res.nfev)


def solve_q3(dt=0.1, workers=-1, seed=0, maxiter=150, popsize=15):
    _CFG.update(k=1, sample=_SAMPLE_DE, dt=dt, t_end=hit_time(1),
                lam=1.0, mu=0.01, nu=0.001)
    dm = _dt_max(1)
    bounds = [(0.0, 360.0), (70.0, 140.0),
              (0.0, 10.0), (0.0, dm), (1.0, 6.0), (0.0, dm),
              (1.0, 6.0), (0.0, dm)]
    res = _run_de(_q3_obj, bounds, popsize, maxiter, workers, seed)
    bombs = _q3_bombs(res.x)
    fine = cylinder_surface(48, 4)
    Tf, _, _, _ = shield_all(1, bombs, fine, 0.001, hit_time(1))
    return dict(x=res.x, bombs=bombs, T=Tf, nfev=res.nfev)


def solve_q4(dt=0.1, workers=-1, seed=0, maxiter=150, popsize=15):
    _CFG.update(k=1, sample=_SAMPLE_DE, dt=dt, t_end=hit_time(1),
                lam=1.0, mu=0.01, nu=0.001)
    bounds = []
    for i in (1, 2, 3):
        bounds += [(0.0, 360.0), (70.0, 140.0), (0.0, 15.0), (0.0, _dt_max(i))]
    res = _run_de(_q4_obj, bounds, popsize, maxiter, workers, seed)
    bombs = _q4_bombs(res.x)
    fine = cylinder_surface(48, 4)
    Tf, _, _, _ = shield_all(1, bombs, fine, 0.001, hit_time(1))
    return dict(x=res.x, bombs=bombs, T=Tf, nfev=res.nfev)


# ======================================================================
# 问题 5：5 机 ×≤3 弹 vs 3 导弹（分层：固定分配 + 每导弹独立 DE）
# ======================================================================

# 分配（启发式，按无人机位置与各导弹视线 y 范围的匹配）：
#   M1 视线 y∈[0,200]  ← FY1(y=0)
#   M2 视线 y∈[200,600] ← FY2(y=1400), FY4(y=2000)
#   M3 视线 y∈[-600,200] ← FY3(y=-3000), FY5(y=-2000)
Q5_ASSIGN = {
    1: [(1, 3)],              # M1 ← FY1（y=0，恰在 M1 航线）
    2: [(2, 3)],              # M2 ← FY2（+y 侧，视线 y∈[200,600]）
    3: [(5, 3)],              # M3 ← FY5（-y 侧，视线 y∈[-600,200]）
}


def _decode_spec(x, spec):
    """spec: [(drone_id, n_bombs)] → 烟幕弹列表。gap 编码满足投放间隔 ≥1 s。"""
    bombs = []
    idx = 0
    for drone_id, nb in spec:
        theta, v = x[idx], x[idx + 1]
        idx += 2
        t_r = x[idx]; dt0 = x[idx + 1]
        idx += 2
        t_rs, dts = [t_r], [dt0]
        for _ in range(1, nb):
            g = x[idx]; dtj = x[idx + 1]
            idx += 2
            t_rs.append(t_rs[-1] + g); dts.append(dtj)
        for tr, dtj in zip(t_rs, dts):
            det, td = detonation(drone_id, theta, v, tr, dtj)
            bombs.append((det, td))
    return bombs


def _spec_bounds(spec, t_r_max=15.0, gap_max=8.0):
    b = []
    for drone_id, nb in spec:
        b += [(0.0, 360.0), (70.0, 140.0)]
        b += [(0.0, t_r_max), (0.0, _dt_max(drone_id))]
        for _ in range(1, nb):
            b += [(1.0, gap_max), (0.0, _dt_max(drone_id))]
    return b


def _q5_obj(x):
    return _fit(_decode_spec(x, _CFG['spec']))


def simultaneous_time(missile_bombs, sample_pts, dt=0.001):
    """三导弹同时被完全遮蔽的总时长。missile_bombs: {k: bombs}。"""
    t_end = min(hit_time(k) for k in missile_bombs)
    all_tds = [td for bombs in missile_bombs.values() for _, td in bombs]
    lo = max(0.0, min(all_tds))
    hi = min(t_end, max(td + DURATION for td in all_tds))
    if hi <= lo:
        return 0.0
    t = np.arange(lo, hi + dt, dt)
    sim = np.ones(len(t), dtype=bool)
    for k, bombs in missile_bombs.items():
        Mpos = missile_pos(k, t)
        blocked_all = np.ones(len(t), dtype=bool)
        for Q in sample_pts:
            blocked_q = np.zeros(len(t), dtype=bool)
            for det, td in bombs:
                active = (t >= td - 1e-9) & (t <= td + DURATION + 1e-9)
                C = smoke_centers(det, td, t)
                blocked_q |= active & (seg_dist(C, Mpos, Q) <= R_SMOKE)
            blocked_all &= blocked_q
        sim &= blocked_all
    return dt * float(sim.sum())


def _add_obj(x):
    new = _decode_spec(x, _CFG['spec'])
    return _fit(_CFG['fixed'] + new)


def solve_add_drone(k, drone_id, fixed_bombs, dt=0.1, workers=-1, seed=0, maxiter=150):
    """贪心加机：给导弹 k 的 fixed_bombs 追加 drone_id 的 3 弹（独立 8 维 DE）。
    返回 (new_bombs, 联合总时长)。"""
    _CFG.update(k=k, sample=_SAMPLE_DE, dt=dt, t_end=hit_time(k),
                lam=1.0, mu=0.01, nu=0.001, spec=[(drone_id, 3)], fixed=fixed_bombs)
    dm = _dt_max(drone_id)
    bounds = [(0.0, 360.0), (70.0, 140.0), (0.0, 10.0), (0.0, dm),
              (1.0, 6.0), (0.0, dm), (1.0, 6.0), (0.0, dm)]
    res = _run_de(_add_obj, bounds, 15, maxiter, workers, seed)
    new = _decode_spec(res.x, [(drone_id, 3)])
    fine = cylinder_surface(48, 4)
    Tf, _, _, _ = shield_all(k, fixed_bombs + new, fine, 0.001, hit_time(k))
    return res.x, new, Tf


def solve_q5(dt=0.1, workers=-1, seed=0, maxiter=250, popsize=15):
    fine = cylinder_surface(48, 4)
    results = {}
    for k in (1, 2, 3):
        spec = Q5_ASSIGN[k]
        _CFG.update(k=k, sample=_SAMPLE_DE, dt=dt, t_end=hit_time(k),
                    lam=1.0, mu=0.01, nu=0.001, spec=spec)
        res = _run_de(_q5_obj, _spec_bounds(spec), popsize, maxiter, workers, seed)
        bombs = _decode_spec(res.x, spec)
        Tf, _, _, _ = shield_all(k, bombs, fine, 0.001, hit_time(k))
        results[k] = dict(x=res.x, spec=spec, bombs=bombs, T=Tf)
    T_sum = sum(results[k]['T'] for k in (1, 2, 3))
    T_min = min(results[k]['T'] for k in (1, 2, 3))
    T_sim = simultaneous_time({k: results[k]['bombs'] for k in (1, 2, 3)}, fine)
    return dict(results=results, T_sum=T_sum, T_min=T_min, T_sim=T_sim)


if __name__ == "__main__":
    import time
    t0 = time.time()
    r2 = solve_q2()
    print("Q2: T=%.4f  theta=%.2f v=%.2f t_r=%.2f dt=%.2f  (%.0fs)"
          % (r2['T'], r2['theta'], r2['v'], r2['t_r'], r2['dt'], time.time() - t0))
    t0 = time.time()
    r3 = solve_q3()
    print("Q3: T=%.4f  (%.0fs)" % (r3['T'], time.time() - t0))
    for det, td in r3['bombs']:
        print("   起爆点", np.round(det, 1), " t_d=%.2f" % td)

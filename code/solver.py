# -*- coding: utf-8 -*-
"""
solver.py —— 全局优化求解器

思路：直接在"视线"上参数化起爆点，避免盲搜细线状目标区域。

单弹问题变量 (t_los, s, dz, v)：
  t_los : 参考时刻（导弹在该时刻的视线经过起爆点附近）
  s     : 起爆点在视线段 [导弹(t_los), C] 上的比例位置 (0~1)
  dz    : 起爆点相对视线点的竖直偏移 (m)
  v     : 无人机速度 (70~140 m/s)

起爆点 D = (1-s)*P_missile(t_los) + s*C + (0,0,dz)。
由 D 与无人机初始位置反解 (theta, v, t_drop, delta)，用罚函数保证可行性。
"""
import numpy as np
from scipy.optimize import differential_evolution, minimize
import core


def los_point(missile, t_los, s):
    """视线 [导弹(t_los), C] 上比例 s 处的点。"""
    P = core.missile_pos(missile, float(t_los))
    return (1.0 - s) * P + s * core.CENTER


def recover_params(uav, D, v, t_det):
    """由起爆点 D、速度 v、起爆时刻 t_det 反解 (theta, t_drop, delta)。"""
    U0 = core.UAVS[uav]
    z0 = U0[2]
    delta = np.sqrt(max(z0 - D[2], 0.0) / (0.5 * core.G))
    theta = np.degrees(np.arctan2(D[1] - U0[1], D[0] - U0[0])) % 360.0
    t_drop = t_det - delta
    return theta, t_drop, delta


def optimize_single(uav, missile, seed=42, verbose=False):
    """优化单架无人机投 1 弹对单导弹的遮蔽，返回结果字典。

    变量 (t_los, s, dz, offset)：
      t_los  : 视线参考时刻（云团在该时刻位于视线上）
      s      : 起爆点在视线段 [导弹(t_los), C] 上的比例 (0~1)
      dz     : 起爆点相对视线点的竖直偏移 (m)
      offset : 起爆提前量，t_det = t_los − offset ∈ [t_los−20, t_los]，
               保证云团在 t_los 时刻存活。
    由起爆点 D 反解 (theta, v, t_drop, delta)，速度用罚函数约束。
    """
    T = core.missile_impact_time(missile)
    U0 = core.UAVS[uav]
    z0 = U0[2]
    bounds = [(0.0, T), (0.0, 1.0), (-80.0, 80.0), (0.0, core.CLOUD_LIFE)]

    def make_obj(dt):
        def objective(x):
            t_los, s, dz, offset = x
            P = core.missile_pos(missile, float(t_los))
            D = (1.0 - s) * P + s * core.CENTER + np.array([0.0, 0.0, dz])
            delta2 = (z0 - D[2]) / (0.5 * core.G)
            if delta2 < 0.0:                      # 起爆点高于无人机高度，不可行
                return 1e6 + (D[2] - z0) * 100.0
            delta = np.sqrt(delta2)
            t_det = t_los - offset
            if t_det <= 0.0:                      # 起爆时刻必须为正
                return 1e6 - t_det * 100.0
            t_drop = t_det - delta
            r = np.hypot(D[0] - U0[0], D[1] - U0[1])
            v = r / t_det
            pen = 0.0
            if D[2] < 0.0:                        # 起爆点在地下
                pen += (0.0 - D[2]) * 20.0
            if t_drop < 0.0:                      # 投放时刻为负
                pen += (0.0 - t_drop) * 20.0
            if v < core.V_MIN:
                pen += (core.V_MIN - v) * 5.0
            elif v > core.V_MAX:
                pen += (v - core.V_MAX) * 5.0
            bt = core.cloud_blocking_time(D, t_det, missile, dt=dt)
            return -bt + pen
        return objective

    # 阶段 1：粗分辨率全局
    res = differential_evolution(make_obj(0.01), bounds, seed=seed,
                                 popsize=20, maxiter=600, tol=1e-6,
                                 polish=False, init='latinhypercube',
                                 disp=False, workers=1)
    if verbose:
        print(f"  [DE] f={res.fun:.3f}")
    x = res.x

    # 阶段 2：高分辨率 Nelder-Mead 精修
    fine = make_obj(1e-4)
    polish = minimize(fine, x, method='Nelder-Mead',
                      options={'xatol': 1e-3, 'fatol': 1e-5, 'maxiter': 6000})
    if polish.fun < fine(x):
        x = polish.x

    t_los, s, dz, offset = x
    P = core.missile_pos(missile, float(t_los))
    D = (1.0 - s) * P + s * core.CENTER + np.array([0.0, 0.0, dz])
    t_det = t_los - offset
    r = np.hypot(D[0] - U0[0], D[1] - U0[1])
    v = r / t_det
    theta, t_drop, delta = recover_params(uav, D, v, t_det)

    bombs = [{'uav': uav, 'theta': theta, 'v': v, 't_drop': t_drop, 'delta': delta}]
    intervals, total = core.shielding_intervals(bombs, missile, dt=1e-4)
    return {
        'uav': uav, 'missile': missile,
        'theta': float(theta), 'v': float(v),
        't_drop': float(t_drop), 'delta': float(delta),
        'D': core.bomb_pos(uav, theta, v, t_drop, delta),
        't_det': float(t_drop + delta),
        'intervals': intervals, 'total': total,
    }


def _build_bombs_from_los(x, bomb_uavs, missile, need_gap=True):
    """把 LOS 锚定变量解码为 bombs 列表，返回 (bombs, penalty)。

    x 结构: 每弹 (t_los, s, dz, offset) 共 4 项，依次拼接。
    同无人机多弹共享航向/速度，用 v_h 一致性罚函数耦合；need_gap 时
    同机相邻投放间隔 >=1 s。
    """
    n = len(bomb_uavs)
    T = core.missile_impact_time(missile)
    groups = {}
    for i, u in enumerate(bomb_uavs):
        groups.setdefault(u, []).append(i)

    Ds, t_dets, vhs = [], [], []
    for i in range(n):
        t_los, s, dz, offset = x[4 * i:4 * i + 4]
        P = core.missile_pos(missile, float(t_los))
        D = (1.0 - s) * P + s * core.CENTER + np.array([0.0, 0.0, float(dz)])
        t_det = float(t_los - offset)
        U0 = core.UAVS[bomb_uavs[i]]
        vh = (D[:2] - U0[:2]) / t_det
        Ds.append(D)
        t_dets.append(t_det)
        vhs.append(vh)
    Ds = np.array(Ds)
    vhs = np.array(vhs)

    pen = 0.0
    # 分散激励：参考时刻过近的弹会产生重叠遮蔽，惩罚之，促使遮蔽时间分散
    t_los_vals = [x[4 * i] for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            gap = abs(t_los_vals[i] - t_los_vals[j])
            if gap < 3.0:
                pen += (3.0 - gap) * 5.0
    bombs = []
    for u, idxs in groups.items():
        z0 = core.UAVS[u][2]
        vhg = vhs[idxs]
        vbar = vhg.mean(axis=0)
        pen += float(np.abs(vhg - vbar).sum()) * 1.0       # 速度一致性
        v = float(np.linalg.norm(vbar))
        if v < core.V_MIN:
            pen += (core.V_MIN - v) * 5.0
        elif v > core.V_MAX:
            pen += (v - core.V_MAX) * 5.0
        theta = float(np.degrees(np.arctan2(vbar[1], vbar[0])) % 360.0)

        # 每弹：delta / t_drop / 起爆点高度
        row = []
        for i in idxs:
            delta2 = (z0 - Ds[i][2]) / (0.5 * core.G)
            if delta2 < 0.0:
                return [], 1e6 + (Ds[i][2] - z0) * 100.0
            delta = float(np.sqrt(delta2))
            t_drop = float(t_dets[i] - delta)
            pen_row = 0.0
            if t_drop < 0.0:
                pen_row += (0.0 - t_drop) * 20.0
            if Ds[i][2] < 0.0:
                pen_row += (0.0 - Ds[i][2]) * 20.0
            pen += pen_row
            row.append({'uav': u, 'theta': theta, 'v': v,
                        't_drop': t_drop, 'delta': delta})
        # 同机投放间隔 >= 1s
        if need_gap and len(row) > 1:
            ts = sorted(b['t_drop'] for b in row)
            for a, b in zip(ts[:-1], ts[1:]):
                if b - a < core.DROP_GAP:
                    pen += (core.DROP_GAP - (b - a)) * 30.0
        bombs.extend(row)
    return bombs, pen


def _ray_segment_intersect(U0, theta_deg, A, B):
    """射线 U0 + λ(cosθ,sinθ) 与线段 AB(取 xy) 的交点。返回 (λ, s, D_xy) 或 None。"""
    th = np.radians(theta_deg)
    d = np.array([np.cos(th), np.sin(th)])
    AB = B[:2] - A[:2]
    M = np.array([[d[0], -AB[0]], [d[1], -AB[1]]])
    rhs = A[:2] - U0[:2]
    det = M[0, 0] * M[1, 1] - M[0, 1] * M[1, 0]
    if abs(det) < 1e-12:
        return None
    lam, s = np.linalg.solve(M, rhs)
    if lam < 0.0 or s < -1e-6 or s > 1.0 + 1e-6:
        return None
    D_xy = U0[:2] + lam * d
    return lam, s, D_xy


def optimize_multi_path(uav, n_bombs, missile, seed=42, verbose=False):
    """单架无人机沿一条直线路径投 n_bombs 弹（Q3）。

    变量 (theta, v, 每弹 t_los, dz)：
      theta, v       : 无人机航向与速度（共享）
      t_los_i, dz_i  : 第 i 弹的视线参考时刻与竖直偏移
    起爆点 D_xy 由射线(theta)与视线段[导弹(t_los_i), C]的交点唯一确定，
    故同路径一致性自动满足，且各弹 t_los 独立自然促成时间分散。
    """
    T = core.missile_impact_time(missile)
    U0 = core.UAVS[uav]
    z0 = U0[2]
    bounds = [(0.0, 360.0), (core.V_MIN, core.V_MAX)]
    for _ in range(n_bombs):
        bounds += [(0.0, T), (-80.0, 80.0)]

    def make_obj(dt):
        def objective(x):
            theta, v = x[0], x[1]
            bombs = []
            pen = 0.0
            t_dets = []
            for i in range(n_bombs):
                t_los, dz = x[2 + 2 * i], x[3 + 2 * i]
                P = core.missile_pos(missile, float(t_los))
                hit = _ray_segment_intersect(U0, theta, P, core.CENTER)
                if hit is None:
                    return 1e6 + 100.0 * (0.5 - t_los / T) ** 2
                lam, s, D_xy = hit
                t_det = lam / v
                # 云团须在 t_los 时刻存活：t_det ∈ [t_los-20, t_los]
                if t_det > t_los:
                    pen += (t_det - t_los) * 10.0
                if t_det < t_los - core.CLOUD_LIFE:
                    pen += (t_los - core.CLOUD_LIFE - t_det) * 10.0
                D_z = (1.0 - s) * P[2] + s * core.CENTER[2] + dz
                delta2 = (z0 - D_z) / (0.5 * core.G)
                if delta2 < 0.0:
                    return 1e6 + (D_z - z0) * 100.0
                delta = float(np.sqrt(delta2))
                t_drop = t_det - delta
                if t_drop < 0.0:
                    pen += (0.0 - t_drop) * 20.0
                if D_z < 0.0:
                    pen += (0.0 - D_z) * 20.0
                bombs.append({'uav': uav, 'theta': float(theta), 'v': float(v),
                              't_drop': float(t_drop), 'delta': delta})
                t_dets.append(t_drop)
            # 同机投放间隔 >= 1s
            ts = sorted(t_dets)
            for a, b in zip(ts[:-1], ts[1:]):
                if b - a < core.DROP_GAP:
                    pen += (core.DROP_GAP - (b - a)) * 30.0
            bt = core.shielding_time(bombs, missile, dt=dt)
            return -bt + pen
        return objective

    res = differential_evolution(make_obj(0.02), bounds, seed=seed,
                                 popsize=20, maxiter=400, tol=1e-4,
                                 polish=False, init='latinhypercube',
                                 disp=False, workers=1)
    if verbose:
        print(f"  [DE] f={res.fun:.3f}")
    x = res.x
    theta, v = x[0], x[1]
    bombs = []
    for i in range(n_bombs):
        t_los, dz = x[2 + 2 * i], x[3 + 2 * i]
        P = core.missile_pos(missile, float(t_los))
        lam, s, D_xy = _ray_segment_intersect(U0, theta, P, core.CENTER)
        t_det = lam / v
        D_z = (1.0 - s) * P[2] + s * core.CENTER[2] + dz
        delta = float(np.sqrt((z0 - D_z) / (0.5 * core.G)))
        t_drop = t_det - delta
        bombs.append({'uav': uav, 'theta': float(theta), 'v': float(v),
                      't_drop': float(t_drop), 'delta': delta})
    intervals, total = core.shielding_intervals(bombs, missile, dt=1e-4)
    return {'bombs': bombs, 'intervals': intervals, 'total': total}


def optimize_multi(bomb_uavs, missile, seed=42, verbose=False):
    """多弹对单导弹的优化。bomb_uavs: 每枚弹对应的无人机名列表。

    返回 {bombs, intervals, total}。用于 Q3（FY1×3）、Q4（FY1/FY2/FY3）。
    """
    n = len(bomb_uavs)
    T = core.missile_impact_time(missile)
    bounds = []
    for _ in range(n):
        bounds += [(0.0, T), (0.0, 1.0), (-80.0, 80.0), (0.0, core.CLOUD_LIFE)]

    def make_obj(dt):
        def objective(x):
            bombs, pen = _build_bombs_from_los(x, bomb_uavs, missile, need_gap=True)
            if not bombs:
                return pen
            bt = core.shielding_time(bombs, missile, dt=dt)
            return -bt + pen
        return objective

    res = differential_evolution(make_obj(0.02), bounds, seed=seed,
                                 popsize=20, maxiter=300, tol=1e-4,
                                 polish=False, init='latinhypercube',
                                 disp=False, workers=1)
    if verbose:
        print(f"  [DE] f={res.fun:.3f}")
    x = res.x

    bombs, _ = _build_bombs_from_los(x, bomb_uavs, missile, need_gap=True)
    intervals, total = core.shielding_intervals(bombs, missile, dt=1e-4)
    return {'bombs': bombs, 'intervals': intervals, 'total': total}

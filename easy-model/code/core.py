# -*- coding: utf-8 -*-
"""
core.py —— 烟幕干扰弹投放策略 核心引擎

包含：常量、运动学（导弹/无人机/炸弹/云团）、遮蔽判定、有效遮蔽时长求值。

坐标系：假目标原点 O=(0,0,0)；真目标圆柱 r=7, h=10, 下底面圆心 (0,200,0)，
        视线参考点取几何中心 C=(0,200,5)。
时间：t=0 为雷达发现时刻。导弹直飞原点(假目标)，速率 300 m/s。
"""
import numpy as np

# ---------------------------------------------------------------- 常量
G = 9.8                    # 重力加速度 m/s^2
MISSILE_SPEED = 300.0      # 导弹速率 m/s
CLOUD_RADIUS = 10.0        # 云团半径 m
SINK_SPEED = 3.0           # 云团下沉速度 m/s
CLOUD_LIFE = 20.0          # 云团有效寿命 s
V_MIN, V_MAX = 70.0, 140.0 # 无人机速度范围 m/s
DROP_GAP = 1.0             # 同机相邻投放最小间隔 s

# 真目标中心（视线参考点）
CENTER = np.array([0.0, 200.0, 5.0])

# 导弹初始位置
MISSILES = {
    'M1': np.array([20000.0, 0.0, 2000.0]),
    'M2': np.array([19000.0, 600.0, 2100.0]),
    'M3': np.array([18000.0, -600.0, 1900.0]),
}

# 无人机初始位置
UAVS = {
    'FY1': np.array([17800.0, 0.0, 1800.0]),
    'FY2': np.array([12000.0, 1400.0, 1400.0]),
    'FY3': np.array([6000.0, -3000.0, 700.0]),
    'FY4': np.array([11000.0, 2000.0, 1800.0]),
    'FY5': np.array([13000.0, -2000.0, 1300.0]),
}


# ---------------------------------------------------------------- 运动学
def missile_pos(name, t):
    """导弹 name 在 t 时刻的位置。t 标量->(3,)，1D数组->(N,3)。"""
    p0 = MISSILES[name]
    u = -p0 / np.linalg.norm(p0)
    t = np.asarray(t, dtype=float)
    if t.ndim == 0:
        return p0 + MISSILE_SPEED * u * float(t)
    return p0 + MISSILE_SPEED * t[:, None] * u


def missile_impact_time(name):
    """导弹命中假目标(原点)的时刻。"""
    return np.linalg.norm(MISSILES[name]) / MISSILE_SPEED


def uav_pos(name, theta_deg, v, t):
    """无人机 name 在 t 时刻的位置（等高度，z 不变）。t 为标量。"""
    th = np.radians(theta_deg)
    u0 = UAVS[name]
    return np.array([u0[0] + v * np.cos(th) * t,
                     u0[1] + v * np.sin(th) * t,
                     u0[2]])


def delta_max(name):
    """引信延迟上界：起爆点须在空中 D_z >= 0 -> delta <= sqrt(z0/4.9)。"""
    return float(np.sqrt(UAVS[name][2] / (0.5 * G)))


def bomb_pos(name, theta_deg, v, t_drop, delta):
    """起爆点 D：投放点 + 水平初速*delta + 重力下落。"""
    th = np.radians(theta_deg)
    d = uav_pos(name, theta_deg, v, t_drop)          # 投放点
    return np.array([d[0] + v * np.cos(th) * delta,
                     d[1] + v * np.sin(th) * delta,
                     d[2] - 0.5 * G * delta * delta])


# ---------------------------------------------------------------- 遮蔽判定
def _dist_point_segment(S, A, B):
    """点 S 到线段 AB 的最短距离与垂足参数 s(clamped)。A,B,S 形状 (...,3)。"""
    v = B - A
    w = S - A
    vv = np.einsum('...i,...i->...', v, v)
    s = np.einsum('...i,...i->...', w, v) / np.where(vv > 1e-12, vv, 1.0)
    s = np.clip(s, 0.0, 1.0)
    closest = A + s[..., None] * v
    return np.linalg.norm(S - closest, axis=-1), s


def blocks(S, A, B, radius=CLOUD_RADIUS):
    """云团球(心 S, 半径 radius)是否遮挡视线段 AB (A=导弹, B=真目标中心 C)。

    判定：云团球与视线线段 AB 相交，即 S 到线段的最短距离 <= radius。
    该条件天然涵盖三种真实遮蔽：烟幕居中(0<s<1)、导弹在烟幕内(s=0)、
    目标在烟幕内(s=1)。S 为 None 表示云团不存活。
    """
    if S is None:
        return False
    d, _ = _dist_point_segment(S, A, B)
    return bool(d <= radius)


# ---------------------------------------------------------------- 有效遮蔽时长
def _indicator(bombs, missile_name, t):
    """返回 E(t) 布尔数组（t 为 1D 数组）。bombs 为 list[dict(uav,theta,v,t_drop,delta)]。"""
    t = np.asarray(t, dtype=float)
    n = len(t)
    A = missile_pos(missile_name, t)          # (N,3)
    B = CENTER
    E = np.zeros(n, dtype=bool)
    for b in bombs:
        th = np.radians(b['theta'])
        D = bomb_pos(b['uav'], b['theta'], b['v'], b['t_drop'], b['delta'])
        t_det = b['t_drop'] + b['delta']
        alive = (t >= t_det) & (t <= t_det + CLOUD_LIFE)
        if not alive.any():
            continue
        S = np.empty((n, 3))
        S[:, 0] = D[0]
        S[:, 1] = D[1]
        S[:, 2] = D[2] - SINK_SPEED * (t - t_det)
        d, _ = _dist_point_segment(S, A, B)
        blocked = d <= CLOUD_RADIUS
        E |= (alive & blocked)
    return E


def shielding_time(bombs, missile_name, dt=0.01):
    """有效遮蔽时长（秒）。bombs 为 list[dict(uav,theta,v,t_drop,delta)]。

    dt：时间分辨率。优化时用 0.01（快），最终答案用 1e-4（精确）。
    """
    T = missile_impact_time(missile_name)
    t = np.arange(0.0, T + dt, dt)
    if len(t) == 0:
        return 0.0
    E = _indicator(bombs, missile_name, t)
    return float(E.sum()) * dt


def cloud_blocking_time(D, t_det, missile_name, dt=0.01, radius=CLOUD_RADIUS):
    """单个云团（起爆点 D, 起爆时刻 t_det）对导弹的遮蔽时长（二值判定）。"""
    T = missile_impact_time(missile_name)
    t_start = float(t_det)
    t_end = min(t_det + CLOUD_LIFE, T)
    if t_end <= t_start:
        return 0.0
    t = np.arange(t_start, t_end + dt, dt)
    A = missile_pos(missile_name, t)
    S = np.empty((len(t), 3))
    S[:, 0] = D[0]
    S[:, 1] = D[1]
    S[:, 2] = D[2] - SINK_SPEED * (t - t_det)
    d, _ = _dist_point_segment(S, A, CENTER)
    return float((d <= radius).sum()) * dt


def cloud_surrogate(D, t_det, missile_name, radius, dt=0.01):
    """接近度积分 ∫ max(0, radius − dist(S(t), 视线)) dt。

    用于引导全局优化：radius 取较大值(如 30~80 m)时，该目标在云团靠近视线
    的较宽区域内非零且平滑，给差分进化提供可攀爬的梯度；随后逐步缩小
    radius 逼近真实二值遮蔽目标(radius=10)。
    """
    T = missile_impact_time(missile_name)
    t_start = float(t_det)
    t_end = min(t_det + CLOUD_LIFE, T)
    if t_end <= t_start:
        return 0.0
    t = np.arange(t_start, t_end + dt, dt)
    A = missile_pos(missile_name, t)
    S = np.empty((len(t), 3))
    S[:, 0] = D[0]
    S[:, 1] = D[1]
    S[:, 2] = D[2] - SINK_SPEED * (t - t_det)
    d, _ = _dist_point_segment(S, A, CENTER)
    return float(np.maximum(0.0, radius - d).sum()) * dt


def closeness_array(bombs, missile_name, radius, t):
    """某导弹在时间网格 t 上的'接近度'数组 c(t)。

    c(t) = max_bombs max(0, radius − dist(云团, 视线))，命中时刻后取 radius
    （导弹已命中则不再构成约束）。用于 Q5 联合调度的平滑代理目标。
    """
    t = np.asarray(t, dtype=float)
    n = len(t)
    A = missile_pos(missile_name, t)
    c = np.zeros(n)
    for b in bombs:
        D = bomb_pos(b['uav'], b['theta'], b['v'], b['t_drop'], b['delta'])
        t_det = b['t_drop'] + b['delta']
        alive = (t >= t_det) & (t <= t_det + CLOUD_LIFE)
        if not alive.any():
            continue
        S = np.empty((n, 3))
        S[:, 0] = D[0]
        S[:, 1] = D[1]
        S[:, 2] = D[2] - SINK_SPEED * (t - t_det)
        d, _ = _dist_point_segment(S, A, CENTER)
        close = np.where(alive, np.maximum(0.0, radius - d), 0.0)
        c = np.maximum(c, close)
    Tm = missile_impact_time(missile_name)
    c = np.where(t < Tm, c, radius)
    return c


def simultaneous_shielding_time(bombs_by_missile, dt=1e-4):
    """Q5 目标 (a)：真目标同时被所有(仍飞行)导弹遮蔽的总时长。

    bombs_by_missile: dict{导弹名 -> 该导弹的炸弹列表}。
    G(t) = ∧_m (E_m(t) ∨ t>=T_m)，即各导弹命中前其视线必须都被挡。
    """
    missiles = list(bombs_by_missile.keys())
    T_end = max(missile_impact_time(m) for m in missiles)
    t = np.arange(0.0, T_end + dt, dt)
    G = np.ones(len(t), dtype=bool)
    for m in missiles:
        Tm = missile_impact_time(m)
        E = _indicator(bombs_by_missile[m], m, t)
        airborne = t < Tm
        G &= (E | ~airborne)
    return float(G.sum()) * dt


def shielding_intervals(bombs, missile_name, dt=1e-4):
    """返回遮蔽区间的起止时刻列表 [(t0,t1), ...] 与总时长。

    用于 Q1 及最终结果报告（精确到 dt）。
    """
    T = missile_impact_time(missile_name)
    t = np.arange(0.0, T + dt, dt)
    E = _indicator(bombs, missile_name, t)
    intervals = []
    n = len(t)
    i = 0
    while i < n:
        if E[i]:
            j = i
            while j + 1 < n and E[j + 1]:
                j += 1
            intervals.append((float(t[i]), float(t[min(j + 1, n - 1)])))
            i = j + 1
        else:
            i += 1
    total = sum(b - a for a, b in intervals)
    return intervals, total

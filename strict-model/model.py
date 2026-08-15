"""CUMCM 2025A 烟幕干扰弹投放策略 —— 核心物理模型与几何判定。

物理与几何均按《建模思路.md》实现：
- 导弹匀速直线飞向原点；无人机等高度直线飞行；烟幕弹平抛；烟幕成球下沉 20 s。
- "完全遮蔽"：导弹看不到真目标圆柱上任何一点（多球合力，见定理 A/B）。
"""
import numpy as np

# ---- 常数 ----
G = 9.8
R_SMOKE = 10.0
V_MISSILE = 300.0
SINK = 3.0          # 烟幕下沉速度 m/s
DURATION = 20.0     # 烟幕有效期 s

# ---- 真目标圆柱 ----
T_CX, T_CY, T_R, T_H = 0.0, 200.0, 7.0, 10.0

# ---- 导弹初始位置 ----
MISSILES = {
    1: np.array([20000.0, 0.0, 2000.0]),
    2: np.array([19000.0, 600.0, 2100.0]),
    3: np.array([18000.0, -600.0, 1900.0]),
}

# ---- 无人机初始位置 ----
DRONES = {
    1: np.array([17800.0, 0.0, 1800.0]),
    2: np.array([12000.0, 1400.0, 1400.0]),
    3: np.array([6000.0, -3000.0, 700.0]),
    4: np.array([11000.0, 2000.0, 1800.0]),
    5: np.array([13000.0, -2000.0, 1300.0]),
}


# ======================================================================
# 运动学
# ======================================================================

def missile_dir(k):
    """导弹 k 的单位飞行方向（指向原点）。"""
    P = MISSILES[k]
    return -P / np.linalg.norm(P)


def missile_pos(k, t):
    """导弹 k 在时刻 t 的位置；t 可为标量或数组，返回 (..., 3)。"""
    u = missile_dir(k)
    return MISSILES[k] + V_MISSILE * np.asarray(t, dtype=float)[..., None] * u


def hit_time(k):
    """导弹 k 命中假目标（原点）的时刻。"""
    return np.linalg.norm(MISSILES[k]) / V_MISSILE


def drone_pos(i, theta, v, t):
    """无人机 i 在时刻 t 的位置（等高度直线）。theta 单位度，以 +x 为 0 逆时针为正。"""
    x0, y0, z0 = DRONES[i]
    th = np.radians(theta)
    return np.array([x0 + v * np.cos(th) * t, y0 + v * np.sin(th) * t, z0])


def detonation(i, theta, v, t_r, dt):
    """无人机 i 在 t_r 投放、引信延迟 dt 后的 (起爆点, 起爆时刻)。"""
    x0, y0, z0 = DRONES[i]
    th = np.radians(theta)
    t_d = t_r + dt
    x = x0 + v * np.cos(th) * t_d
    y = y0 + v * np.sin(th) * t_d
    z = z0 - 0.5 * G * dt ** 2
    return np.array([x, y, z]), t_d


def smoke_centers(det, t_d, t):
    """烟幕球心在时刻 t 的位置（球心以 3 m/s 下沉）；t 可为数组，返回 (..., 3)。"""
    t = np.asarray(t, dtype=float)
    return det[None, :] + np.array([0.0, 0.0, -SINK]) * (t - t_d)[..., None]


# ======================================================================
# 几何判定
# ======================================================================

def seg_dist(C, A, B):
    """点 C 到线段 [A,B] 的距离；A、B、C 广播到 (..., 3)。"""
    v = B - A
    w = C - A
    c2 = np.sum(v * v, axis=-1)
    c1 = np.sum(w * v, axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        tt = np.clip(c1 / c2, 0.0, 1.0)
    tt = np.where(c2 <= 0.0, 0.0, tt)      # 线段退化为点
    closest = A + tt[..., None] * v
    return np.sqrt(np.sum((C - closest) ** 2, axis=-1))


def cylinder_circles(n=48):
    """定理 A：单球判定只需上下两个圆环。返回 (2n, 3) 采样点。"""
    ang = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    pts = []
    for z in (0.0, T_H):
        for a in ang:
            pts.append([T_R * np.cos(a), T_CY + T_R * np.sin(a), z])
    return np.array(pts)


def cylinder_surface(n=48, k=4, with_disks=True):
    """定理 B：多球判定采样表面（侧壁 k+1 个高度 + 上下圆盘内部）。返回 (N, 3)。"""
    pts = []
    for zi in np.linspace(0.0, T_H, k + 1):
        for a in np.linspace(0.0, 2.0 * np.pi, n, endpoint=False):
            pts.append([T_R * np.cos(a), T_CY + T_R * np.sin(a), zi])
    if with_disks:
        for z in (0.0, T_H):
            for a in np.linspace(0.0, 2.0 * np.pi, max(8, n // 2), endpoint=False):
                pts.append([0.5 * T_R * np.cos(a), T_CY + 0.5 * T_R * np.sin(a), z])
            pts.append([0.0, T_CY, z])
    return np.array(pts)


# ======================================================================
# 遮蔽时长
# ======================================================================

def shield_time(k, bombs, sample_pts, dt=0.01, t_end=None):
    """导弹 k 被 bombs 完全遮蔽的总时长（多球合力，取并集）。

    bombs: list of (起爆点(3,), 起爆时刻 t_d)。
    sample_pts: (N, 3) 圆柱表面采样点。
    返回 float（遮蔽总时长，秒）。
    """
    if t_end is None:
        t_end = hit_time(k)
    t = np.arange(0.0, t_end + dt, dt)
    M = missile_pos(k, t)                 # (N_t, 3)
    n_t = len(t)
    blocked_all = np.ones(n_t, dtype=bool)
    for Q in sample_pts:
        blocked_q = np.zeros(n_t, dtype=bool)
        for det, td in bombs:
            active = (t >= td - 1e-9) & (t <= td + DURATION + 1e-9)
            if not active.any():
                continue
            C = smoke_centers(det, td, t)
            d = seg_dist(C, M, Q)
            blocked_q |= active & (d <= R_SMOKE)
        blocked_all &= blocked_q
    return dt * float(blocked_all.sum())

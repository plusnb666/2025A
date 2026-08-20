function [X0, t_star, feasible] = predict_intercept(j, mi, S)
% 预测拦截点策略 (MD §7.2): 求烟幕弹轨迹与导弹 mi 轨迹重合的最小可行时刻
%   重合条件 P_s,j(t) = P_m,mi(t) 分解为解析方程组:
%     x_fy(0) + v*cos(theta)*t = x_m(t)
%     y_fy(0) + v*sin(theta)*t = y_m(t)
%     z_fy(0) - g*(s*t)^2/2     = z_m(t),   s = (t-td)/t 为落体时间比例
%   解: s = (1/t)*sqrt(2*(z_fy0-z_m(t))/g),  v = (1/t)*|P_m(1:2)-P_fy(1:2)|
%   可行条件: z_fy0 >= z_m(t), 0<=s<=1, vmin<=v<=vmax
%   遍历时间取最小可行 t (导弹逼近目标后视线角速度增大, 越早拦截越有利)
%   返回 X0 = [theta, v, td, tb] (初始起爆延迟取 0)
X0 = [0 0 0 0];  t_star = 0;  feasible = false;
P0 = S.Pfy0(j,:);
for t = (0.01 : 0.01 : S.t_hit(mi))   % 行向量迭代, 逐标量时间 t
    Pm = missile_pos(mi, t, S);
    dz = P0(3) - Pm(3);
    if dz < 0, continue; end
    s = (1/t) * sqrt(2*dz / S.g);
    if s < 0 || s > 1, continue; end
    v = (1/t) * norm(Pm(1:2) - P0(1:2));
    if v < S.vmin || v > S.vmax, continue; end
    theta = atan2(Pm(2)-P0(2), Pm(1)-P0(1));
    td     = t*(1 - s);              % s = (t - td)/t
    X0     = [theta, v, td, td];
    t_star = t;  feasible = true;
    return;                          % 最小可行时刻即最优
end
end

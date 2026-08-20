function solve_Q2(quick)
% 问题2: 单机单弹最优投放策略 (MD §5)
%   决策变量 X = [theta, v, td, tb] (4维), 最大化对 M1 的遮蔽时长
%   求解: 预测拦截点解析解作种子 + 差分进化全局寻优
%   论文未单列本问; 公开基准参考值约 4.724 s (非论文数据)
S = params();
if nargin < 1, quick = false; end
if quick
    S.scan_dt = 0.1;   % 快速自检用粗扫步长
end
P2 = sample_target('single', S);            % 单弹: 两底圆周 300 点

obj  = @(x) eval_clouds(1, clouds_of(x, S), P2, S);
cons = @(x) cons_Q2(x, S);
LB = [0, S.vmin, 0, 0];
UB = [2*pi, S.vmax, 60, 80];

% ---- 预测拦截点解析初始化 (MD §7.2) ----
[X0, t_star, ok] = predict_intercept(1, 1, S);
seeds = [];
if ok
    jit = [0.05, 5, 1, 1] .* randn(10, 4);
    seeds = [X0; min(max(X0 + jit, LB), UB)];
    fprintf('预测拦截点初始解: t*=%.2f s, theta=%.1f°, v=%.2f m/s, td=%.2f s\n', ...
        t_star, mod(rad2deg(X0(1)), 360), X0(2), X0(3));
end

if quick
    opt = struct('NP', 20, 'Gmax', 30, 'F', 0.5, 'CR', 0.9, 'seed', seeds);
else
    opt = struct('NP', 100, 'Gmax', 500, 'F', 0.5, 'CR', 0.9, 'seed', seeds);
end
tic;
[Xbest, fbest] = de_optimize(obj, cons, LB, UB, opt);
el = toc;

[Rd, Rb] = bomb_pts(1, Xbest(1), Xbest(2), Xbest(3), Xbest(4), S);
fprintf('最优策略: 航向 theta = %.2f°, 速度 v = %.2f m/s\n', ...
    mod(rad2deg(Xbest(1)), 360), Xbest(2));
fprintf('          投放时刻 td = %.4f s, 起爆时刻 tb = %.4f s\n', Xbest(3), Xbest(4));
fprintf('          投放点 (%.4f, %.4f, %.4f) m\n', Rd);
fprintf('          起爆点 (%.4f, %.4f, %.4f) m\n', Rb);
fprintf('最优有效遮蔽时长 T = %.4f s (耗时 %.1f s)\n', fbest, el);
end

function clouds = clouds_of(x, S)
[~, Rb] = bomb_pts(1, x(1), x(2), x(3), x(4), S);
clouds = [x(4), Rb];
end

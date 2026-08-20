function solve_Q3(quick)
% 问题3: 单机连续投放 3 枚弹 (MD §6, 论文 §2)
%   决策变量 X = [theta, v, td1, td2, td3, tb1, tb2, tb3] (8维)
%   目标: 3 枚云团遮蔽区间的并集测度 (多弹判定: 5层x50点)
%   算法: 差分进化 NP=100, Gmax=500, F=0.5, CR=0.9, 可行性规则
%   论文参考结果: 总遮蔽时长 6.403 s (耗时约 26.5 min)
S = params();
if nargin < 1, quick = false; end
if quick
    S.scan_dt = 0.1;   % 快速自检用粗扫步长
end
P2 = sample_target('multi', S);             % 多弹: 5 层 x 50 点

obj  = @(x) eval_clouds(1, clouds_of(x, S), P2, S);
cons = @(x) cons_Q3(x, S);
LB = [0, S.vmin, 0, 0, 0, 0, 0, 0];
UB = [2*pi, S.vmax, 60, 60, 60, 80, 80, 80];

% 引导种子: 链式投弹模式(首弹立即投放立即起爆, 后续弹按1s间隔) + 预测拦截点解
% 目的: 帮助 DE 脱离"仅首弹有效 2.556 s"的适应度平台 (DE 规格本身不变, 仍为论文 Step1-5)
seeds = [];
for th = [0, atan(0.119), pi, -pi/2, pi/2]
    for v = [70, 100, 116.8, 140]
        seeds = [seeds; th, v, 0, 1, 2, 0, 1, 2]; %#ok<AGROW>
    end
end
[X0, ~, ok] = predict_intercept(1, 1, S);
if ok
    seeds = [seeds; X0(1), X0(2), X0(3), X0(3)+1, X0(3)+2, ...
                     X0(4), X0(4)+1, X0(4)+2]; %#ok<AGROW>
end
if quick
    opt = struct('NP', 20, 'Gmax', 30, 'F', 0.5, 'CR', 0.9, 'seed', seeds);
else
    opt = struct('NP', 100, 'Gmax', 500, 'F', 0.5, 'CR', 0.9, 'seed', seeds);
end
tic;
[Xbest, fbest] = de_optimize(obj, cons, LB, UB, opt);
el = toc;

% ---- 结果输出 (与论文表1 格式一致) ----
fprintf('最优策略: 航向 theta = %.2f°, 速度 v = %.2f m/s\n', ...
    rad2deg(Xbest(1)), Xbest(2));
fprintf('总有效遮蔽时长 T = %.4f s (耗时 %.1f s)\n', fbest, el);
fprintf('表1  烟幕干扰弹投放与效能数据\n');
fprintf('%-8s %12s %12s %12s %12s %12s %12s %12s %12s %12s\n', ...
    '弹序号','投放X','投放Y','投放Z','起爆X','起爆Y','起爆Z','生效时间','失效时间','有效时长');
rows = zeros(3,10);
data = cell(3,12);
for k = 1:3
    [Rd, Rb] = bomb_pts(1, Xbest(1), Xbest(2), Xbest(2+k), Xbest(5+k), S);
    clouds_k = [Xbest(5+k), Rb];
    [~, Ivk] = eval_clouds(1, clouds_k, P2, S);   % 该弹自身的遮蔽区间
    if isempty(Ivk), Ivk = [0 0]; end
    tk = union_measure(Ivk);
    rows(k,:) = [k, Rd, Rb, Ivk(1,1), Ivk(end,2), tk];
    fprintf('%-8d %12.4f %12.4f %12.4f %12.4f %12.4f %12.4f %12.5f %12.5f %12.5f\n', rows(k,:));
    if k == 1   % 无人机运动方向/速度只填一次 (DOCX 输出格式)
        data(k,:) = {rad2deg(Xbest(1)), Xbest(2), k, Rd(1), Rd(2), Rd(3), ...
                     Rb(1), Rb(2), Rb(3), Ivk(1,1), Ivk(end,2), tk};
    else
        data(k,:) = {NaN, NaN, k, Rd(1), Rd(2), Rd(3), ...
                     Rb(1), Rb(2), Rb(3), Ivk(1,1), Ivk(end,2), tk};
    end
end
export_table('result1.xlsx', ...
    {'无人机运动方向','无人机运动速度','干扰弹编号', ...
     '投放点x','投放点y','投放点z','起爆点x','起爆点y','起爆点z', ...
     '生效时间','失效时间','有效干扰时长'}, data);
end

function clouds = clouds_of(x, S)
clouds = zeros(3,4);
for k = 1:3
    [~, Rb] = bomb_pts(1, x(1), x(2), x(2+k), x(5+k), S);
    clouds(k,:) = [x(5+k), Rb];
end
end

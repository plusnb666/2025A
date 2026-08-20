function solve_Q4(quick)
% 问题4: 3 架无人机各投 1 枚弹协同干扰 M1 (MD §7, 论文 §3)
%   决策变量: 每机 X_j = [theta_j, v_j, td_j, tb_j], 共 12 维
%   目标: 3 枚云团遮蔽区间的并集测度 (多弹判定: 5层x50点)
%   求解: ① 预测拦截点解析初始解 (论文 §3.2, 作为候选之一)
%         ② 全局粗网格: 对 (θ,v,td,Δtb) 离散遍历 (几何分析: 云团应位于导弹与
%            真目标连线附近, 故 θ,v,td 全域扫描; 论文自身报告的最优解亦非拦截点
%            邻域内的点, 见 MD 附录B 说明)
%         ③ 以②最优为锚点的邻域精细网格 (MD §7.2 "X0 邻域离散化遍历"精化)
%   论文参考结果: 总遮蔽时长 11.126 s (耗时约 550 s)
S = params();
if nargin < 1, quick = false; end
if quick
    S.scan_dt = 0.1;   % 快速自检用粗扫步长
end
P2 = sample_target('multi', S);             % 多弹: 5 层 x 50 点

if quick   % 快速网格 / 完整网格
    thg0 = 0:deg2rad(45):deg2rad(315);  vg0 = 70:35:140;  tg0 = 0:5:60;   dg0 = 0:3:6;
    thg  = -6:3:6;  vg = -9:4.5:9;  tg = -1.5:0.75:1.5;  dg = 0:1.5:6;
else
    thg0 = 0:deg2rad(20):deg2rad(340); vg0 = 70:10:140;  tg0 = 0:2:60;  dg0 = 0:1.5:6;
    thg  = -10:2:10; vg = -10:2.5:10;  tg = -2:0.4:2;    dg = 0:0.75:6;
end

% ---- ① 各机预测拦截点解析初始解 ----
X = zeros(3,4);
for j = 1:3
    [X(j,:), t_star, ok] = predict_intercept(j, 1, S);
    if ~ok, error('无人机 FY%d 无可行拦截点', j); end
    fprintf('FY%d 拦截点初始解: t*=%.2f s, theta=%.1f°, v=%.2f m/s, td=%.2f s\n', ...
        j, t_star, mod(rad2deg(X(j,1)), 360), X(j,2), X(j,3));
end

% ---- ②③ 逐机: 全局粗网格 + 邻域精细网格 ----
for j = 1:3
    best  = X(j,:);
    fbest = eval_clouds(1, all_clouds(X, best, j, S), P2, S);
    for th = thg0                       % ② 全局粗网格
        for v = vg0
            for td = tg0
                for dtb = dg0
                    xj = [th, v, td, td + dtb];
                    [T, ~] = eval_clouds(1, all_clouds(X, xj, j, S), P2, S);
                    if T > fbest, fbest = T;  best = xj; end
                end
            end
        end
    end
    anchor = best;                      % ③ 以②最优为锚点的邻域精细网格
    for dth = thg
        th = anchor(1) + deg2rad(dth);
        for dv = vg
            v = min(max(anchor(2) + dv, S.vmin), S.vmax);
            for dtd = tg
                td = max(anchor(3) + dtd, 0);
                for dtb = dg
                    xj = [th, v, td, td + dtb];
                    [T, ~] = eval_clouds(1, all_clouds(X, xj, j, S), P2, S);
                    if T > fbest, fbest = T;  best = xj; end
                end
            end
        end
    end
    X(j,:) = best;
    fprintf('FY%d 优化后: theta=%.4f°, v=%.4f m/s, td=%.4f s, tb=%.4f s\n', ...
        j, mod(rad2deg(best(1)), 360), best(2), best(3), best(4));
end

% ---- 结果输出 (与论文表2 格式一致) ----
[~, Iv] = eval_clouds(1, all_clouds(X, X(1,:), 1, S), P2, S);
Ttotal = union_measure(Iv);
fprintf('总有效遮蔽时长 T = %.4f s\n', Ttotal);
fprintf('表2  烟幕干扰弹投放策略\n');
fprintf('%-6s %10s %10s %12s %12s %12s %12s %12s %12s %12s %12s %12s\n', ...
    '无人机','航向(°)','速度(m/s)','投放X','投放Y','投放Z','起爆X','起爆Y','起爆Z','生效时间','失效时间','有效时长');
rows = zeros(3,12);
data = cell(3,12);
for j = 1:3
    [Rd, Rb] = bomb_pts(j, X(j,1), X(j,2), X(j,3), X(j,4), S);
    clouds_j = [X(j,4), Rb];
    [~, Ivj] = eval_clouds(1, clouds_j, P2, S);   % 该机云团自身的遮蔽区间
    if isempty(Ivj), Ivj = [0 0]; end
    tj = union_measure(Ivj);
    rows(j,:) = [j, mod(rad2deg(X(j,1)), 360), X(j,2), Rd, Rb, Ivj(1,1), Ivj(end,2), tj];
    fprintf('%-6d %10.4f %10.4f %12.4f %12.4f %12.4f %12.4f %12.4f %12.4f %12.5f %12.5f %12.5f\n', rows(j,:));
    data(j,:) = {j, mod(rad2deg(X(j,1)), 360), X(j,2), Rd(1), Rd(2), Rd(3), ...
                 Rb(1), Rb(2), Rb(3), Ivj(1,1), Ivj(end,2), tj};
end
export_table('result2.xlsx', ...
    {'无人机编号','方向(°)','速度(m/s)', ...
     '投放点x','投放点y','投放点z','起爆点x','起爆点y','起爆点z', ...
     '生效时间','失效时间','有效干扰时长'}, data);
end

function cc = all_clouds(X, xj, j, S)
% 3 架无人机的云团集合 (第 j 架用候选 xj, 其余用当前最优)
cc = zeros(3,4);
for q = 1:3
    xq = X(q,:);
    if q == j, xq = xj; end
    [~, Rb] = bomb_pts(q, xq(1), xq(2), xq(3), xq(4), S);
    cc(q,:) = [xq(4), Rb];
end
end

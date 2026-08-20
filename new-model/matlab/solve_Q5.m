function solve_Q5(quick)
% 问题5: 5 架无人机 × 至多 3 枚弹 × 3 枚导弹 (MD §8, 论文 §4)
%   分层优化:
%     第一层  任务分配 —— 理论最大遮蔽效益 c_ij + max-min 整数线性规划 (y∈{0,3})
%     第二层  子问题独立求解 —— 各机首弹: 预测拦截点初始解 + 全局粗网格 + 邻域精细
%             网格 (同问题4); 后续两枚弹: 按 1 s 间隔投放并对各自起爆时刻局部网格微调
%   目标: T_total = |T1∩T2∩T3| (三枚导弹遮蔽时间集合的交集测度, 式(19))
%   论文参考: 分配 FY1,FY5→M1; FY2,FY4→M2; FY3→M3, T=21.077 s (约146.5 s)
S = params();
if nargin < 1, quick = false; end
if quick
    S.scan_dt = 0.1;   % 快速自检用粗扫步长
end
P2 = sample_target('multi', S);             % 多弹: 5 层 x 50 点

% ================= 第一层: 基于效益评估的任务分配 =================
Pref = S.Pm0 - repmat([5000 0 0], 3, 1);    % 投放参考点: 导弹初始位置沿 x 负向偏移 5 km
c = zeros(3,5);
for i = 1:3
    for j = 1:5
        c(i,j) = max(0, 20 - norm(S.Pfy0(j,:) - Pref(i,:)) / 140);   % 式(17)
    end
end
fprintf('理论最大遮蔽效益 c_ij 矩阵 (行=导弹, 列=无人机):\n');
disp(c);

% max-min ILP (式(18)): 枚举整机分配 (每机专一导弹, 每导弹至少 1 机, y=3)
best1 = -inf;  best2 = -inf;  best_asgn = zeros(1,5);
for code = 0 : 3^5-1
    cc = code;  asgn = zeros(1,5);
    for j = 1:5
        asgn(j) = mod(cc,3) + 1;  cc = floor(cc/3);
    end
    if numel(unique(asgn)) < 3, continue; end
    score = zeros(3,1);
    for i = 1:3
        score(i) = 3 * sum(c(i, asgn == i));
    end
    s1 = min(score);  s2 = sum(score);      % max-min 主目标, 总效益次目标
    if s1 > best1 || (s1 == best1 && s2 > best2)
        best1 = s1;  best2 = s2;  best_asgn = asgn;
    end
end
for i = 1:3
    fprintf('任务分配: 导弹 M%d <- 无人机 %s\n', i, sprintf('FY%d ', find(best_asgn == i)));
end
fprintf('(注: 论文报告的分配 FY1,FY5→M1; FY2,FY4→M2; FY3→M3, 见 MD 附录B 说明)\n');

% ================= 第二层: 子问题独立求解 =================
if quick   % 网格设置 (快速/完整)
    thg0 = 0:deg2rad(45):deg2rad(315);  vg0 = 70:35:140;  tg0 = 0:5:60;   dg0 = 0:3:6;
    thg  = -6:3:6;  vg = -9:4.5:9;  tg = -1.5:0.75:1.5;  dg = 0:1.5:6;
else
    thg0 = 0:deg2rad(30):deg2rad(330);  vg0 = 70:14:140;  tg0 = 0:3:60;  dg0 = 0:1.5:6;
    thg  = -10:2:10; vg = -10:2.5:10;   tg = -2:0.4:2;   dg = 0:0.75:6;
end
X  = zeros(5,4);               % 每机飞行参数 [theta, v, td1, tb1]
td = zeros(5,3);  tb = zeros(5,3);
Rd = zeros(5,3,3);  Rb = zeros(5,3,3);   dur = zeros(5,3);

% 阶段 A: 各机预测拦截点初始化 (首弹), 后续弹按 1 s 间隔
for i = 1:3
    js = find(best_asgn == i);
    for j = js
        [X(j,:), t_star, ok] = predict_intercept(j, i, S);
        if ~ok, error('FY%d 对 M%d 无可行拦截点', j, i); end
        fprintf('FY%d→M%d 拦截点初始解: t*=%.2f s, theta=%.1f°, v=%.2f m/s\n', ...
            j, i, t_star, mod(rad2deg(X(j,1)), 360), X(j,2));
        td(j,1) = X(j,3);  tb(j,1) = X(j,4);
        td(j,2) = td(j,1) + S.dt_min;  tb(j,2) = td(j,2);
        td(j,3) = td(j,1) + 2*S.dt_min; tb(j,3) = td(j,3);
    end
end

% 阶段 B: 各机首弹两阶段网格优化 (目标: 该导弹全部云团的并集时长)
for i = 1:3
    js = find(best_asgn == i);
    for j = js
        best  = X(j,:);
        fbest = eval_clouds(i, clouds_for_missile(i, best_asgn, X, td, tb, S), P2, S);
        for th = thg0                   % 全局粗网格
            for v = vg0
                for t1 = tg0
                    for dtb = dg0
                        td(j,1) = t1;  tb(j,1) = t1 + dtb;  X(j,1:2) = [th, v];
                        [T, ~] = eval_clouds(i, clouds_for_missile(i, best_asgn, X, td, tb, S), P2, S);
                        if T > fbest, fbest = T;  best = [th, v, t1, t1+dtb]; end
                    end
                end
            end
        end
        anchor = best;                  % 邻域精细网格
        for dth = thg
            th = anchor(1) + deg2rad(dth);
            for dv = vg
                v = min(max(anchor(2) + dv, S.vmin), S.vmax);
                for dtd = tg
                    t1 = max(anchor(3) + dtd, 0);
                    for dtb = dg
                        td(j,1) = t1;  tb(j,1) = t1 + dtb;  X(j,1:2) = [th, v];
                        [T, ~] = eval_clouds(i, clouds_for_missile(i, best_asgn, X, td, tb, S), P2, S);
                        if T > fbest, fbest = T;  best = [th, v, t1, t1+dtb]; end
                    end
                end
            end
        end
        X(j,:) = best;  td(j,1) = best(3);  tb(j,1) = best(4);
        % 后续弹按 1 s 间隔锚定在优化后的首弹投放时刻上
        td(j,2) = td(j,1) + S.dt_min;     tb(j,2) = td(j,2);
        td(j,3) = td(j,1) + 2*S.dt_min;   tb(j,3) = td(j,3);
        fprintf('FY%d→M%d 首弹优化: theta=%.2f°, v=%.2f m/s, td=%.2f s, tb=%.2f s\n', ...
            j, i, mod(rad2deg(best(1)), 360), best(2), best(3), best(4));
    end
end

% 阶段 C: 第 2、3 枚弹起爆时刻局部网格微调 (投放时刻保持 1 s 间隔)
for i = 1:3
    js = find(best_asgn == i);
    for j = js
        for k = 2:3
            tdk = td(j,k);  best_tb = tdk;  fbest = -inf;
            for dtb = dg
                tb(j,k) = tdk + dtb;
                [T, ~] = eval_clouds(i, clouds_for_missile(i, best_asgn, X, td, tb, S), P2, S);
                if T > fbest, fbest = T;  best_tb = tb(j,k); end
            end
            tb(j,k) = best_tb;
        end
    end
end

% ================= 汇总: 交集测度 + 逐弹效能 =================
Iv_m = cell(3,1);
for i = 1:3
    [~, Iv_m{i}] = eval_clouds(i, clouds_for_missile(i, best_asgn, X, td, tb, S), P2, S);
end
Ttotal = intersect_measure(Iv_m{1}, Iv_m{2}, Iv_m{3});

for i = 1:3
    js = find(best_asgn == i);
    for j = js
        for k = 1:3
            [Rdk, Rbk] = bomb_pts(j, X(j,1), X(j,2), td(j,k), tb(j,k), S);
            Rd(j,k,:) = Rdk;  Rb(j,k,:) = Rbk;
            [~, Ivk] = eval_clouds(i, [tb(j,k), Rbk], P2, S);   % 该弹自身遮蔽区间
            dur(j,k) = union_measure(Ivk);
        end
    end
end

fprintf('总有效遮蔽时长 T_total = |T1∩T2∩T3| = %.4f s\n', Ttotal);
fprintf('(注: 论文表3 的 21.077 s 实为各弹有效干扰时长之和 %.4f s, 非交集测度, 见 MD 附录B 第7条)\n', sum(dur(:)));
fprintf('表3  烟幕干扰弹投放策略\n');
fprintf('%-6s %8s %8s %6s %10s %10s %10s %10s %10s %10s %10s %8s\n', ...
    '无人机','方向(°)','速度','弹号','投放X','投放Y','投放Z','起爆X','起爆Y','起爆Z','有效时长','干扰导弹');
data = cell(15,12);
r = 0;
for j = 1:5
    for k = 1:3
        r = r + 1;
        fprintf('%-6s %8.2f %8.2f %6d %10.2f %10.2f %10.2f %10.2f %10.2f %10.2f %10.2f %8s\n', ...
            sprintf('FY%d', j), mod(rad2deg(X(j,1)), 360), X(j,2), k, ...
            Rd(j,k,1), Rd(j,k,2), Rd(j,k,3), Rb(j,k,1), Rb(j,k,2), Rb(j,k,3), ...
            dur(j,k), sprintf('M%d', best_asgn(j)));
        data(r,:) = {sprintf('FY%d', j), mod(rad2deg(X(j,1)), 360), X(j,2), k, ...
            Rd(j,k,1), Rd(j,k,2), Rd(j,k,3), Rb(j,k,1), Rb(j,k,2), Rb(j,k,3), ...
            dur(j,k), sprintf('M%d', best_asgn(j))};
    end
end
export_table('result3.xlsx', ...
    {'无人机编号','方向(°)','速度(m/s)','干扰弹编号', ...
     '投放点x','投放点y','投放点z','起爆点x','起爆点y','起爆点z', ...
     '有效干扰时长','干扰导弹编号'}, data);
end

function cc = clouds_for_missile(i, asgn, X, td, tb, S)
% 干扰导弹 i 的全部无人机云团集合 [t_b, P_bx, P_by, P_bz]
js = find(asgn == i);
cc = zeros(numel(js)*3, 4);
m = 0;
for j = js
    for k = 1:3
        [~, Rbk] = bomb_pts(j, X(j,1), X(j,2), td(j,k), tb(j,k), S);
        m = m + 1;
        cc(m,:) = [tb(j,k), Rbk];
    end
end
cc = cc(1:m, :);
end

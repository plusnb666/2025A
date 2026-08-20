% dump_q5_intervals.m
% 从 Q5 完整模式解 (run_all_full_log.txt) 反算各弹遮蔽区间并转储, 供画图脚本使用
% 解参数: 首弹 (theta, v, td1, tb1) 取自日志"首弹优化"行;
%         第2/3枚弹 td = td1 + (k-1)*1s, tb 由起爆点 z 反推 (Δz = 0.5*g*Δt^2);
% 输出 q5_intervals.txt: 逐弹区间 + 各导弹遮蔽区间并集
S = params();  S.scan_dt = 0.05;
P2 = sample_target('multi', S);

theta = [178, 280, 82, 0, 118];     % FY1..FY5 航向(deg)
v     = [107, 89, 117, 70, 122];    % 速度
td1   = [0, 8.2, 23.6, 24, 13.4];   % 首弹投放时刻
tb1   = [3.0, 11.2, 26.6, 28.5, 14.9];   % 首弹起爆时刻
z0    = S.Pfy0(:,3)';               % 各机飞行高度
% 各弹起爆点 z (表3, run_all_full_log.txt)
zb = [1755.90 1800.00 1800.00;      % FY1
      1355.90 1375.19 1400.00;      % FY2
       655.90  688.98  700.00;      % FY3
      1700.78 1800.00 1800.00;      % FY4
      1288.97 1300.00 1300.00];     % FY5
asgn = [1, 2, 1, 1, 3];             % FY1..FY5 -> 干扰的导弹

td = zeros(5,3);  tb = zeros(5,3);
for j = 1:5
    td(j,1) = td1(j);  tb(j,1) = tb1(j);
    for k = 2:3
        td(j,k) = td1(j) + (k-1)*S.dt_min;
        dtau = sqrt(max((z0(j) - zb(j,k)) / (0.5*S.g), 0));
        tb(j,k) = td(j,k) + dtau;
    end
end

fid = fopen('q5_intervals.txt', 'w', 'n', 'UTF-8');
% 逐弹遮蔽区间 (该弹自身云团 vs 其干扰的导弹)
for j = 1:5
    for k = 1:3
        [~, Rbk] = bomb_pts(j, deg2rad(theta(j)), v(j), td(j,k), tb(j,k), S);
        [~, Iv] = eval_clouds(asgn(j), [tb(j,k), Rbk], P2, S);
        fprintf(fid, 'bomb %d %d %.6f %.6f %d', j, k, td(j,k), tb(j,k), size(Iv,1));
        for q = 1:size(Iv,1)
            fprintf(fid, ' %.6f %.6f', Iv(q,1), Iv(q,2));
        end
        fprintf(fid, ' %.6f\n', union_measure(Iv));
    end
end
% 各导弹遮蔽区间并集
for i = 1:3
    js = find(asgn == i);
    cc = zeros(0,4);
    for j = js
        for k = 1:3
            [~, Rbk] = bomb_pts(j, deg2rad(theta(j)), v(j), td(j,k), tb(j,k), S);
            cc = [cc; tb(j,k), Rbk]; %#ok<AGROW>
        end
    end
    [~, Iv] = eval_clouds(i, cc, P2, S);
    fprintf(fid, 'missile %d %d', i, size(Iv,1));
    for q = 1:size(Iv,1)
        fprintf(fid, ' %.6f %.6f', Iv(q,1), Iv(q,2));
    end
    fprintf(fid, '\n');
end
fclose(fid);
fprintf('dump done -> q5_intervals.txt\n');

%% 烟幕干扰弹投放场景 三维图 (等价于 easy-model/code/visualize.py 的 fig1)
%  绘制：3 条导弹轨迹、5 架无人机、真目标(圆柱)、假目标(原点)、
%        Q4 最优云团(球) 及其投放轨迹。
%  Q4 参数来自 easy-model 求解(seed=42)，如需更新可重新求解后替换 Q4 数组。
clear; clc; close all;

%% ---- 常量 ----
g = 9.8;              % 重力加速度 m/s^2

% 颜色（RGB 三元组，与 Python 版一致）
cBlue   = [42 120 214]/255;    % #2a78d6
cOrange = [235 104 52]/255;    % #eb6834
cAqua   = [27 175 122]/255;    % #1baf7a
cRed    = [227 73 72]/255;     % #e34948
cGray   = [82 81 78]/255;      % #52514e

% 导弹初始位置 (x,y,z)，速率 300 m/s，方向指向假目标原点
Missiles.M1 = [20000,    0, 2000];
Missiles.M2 = [19000,  600, 2100];
Missiles.M3 = [18000, -600, 1900];
missileColor = struct('M1', cBlue, 'M2', cOrange, 'M3', cAqua);

% 无人机初始位置 (x,y,z)
UAVs.FY1 = [17800,    0, 1800];
UAVs.FY2 = [12000, 1400, 1400];
UAVs.FY3 = [ 6000,-3000,  700];
UAVs.FY4 = [11000, 2000, 1800];
UAVs.FY5 = [13000,-2000, 1300];

%% ---- 图 ----
figure('Color','w','Position',[80 80 960 760]);
hold on; grid on; box on;

% 导弹轨迹（起点 -> 假目标原点）
mn = fieldnames(Missiles);
for k = 1:numel(mn)
    p0 = Missiles.(mn{k});
    plot3([p0(1) 0], [p0(2) 0], [p0(3) 0], '-', ...
        'Color', missileColor.(mn{k}), 'LineWidth', 1.6);
    text(p0(1), p0(2), p0(3)+150, [' ' mn{k}], ...
        'Color', missileColor.(mn{k}), 'FontWeight','bold');
end

% 无人机初始位置
un = fieldnames(UAVs);
for k = 1:numel(un)
    p = UAVs.(un{k});
    scatter3(p(1), p(2), p(3), 28, 'filled', ...
        'MarkerFaceColor','w', 'MarkerEdgeColor', cGray, 'LineWidth', 1.1);
    text(p(1), p(2), p(3)+140, un{k}, 'Color', cGray);
end

% 真目标：竖直圆柱（半径 7，高 10，底面圆心 (0,200,0)）
[Xc, Yc, Zc] = cylinder(7, 48);
Zc = Zc * 10;                                   % 高度 10
surf(Xc, Yc + 200, Zc, 'FaceColor', cRed, 'FaceAlpha', 0.6, 'EdgeColor','none');
text(0, 200, 70, '真目标', 'Color', cRed, 'FontWeight','bold');

% 假目标：原点
scatter3(0, 0, 0, 60, 'x', 'MarkerEdgeColor','k', 'LineWidth', 2);
text(0, -350, 100, '假目标(原点)', 'Color','k');

%% ---- Q4 最优云团 + 投放轨迹 ----
% 每行: [航向(°), 速度(m/s), 投放时刻(s), 引信延迟(s)]，对应 FY1/FY2/FY3
Q4 = [178.49, 110.98,  0.039,  3.123;    % FY1
      245.41, 139.55,  3.402,  7.172;    % FY2
      151.91, 121.61, 44.088, 11.790];   % FY3
uavOfQ4 = {'FY1','FY2','FY3'};

for k = 1:size(Q4,1)
    theta = Q4(k,1); v = Q4(k,2); td = Q4(k,3); dl = Q4(k,4);
    u0 = UAVs.(uavOfQ4{k});
    th = deg2rad(theta);

    % 投放点、起爆点（炸弹平抛 + 重力下落）
    drop = [u0(1) + v*cos(th)*td,  u0(2) + v*sin(th)*td,  u0(3)];
    det  = [drop(1) + v*cos(th)*dl, drop(2) + v*sin(th)*dl, drop(3) - 0.5*g*dl^2];

    % 投放轨迹（虚线）
    plot3([drop(1) det(1)], [drop(2) det(2)], [drop(3) det(3)], '--', ...
        'Color', cBlue, 'LineWidth', 0.9);

    % 云团球（半径 10）
    [Sx, Sy, Sz] = sphere(24);
    surf(Sx*10 + det(1), Sy*10 + det(2), Sz*10 + det(3), ...
        'FaceColor', cBlue, 'FaceAlpha', 0.28, 'EdgeColor','none');
end

%% ---- 坐标与视角 ----
xlabel('x (m)'); ylabel('y (m)'); zlabel('z (m)');
xlim([-500 20500]); ylim([-3300 2300]); zlim([0 2400]);
title('烟幕干扰弹投放场景三维图（蓝球为 Q4 最优云团，虚线为投放轨迹）');

% 压缩 x 轴使导弹下降轨迹更清晰（等价 Python 版 box_aspect=[1.4 0.6 0.7]）
% 想恢复真实比例可改为 pbaspect auto 或注释掉本行
pbaspect([1.4 0.6 0.7]);
view([-37.5 20]);    % 视角（方位角, 仰角），可自行调整

hold off;

%% ---- 自动保存图片 ----
% 输出到 ../figures/fig1_几何三维图_matlab.png（300 dpi）
outdir = fullfile(fileparts(mfilename('fullpath')), '..', 'figures');
if ~exist(outdir, 'dir'); mkdir(outdir); end
outfile = fullfile(outdir, 'fig1_几何三维图_matlab.png');
if exist('exportgraphics', 'builtin') || exist('exportgraphics', 'file')
    exportgraphics(gcf, outfile, 'Resolution', 300);   % MATLAB R2020a+
else
    print(gcf, outfile, '-dpng', '-r300');             % 旧版 MATLAB 回退
end
fprintf('图片已保存: %s\n', outfile);

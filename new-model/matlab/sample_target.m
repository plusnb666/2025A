function P2 = sample_target(mode, S)
% 真目标圆柱体的离散采样点 (MD §3.4/§3.5)
%   mode = 'single': 上下底面圆周各 n_single 点 —— 单弹判定(命题1降维, 仅查两底圆周)
%   mode = 'multi' : 5 个高度层圆周各 n_multi 点 —— 多弹判定(遮挡体非凸, 沿高度分层)
% 返回 Nx3 采样点矩阵
if strcmp(mode, 'single')
    n = S.n_single;
    phi = linspace(0, 2*pi, n+1)';  phi(end) = [];
    xy = [S.cr*cos(phi), S.cy + S.cr*sin(phi)];      % 圆周点 (x, y)
    P2 = [xy, S.zc(1)*ones(n,1);
          xy, S.zc(2)*ones(n,1)];                    % 下底面 z=0 + 上底面 z=10
else
    n = S.n_multi;
    phi = linspace(0, 2*pi, n+1)';  phi(end) = [];
    xy = [S.cr*cos(phi), S.cy + S.cr*sin(phi)];
    P2 = zeros(n*numel(S.z_layers), 3);
    for l = 1:numel(S.z_layers)
        P2((l-1)*n+1 : l*n, :) = [xy, S.z_layers(l)*ones(n,1)];
    end
end
end

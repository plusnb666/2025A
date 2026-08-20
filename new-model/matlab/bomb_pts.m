function [Rd, Rb] = bomb_pts(j, theta, v, td, tb, S)
% 无人机 j 一枚烟幕弹的投放点 Rd 与起爆点 Rb (MD 式(3)(4)代入)
%   投放点: 无人机 td 时刻位置
%   起爆点: 水平方向继承无人机速度, 竖直方向自由落体 (dtau = tb - td 为起爆延迟)
Rd   = uav_pos(j, theta, v, td, S);
dtau = tb - td;
d    = [cos(theta), sin(theta), 0];
Rb   = Rd + [v*dtau*d(1), v*dtau*d(2), -0.5*S.g*dtau^2];
end

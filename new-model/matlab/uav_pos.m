function Pfy = uav_pos(j, theta, v, t, S)
% 无人机 j (航向 theta, 速度 v) 在 t 时刻的位置 (MD 式(2))
%   theta: 航向角(rad, 与x轴正方向夹角, 逆时针为正);  t: 标量或列向量
d = [cos(theta), sin(theta), 0];
Pfy = S.Pfy0(j,:) + v * t(:) * d;
end

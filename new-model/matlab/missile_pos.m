function Pm = missile_pos(i, t, S)
% 导弹 i 在 t 时刻的位置向量 (MD 式(1))
%   i: 导弹编号 1..3;  t: 标量或列向量
%   P_{m,i}(t) = P_{m,i}(0) + v_m * t * n_{m,i},  n_{m,i} = -P_{m,i}(0)/|P_{m,i}(0)|
P0 = S.Pm0(i,:);
n  = -P0 / norm(P0);
Pm = P0 + S.v_m * t(:) * n;
end

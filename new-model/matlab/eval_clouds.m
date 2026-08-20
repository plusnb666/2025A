function [T, Iv] = eval_clouds(mi, clouds, P2, S)
% 导弹 mi 在给定云团集合下的总有效遮蔽时长 (各弹遮蔽区间的并集测度)
%   clouds: Kx4 = [t_b, P_bx, P_by, P_bz] (允许空)
%   P2: 目标采样点矩阵;  T: 总遮蔽时长;  Iv: K2x2 遮蔽区间列表
if isempty(clouds)
    T = 0;  Iv = zeros(0,2);  return;
end
t0  = max(0, min(clouds(:,1)));                     % 最早起爆时刻起才可能有云团
t1  = min(max(clouds(:,1)) + S.Ts, S.t_hit(mi));    % 云团全部失效或导弹抵达原点
fun = @(t) bool_cover(t, missile_pos(mi, t, S), clouds, P2, S);
Iv  = cover_intervals(fun, t0, t1, S);
T   = union_measure(Iv);
end

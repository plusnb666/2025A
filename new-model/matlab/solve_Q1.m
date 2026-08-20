function solve_Q1(quick)
% 问题1: 单机单弹固定参数的确定性计算 (MD §4, 论文 §5 数值算例基础场景)
%   已知: FY1 速度 v=120 m/s, 航向指向假目标(theta=180°),
%         投放时刻 td=1.5 s, 起爆时刻 tb=5.1 s, 干扰导弹 M1
%   方法: 运动学解析计算 + 凸性化简遮蔽判定(上下底圆周各300点) + 二分法
%   论文参考结果: 遮蔽区间 [8.056445, 9.448088] s, 总时长 1.391643 s
S = params();
if nargin < 1, quick = false; end %#ok<NASGU>
theta = pi;  v = 120;  td = 1.5;  tb = 5.1;

[Rd, Rb] = bomb_pts(1, theta, v, td, tb, S);
fprintf('投放点: (%.4f, %.4f, %.4f) m\n', Rd);
fprintf('起爆点: (%.4f, %.4f, %.4f) m\n', Rb);

P2 = sample_target('single', S);            % 上下底面圆周各 300 采样点
clouds = [tb, Rb];
t0 = max(0, tb);  t1 = min(tb + S.Ts, S.t_hit(1));
fun = @(t) bool_cover(t, missile_pos(1, t, S), clouds, P2, S);
Iv = cover_intervals(fun, t0, t1, S);
T  = union_measure(Iv);

fprintf('遮蔽区间:\n');
for q = 1:size(Iv,1)
    fprintf('  [%.6f, %.6f]   时长 %.6f s\n', Iv(q,1), Iv(q,2), Iv(q,2)-Iv(q,1));
end
fprintf('总有效遮蔽时长 T = %.6f s\n', T);
end

function Phi = cons_Q2(x, S)
% 问题2 约束违反度 Φ(X) = Σ max{0, g_j} + 1(Z_smoke < 10)  (MD §5.1)
%   x = [theta, v, td, tb] (单机单弹)
Phi = max(0, S.vmin - x(2)) + max(0, x(2) - S.vmax);   % 速度约束
Phi = Phi + max(0, x(3) - x(4));                        % 时序: tb >= td
dtau = x(4) - x(3);
zb   = S.Pfy0(1,3) - 0.5*S.g*dtau^2;                    % 起爆高度
Phi  = Phi + (zb < 10);                                 % 烟幕高度约束 Z_smoke >= 10
end

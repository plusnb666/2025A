function Phi = cons_Q3(x, S)
% 问题3 约束违反度 Φ(X) = Σ max{0, g_j} + Σ 1(Z_smoke,k < 10)  (MD §6.1/§6.2)
%   x = [theta, v, td1, td2, td3, tb1, tb2, tb3] (单机 3 弹)
Phi = max(0, S.vmin - x(2)) + max(0, x(2) - S.vmax);   % 无人机性能约束
for k = 1:3
    td = x(2+k);  tb = x(5+k);
    Phi = Phi + max(0, td - tb);                        % 时序: tb,k >= td,k
    dtau = tb - td;
    zb   = S.Pfy0(1,3) - 0.5*S.g*dtau^2;                % 起爆高度
    Phi  = Phi + (zb < 10);                             % 烟幕高度约束 Z_smoke,k >= 10
end
Phi = Phi + max(0, x(3) + S.dt_min - x(4)) ...          % 投放间隔 >= 1 s
          + max(0, x(4) + S.dt_min - x(5));
end

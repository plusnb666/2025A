function hit = seg_sphere(P1, P2, C, r)
% 线段-球相交解析判定 (MD §3.2, 论文式(7)判别式形式)
%   P1: 1x3 导弹位置;  P2: Nx3 目标采样点;  C: 1x3 球心;  r: 半径
%   视线线段参数化 P(s) = P1 + s(P2-P1), s∈[0,1]
%   相交 <=> 二次方程 a*s^2 + b*s + c = 0 有实根且 {s1,s2}∩[0,1]≠∅
%   返回 Nx1 逻辑向量
d = P2 - P1;                 % Nx3, d = P2 - P1
m = P1 - C;                  % 1x3, m = P1 - C
a = sum(d.^2, 2);            % Nx1, a = |d|^2 > 0 (导弹与目标不重合)
b = 2 * (d * m');            % Nx1, b = 2 m·d
c = sum(m.^2) - r^2;         % 标量, c = |m|^2 - r^2
Delta = b.^2 - 4*a.*c;       % 判别式
hit = false(size(a));
ok  = Delta >= 0;
sq  = sqrt(Delta(ok));
s1  = (-b(ok) - sq) ./ (2*a(ok));
s2  = (-b(ok) + sq) ./ (2*a(ok));
hit(ok) = (s1 <= 1) & (s2 >= 0);
end

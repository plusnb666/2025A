function Iv = cover_intervals(fun, t0, t1, S)
% 粗扫 + 二分法求 Bool(t)=1 的连续遮蔽区间 (MD §3.6)
%   fun: 函数句柄 fun(t) -> Bool;  搜索窗口 [t0, t1]
%   第一步: 以 scan_dt 粗扫定位区间内部点
%   第二步: 对每个 0->1 / 1->0 跳变边分别二分, 精度 eps_t
%   返回 Kx2 区间列表 [t_in, t_out] (可能为空)
ts = ((t0 - S.scan_dt) : S.scan_dt : (t1 + S.scan_dt))';
b  = false(numel(ts), 1);
for k = 1:numel(ts)
    b(k) = fun(ts(k));
end
edges = diff([false; b; false]);   % 两端补 false, 处理首尾边沿
rise  = find(edges ==  1);         % Bool 0->1 的位置(对应 b 的索引)
fall  = find(edges == -1) - 1;     % Bool 1->0 的位置
Iv = zeros(numel(rise), 2);
for q = 1:numel(rise)
    % 起点二分: fun(lo)=0, fun(hi)=1
    lo = ts(rise(q)-1);  hi = ts(rise(q));
    while hi - lo > S.eps_t
        mid = (lo + hi)/2;
        if fun(mid), hi = mid; else, lo = mid; end
    end
    t_in = hi;
    % 终点二分: fun(lo)=1, fun(hi)=0
    lo = ts(fall(q));  hi = ts(fall(q)+1);
    while hi - lo > S.eps_t
        mid = (lo + hi)/2;
        if fun(mid), lo = mid; else, hi = mid; end
    end
    t_out = lo;
    Iv(q,:) = [t_in, t_out];
end
end

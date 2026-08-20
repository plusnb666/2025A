function L = union_measure(Iv)
% 区间列表的并集测度 (总遮蔽时长 = 各遮蔽区间的并集, MD §3.6 扫描线)
%   Iv: Kx2 = [t_in, t_out];  返回并集总长
if isempty(Iv), L = 0; return; end
Iv = sortrows(Iv, 1);
L = 0;  a = Iv(1,1);  b = Iv(1,2);
for k = 2:size(Iv,1)
    if Iv(k,1) <= b
        b = max(b, Iv(k,2));          % 区间重叠, 延长
    else
        L = L + (b - a);              % 区间断开, 结算
        a = Iv(k,1);  b = Iv(k,2);
    end
end
L = L + (b - a);
end

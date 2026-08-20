function b = bool_cover(t, Pm, clouds, P2, S)
% 时刻 t 的遮蔽状态 Bool(t) (完全遮蔽准则, MD 式(5)(8)(10)(15))
%   Pm:     1x3 导弹位置
%   clouds: Kx4 = [t_b, P_bx, P_by, P_bz] 各弹起爆时刻与起爆点
%   P2:     目标采样点 (sample_target 生成)
%   有效云团: t∈[t_b, t_b+Ts], 云团中心 C = P_b - [0,0,v_sink*(t-t_b)] (式(4))
%   返回: 所有采样点视线均与至少一个有效云团相交 => true
b = false;
if isempty(clouds), return; end
mask = (t >= clouds(:,1)) & (t <= clouds(:,1) + S.Ts);
cc = clouds(mask, :);
if isempty(cc), return; end
N    = size(P2,1);
occl = false(N,1);
for k = 1:size(cc,1)
    C = cc(k,2:4) - [0 0 S.v_sink*(t - cc(k,1))];
    idx = find(~occl);                          % 只测尚未被遮蔽的点
    occl(idx) = seg_sphere(Pm, P2(idx,:), C, S.r);
    if all(occl)
        b = true; return;                       % 全部采样点已遮蔽
    end
end
% 遍历完所有有效云团仍未全部覆盖 => Bool=0
end

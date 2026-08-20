function L = intersect_measure(varargin)
% 多个区间集合交集的测度 (问题5: T_total = |T1∩T2∩T3|, MD 式(19))
%   用法: intersect_measure(Iv1, Iv2, Iv3)
%   事件扫描: 各集合先合并自身并集, 再统计所有集合同时活跃的时段
M = numel(varargin);
events = zeros(0,2);                 % [时刻, ±1]
for m = 1:M
    Iv = varargin{m};
    if isempty(Iv), L = 0; return; end
    Iv = sortrows(Iv, 1);
    merged = zeros(0,2);
    for k = 1:size(Iv,1)
        if isempty(merged) || Iv(k,1) > merged(end,2)
            merged = [merged; Iv(k,:)]; %#ok<AGROW>
        else
            merged(end,2) = max(merged(end,2), Iv(k,2));
        end
    end
    events = [events;  merged(:,1)   ones(size(merged,1),1);
                       merged(:,2)  -ones(size(merged,1),1)]; %#ok<AGROW>
end
events = sortrows(events, 1);
L = 0;  active = 0;  prev = 0;
for k = 1:size(events,1)
    if active == M
        L = L + events(k,1) - prev;  % 全部集合同时活跃
    end
    active = active + events(k,2);
    prev = events(k,1);
end
end

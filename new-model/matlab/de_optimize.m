function [Xbest, fbest] = de_optimize(obj, cons, LB, UB, opt)
% 差分进化算法 (MD §6.2 完整规格, 论文 §2.2)
%   最大化 obj(X);  cons(X) 为约束违反度 Φ>=0 (0 表示可行)
%   opt 字段: NP 种群规模, Gmax 最大迭代, F 缩放因子, CR 交叉概率,
%             seed 可选 NsxD 种子个体矩阵 (如预测拦截点解析解)
%   Step1 拒绝采样初始化(保证初始种群可行) -> Step2 约束违反度
%   -> Step3 变异/交叉/边界截断 -> Step4 可行性规则选择 -> Step5 迭代终止
NP = opt.NP;  G = opt.Gmax;  F = opt.F;  CR = opt.CR;
D  = numel(LB);  LB = LB(:)';  UB = UB(:)';
X = zeros(NP, D);  f = zeros(NP,1);  phi = zeros(NP,1);

% ---- Step1 种群初始化(拒绝采样) ----
cnt = 0;  guard = 0;
if isfield(opt, 'seed') && ~isempty(opt.seed)
    ns = min(size(opt.seed,1), NP);      % 种子数量不得超过种群规模
    for s = 1:ns
        cnt = cnt + 1;
        X(cnt,:) = min(max(opt.seed(s,:), LB), UB);
        phi(cnt) = cons(X(cnt,:));  f(cnt) = obj(X(cnt,:));
    end
end
while cnt < NP && guard < 1e6
    x = LB + (UB - LB) .* rand(1, D);
    p = cons(x);
    if p == 0                     % 仅保留可行个体
        cnt = cnt + 1;  X(cnt,:) = x;  phi(cnt) = 0;  f(cnt) = obj(x);
    end
    guard = guard + 1;
end
while cnt < NP                    % 兜底: 约束过严时放宽为最小违反度个体
    x = LB + (UB - LB) .* rand(1, D);
    cnt = cnt + 1;  X(cnt,:) = x;  phi(cnt) = cons(x);  f(cnt) = obj(x);
end
fbest = max(f(phi == 0));  bi = find(f == fbest & phi == 0, 1);
Xbest = X(bi,:);

% ---- 进化主循环 ----
for g = 1:G
    for i = 1:NP
        % Step3a 变异: 随机选 3 个互不相同且不同于 i 的索引
        idx = randperm(NP);  idx(idx == i) = [];
        V = X(idx(1),:) + F * (X(idx(2),:) - X(idx(3),:));
        % Step3b 二项式交叉 (必选维度 jrand 保证 U != X)
        jrand = randi(D);
        U = X(i,:);
        sel = (rand(1,D) <= CR) | ((1:D) == jrand);
        U(sel) = V(sel);
        % Step3c 边界截断
        U = max(LB, min(U, UB));
        % Step4 可行性规则选择
        fU = obj(U);  phiU = cons(U);
        if     phiU == 0 && phi(i) == 0   % 均可行: 取目标更优
            if fU > f(i), X(i,:) = U;  f(i) = fU;  phi(i) = phiU; end
        elseif phiU == 0 && phi(i) ~= 0   % 一可行一不可行: 取可行
            X(i,:) = U;  f(i) = fU;  phi(i) = phiU;
        elseif phiU ~= 0 && phi(i) ~= 0   % 均不可行: 取违反度更小
            if phiU < phi(i), X(i,:) = U;  f(i) = fU;  phi(i) = phiU; end
        end
    end
    fbest = max(f(phi == 0));  bi = find(f == fbest & phi == 0, 1);
    Xbest = X(bi,:);
end
end

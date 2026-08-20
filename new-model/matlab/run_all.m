function run_all(quick)
% 依次求解五个问题并输出论文格式表格与 result1/2/3.xlsx
%   run_all(true)  : 快速自检 (缩小种群/迭代/网格, 粗扫步长 0.1 s)
%   run_all(false) : 完整求解 (论文参数: NP=100, Gmax=500, 细网格, 粗扫步长 0.05 s)
%                   注意完整求解耗时较长 (问题3 约 20-30 min, 问题4 约 10 min,
%                   问题5 约 10-20 min, 与论文报告的 26.5 min / 550 s / 146.5 s 同量级)
if nargin < 1, quick = true; end
fprintf('========== 问题1: 单机单弹固定参数 (确定性计算) ==========\n');
solve_Q1(quick);
fprintf('\n========== 问题2: 单机单弹最优投放策略 (预测拦截点+差分进化) ==========\n');
solve_Q2(quick);
fprintf('\n========== 问题3: 单机连续投放 3 枚弹 (差分进化) ==========\n');
solve_Q3(quick);
fprintf('\n========== 问题4: 3 机各 1 弹协同 (预测拦截点+局部网格) ==========\n');
solve_Q4(quick);
fprintf('\n========== 问题5: 5 机 x 3 弹 x 3 导弹 (分层优化) ==========\n');
solve_Q5(quick);
fprintf('\n全部求解完成。\n');
end

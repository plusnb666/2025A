function export_table(fname, header, data)
% 将结果写入 xlsx 文件 (列格式与题目要求的 result1/2/3.xlsx 及论文表格一致)
%   fname: 文件名;  header: 1xN 单元格表头;  data: KxN 单元格数据
T = cell2table(data, 'VariableNames', header);
writetable(T, fname);
fprintf('已写出结果文件: %s\n', fname);
end
